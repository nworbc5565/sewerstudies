import arcpy
from arcpy import env
import random
import HHCalculations
#import configparser
from utils import random_alphanumeric
import os
# =================
# DATA CONNECTIONS
# =================

#grab env variables
# config = configparser.ConfigParser()
# DOC_ROOT = os.path.dirname(os.path.realpath(__file__))
# config.read(os.path.join(DOC_ROOT, 'config.ini'))
env.workspace = geodb = r'\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small_Sewer_Capacity.gdb'
study_sewers = geodb + r'\StudiedSewers'#r"\StudiedWasteWaterGravMains"
study_areas = geodb + r"\Small_Sewer_Drainage_Areas"
model_sheds = geodb + r"\ModelSheds"
all_pipes =  r'Database Connections\DataConv.sde\DataConv.GISAD.Waste Water Network\DataConv.GISAD.wwGravityMain'
#r"Waste Water Network\Waste Water Gravity Mains"


def unique_values(table, field):
	"""
	returns list of unique values in a given field(s) in a table. if more than
	one field is passed in, uniqueness is checked considering both fields, where
	duplicates may exists as long as duplicates do not exist when considering
	both fields.
	"""
	with arcpy.da.SearchCursor(table, field) as cursor:
		#return sorted({row[0] for row in cursor})
		#forces a dictionary which allows only one key to exist (unique)
		return sorted({row for row in cursor})

def unique_values_new(table, field=None, fields=None, sql_ready=False):
	"""
	returns list of unique values in a given field(s) in a table. if more than
	one field is passed in, uniqueness is checked considering both fields, where
	duplicates may exists as long as duplicates do not exist when considering
	both fields.
	"""
	#returns list of unique values in a given field, in a table
	if fields is not None:
		#check for uniqueness across multple columns, return flattened strings
		with arcpy.da.SearchCursor(table, fields) as cursor:

			#uniques = sorted({row[0] for row in cursor})
			uniques = sorted({row for row in cursor})

			if sql_ready:
				#remove unicode thing and change to tuple
				return str(tuple(uniques)).replace("u", "")
			else:
				return uniques

	else:
		with arcpy.da.SearchCursor(table, field) as cursor:

			#uniques = sorted({row[0] for row in cursor})
			uniques = sorted({row[0] for row in cursor})

			if sql_ready:
				#remove unicode thing and change to tuple
				return str(tuple(uniques)).replace("u", "")
			else:
				return uniques


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
		#compare field names (convert temporarily to upper)
		if (not fieldname.upper() in [s.upper() for s in matchFieldNames]
			and not fieldname.upper() in [s.upper() for s in hiddenFieldsNames]):
			#print "drop: " + fieldname
			dropFieldsList.append(fieldname)

	#concatentate list and drop the fields
	dropFields = ";".join(dropFieldsList)

	arcpy.DeleteField_management(in_table=editSchemaTable, drop_field=dropFields)

	#add necessary fields
	addFieldsList = []
	for fieldname in matchFieldNames:
		#create list of field names to be added
		if not fieldname.upper() in [s.upper() for s in editFieldsNames]:
			addFieldsList.append(fieldname)
			print "add: " + fieldname

	for field in arcpy.ListFields(matchToTable):
		#print (field.name + " " + field.type.upper())
		if field.name.upper() in [s.upper() for s in addFieldsList]:
			print ("adding " + field.name + " " + field.type.upper())
			arcpy.AddField_management(in_table = editSchemaTable, field_name = field.name, field_type = field.type.upper(), field_length = field.length)



