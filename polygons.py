"""
Model exported as python.
Name : REN_RUS Poligonos
Group : 
With QGIS : 33001

This script is an export of a QGIS 3 model created with the Model Builder. 
Its purpose is transforming a georeferenced old cadastral map in raster format, 
respresenting one cadastral polygon, in order to obtain a vector shape approximating 
said cadastral polygon.
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Ren_rusPoligonos(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterNumber('distanciabuffer', 'DistanciaBuffer', type=QgsProcessingParameterNumber.Double, minValue=0, defaultValue=15))
        self.addParameter(QgsProcessingParameterRasterLayer('entrada', 'entrada', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('polgonosctpigc', 'Pol�gonos CTP_IGC', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Final', 'Final', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(17, model_feedback)
        results = {}
        outputs = {}

        # Extraer por atributo
        alg_params = {
            'FIELD': 'pol',
            'INPUT': parameters['polgonosctpigc'],
            'OPERATOR': 0,  # =
            'VALUE': QgsExpression(" substr(layer_property( @entrada ,'name'),15,3)").evaluate(),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtraerPorAtributo'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Traducir (convertir formato)
        alg_params = {
            'COPY_SUBDATASETS': False,
            'DATA_TYPE': 0,  # Usar el tipo de datos de la capa de entrada
            'EXTRA': '-outsize 40% 0 -b 1 -r average',
            'INPUT': parameters['entrada'],
            'NODATA': None,
            'OPTIONS': '',
            'TARGET_CRS': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TraducirConvertirFormato'] = processing.run('gdal:translate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Buffer CTP
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': QgsExpression(' @distanciabuffer /2').evaluate(),
            'END_CAP_STYLE': 0,  # Redondo
            'INPUT': outputs['ExtraerPorAtributo']['OUTPUT'],
            'JOIN_STYLE': 1,  # Inglete
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferCtp'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Combar (reproyectar)
        alg_params = {
            'DATA_TYPE': 0,  # Usar el tipo de datos de la capa de entrada
            'EXTRA': '-srcnodata 1',
            'INPUT': outputs['TraducirConvertirFormato']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Vecino m�s pr�ximo
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CombarReproyectar'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # P�xeles r�ster a puntos
        alg_params = {
            'FIELD_NAME': 'VALUE',
            'INPUT_RASTER': outputs['CombarReproyectar']['OUTPUT'],
            'RASTER_BAND': 1,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PxelesRsterAPuntos'] = processing.run('native:pixelstopoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Intersecci�n CTP
        alg_params = {
            'INPUT': outputs['PxelesRsterAPuntos']['OUTPUT'],
            'INPUT_FIELDS': [''],
            'OVERLAY': outputs['BufferCtp']['OUTPUT'],
            'OVERLAY_FIELDS': [''],
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['InterseccinCtp'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': parameters['distanciabuffer'],
            'END_CAP_STYLE': 0,  # Redondo
            'INPUT': outputs['InterseccinCtp']['OUTPUT'],
            'JOIN_STYLE': 1,  # Inglete
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Borrar agujeros
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'MIN_AREA': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BorrarAgujeros'] = processing.run('native:deleteholes', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Debuffer-buffer
        alg_params = {
            'Distancia': QgsExpression(' @distanciabuffer /2').evaluate(),
            'Poligonos': outputs['BorrarAgujeros']['OUTPUT'],
            'native:buffer_2:Final': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Debufferbuffer'] = processing.run('model:Debuffer-buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Filtrar por tipo de geometr�a
        alg_params = {
            'INPUT': outputs['Debufferbuffer']['native:buffer_2:Final'],
            'POLYGONS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FiltrarPorTipoDeGeometra'] = processing.run('native:filterbygeometry', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Multiparte a monoparte
        alg_params = {
            'INPUT': outputs['FiltrarPorTipoDeGeometra']['POLYGONS'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultiparteAMonoparte'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Mantener las N partes mas grandes
        alg_params = {
            'PARTS': 1,
            'POLYGONS': outputs['MultiparteAMonoparte']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MantenerLasNPartesMasGrandes'] = processing.run('qgis:keepnbiggestparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Simplificar
        alg_params = {
            'INPUT': outputs['MantenerLasNPartesMasGrandes']['OUTPUT'],
            'METHOD': 0,  # Distancia (Douglas-Peucker)
            'TOLERANCE': QgsExpression(' @distanciabuffer *1.5').evaluate(),
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Simplificar'] = processing.run('native:simplifygeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Filtrar por tipo de geometr�a 2
        alg_params = {
            'INPUT': outputs['Simplificar']['OUTPUT'],
            'POLYGONS': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FiltrarPorTipoDeGeometra2'] = processing.run('native:filterbygeometry', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Buffer final
        alg_params = {
            'DISSOLVE': True,
            'DISTANCE': QgsExpression('- @distanciabuffer /4').evaluate(),
            'END_CAP_STYLE': 0,  # Redondo
            'INPUT': outputs['FiltrarPorTipoDeGeometra2']['POLYGONS'],
            'JOIN_STYLE': 1,  # Inglete
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BufferFinal'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Rehacer campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': "layer_property(@entrada ,'name')",'length': 50,'name': 'capa','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': "substr(layer_property(@entrada ,'name'),1,7)",'length': 7,'name': 'serie','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': "substr(layer_property(@entrada ,'name'),9,5)",'length': 5,'name': 'mun','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': "substr(layer_property(@entrada ,'name'),15,3)",'length': 3,'name': 'pol','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'expression': "substr(layer_property(@entrada ,'name'),19,1)",'length': 1,'name': 'hoja','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}],
            'INPUT': outputs['BufferFinal']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RehacerCampos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Mantener las N partes mas grandes 2
        alg_params = {
            'PARTS': 1,
            'POLYGONS': outputs['RehacerCampos']['OUTPUT'],
            'OUTPUT': parameters['Final']
        }
        outputs['MantenerLasNPartesMasGrandes2'] = processing.run('qgis:keepnbiggestparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Final'] = outputs['MantenerLasNPartesMasGrandes2']['OUTPUT']
        return results

    def name(self):
        return 'REN_RUS Poligonos'

    def displayName(self):
        return 'REN_RUS Poligonos'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Ren_rusPoligonos()
