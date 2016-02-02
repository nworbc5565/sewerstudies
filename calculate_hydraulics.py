#Calculated or recalculate hydraulic calcs for a given Project ID 

import arcpy
from arcpy import env

study_pipes = arcpy.GetParameterAsText(0)
study_area_id = arcpy.GetParameterAsText(1)
project_id = arcpy.GetParameterAsText(2) #optional


#define default hydraulic params
default_min_slope = 0.01 # percent - assumed when slope is null
default_TC_slope = 5.0 # percent - conservatively assumed for travel time calculation when slope


#define hydraulic equations
def getMannings( shape, diameter ):
	n = 0.015 #default value
	if ((shape == "CIR" or shape == "CIRCULAR") and (diameter <= 24) ):
		n = 0.015
	elif ((shape == "CIR" or shape == "CIRCULAR") and (diameter > 24) ):
		n = 0.013
	return n

def xarea( shape, diameter, height, width ):
	#calculate cross sectional area of pipe 
	#supports circular, egg, and box shape
	if (shape == "CIR" or shape == "CIRCULAR"):
		return 3.1415 * (math.pow((diameter/12),2 ))/4
	elif (shape == "EGG" or shape == "EGG SHAPE"):
		return 0.5105* math.pow((height/12),2 )
	elif (shape == "BOX" or shape == "BOX SHAPE"):
		return height*width/144

def  minSlope( slope ):
	#replaces null slope value with the assumed minimum 0.01%
	if slope == None:
		return 0.01
	else:
		return slope

def  hydraulicRadius(shape, diameter, height, width ):
	#calculate full flow hydraulic radius of pipe
	#supports circular, egg, and box shape
	if (shape == "CIR" or shape == "CIRCULAR"):
		return (diameter/12)/4
	elif (shape == "EGG" or shape == "EGG SHAPE"):
		return 0.1931* (height/12)
	elif (shape == "BOX" or shape == "BOX SHAPE"):
		return (height*width) / (2*height + 2*width) /12

def minSlopeRequired (shape, diameter, height, width, peakQ) :
	
	n = getMannings(shape, diameter)
	A = xarea(shape, diameter, height, width)
	Rh = hydraulicRadius(shape, diameter, height, width )
	
	s =  math.pow((n * peakQ) / ( 1.49 * A * math.pow(Rh, 0.667) ), 2)
	return s
	
def checkCriticalPipeNull(tc, study, capacity):
	if ( (tc == "Y" or study == "Y" ) and ( capacity <= 0) ) :
		return "CHECK"
	else:
		return None

	
#iterate through each sewer pipe within a given project or study ID
#first, identify the cursor scope based on user input
if project_id is not None and project_id != "":
	
	#use project ID as the scope, i.e. run calcs on all pipes in project
	study_pipes_cursor = arcpy.UpdateCursor(study_pipes, where_clause = "Project_ID = " + project_id)
	arcpy.AddMessage("\t running calcs on Project ID = " + str(project_id))
	
elif study_area_id is not None and study_area_id != "":
	#use the study ID as scope, i.e. run calcs on pipes only in a given study area
	study_pipes_cursor = arcpy.UpdateCursor(study_pipes, where_clause = "StudyArea_ID = '" + study_area_id + "'")
	arcpy.AddMessage("\t running calcs on Study Area ID = " + str(study_area_id))


for pipe in study_pipes_cursor:
	
	
	#Grab pipe parameters
	S 		= pipe.getValue("Slope")
	L 		= pipe.getValue("Shape_Length") # length of segment
	D 		= pipe.getValue("Diameter")
	H 		= pipe.getValue("Height")
	W 		= pipe.getValue("Width")
	Shape 	= pipe.getValue("PIPESHAPE")
	U_el	= pipe.getValue("UpStreamElevation")
	D_el	= pipe.getValue("DownStreamElevation")
	id 		= pipe.getValue("OBJECTID")
	TC		= pipe.getValue("TC_Path")
	ss		= pipe.getValue("StudySewer")
	tag 	= pipe.getValue("Tag")
	
	#check if slope is Null, and replace Null with default min value
	arcpy.AddMessage("checking  pipe "  + str(id))
	if S is None:
		if (U_el is not None) and (D_el is not None):
			S = ( (U_el - D_el) / L ) * 100 #percent
			pipe.setValue("Hyd_Study_Notes", "Autocalculated Slope")
			arcpy.AddMessage("\t calculated slope = " + str(S) + ", ID = " + str(id))
		else:	
			S = default_min_slope
			pipe.setValue("Hyd_Study_Notes", "Minimum " + str(S) +  " slope assumed")
			arcpy.AddMessage("\t min slope assumed = " + str(S)  + ", ID = " + str(id))
		
		arcpy.AddMessage("slope before writing = " + str(S)  + ", ID = " + str(id))
		pipe.setValue("Slope", round(float(S), 2))
			
	
	# check if any required data points are null, and skip accordingly
	if ((D is None) and (H is None)) or (Shape == "UNK"):
		
		#check if this is an important pipe and flag accordingly
		if (TC == "Y" or ss == "Y" and (tag is None)):
			pipe.setValue("Tag", "CHECK")
			arcpy.AddWarning("skipped critical pipe " + str(pipe.getValue("OBJECTID")))
		continue # skip this pipe
		
	
	#compute pipe velocity
	V = (1.49/ getMannings(Shape, D)) * math.pow(hydraulicRadius(Shape, D, H, W), 0.667) * math.pow(float(S)/100, 0.5)
	pipe.setValue("Velocity", round(float(V), 2)) #arcpy.AddMessage("Velocity = " + str(V))
	
	#compute the capacity
	Qmax = xarea(Shape, D, H, W) * V
	pipe.setValue("Capacity", round(float(Qmax), 2)) #arcpy.AddMessage("Qmax = " + str(Qmax))
	
	
	#compute travel time in the pipe segment
	if (S == 0.01): 
		v_conservative = (1.49/ getMannings(Shape, D)) * math.pow(hydraulicRadius(Shape, D, H, W), 0.667) * math.pow(default_TC_slope/100, 0.5)
		T = (L / v_conservative) / 60 # minutes
	else:
		T = (L / V) / 60 # minutes
	
	pipe.setValue("TravelTime_min", round(float(T), 3)) #arcpy.AddMessage("time = " + str(T))
	study_pipes_cursor.updateRow(pipe)
	
del study_pipes_cursor, study_pipes

