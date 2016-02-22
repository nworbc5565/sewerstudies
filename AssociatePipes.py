import arcpy
from arcpy import env
import random
import HHCalculations

all_pipes =  r"Waste Water Network\Waste Water Gravity Mains" #r"Database Connections\DataConv.sde\DataConv.GISAD.Waste Water Network" #arcpy.GetParameterAsText(0) # r"Waste Water Network\Waste Water Gravity Mains" #
#study_pipes = arcpy.GetParameterAsText(1) #"StudiedWasteWaterGravMains" 
#DAs = arcpy.GetParameterAsText(2) #r"Drainage Areas\Small_Sewer_Drainage_Areas" 
project_id = arcpy.GetParameterAsText(0)

geodb = r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small_Sewer_Capacity.gdb"
study_pipes = geodb + r"\StudiedWasteWaterGravMains"
study_areas = geodb + r"\Small_Sewer_Drainage_Areas"

	
def unique_values(table, field):
	#returns list of unique values in a given field, in a table
	with arcpy.da.SearchCursor(table, [field]) as cursor:
		return sorted({row[0] for row in cursor})


def listHiddenFields(table):
	
	#return of list of hidden fields in a table
	desc = arcpy.Describe(table)
	field_info = desc.fieldInfo
	list = []
	# Use the count property to iterate through all the fields
	for index in range(0, field_info.count):
		# Print fieldinfo properties
		if field_info.getVisible(index) == "HIDDEN":
			print("Hidden Field Name: {0}".format(field_info.getFieldName(index)))
			list.append(field_info.getFieldName(index))
	
	return list
	
def matchSchemas(matchToTable, editSchemaTable):
		
	#find fields to remove from editSchemaTable (those in editSchemaTable but not in matchToTable)
	
	#get lists of field names
	hiddenFieldsNames = [] #listHiddenFields(matchToTable)
	matchFieldNames = [field.name for field in arcpy.ListFields(matchToTable)]
	editFieldsNames = [field.name for field in arcpy.ListFields(editSchemaTable)] #listFieldNames(editSchemaTable) #arcpy.ListFields(editSchemaTable)
	
	#create list of fields to drop from the edit Schema table
	dropFieldsList = []
	for fieldname in editFieldsNames:
		if not fieldname in matchFieldNames and not fieldname in hiddenFieldsNames:
			print "drop: " + fieldname
			dropFieldsList.append(fieldname)
	
	#concatentate list and drop the fields
	dropFields = ";".join(dropFieldsList)
	arcpy.DeleteField_management(in_table=editSchemaTable, drop_field=dropFields)
	
	#add necessary fields
	addFieldsList = []
	for fieldname in matchFieldNames:
		#create list of field names to be added
		if not fieldname in editFieldsNames:
			addFieldsList.append(fieldname)
			print "add: " + fieldname
	
	for field in arcpy.ListFields(matchToTable):
		#print (field.name + " " + field.type.upper())
		if field.name in addFieldsList:
			print ("adding " + field.name + " " + field.type.upper())
			arcpy.AddField_management(in_table = editSchemaTable, field_name = field.name, field_type = field.type.upper(), field_length = field.length)
	
	
	
def makeTempDAandJoinPipes(project_id):
	#unique list of StudyArea_IDs found in studied sewers 
	#tuple, and replace used to reformat the python list to an SQL friendly string
	uniqs = str(tuple(unique_values(study_pipes, "StudyArea_ID"))).replace("u", "") 

	#create random names for temporary DA and sewer layers
	DAs_temp = "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	sewers = "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

	#create temporary DA layer comprised only of DAs that do not have a Study Area ID found in the study_pipes layer (prevents duplicates)
	where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
	arcpy.MakeFeatureLayer_management(study_areas, DAs_temp, where_clause = where)
	arcpy.SpatialJoin_analysis(all_pipes, join_features = DAs_temp, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")
	
#def associatePipes(all_pipes, study_pipes, study_areas, project_id):
def associatePipes(project_id):
	#unique list of StudyArea_IDs found in studied sewers 
	#tuple, and replace used to reformat the python list to an SQL friendly string
	uniqs = str(tuple(unique_values(study_pipes, "StudyArea_ID"))).replace("u", "") 

	#create random names for temporary DA and sewer layers
	DAs_temp = "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	sewers = "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

	#create temporary DA layer comprised only of DAs that do not have a Study Area ID found in the study_pipes layer (prevents duplicates)
	where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
	print (where)
	arcpy.MakeFeatureLayer_management(study_areas, DAs_temp, where_clause = where)
	 
	#spatially join the waste water network to the temp Drainage Areas (only areas with Study Area ID not in the StudyPipes)
	arcpy.SpatialJoin_analysis(all_pipes, join_features = DAs_temp, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")


	#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
	arcpy.AddMessage("\t matching schema")
	matchSchemas(study_pipes, sewers) 
	

	#run calculations on the temporary pipe scope, apply default flags this time
	temp_pipes_cursor = arcpy.UpdateCursor(sewers)
	HHCalculations.applyDefaultFlags(temp_pipes_cursor)


	#append the sewers copied from the waste water mains layer to the studied sewers layer
	arcpy.AddMessage("\t appending sewers to Studied Pipes layer")
	arcpy.Append_management(inputs = sewers, target = study_pipes, schema_type = "NO_TEST", field_mapping = "#", subtype = "#")

	#memory clean up
	arcpy.Delete_management(sewers)
	arcpy.Delete_management(DAs_temp)
	del temp_pipes_cursor
	
	


