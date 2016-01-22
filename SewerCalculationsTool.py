#With pipe data that has already been associated with a drainage area and given TC
#and study sewer tags, this module computes tc, capacity, intensity, and peak runoff
#for each drainage study area. 
#Note that data will be overwritten in the given drainage area table


# Import arcpy module
import arcpy
from arcpy import env

#grab the input drainage area layer and pipes of interest
DAs = arcpy.GetParameterAsText(0) 
all_study_pipes = arcpy.GetParameterAsText(1)
project_id = arcpy.GetParameterAsText(2)

#iterate through each DA within a given project and sum the TCs with their DrainageArea_ID
drainage_areas_cursor = arcpy.UpdateCursor(DAs, where_clause = "Project_ID = " + project_id)

for drainage_area in drainage_areas_cursor:
	
	#work with each study area and determine the pipe calcs based on study area id
	study_area_id = drainage_area.getValue("StudyArea_ID")
	
	#CALCULATIONS ON TC PATH PIPES
	tc_pipes = arcpy.UpdateCursor(all_study_pipes, where_clause = "TC_Path = 'Y'") #reset the cursor
	tc = 3.0000 #set the initial tc to 3 minutes
	for pipe in tc_pipes:
		if pipe.getValue("StudyArea_ID") == study_area_id:
		
			tc += float(pipe.getValue("TravelTime_min") or 0) #the 'float or 0' handles null values
	
	
	
	#CALCULATIONS ON STUDY PIPES
	capacity = 999999 #set the initial capacity, find the min value
	sticker_link = None #find the study pipe sticker link
	intall_year = None #find the install year for the study pipe
	study_pipes = arcpy.UpdateCursor(all_study_pipes, where_clause = "StudySewer = 'Y'") #reset the cursor 
	
	for pipe in study_pipes:
		if pipe.getValue("StudyArea_ID") == study_area_id:
			
			#grab the sticker link and install year once
			if sticker_link is None: 
				sticker_link = pipe.getValue("STICKERLINK")
				intall_year = pipe.getValue("Year_Installed")
			
			#check and replace if the current row capacity is less than the capacity 
			capacity = min(capacity, pipe.getValue("Capacity"))
			
	
	#RUNOFF CALCULATIONS
	C = drainage_area.getValue("Runoff_Coefficient")
	A = drainage_area.getValue("SHAPE_Area") / 43560
	I = 116 / ( tc + 17)
	peak_runoff = C * I * A
	
	#set row values and update row
	drainage_area.setValue("Capacity", capacity)
	drainage_area.setValue("TimeOfConcentration", tc)
	drainage_area.setValue("StickerLink", sticker_link)
	drainage_area.setValue("InstallDate", intall_year)
	drainage_area.setValue("Intsensity", I) #NOTE -> spelling error in field name
	drainage_area.setValue("Peak_Runoff", peak_runoff)
	drainage_areas_cursor.updateRow(drainage_area)
	
	#print(study_area_id + " " + repr(tc) + " " + repr(capacity) + " " + repr(sticker_link) + "\n")

del drainage_areas_cursor, tc_pipes, study_pipes	
