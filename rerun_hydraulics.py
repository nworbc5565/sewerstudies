#Calculated or recalculate hydraulic calcs for a given Project ID 

import HHCalculations
import HydraulicStudyGeneralTools
import arcpy
from arcpy import env


# study_pipes = arcpy.GetParameterAsText(0)
# study_area_id = arcpy.GetParameterAsText(1)
# project_id = arcpy.GetParameterAsText(2) #optional
geodb = r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small_Sewer_Capacity.gdb"
study_pipes = geodb + r"\StudiedWasteWaterGravMains"
study_areas = geodb + r"\Small_Sewer_Drainage_Areas"

study_area_id = arcpy.GetParameterAsText(0)
project_id = arcpy.GetParameterAsText(1) #optional

	
#iterate through each sewer pipe within a given project or study ID
#first, identify the cursor scope based on user input
if project_id is not None and project_id != "":
	
	#use project ID as the scope, i.e. run calcs on all pipes in project
	study_pipes_cursor 		= arcpy.UpdateCursor(study_pipes, where_clause = "Project_ID = " + project_id)
	drainage_areas_cursor 	= arcpy.UpdateCursor(study_areas, where_clause = "Project_ID = " + project_id)
	arcpy.AddMessage("\t running calcs on Project ID = " + str(project_id))
	
elif study_area_id is not None and study_area_id != "":
	#use the study ID as scope, i.e. run calcs on pipes only in a given study area
	study_pipes_cursor 		= arcpy.UpdateCursor(study_pipes, where_clause = "StudyArea_ID = '" + study_area_id + "'")
	drainage_areas_cursor 	= arcpy.UpdateCursor(study_areas, where_clause = "StudyArea_ID = '" + study_area_id + "'")
	
	
	#grab the project id 
	project_id = study_area_id[:study_area_id.find("_")]
	arcpy.AddMessage("\t running calcs on Study Area ID = " + str(study_area_id) + "/n/t" + "project_id = " + project_id)

#run calculations on the selected pipe scope
HHCalculations.runCalcs(study_pipes_cursor)
HHCalculations.runHydrology(drainage_areas_cursor)
if project_id is not None and project_id != "":
	HydraulicStudyGeneralTools.updateDAIndex(project_id)

