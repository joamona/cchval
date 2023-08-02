"""
This script generates one XML metadata file for every georeferenced raster map 
corresponding to one cadastral polygon. This is accomplished by modifying a template, 
and using information from a CSV containing the mean displacements from the georeferencing, 
plus some functions from the GDAL package.
"""


import csv
from osgeo import gdal, ogr, osr

URL_SERVER = 'https://myserver.com/my_file_folder/'

municipio = '46021' # Municipality code
municipio_nombre = 'ALDAIA' # Municipality name
serie = 'CTP_IGC' # Series code
serie_nombre = 'Catastro Topográfico Parcelario' # Series name
fecha = '2022-04-13' # Date of creation
escala='2000' # Map scale

line_count = 0

"""
A loop is executed using a CSV file containing the displacement information separated by cadastral polygons.
That file has the following structure, as an example:

pol,hoja,count,unique,min,max,range,sum,mean,median,stddev,minority,majority,q1,q3,iqr
"25","1","18","18",1.89523355087113,13.9407256824486,12.0454921315775,128.069993887759,7.11499966043106,6.80090727174679,3.30691046103146,1.89523355087113,1.89523355087113,4.48511228296756,9.43558440822901,4.95047212526145
...

"""
with open('CTP_IGC_estadisticas.csv', 'r', encoding='utf-8') as estadisticas_puntos:
    csv_reader = csv.reader(estadisticas_puntos, delimiter=',')
    for row in csv_reader:
        
        claves = {}

        # Discard the header
        if line_count == 0:
            line_count += 1
        else:
            poligono = row[0] # Cadastral polygon ID
            hoja = row[1] # Sheet number

            ruta=f'C:\\Users\\alvar\\Documents\\Catastro\\GeoTIFF\\{serie}\\{serie}_{municipio}_{poligono.zfill(3)}-{hoja}.tif' # Path to the georeferenced raster

            # Extent in geographic coordinates, using GDAL
            src=gdal.Open(ruta)
            ulx, xres, xskew, uly, yskew, yres  = src.GetGeoTransform()
            lrx = ulx + (src.RasterXSize * xres)
            lry = uly + (src.RasterYSize * yres)

            source = osr.SpatialReference()
            source.ImportFromWkt(src.GetProjection())
            target = osr.SpatialReference()
            target.ImportFromEPSG(4326)
            transform = osr.CoordinateTransformation(source, target)

            # Key definition

            # File identifier
            claves['identificador'] = serie+'_' + municipio+'_'+poligono.zfill(3)+'-'+hoja

            # Date
            claves['fecha'] = fecha

            # Description
            claves['descripcion'] = f'Municipio de {municipio_nombre}. {serie_nombre}. Polígono {poligono.zfill(3)}, hoja {hoja}. Plano Georreferenciado'

            # Mean displacement
            claves['error_medio'] = row[8]

            # URLs to resources
            claves['url_plano']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/planos_georreferenciados/{serie}_{municipio}_{poligono.zfill(3)}-{hoja}.tif'
            claves['url_original']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/planos_originales/{serie}_{municipio}_{poligono.zfill(3)}-{hoja}_original.tif'
            claves['url_puntos']=f'{URL_SERVER}/{serie}/{municipio}/{serie}_{municipio}_puntos.gml'
            claves['url_fichaspropietarios']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/{serie}_{municipio}_{poligono.zfill(3)}_fichaspropietarios.zip'
            claves['url_croquis']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/{serie}_{municipio}_{poligono.zfill(3)}_croquis.zip'
            claves['url_caracteristicas']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/{serie}_{municipio}_{poligono.zfill(3)}_hojas_caracteristicas.zip'
            claves['url_libretacampo']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/{serie}_{municipio}_{poligono.zfill(3)}_libreta_campo.zip'
            claves['url_fichasavance']=f'{URL_SERVER}/{serie}/{municipio}/{poligono.zfill(3)}/{serie}_{municipio}_{poligono.zfill(3)}_avance_fichas.zip'
            
            # Number of pixel rows and columns in raster
            claves['num_filas']=str(src.RasterYSize)
            claves['num_columnas']=str(src.RasterXSize)

            # GSD
            claves['GSD']=str(xres)

            # Scale
            claves['escala']=escala

            # Bounding box
            claves['lim_oeste']=str(transform.TransformPoint(ulx, uly)[0])
            claves['lim_este']=str(transform.TransformPoint(lrx, lry)[0])
            claves['lim_norte']=str(transform.TransformPoint(ulx, uly)[1])
            claves['lim_sur']=str(transform.TransformPoint(lrx, lry)[1])

            # Map series code
            claves['serie']=serie

            """
            Using a metadata template, where all previously defined keys are put inside double brackets in place of the content.

            As an example:
            <gmd:fileIdentifier>
                <gco:CharacterString>{{identificador}}</gco:CharacterString>
            </gmd:fileIdentifier>

            In that way, a simple search and replace can substitute all values in the template simply searching for the corresponding key
            """
            with open('plantilla.xml', 'r', encoding='utf-8') as plantilla:
                metadato = plantilla.read()

                # Metadata template file path
                ruta_metadato=f'C:\\Users\\alvar\\Documents\\Catastro\\Metadatos\\{serie}_{municipio}_{poligono.zfill(3)}-{hoja}.xml'

                # For every key in dict, search and replace with its value
                for clave in claves:
                    search_text='{{'+clave+'}}'
                    replace_text=claves[clave]
                    metadato=metadato.replace(search_text,replace_text)
                
                # Save the file using the standardized filename for each polygon and sheet
                with open(ruta_metadato,'w', encoding='utf-8') as file:
                    file.write(metadato)

            
                
