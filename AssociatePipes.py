import arcpy
from arcpy import env
import HydraulicStudyGeneralTools

#grab the project ID from the user
project_id = arcpy.GetParameterAsText(0)

#copy and asociate the wwGravMains to the study sewer laywer
HydraulicStudyGeneralTools.associatePipes(project_id)
