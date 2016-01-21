import arcpy
from arcpy import env
import random

all_pipes = arcpy.GetParameterAsText(0)
study_pipes = arcpy.GetParameterAsText(1)
DAs = arcpy.GetParameterAsText(2)
project_id = arcpy.GetParameterAsText(3)

#set code blocks
capacity_exp = "xarea(  !PIPESHAPE! , !Diameter!, !Height!, !Width! ) * (1.49/getMannings(!PIPESHAPE!, !Diameter!)) * math.pow(hydR( !PIPESHAPE! , !Diameter!, !Height!, !Width! ) , 0.667) * math.pow( !Slope!/100, 0.5 )"
velocity_exp = "(1.49/getMannings(!PIPESHAPE!, !Diameter!)) * math.pow(hydR( !PIPESHAPE! , !Diameter!, !Height!, !Width! ) , 0.667) * math.pow( !Slope!/100, 0.5 )"
travel_time_exp = "!shape.length!/ !Velocity! /60"
#default_N = "N" #this is stupid if i really need to do this to get things to work

code_block = """def getMannings( shape, diameter ):
  n = 0.015 #default value
  if ((shape == "CIR" or shape == "CIRCULAR") and (diameter <= 24) ):
	n = 0.015
  elif ((shape == "CIR" or shape == "CIRCULAR") and (diameter > 24) ):
	n = 0.013
  return n

def  xarea( shape, diameter, height, width ):
  
  #calculate cross sectional area of pipe 
  #supports circular, egg, and box shape
  
  if (shape == "CIR" or shape == "CIRCULAR"):
    return 3.1415 * (math.pow((diameter/12),2 ))/4
  elif (shape == "EGG" or shape == "EGG SHAPE"):
    return 0.5105* math.pow((height/12),2 )
  elif (shape == "BOX" or shape == "BOX SHAPE"):
    return height*width/144
	
def  hydR(shape, diameter, height, width ):
  
  #calculate full flow hydraulic radius of pipe 
  #supports circular, egg, and box shape
  
  if (shape == "CIR" or shape == "CIRCULAR"):
    return (diameter/12)/4
  elif (shape == "EGG" or shape == "EGG SHAPE"):
    return 0.1931* (height/12)
  elif (shape == "BOX" or shape == "BOX SHAPE"):
    return (height*width) / (2*height + 2*width) /12"""



drainage_areas_cursor = arcpy.UpdateCursor(DAs, where_clause = "Project_ID = " + project_id)

for drainage_area in drainage_areas_cursor:
	
	#select current Study Area and create where clause
	study_area_id = drainage_area.getValue("StudyArea_ID")
	where = "StudyArea_ID = '" + study_area_id + "'"
	
	#make sure pipes with this StudyArea_ID have not already been added to the StudiedWasteWaterPipes (prevent duplicates)
	pipes_already_studied = False
	check_cursor = arcpy.UpdateCursor(study_pipes, where_clause = where)
	for p in check_cursor:
		pipes_already_studied = True
		break
	if pipes_already_studied:
		arcpy.AddWarning("Skipped pipes in Study Area " + study_area_id + ".")
		continue #skip this iteration because pipes with this study area ID 
	
	#generate temp Random DA and sewer layer name 
	DA = "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6)) 
	sewers = "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	
	#Create a temporary drainage area 
	arcpy.MakeFeatureLayer_management(DAs, DA, where_clause = "StudyArea_ID = '" + study_area_id + "'")
	
	#spatially join the waster water mains to their Drainage Areas
	arcpy.SpatialJoin_analysis(all_pipes, join_features = DA, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")
	
	
	#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
		#ultimately this should maybe be less hardcoded - loop through schema of each and add/delete columns accordingly
	#delete unnecessary fields from drainage area
	arcpy.DeleteField_management(in_table=sewers, drop_field="Join_Count;TARGET_FID;Peak_Runoff;TimeOfConcentration;ConnectionPoint;Intsensity;StickerLink_1;Capacity;PipeLength;Size;InstallDate;Runoff_Coefficient")
	
	#make joined_sewers schema match the study sewers schema
	arcpy.AddField_management(in_table = sewers, field_name = "TC_Path", field_type = "TEXT", field_precision = "#", field_scale = "#", field_length = "1", field_alias = "#", field_is_nullable = "NULLABLE", field_is_required = "NON_REQUIRED", field_domain = "#")
	arcpy.AddField_management(in_table = sewers, field_name = "StudySewer", field_type = "TEXT", field_length = "1")
	arcpy.AddField_management(in_table = sewers, field_name = "Capacity", field_type = "DOUBLE")
	arcpy.AddField_management(in_table = sewers, field_name = "Velocity", field_type = "DOUBLE")
	arcpy.AddField_management(in_table = sewers, field_name = "TravelTime_min", field_type = "DOUBLE")
	arcpy.AddField_management(in_table = sewers, field_name = "Tag", field_type = "TEXT", field_length = "50")
	
	
	#run calculations on temp sewers layer to populate the capacity, velocity, and travel time fields
	# Execute CalculateField 
	arcpy.CalculateField_management(sewers, "Capacity", capacity_exp, "PYTHON_9.3", code_block)
	arcpy.CalculateField_management(sewers, "Velocity", velocity_exp, "PYTHON_9.3", code_block)
	arcpy.CalculateField_management(sewers, "TravelTime_min", travel_time_exp, "PYTHON_9.3", code_block)
	
	#default values for symbology
	arcpy.CalculateField_management(sewers, "TC_Path", "'N'", "PYTHON_9.3")
	arcpy.CalculateField_management(sewers, "StudySewer", "'N'", "PYTHON_9.3")
	
	#append the sewers copied from the waste water mains layer to the studied sewers layer
	arcpy.Append_management(inputs = sewers, target = study_pipes, schema_type = "TEST", field_mapping = "#", subtype = "#")
	
	arcpy.Delete_management(sewers)
	arcpy.Delete_management(DA)
