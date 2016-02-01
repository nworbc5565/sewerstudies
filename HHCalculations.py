#hydraulic and hydrologic calculation tools
def minSlopeRequired (shape, diameter, height, width, peakQ) :
	
	n = getMannings(shape, diameter)
	A = xarea(shape, diameter, height, width)
	Rh = hydraulicRadius(shape, diameter, height, width )
	
	s =  math.pow((n * peakQ) / ( 1.49 * A * math.pow(Rh, 0.667) ), 2)
	return s