def makeTempDAandJoinPipes(project_id):
	#unique list of StudyArea_IDs found in studied sewers
	#tuple, and replace used to reformat the python list to an SQL friendly string
	uniqs = str(tuple(unique_values(study_sewers, "StudyArea_ID"))).replace("u", "")

	#create random names for temporary DA and sewer layers
	DAtmp = "DA_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))
	sewers = "sewers_" + ''.join(random.choice('0123456789ABCDEF') for i in range(6))

	#create temporary DA layer comprised only of DAs that do not have a Study Area ID found in the study_sewers layer (prevents duplicates)
	where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
	arcpy.MakeFeatureLayer_management(study_areas, DAtmp, where_clause = where)
	arcpy.SpatialJoin_analysis(all_pipes, join_features = DAtmp, out_feature_class = sewers, join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_COMMON", match_option = "WITHIN_A_DISTANCE", search_radius = "5 Feet")

def removeRowsWithAttribute(table, field, value):

	where = field + " = " + value
	print where
	cursor = arcpy.UpdateCursor(table, where_clause=where)
	for row in cursor:
		print row.getValue("OBJECTID")
		cursor.deleteRow (row)


def trace_upstream(startid, table=r"Small_Sewer_Drainage_Areas",
					return_field = 'StudyArea_ID',
					downstream_field='DownStreamStudyAreaID',
					search_field = 'StudyArea_ID'):
	"""
	return a list of study areas ids that cumulatively drain into the
	given study area. This functions requires that study areas have a downstream
	study area assigned where appropriate.

	if the upstream lookup field is different than the return field, set this in
	upstream_field. Otherwise this should be None

	not currently working except for default case

	#RECURSIVE_FUNCTION
	"""

	upstream_ids = []
	def find_upstream_elements(current_id):
		#search for elements having the current element's ID as their
		#downstream ID. E.g. DownStreamStudyAreaID = '90001_08'
		where = "{} = '{}'".format(downstream_field, current_id)
		print where
		upstream_cursor = arcpy.SearchCursor(table, where_clause=where)

		for row in upstream_cursor:

			#upstream_id = row.getValue(return_field)
			print row.getValue(return_field)
			upstream_ids.append(row.getValue(return_field))

			#find_upstream_elements(upstream_id)
			find_upstream_elements(row.getValue(search_field))


	#kick it off
	find_upstream_elements(startid)

	return upstream_ids

def associate_study_sewers(project_id):

	"""
	given a project ID, create a copy of sewers from the WasterWaterGravMains
	layer into the StudySewers layer based on a spatial join of drainage areas
	within the current project.

	Process/Logic:
		0. 	spatially join (intersect) current study area to existing study areas.
		 	associate those studied sewers (from the intersected existintg study
			sewers) with the current study area in the roles table.
		1. 	spatially join WasterWaterGravMains to the subset of drainage areas
			filtered by project_id that do not fall within an existing study area.
			(Achieved with Erase tool?)
		2. 	if spatially joined sewers do not already exist in the StudySewers,
			copy them into the StudySewers layer.
		3. 	tabulate all sewers spatially joined within this project_id in the
			StudySewersRoles table, keeping track of their facilityid and their
			current StudyArea_ID. (one to many relationship). Prevent duplicates
			in the StudySewersRoles table by comparing FacililityID and Role: no
			entry should share a facilityid and role (though duplicates of
			facilityid are expected)
	"""

	#unique list of FACILITYID's found in studied sewers (this is redundant)
	#tuple, and replace used to reformat the python list to an SQL friendly string
	roles = os.path.join(geodb, 'StudySewerRoles')
	uniqs = str(tuple(unique_values(study_sewers, ["FACILITYID"]))).replace("u", "")
	uniq_areas = unique_values_new(roles, ['StudyAreaID'], sql_ready=True)

	#create random names for temporary DA and sewer layers
	DAtmp = "DA_" + random_alphanumeric(n=6)
	studied_DAs = 'studied_DAs_' + random_alphanumeric(n=6)
	unstudied_DAs = 'unstudiedDAs_'+ random_alphanumeric(n=6)
	unstudied_sewers = "sewers_" + random_alphanumeric(n=6)
	studied_sewers = "studiedsewers_" + random_alphanumeric(n=6)
	sewers2	= "sewersShedJoin_" + random_alphanumeric(n=6)

	#create temporary layer of drainage areas sharing the input project_id

	where = "Project_ID = {} AND StudyArea_ID NOT IN {}".format(project_id, uniq_areas)
	arcpy.MakeFeatureLayer_management(study_areas, DAtmp, where_clause = where)

	#isolate any DAs within current scope that already have been studied
	arcpy.Intersect_analysis([study_areas, DAtmp], out_feature_class=studied_DAs)
	ss_ids_inscope = unique_values(studied_DAs, ['StudyArea_ID']) #FACILITYIDs already studied
	print 'ss_ids_inscope= {}'.format(ss_ids_inscope)
	return 0
	#isolate the drainage areas that have not been studied previously. these
	#will be used to spatially join sewers from ww grav mains
	arcpy.Erase_analysis(DAtmp, study_areas, out_feature_class=unstudied_DAs)

	#spatially join the waste water network to the temp Drainage Areas
	arcpy.SpatialJoin_analysis(
		all_pipes,
		join_features = unstudied_DAs,
		out_feature_class = unstudied_sewers,
		join_type = "KEEP_COMMON",
		)

	#remove SLANTS and anything else unnecessary
	removeRowsWithAttribute(unstudied_sewers, "PIPE_TYPE", "'SLANT'")

	#spatially join the new unstudied study sewers to the model shed
	arcpy.AddMessage("\t Joining Model Sheds")
	arcpy.SpatialJoin_analysis(
		unstudied_sewers,
		join_features = model_sheds,
		out_feature_class = sewers2,
		join_type = "KEEP_COMMON"
		)

	#determine which of the temp sewers should be copied into the studysewers
	#& StudySewersRoles tables. Don't copy sewers with duplicate facilityid & StudyArea_ID

	unique_sewers = unique_values(study_sewers, ['FacilityID'])
	unique_roles = unique_values(roles, ['FacilityID', 'StudyAreaID'])
	print 'unique_roles = {}'.format(unique_roles)
	#print 'unique_sewers = {}'.format(unique_sewers)
	return 0
	sewers_cursor = arcpy.da.SearchCursor(sewers2, ['FacilityID', 'StudyArea_ID']) #FIX THIS underscore convention
	roles_cursor = arcpy.da.InsertCursor(roles, ['FacilityID', 'StudyAreaID'])
	print 'populating roles'
	print
	defultrole = 'SSTC'
	for row in sewers_cursor:

		if row not in unique_roles:
			#add this data to the unique roles table
			print row
			roles_cursor.insertRow(row)

		if row[0] in unique_sewers:
			#if the curren row is found within the list of uniq FacilityID/StudyID
			#combos, then this row is not unique and should not be appended to the
			#study_sewers. However, it should be
			sewers_cursor.deleteRow()

	del roles_cursor
	del sewers_cursor
	#append data to StudySewersRoles table

	#run calculations on the temporary pipe scope, apply default flags this time
	temp_pipes_update_cursor = arcpy.UpdateCursor(sewers2)
	for row in temp_pipes_update_cursor:
		#REMOVE SEWERS WHOSE FACILITY ID ALREADY EXISTS IN THE STUDY SEWERS LAYER
		pass
		#NOTE FINISH THIS!

	#print 'apply flags'
	#HHCalculations.applyDefaultFlags(temp_pipes_cursor)

	#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
	print 'matching schema'
	arcpy.AddMessage("\t matching schema")
	matchSchemas(study_sewers, sewers2)

	#append the sewers copied from the waste water mains layer to the studied sewers layer
	arcpy.AddMessage("\t appending sewers to Studied Pipes layer")
	arcpy.Append_management(
		inputs = sewers2,
		target = study_sewers,
		schema_type = "NO_TEST",
		field_mapping = "#",
		subtype = "#"
		)

	#memory clean up
	arcpy.Delete_management(sewers)
	arcpy.Delete_management(sewers2)
	arcpy.Delete_management(DAtmp)
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
