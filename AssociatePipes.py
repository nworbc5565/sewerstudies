import arcpy
from arcpy import env
import HydraulicStudyGeneralTools

#grab the project ID from the user
project_id = arcpy.GetParameterAsText(0)
from_sewers = arcpy.GetParameterAsText(1)
study_sewers = arcpy.GetParameterAsText(2)
study_areas = arcpy.GetParameterAsText(3)

#copy and asociate the wwGravMains to the study sewer laywer
HydraulicStudyGeneralTools.associatePipes(project_id, from_sewers,
                                          study_sewers, study_areas)
