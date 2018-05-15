import numpy

input_points=arcpy.GetParameterAsText(0)
point_lyr=arcpy.MakeFeatureLayer_management(input_points,"layerr")


test_array=[1,2,3,4,5]
standard_dev=numpy.std(test_array)

print standard_dev

