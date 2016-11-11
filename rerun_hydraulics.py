#Calculated or recalculate hydraulic calcs for a given Project ID
import HHCalculations
import ssha_tools
import Working_RC_Calcs
import arcpy

study_area_id = arcpy.GetParameterAsText(0)
project_id = arcpy.GetParameterAsText(1) #optional
study_sewers = arcpy.GetParameterAsText(2)
study_areas = arcpy.GetParameterAsText(3)
study_area_indices = arcpy.GetParameterAsText(4)

#run calculations on the selected pipe scope
HHCalculations.run_hydraulics(project_id, study_sewers, study_area_id)
HHCalculations.run_hydrology(project_id, study_sewers, study_areas, study_area_id)
if project_id is not None and project_id != "":
	ssha_tools.updateDAIndex(project_id, study_areas, study_area_indices)
