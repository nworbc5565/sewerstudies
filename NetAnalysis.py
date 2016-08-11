#sys.path.append(r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Scripts")
#mxd = arcpy.mapping.MapDocument(r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small Sewer Capacity_160301new.mxd")
import arcpy
from arcpy import env

#pipes_net =  r"Waste Water Network\Waste Water Gravity Mains"
pipes_net = r"Database Connections/DataConv.sde/DataConv.GISAD.Waste Water Network/DataConv.GISAD.WasteNetwork"
def traceUpStream (flags, mxd):

#2.2 Obtain isolation area by tracing geometric network, getting list of isolated pipes and saving selection
    #try:in_flags="HydraulicStudyNodes", in_trace_task_type="TRACE_UPSTREAM",
	arcpy.env.addOutputsToMap = False 
	arcpy.TraceGeometricNetwork_management(in_geometric_network=pipes_net, out_network_layer="WW_Mains_From_Net",in_flags=flags, in_trace_task_type="TRACE_UPSTREAM", in_disable_from_trace="DataConv.GISAD.wwVentPipe")
	arcpy.env.addOutputsToMap = True
	
	subLayer = "WW_Mains_From_Net" + r"\wwGravityMain"
	print "sublayer = " + subLayer
	arcpy.FeatureClassToFeatureClass_conversion(subLayer, env.workspace, "Mains_Isolation")
	
	#remove wwnet
	df = arcpy.mapping.ListDataFrames(mxd)[0]
	for i in arcpy.mapping.ListLayers(mxd , "WW_Mains_From_Net"):
		print "Deleting layer", i
		arcpy.mapping.RemoveLayer(df , i)
	
	
	

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "HydraulicStudyNodes"
#arcpy.TraceGeometricNetwork_management(in_geometric_network="Database Connections/DataConv.sde/DataConv.GISAD.Waste Water Network/DataConv.GISAD.WasteNetwork", out_network_layer="DataConv.GISAD.wwGravityMain", in_flags="HydraulicStudyNodes", in_trace_task_type="TRACE_UPSTREAM", in_barriers="", in_junction_weight="", in_edge_along_digitized_weight="", in_edge_against_digitized_weight="", in_disable_from_trace="DataConv.GISAD.wwVentPipe", in_trace_ends="NO_TRACE_ENDS", in_trace_indeterminate_flow="NO_TRACE_INDETERMINATE_FLOW", in_junction_weight_filter="", in_junction_weight_range="", in_junction_weight_range_not="AS_IS", in_edge_along_digitized_weight_filter="", in_edge_against_digitized_weight_filter="", in_edge_weight_range="", in_edge_weight_range_not="AS_IS")

#arcpy.ImportToolbox(r"\\PWDHQR\Data\Planning & Research\Linear Asset Management Program\Water Sewer Projects Initiated\03 GIS Data\Hydraulic Studies\Small_Sewer_Capacity.gdb\Small_Sewer_Calcs.tbx")
#arcpy.tracingGN(Flags="Feature Set", Barriers="Feature Set", Sysvalves_Layer="Sysvalves_Layer3")