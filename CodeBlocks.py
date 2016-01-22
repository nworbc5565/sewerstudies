#Code blocks used for Calculate Field functionality

code_block = """def getMannings( shape, diameter ):
  n = 0.015 #default value
  if ((shape == "CIR" or shape == "CIRCULAR") and (diameter <= 24) ):
	n = 0.015
  elif ((shape == "CIR" or shape == "CIRCULAR") and (diameter > 24) ):
	n = 0.013
  return n

def  xarea( shape, diameter, height, width ):
  
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
	
def  hydR(shape, diameter, height, width ):
  
  #calculate full flow hydraulic radius of pipe 
  #supports circular, egg, and box shape
  
  if (shape == "CIR" or shape == "CIRCULAR"):
    return (diameter/12)/4
  elif (shape == "EGG" or shape == "EGG SHAPE"):
    return 0.1931* (height/12)
  elif (shape == "BOX" or shape == "BOX SHAPE"):
    return (height*width) / (2*height + 2*width) /12"""