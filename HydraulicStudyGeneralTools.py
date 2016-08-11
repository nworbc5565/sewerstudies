import arcpy
from arcpy import env
import random
import HHCalculations
import configparser

# =================
# DATA CONNECTIONS
# =================

#grab env variables
config = configparser.ConfigParser()
config.read('config.ini')
env.workspace = geodb = config['paths']['geodb']
study_pipes = geodb + r"\StudiedWasteWaterGravMains"
study_areas = geodb + r"\Small_Sewer_Drainage_Areas"
model_sheds = geodb + r"\ModelSheds"
all_pipes =  r"Waste Water Network\Waste Water Gravity Mains"


def unique_values(table, field):
	#returns list of unique values in a given field, in a table
	with arcpy.da.SearchCursor(table, [field]) as cursor:
		return sorted({row[0] for row in cursor})


def listHiddenFields(table):

	#return of list of hidden fields in a table
	desc = arcpy.Describe(table)
	field_info = desc.fieldInfo #this crashes sometimes here
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
	hiddenFieldsNames = [] #listHiddenFields(matchToTable) #this was crashing
	matchFieldNames = [field.name for field in arcpy.ListFields(matchToTable)]
	editFieldsNames = [field.name for field in arcpy.ListFields(editSchemaTable)] #listFieldNames(editSchemaTable) #arcpy.ListFields(editSchemaTable)

	#remove subtypes
	#subtypeList = ["1", "2", "3", "4", "5", "6"]# these exist in the Dataconv

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

def removeRowsWithAttribute(table, field, value):

	where = field + " = " + value
	print where
	cursor = arcpy.UpdateCursor(table, where_clause=where)
	for row in cursor:
		print row.getValue("OBJECTID")
		cursor.deleteRow (row)


def associatePipes(project_id):

	#copy and associate pipes to the study sewer layer

	#unique list of StudyArea_IDs found in studied sewers
	#tuple, and replace used to reformat the python list to an SQL friendly string
	uniqs = str(tuple(unique_values(study_pipes, "StudyArea_ID"))).replace("u", "")

	#create random names for temporary DA and sewer layers
	DAs_temp 		= "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	sewers 			= "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	sewers2	= "sewersShedJoin_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

	#create temporary DA layer comprised only of DAs that do not have a Study Area ID found in the study_pipes layer (prevents duplicates)
	where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
	arcpy.MakeFeatureLayer_management(study_areas, DAs_temp, where_clause = where)

	#spatially join the waste water network to the temp Drainage Areas (only areas with Study Area ID not in the StudyPipes)
	arcpy.SpatialJoin_analysis(all_pipes, join_features = DAs_temp, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")

	#remove SLANTS and anything else unnecessary
	removeRowsWithAttribute(sewers, "PIPE_TYPE", "'SLANT'")

	#spatially join the new study sewers to the model shed (grab the outfall data)
	arcpy.SpatialJoin_analysis(sewers, join_features = model_sheds, out_feature_class = sewers2, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option="INTERSECT", search_radius = "")
	arcpy.AddMessage("\t Joining Model Sheds")

	#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
	arcpy.AddMessage("\t matching schema")
	matchSchemas(study_pipes, sewers2)

	#run calculations on the temporary pipe scope, apply default flags this time
	temp_pipes_cursor = arcpy.UpdateCursor(sewers2)
	HHCalculations.applyDefaultFlags(temp_pipes_cursor)

	#append the sewers copied from the waste water mains layer to the studied sewers layer
	arcpy.AddMessage("\t appending sewers to Studied Pipes layer")
	arcpy.Append_management(inputs = sewers2, target = study_pipes, schema_type = "NO_TEST", field_mapping = "#", subtype = "#")

	#memory clean up
	arcpy.Delete_management(sewers)
	arcpy.Delete_management(sewers2)
	arcpy.Delete_management(DAs_temp)
	del temp_pipes_cursor

def DAIndexExists(project_id_or_Cursor):

	#check if DA index feature class exists given a stirng or cursor object
	project_id = None
	if type(project_id_or_Cursor) is arcpy.Cursor:
		print "is cursor"
		for row in project_id_or_Cursor:
			project_id = row.getValue("Project_ID")
			break

	if type(project_id_or_Cursor) is str:
		print "is string"
		project_id = project_id_or_Cursor


	return arcpy.Exists(geodb + r"\StudyAreaIndices\DA_" + str(project_id))


def updateDAIndexRow (drainage_area):

	study_area_id = drainage_area.getValue("StudyArea_ID")
	project_id = drainage_area.getValue("Project_ID")
	indexFeatureClass = geodb + r"\StudyAreaIndices\DA_" + str(project_id)

	indexUpdateCursor = arcpy.UpdateCursor(indexFeatureClass, where_clause = "StudyArea_ID = '" + study_area_id + "'")

	#one iteration for single study area
	for da_index_row in indexUpdateCursor:

		#set row values and update row
		da_index_row.setValue("Capacity", 				drainage_area.getValue("Capacity"))
		da_index_row.setValue("TimeOfConcentration", 	drainage_area.getValue("TimeOfConcentration"))
		da_index_row.setValue("StickerLink", 			drainage_area.getValue("StickerLink"))
		da_index_row.setValue("InstallDate",			drainage_area.getValue("InstallDate"))
		da_index_row.setValue("Intsensity", 			drainage_area.getValue("Intsensity"))#NOTE -> spelling error in field name
		da_index_row.setValue("Peak_Runoff", 			drainage_area.getValue("Peak_Runoff"))
		da_index_row.setValue("Size", 					drainage_area.getValue("Size"))
		da_index_row.setValue("ReplacementSize",		drainage_area.getValue("ReplacementSize"))
		da_index_row.setValue("MinimumGrade", 			drainage_area.getValue("MinimumGrade"))
		indexUpdateCursor.updateRow(da_index_row)

	del indexUpdateCursor

def updateDAIndex (project_id):

	#check if index already exists
	indexLayer = geodb + r"\StudyAreaIndices\DA_" + project_id
	dataset = "StudyAreaIndices"
	#try:
	if arcpy.Exists(indexLayer):
		print "exists: " + indexLayer
		arcpy.Delete_management(indexLayer)




	where = "Project_ID = " + project_id
	layer_name = "DA_" + project_id

	#arcpy.env.workspace = geodb + r"\StudyAreaIndices"

	arcpy.MakeFeatureLayer_management(study_areas, indexLayer, where_clause = where)
	arcpy.FeatureClassToFeatureClass_conversion(indexLayer, geodb + "\\" + dataset, layer_name)
	arcpy.Delete_management(indexLayer)

	#except:
		#arcpy.AddWarning("Failed to update Drainage Area index feature class. Ensure this feature class is not in use elsewhere: \n\t" + indexLayer)
	#arcpy.Rename_management(layer_name + "_1", layer_name)

	return indexLayer
