"""Converts features to well known text. Output will be generated in ArcGIS Pro project folder.
 ArcGIS Toolbox script includes 4 parameters:

Input - Shapefile or feature class to be converted to well known text.
Output - name of output csv generated in project folder.
Field - Input field which will be used as the primary key in the output.
Explode Multipart - Checkbox which triggers multipart to singlepart conversion."""

import pandas as pd
import arcpy

fc = arcpy.GetParameter(0)
output = arcpy.GetParameter(1)
key_field = arcpy.GetParameter(2)
explode_multipart = arcpy.GetParameter(3)

# use WGS84
sr = arcpy.SpatialReference(4326)
# output format
df = pd.DataFrame(columns=['key', 'wkt'])

# eliminate holes
arcpy.EliminatePolygonPart_management(fc, 'in_memory\\temp_fc', condition='PERCENT', part_area_percent='10', part_option='CONTAINED_ONLY')

# discover multipart features.
arcpy.AddField_management('in_memory\\temp_fc', 'multipart', 'LONG')
arcpy.CalculateField_management('in_memory\\temp_fc', 'multipart', "!Shape!.partCount", "PYTHON3", None)

# Convert geometry to well known text and project in WGS84.
i = 0
arcpy.AddMessage(str(key_field))
for row in arcpy.da.SearchCursor('in_memory\\temp_fc', ['SHAPE@WKT', '{}'.format(key_field), 'multipart'], spatial_reference=sr):
    # skip multipart
    if row[2] > 1:
        continue
    wkt = row[0]
    route_name = row[1]
    # add to dataframe
    i += 1
    df.loc[i] = [route_name, wkt]

# create wkt for multipart features
arcpy.FeatureClassToFeatureClass_conversion('in_memory\\temp_fc', out_name='temp_fc2', where_clause="multipart > 1")
arcpy.management.MultipartToSinglepart('temp_fc2', 'in_memory\\singlepart_fc')

if explode_multipart is True:
    multipart = []
    for row in arcpy.da.SearchCursor('in_memory\\singlepart_fc', ['SHAPE@WKT', '{}'.format(key_field)], spatial_reference=sr):
        multipart.append(row[1])
        wkt = row[0]
        route_name = row[1] + '-' + str(multipart.count(row[1]))
        # add to dataframe
        i += 1
        df.loc[i] = [route_name, wkt]
    arcpy.AddMessage('Multipart Features Processed: ')
    arcpy.AddMessage(list(set(multipart)))

df.to_csv('{}.csv'.format(output))

