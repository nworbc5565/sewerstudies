import arcpy
from arcpy import env
import random
import HHCalculations

all_pipes = arcpy.GetParameterAsText(0) # r"Waste Water Network\Waste Water Gravity Mains" #
study_pipes = arcpy.GetParameterAsText(1) #"StudiedWasteWaterGravMains" 
DAs = arcpy.GetParameterAsText(2) #r"Drainage Areas\Small_Sewer_Drainage_Areas" 
project_id = arcpy.GetParameterAsText(3)

	
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
arcpy.AddField_management(in_table = sewers, field_name = "Slope_Used", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "Capacity", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "Velocity", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "TravelTime_min", field_type = "DOUBLE")
arcpy.AddField_management(in_table = sewers, field_name = "Tag", field_type = "TEXT", field_length = "50")
arcpy.AddField_management(in_table = sewers, field_name = "Hyd_Study_Notes", field_type = "TEXT", field_length = "200")


#run calculations on the temporary pipe scope, apply default flags this time
#temp_pipes_cursor = arcpy.UpdateCursor(sewers)
#HHCalculations.runCalcs(temp_pipes_cursor, applyDefaultFlags = True)


#append the sewers copied from the waste water mains layer to the studied sewers layer
arcpy.AddMessage("\t appending sewers to Studied Pipes layer")
arcpy.Append_management(inputs = sewers, target = study_pipes, schema_type = "TEST", field_mapping = "#", subtype = "#")

#memory clean up
arcpy.Delete_management(sewers)
arcpy.Delete_management(DAs_temp)
del temp_pipes_cursor
	
	


	
