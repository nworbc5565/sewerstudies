import arcpy
from arcpy import env
import random
import CodeBlocks

all_pipes = arcpy.GetParameterAsText(0)
study_pipes = arcpy.GetParameterAsText(1)
DAs = arcpy.GetParameterAsText(2)
project_id = arcpy.GetParameterAsText(3)

#read code blocks from imported file
code_block = CodeBlocks.code_block 

#set code blocks
capacity_exp = "round( xarea(  !PIPESHAPE! , !Diameter!, !Height!, !Width! ) * (1.49/getMannings(!PIPESHAPE!, !Diameter!)) * math.pow(hydR( !PIPESHAPE! , !Diameter!, !Height!, !Width! ) , 0.667) * math.pow( !Slope!/100, 0.5 ), 2)"
velocity_exp = "round( (1.49/getMannings(!PIPESHAPE!, !Diameter!)) * math.pow(hydR( !PIPESHAPE! , !Diameter!, !Height!, !Width! ) , 0.667) * math.pow( !Slope!/100, 0.5 ) , 2)"
travel_time_exp = "round( !shape.length!/ !Velocity! /60 , 2)"
min_slope_exp = "minSlope(!Slope!)"


	
def unique_values(table, field):
	#returns list of unique values in a given field, in a table
	with arcpy.da.SearchCursor(table, [field]) as cursor:
		return sorted({row[0] for row in cursor})
		
#unique list of StudyArea_IDs found in studied sewers 
#tuple, and replace used to reformat the python list to an SQL friendly string
uniqs = str(tuple(unique_values(study_pipes, "StudyArea_ID"))).replace("u", "") 

#create random names for temporary DA and sewer layers
DAs_temp = "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
sewers = "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

#create temporary DA layer comprised only of DAs that do not have a Study Area ID found in the study_pipes layer (prevents duplicates)
where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
arcpy.MakeFeatureLayer_management(DAs, DAs_temp, where_clause = where)
 
#spatially join the waste water network to the temp Drainage Areas (only areas with Study Area ID not in the StudyPipes)
arcpy.SpatialJoin_analysis(all_pipes, join_features = DAs_temp, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")


#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
#ultimately this should maybe be less hard-coded - loop through schema of each and add/delete columns accordingly
#delete unnecessary fields from drainage area
arcpy.AddMessage("\t matching schema")
arcpy.DeleteField_management(in_table=sewers, drop_field="Join_Count;TARGET_FID;Peak_Runoff;TimeOfConcentration;ConnectionPoint;Intsensity;StickerLink_1;Capacity;PipeLength;Size;InstallDate;Runoff_Coefficient;MinimumGrade")

#make joined_sewers schema match the study sewers schema
arcpy.AddField_management(in_table = sewers, field_name = "TC_Path", field_type = "TEXT", field_precision = "#", field_scale = "#", field_length = "1", field_alias = "#", field_is_nullable = "NULLABLE", field_is_required = "NON_REQUIRED", field_domain = "#")
arcpy.AddField_management(in_table = sewers, field_name = "StudySewer", field_type = "TEXT", field_length = "1")
arcpy.AddField_management(in_table = sewers, field_name = "Capacity", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "Velocity", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "TravelTime_min", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "Tag", field_type = "TEXT", field_length = "50")
arcpy.AddField_management(in_table = sewers, field_name = "Hyd_Study_Notes", field_type = "TEXT", field_length = "200")


arcpy.AddMessage("\t running hydraulic calculations")
#run calculations on temp sewers layer to populate the default slope (if null), capacity, velocity, and travel time fields
#Execute CalculateField 
arcpy.CalculateField_management(sewers, "Slope", min_slope_exp, "PYTHON_9.3", code_block)
arcpy.CalculateField_management(sewers, "Capacity", capacity_exp, "PYTHON_9.3", code_block)
arcpy.CalculateField_management(sewers, "Velocity", velocity_exp, "PYTHON_9.3", code_block)
arcpy.CalculateField_management(sewers, "TravelTime_min", travel_time_exp, "PYTHON_9.3", code_block)

#default values for symbology
arcpy.CalculateField_management(sewers, "TC_Path", "'N'", "PYTHON_9.3")
arcpy.CalculateField_management(sewers, "StudySewer", "'N'", "PYTHON_9.3")

#append the sewers copied from the waste water mains layer to the studied sewers layer
arcpy.AddMessage("\t appending sewers to Studied Pipes layer")
arcpy.Append_management(inputs = sewers, target = study_pipes, schema_type = "TEST", field_mapping = "#", subtype = "#")

#memory clean up
arcpy.Delete_management(sewers)
arcpy.Delete_management(DAs_temp)

	
	


	
