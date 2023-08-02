"""
This script takes advantage of the Geoserver REST API to create layer groups automatically, 
given the standardized naming used throughout the project. It also includes some extra code 
used to change the default layer styles or blending mode via the API.
"""

import requests
from xml.etree import ElementTree
import xmltodict

URL_GEOSERVER = 'https://myserver.com/geoserver/'

# Login credentials
auth=('...', '...') 

# Municipality code
municipio="46021"

# Map series code
serie="REN_RUS"

# Base REST API URL
urlbase=URL_GEOSERVER + 'rest/'

# WMS URL
urlwms=URL_GEOSERVER + serie + '/wms'

# --------------------------------------------------------------
# MAIN SCRIPT - GENERATING LAYER GROUPS FOR SERIES-MUNICIPALITY
# --------------------------------------------------------------

# 1.- Obtaining bounding boxes for all individual layers to be grouped

# Getting layer list
params = {'request' : 'GetCapabilities',}
response = requests.get(urlwms, params=params, auth=auth, verify=False)
obj = xmltodict.parse(response.content)

# Storing bounding boxes in dict
extremos={}
westBoundLongitude=[]
eastBoundLongitude=[]
southBoundLatitude=[]
northBoundLatitude=[]
for capa in obj["WMS_Capabilities"]["Capability"]["Layer"]["Layer"]:
    extremos[capa["Name"]]=[float(capa["EX_GeographicBoundingBox"]["westBoundLongitude"]),float(capa["EX_GeographicBoundingBox"]["eastBoundLongitude"]),float(capa["EX_GeographicBoundingBox"]["southBoundLatitude"]),float(capa["EX_GeographicBoundingBox"]["northBoundLatitude"])]
    westBoundLongitude.append(float(capa["EX_GeographicBoundingBox"]["westBoundLongitude"]))
    eastBoundLongitude.append(float(capa["EX_GeographicBoundingBox"]["eastBoundLongitude"]))
    southBoundLatitude.append(float(capa["EX_GeographicBoundingBox"]["southBoundLatitude"]))
    northBoundLatitude.append(float(capa["EX_GeographicBoundingBox"]["northBoundLatitude"]))


# 2.- Creating XML containing all layers to be added in the municipality+series group

root = ElementTree.Element('layerGroup')
child = ElementTree.SubElement(root,"name")
child.text=serie+"_"+municipio

child = ElementTree.SubElement(root,"mode")
child.text="SINGLE"

child = ElementTree.SubElement(root,"title")
child.text=serie+"_"+municipio

child = ElementTree.SubElement(root,"workspace")
child2 = ElementTree.SubElement(child,"name")
child2.text=serie

child = ElementTree.SubElement(root,"publishables")

# For each layer in series and municipality
response = requests.get(urlbase+'workspaces/'+serie+'/layers', auth=auth, verify=False)
datos=response.json()
for elem in datos['layers']['layer']:
    if elem['name'][0:13]==serie+'_'+municipio:
        child2 = ElementTree.SubElement(child,"published")
        child2.set("type","layer")
        child3 = ElementTree.SubElement(child2,"name")
        child3.text = elem["name"]

child = ElementTree.SubElement(root,"bounds")
child2 = ElementTree.SubElement(child,"minx")
child2.text=str(min(westBoundLongitude))

child2 = ElementTree.SubElement(child,"maxx")
child2.text=str(max(eastBoundLongitude))

child2 = ElementTree.SubElement(child,"miny")
child2.text=str(min(southBoundLatitude))

child2 = ElementTree.SubElement(child,"maxy")
child2.text=str(max(northBoundLatitude))

child2 = ElementTree.SubElement(child,"crs")
child2.text="EPSG:4326"


# 3.- Creating the layer group

data=ElementTree.tostring(root)
headers = {'Content-type': 'text/xml',}
response = requests.post(urlbase+'workspaces/'+serie+'/layergroups', auth=auth, data=data, headers=headers, verify=False)



# --------------------------------------------------------------
# OTHER USEFUL SCRIPTS
# --------------------------------------------------------------


# A.- Modifying style for all layers in series
# --------------------------------------------------------------

# Style name to be applied
estilo='cchval_CTP_IGC_rojo'

# Request to the API to get layer list
response = requests.get(urlbase+'workspaces/'+serie+'/layers', auth=auth, verify=False)
datos=response.json()

# Iterate layer list
for elem in datos['layers']['layer']:
    headers = {'Content-type': 'text/xml',}

    # Set defaultStyle name
    data = '<layer><defaultStyle><name>'+estilo+'</name></defaultStyle></layer>'

    # PUT request
    response = requests.put(urlbase+'workspaces/'+serie+'/layers/'+elem['name'], headers=headers, data=data, auth=auth, verify=False)


# B.- Changing mode of the layer group
# --------------------------------------------------------------
#     For example, to OPAQUE_CONTAINER, so all individual layers are not shown when accesing the layer list

headers = {'Content-type': 'text/xml',}
data = '<layerGroup><mode>'+'OPAQUE_CONTAINER'+'</mode></layerGroup>'
response = requests.put(urlbase+'workspaces/'+serie+'/layergroups/'+serie, headers=headers, data=data, auth=auth, verify=False)