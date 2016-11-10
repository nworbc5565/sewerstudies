import arcpy

# ====================
# DATABASE CONNECTIONS
# ====================

geodb = r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small_Sewer_Capacity.gdb"
StudyAreaFile = geodb + r"\Small_Sewer_Drainage_Areas"

# =======================
# HYDROLOGIC CALCULATIONS
# =======================

def FindPerviousArea(temporary_clip):
	temporary_clip_cursor=arcpy.SearchCursor(temporary_clip) #Make search cursor for temporary_clip
	PerviousArea = 0
	for temporary_clip in temporary_clip_cursor: #Searches through each row in the Temp_PervImperv
		FCODE = temporary_clip.getValue("FCODE")
		if FCODE == 9999:
			RunningArea = temporary_clip.getValue("Shape_Area") #sqft
			PerviousArea= PerviousArea + RunningArea  #sqft
	del temporary_clip_cursor #Delete Cursor
	del temporary_clip #Delete Temporary File
	print PerviousArea
	return PerviousArea

#PerviousStudyArea=FindPerviousArea(Temp_PervImperv)

def FindStudyArea(study_areas, studyarea_id):
#Search through study_areas to find area of current study area
	study_areas_Cursor=arcpy.SearchCursor(study_areas) #Define search cursor
	for study_areas in study_areas_Cursor:
		StudyArea_ID = study_areas.getValue("StudyArea_ID")
		if StudyArea_ID == studyarea_id:
			total_study_area = study_areas.getValue("SHAPE_Area")
	print total_study_area
	return total_study_area

#TotalStudyArea=FindStudyArea(StudyAreaFile)

def RunoffCoefficientCalc (PerviousArea, total_area, study_areas, studyarea_id):
	study_areas_Cursor=arcpy.UpdateCursor(study_areas) #Define search cursor
	PerviousCofficient= 0.35 #Set pervious runoff coefficient
	ImperviousCoefficient = 0.95 #Set impervious runoff coefficient
	PercentPervious = PerviousArea/total_area #Find percent of study area that is pervious
	PercentImpervious = 1-PercentPervious #Find percent of study area that is impervious
	AvgRunOffCoefficient = (PercentPervious * PerviousCofficient)+(PercentImpervious * ImperviousCoefficient) #Calculate Average Runoff Coefficient
	print AvgRunOffCoefficient
	#Set the calculated average runoff coefficient to the value in the study areas layer
	for row in study_areas_Cursor:
		StudyArea_ID = row.getValue("StudyArea_ID")
		if StudyArea_ID == studyarea_id:
			PreviousRC=row.getValue("Runoff_Coefficient")
			print PreviousRC
			row.setValue("Runoff_Coefficient", AvgRunOffCoefficient)
			study_areas_Cursor.updateRow(row)
	del study_areas_Cursor
	return AvgRunOffCoefficient

#RunoffCoefficientCalc(PerviousStudyArea, TotalStudyArea, StudyAreaFile, studyarea_id)

def getC(studyarea_id, project_id):
	where = "StudyArea_ID = '{}'".format(studyarea_id)

# =======================
# TEMPORARY FILE CREATION
# =======================

	#Define Workspace
	arcpy.env.workspace = r"//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb"

	# Makes new layer "out_layer" based on features in the "where_clause". Essentially makes a layer of only the specific Study Area designated in RunHH Tool
	# The following inputs are layers or table views: "Drainage Areas\DA Indices\DA_90000"
	in_features=r"Drainage Areas\DA Indices\DA_%s" %(project_id)
	arcpy.FeatureClassToFeatureClass_conversion(in_features=in_features, out_path=r"//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb", out_name="Temp_SmallSewer", where_clause= where, field_mapping="""StudyArea_ID "StudyArea_ID" true true false 20 Text 0 0 ,First,#,in_features,StudyArea_ID,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0 ,First,#,in_features,Shape_Area,-1,-1""", config_keyword="")

	#Attempting to Fix Refresh bug
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies")
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb")

	#Define Temp File
	Temp_SmallSewer=r"//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb/Temp_SmallSewer"

	#Clips OWD_GISDATA.OWS.Philadelphia to Feature Layer for Study Area
	# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script

	arcpy.Clip_analysis(in_features="OWS_GISDATA.OWS.Philadelphia", clip_features=Temp_SmallSewer, out_feature_class="//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb/Temp_Pervious", cluster_tolerance="")

	#Attempting to Fix Refresh bug
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies")
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb")

	#Define Temp File
	Temp_PervImperv=r"//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb/Temp_Pervious"

# ====
# RUN!
# ====
	PerviousStudyArea=FindPerviousArea(Temp_PervImperv)
	TotalStudyArea=FindStudyArea(StudyAreaFile,studyarea_id)
	FinalRunOffCoefficient=RunoffCoefficientCalc(PerviousStudyArea, TotalStudyArea, StudyAreaFile, studyarea_id)
	print FinalRunOffCoefficient
	#Delete Temp Layers
	arcpy.Delete_management(Temp_PervImperv)
	arcpy.Delete_management(Temp_SmallSewer)
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies")
	arcpy.RefreshCatalog("//PWDHQR/Data/Planning & Research/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies/Small_Sewer_Capacity.gdb")
	return FinalRunOffCoefficient
