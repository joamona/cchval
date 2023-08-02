# CCHVAL. Implementation of Web Map Services of Old Cadastral Maps
This repository hosts some supplementary files used during the research of the article "Implementation of Web Map Services of Old Cadastral Maps", by Álvaro Verdú-Candela, Carmen Femenia-Ribera, Gaspar Mora-Navarro, and Rafael Sierra-Requena.
A total of three Python scripts were developed for this project.

## polygons

This script is an export of a QGIS 3 model created with the Model Builder. Its purpose is transforming a georeferenced old cadastral map in raster format, respresenting one cadastral polygon, in order to obtain a vector shape approximating said cadastral polygon.

## metadata

This script generates one XML metadata file for every georeferenced raster map corresponding to one cadastral polygon. This is accomplished by modifying a template, and using information from a CSV containing the mean displacements from the georeferencing, plus some functions from the GDAL package.

## geoserver_groups
This script takes advantage of the Geoserver REST API to create layer groups automatically, given the standardized naming used throughout the project. It also includes some extra code used to change the default layer styles or blending mode via the API.

## Contact information
Álvaro Verdú-Candela
Department of Cartographic Engineering, Geodesy and Photogrammetry. Universitat Politècnica de València. Camino de Vera s/n, 46022, Valencia, Spain; 
alvercan@etsii.upv.es
