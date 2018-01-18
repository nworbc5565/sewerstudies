from arcpy import Copy_management

#Set local variables
in_data= "P:/Linear Asset Management Program/Water Sewer Projects Initiated/03 GIS Data/Hydraulic Studies"
out_data = "C:/Users/christine.brown/Desktop/SSHA/Small_Sewer_Capacity.gdb"
#execute
Copy_management(in_data, out_data)
