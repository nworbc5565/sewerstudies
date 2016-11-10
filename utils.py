"""
general utilty/convenience functions
"""


#insert convenience tool for random alphanum file name. grab from swmmio on github
def random_alphanumeric(n=6):
	import random
	chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
	return ''.join(random.choice(chars) for i in range(n))

def buildWhereClauseFromList(table, field, valueList):
	"""Takes a list of values and constructs a SQL WHERE
	clause to select those values within a given field and table."""
	import arcpy

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
