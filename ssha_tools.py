import arcpy
import random
import Working_RC_Calcs
import HHCalculations
import utils
import os


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

def updateDAIndex (project_id, study_areas, study_area_indices):

	"""
	update the companion "Drainage Area Index" for the current project id. This
	essentially copies the drainage areas with the project id and creates a new
	feature class. This compainion feature class is used for Data Driven Pages
	functionality.
	"""

	#check if index already exists, delete if necessary
	index_layer = os.path.join(study_area_indices, "DA_" + project_id)
	if arcpy.Exists(index_layer):
		arcpy.AddMessage('{} index exists, overwriting...'.format(project_id))
		arcpy.Delete_management(index_layer)

	where = "Project_ID = " + project_id
	layer_name = "DA_" + project_id

	arcpy.MakeFeatureLayer_management(study_areas, index_layer, where_clause = where)
	arcpy.FeatureClassToFeatureClass_conversion(index_layer, study_area_indices, layer_name)
	arcpy.Delete_management(index_layer)
