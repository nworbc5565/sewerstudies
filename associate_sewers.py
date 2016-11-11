import arcpy
import HHCalculations
import utils


#grab the project ID from the user
project_id = arcpy.GetParameterAsText(0)
from_sewers = arcpy.GetParameterAsText(1)
study_sewers = arcpy.GetParameterAsText(2)
study_areas = arcpy.GetParameterAsText(3)

def associate_sewers_to_area(project_id, from_sewers, study_sewers, study_areas):

	"""
    Copy sewers from the Waste Water Network and append to the StudiedSewers
    layer. Sewers are copied based on spatial join to the drainage areas of
    each study area within a given project scope (Project Number).
    """

    #uniqs = str(tuple(unique_values(study_sewers, "StudyArea_ID"))).replace("u", "")
	uniqs = utils.unique_values(study_sewers, "StudyArea_ID")

	#create random names for temporary DA and sewer layers
	DAs_temp = "DA_" + utils.random_alphanumeric()
	sewers = "sewers_" + utils.random_alphanumeric()
	sewers2	= "sewersShedJoin_" + utils.random_alphanumeric()

	#create temporary DA layer comprised only of DAs that do not have a
	#Study Area ID found in the study_pipes layer (prevents duplicates)
	where = "Project_ID = " + project_id + " AND StudyArea_ID NOT IN " + uniqs
	arcpy.MakeFeatureLayer_management(study_areas, DAs_temp, where_clause = where)


	#spatially join the waste water network to the temp Drainage Areas (only
	#areas with Study Area ID not in the StudyPipes)
	arcpy.SpatialJoin_analysis(from_sewers, join_features = DAs_temp,
							out_feature_class = sewers,
							join_operation = "JOIN_ONE_TO_MANY",
							join_type = "KEEP_COMMON",
							match_option = "HAVE_THEIR_CENTER_IN",
							search_radius = "15 Feet",)


	#remove SLANTS and anything else unnecessary
	utils.remove_rows_with_attribute(sewers, "PIPE_TYPE", "'SLANT'")
	utils.remove_rows_with_attribute(sewers, "LifecycleStatus", "'REM'")

	#spatially join the new study sewers to the model shed (grab the outfall data)
	arcpy.SpatialJoin_analysis(sewers, join_features = 'ModelSheds',
							out_feature_class = sewers2,
							join_operation = "JOIN_ONE_TO_MANY",
							join_type = "KEEP_COMMON",
							match_option="HAVE_THEIR_CENTER_IN",
							search_radius = "",)

	arcpy.AddMessage("\t Joining Model Sheds")

	#MAKE SCHEMA MATCH BETWEEN THE TEMP SEWERS LAYER AND THE TARGET STUDY SEWERS LAYER
	arcpy.AddMessage("\t matching schema")
	utils.match_schemas(study_sewers, sewers2, delete_fields=False)

	#run calculations on the temporary pipe scope, apply default flags this time
	fields = ['OBJECTID', 'TC_Path', 'StudySewer', 'Tag']
	with arcpy.da.UpdateCursor(sewers2, fields) as temp_pipes_cursor:
		HHCalculations.applyDefaultFlags(temp_pipes_cursor)

	#append the sewers copied from the waste water mains layer to the studied sewers layer
	arcpy.AddMessage("\t appending sewers to {}".format(study_sewers))
	arcpy.Append_management(inputs = sewers2,
							target = study_sewers,
							schema_type = "NO_TEST",)

	#memory clean up
	arcpy.Delete_management(sewers)
	arcpy.Delete_management(sewers2)
	arcpy.Delete_management(DAs_temp)


# ===========================
# Run the tool
# ===========================
associate_sewers_to_area(project_id, from_sewers, study_sewers, study_areas)
