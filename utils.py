import arcpy
import random

"""
utilty/convenience functions. especially for working with arcpy
in easier ways
"""

def random_alphanumeric(n=6):
	"""
	generate a list of random alphanumeric chars.
	"""
	chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
	return ''.join(random.choice(chars) for i in range(n))


# =================================
# Utilities for dealing with arcpy
# =================================
def match_schemas(matchToTable, editSchemaTable, delete_fields = True):

	#find fields to remove from editSchemaTable (those in editSchemaTable but not in matchToTable)
	arcpy.AddMessage("matchToTable={}\neditSchemaTable={}".format(matchToTable,editSchemaTable))
	#get lists of field names
	hiddenFieldsNames = [] #listHiddenFields(matchToTable) #this was crashing
	matchFieldNames = [field.name for field in arcpy.ListFields(matchToTable)]
	editFieldsNames = [field.name for field in arcpy.ListFields(editSchemaTable)] #listFieldNames(editSchemaTable) #arcpy.ListFields(editSchemaTable)

	#remove subtypes
	#subtypeList = ["1", "2", "3", "4", "5", "6"]# these exist in the Dataconv

	#create list of fields to drop from the edit Schema table
	if delete_fields:
		dropFieldsList = []
		for fieldname in editFieldsNames:
			if not fieldname in matchFieldNames and not fieldname in hiddenFieldsNames:
				print "drop: " + fieldname
				dropFieldsList.append(fieldname)

		#concatentate list and drop the fields
		dropFields = ";".join(dropFieldsList)

		arcpy.DeleteField_management(in_table=editSchemaTable, drop_field=dropFields)

	#add necessary fields
	addFieldsList = []
	for fieldname in matchFieldNames:
		#create list of field names to be added
		if fieldname not in editFieldsNames:
			addFieldsList.append(fieldname)
			arcpy.AddMessage("Add: {}".format(fieldname))

	#Temp workarond. Remove geometry specific field. Weird bug causes crash when trying to execute arcpy.AddField_management
	addFieldsList.remove('Shape.STLength()')

	for field in arcpy.ListFields(matchToTable):
		print (field.name + " " + field.type.upper())
		if field.name in addFieldsList:
			arcpy.AddMessage("Adding {} + {}".format(field.name, field.type.upper))
			arcpy.AddField_management(in_table = editSchemaTable, field_name = field.name, field_type = field.type.upper(), field_length = field.length)


def unique_values(table, field):

	"""
	returns list of unique values in a given field, in a table. Returned is a
	tuple that is ready for a arcpy SQL statement
	"""
	with arcpy.da.SearchCursor(table, [field]) as cursor:
		uniq_vals = sorted({row[0] for row in cursor})
		uniq_vals_sql_friendly = str(tuple(uniq_vals)).replace("u", "")
		return uniq_vals_sql_friendly

def remove_rows_with_attribute(table, field, value):

	where = field + " = " + value
	print where
	cursor = arcpy.UpdateCursor(table, where_clause=where)
	for row in cursor:
		print row.getValue("OBJECTID")
		cursor.deleteRow (row)
	del cursor

def where_clause_from_user_input(project_id=None, study_area_id=None):
	"""
	given a project_id and or a study_area_id, return a simple where clause
	that can be used in arcpy to limit the scope of functions accordingly
	"""
	if project_id is not None and project_id != "":
		#use project ID as the scope, i.e. run calcs on all pipes in project
		where = "Project_ID = " + project_id
	elif study_area_id is not None and study_area_id != "":
		#use the study ID as scope, i.e. run calcs on pipes only in a given study area
		where = "StudyArea_ID = '" + study_area_id + "'"

	return where

def where_clause_from_list(table, field, valueList):
	"""
	Takes a list of values and constructs a SQL where
	clause to select those values within a given field and table.

	credit: i believe this came straight from stackoverflow somwhere
	"""

	# Add DBMS-specific field delimiters
	fieldDelimited = arcpy.AddFieldDelimiters(arcpy.Describe(table).path, field)

	# Determine field type
	fieldType = arcpy.ListFields(table, field)[0].type

	# Add single-quotes for string field values
	if str(fieldType) == 'String':
	    valueList = ["'%s'" % value for value in valueList]

	# Format WHERE clause in the form of an IN statement
	whereClause = "%s IN(%s)" % (fieldDelimited, ', '.join(map(str, valueList)))
	return whereClause
