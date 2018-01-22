import arcpy
import random
import HHCalculations
import utils
import os

# workspace = "C:/Users/christine.brown/Desktop/SSHA/Small_Sewer_Capacity/Default.gdb"
# arcpy.env.workspace = workspace

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

def updateDAIndex (study_areas, study_area_indices, project_id ="", studyarea_id = ""):

	"""
	update the companion "Drainage Area Index" for the current project id. This
	essentially copies the drainage areas with the project id and creates a new
	feature class. This compainion feature class is used for Data Driven Pages
	functionality.
	"""
	#Use scratchGDB environment to write intermediate data
	tempData = arcpy.env.scratchGDB

	#Setting default value for duplicate records count in Master DA Index
	dupRecordCount = 0

	#check if index already exists, delete if necessary
	# if arcpy.Exists(index_featureclass_path):
	# 	arcpy.AddMessage('{} index exists, overwriting...'.format(project_id))
	# 	arcpy.Delete_management(index_featureclass_path)

	#check study_area_indices for existing records for each study area ID

	if studyarea_id != "":
		field_name = ["StudyArea_ID"]
		where = "StudyArea_ID='{}'".format(studyarea_id)
		arcpy.AddMessage("Updating DA Master Index where: {}".format(where))
		layer_name = "DA_" + studyarea_id
	elif project_id != "":
		field_name = ["Project_ID"]
		where = "Project_ID={}".format(project_id)
		arcpy.AddMessage("Updating DA Master Index where: {}".format(where))
		layer_name = "DA_" + project_id
	else:
		arcpy.AddMessage("Must specific Project or Study Area ID!")

	#Set file path for temporary feature class in scratchGDB
	index_featureclass_path = os.path.join(tempData, layer_name)

	with arcpy.da.UpdateCursor(study_area_indices, field_name, where_clause=where) as daindices_cursor:
		for row in daindices_cursor:
			dupRecordCount = dupRecordCount + 1
			daindices_cursor.deleteRow()
		arcpy.AddMessage("Total duplicate records deleted = {}".format(dupRecordCount))

	#create feature class from small sewer drainage area and store temporarily in the default gdb
	index_featureclass = arcpy.FeatureClassToFeatureClass_conversion(study_areas, tempData, layer_name, where_clause = where)

	#Attempting to match schemas
	#utils.match_schemas(study_area_indices, index_featureclass, delete_fields=True)

	#Manually deleting dropFields causing issues with schema match. Temp fix need to go back and fix properly.
	dropFields = ["SHAPE_STArea__", "SHAPE_STLength__"]
	arcpy.DeleteField_management(index_featureclass, dropFields)

	#append temporary feature class to the DA_Master feature class
	arcpy.Append_management(index_featureclass, study_area_indices, "TEST")
	#delete the feature class in the default gdb
	arcpy.Delete_management(index_featureclass)
