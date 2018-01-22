#Calculated or recalculate hydraulic calcs for a given Project ID
import HHCalculations
import ssha_tools
import Working_RC_Calcs
import arcpy

study_area_ID = arcpy.GetParameterAsText(0)
project_ID= arcpy.GetParameterAsText(1) #optional
study_sewers = arcpy.GetParameterAsText(2)
study_areas = arcpy.GetParameterAsText(3)
study_area_indices = arcpy.GetParameterAsText(4)

#run calculations on the selected pipe scope
HHCalculations.run_hydraulics(project_ID, study_sewers, study_area_ID)
HHCalculations.run_hydrology(project_ID, study_sewers, study_areas, study_area_ID)
if project_ID is not None and project_ID != "":
	ssha_tools.updateDAIndex(study_areas, study_area_indices, project_id = "{}".format(project_ID))
elif study_area_ID is not None and study_area_ID != "":
	ssha_tools.updateDAIndex(study_areas, study_area_indices, studyarea_id = "{}".format(study_area_ID))
