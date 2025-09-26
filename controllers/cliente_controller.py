"""
Controlador para el módulo de Clientes
Maneja la lógica de negocio entre la vista y el modelo
"""
from models.cliente import Cliente
from utils.exceptions import ValidationError, DatabaseError, RecordNotFoundError, ClienteError
from utils.formatters import NumberFormatter
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ClienteController:
    """
    Controlador para gestionar la lógica de negocio de clientes
    """
    
    def __init__(self):
        self.cliente_model = Cliente()
    
    def crear_cliente(self, nombre_completo, numero_identificacion=None, 
                     contacto_telefono=None, contacto_email=None):
        """
        Crear un nuevo cliente con validaciones de negocio
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Returns:
            dict: Resultado de la operación con éxito/error y mensaje
        """
        try:
            # Validar datos de entrada
            validation_result = self.validar_datos_cliente(
                nombre_completo, numero_identificacion, contacto_telefono, contacto_email
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"Error de validación: {', '.join(validation_result['errors'])}"
                }
            
            # Crear cliente
            resultado = self.cliente_model.crear_cliente(
                nombre_completo=nombre_completo.strip(),
                numero_identificacion=numero_identificacion.strip() if numero_identificacion else None,
                contacto_telefono=contacto_telefono.strip() if contacto_telefono else None,
                contacto_email=contacto_email.strip().lower() if contacto_email else None
            )
            
            if resultado['success']:
                return {
                    'success': True,
                    'message': f'Cliente creado exitosamente con ID: {resultado["cliente_id"]}',
                    'cliente_id': resultado['cliente_id']
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
            
        except Exception as e:
            logger.error(f"Error inesperado al crear cliente: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_cliente(self, cliente_id):
        """
        Obtener un cliente por ID con formato para la vista
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            dict: Resultado con datos del cliente formateados
        """
        try:
            resultado = self.cliente_model.obtener_cliente_por_id(cliente_id)
            
            if resultado['success']:
                # Formatear datos para la vista
                cliente_formateado = self._formatear_cliente_para_vista(resultado['cliente'])
                
                return {
                    'success': True,
                    'data': cliente_formateado
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo cliente {cliente_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_cliente_por_identificacion(self, numero_identificacion):
        """
        Obtener un cliente por número de identificación
        
        Args:
            numero_identificacion (str): Número de identificación
            
        Returns:
            dict: Resultado con datos del cliente
        """
        try:
            resultado = self.cliente_model.obtener_cliente_por_identificacion(numero_identificacion)
            
            if resultado['success']:
                cliente_formateado = self._formatear_cliente_para_vista(resultado['cliente'])
                return {
                    'success': True,
                    'data': cliente_formateado
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo cliente por identificación {numero_identificacion}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def listar_clientes(self, filtro_nombre=None, orden='nombre_completo'):
        """
        Obtener lista de clientes con filtros y formato para la vista
        
        Args:
            filtro_nombre (str): Filtro de búsqueda
            orden (str): Campo de ordenamiento
            
        Returns:
            dict: Resultado con lista de clientes formateados
        """
        try:
            clientes = self.cliente_model.obtener_todos_clientes(
                filtro_nombre=filtro_nombre, 
                order_by=orden
            )
            
            # Formatear clientes para la vista
            clientes_formateados = [
                self._formatear_cliente_para_vista(cliente) 
                for cliente in clientes
            ]
            
            return {
                'success': True,
                'data': clientes_formateados,
                'total': len(clientes_formateados)
            }
            
        except Exception as e:
            logger.error(f"Error listando clientes: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': []
            }
    
    def actualizar_cliente(self, cliente_id, **kwargs):
        """
        Actualizar un cliente existente
        
        Args:
            cliente_id (int): ID del cliente
            **kwargs: Campos a actualizar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar que hay campos para actualizar
            campos_validos = ['nombre_completo', 'numero_identificacion', 
                             'contacto_telefono', 'contacto_email']
            campos_actualizar = {k: v for k, v in kwargs.items() if k in campos_validos}
            
            if not campos_actualizar:
                return {
                    'success': False,
                    'message': 'No se proporcionaron campos válidos para actualizar'
                }
            
            # Validar datos si se están actualizando campos críticos
            if any(campo in campos_actualizar for campo in ['nombre_completo', 'numero_identificacion', 
                                                           'contacto_telefono', 'contacto_email']):
                # Obtener cliente actual para validación completa
                cliente_actual = self.cliente_model.obtener_cliente_por_id(cliente_id)
                if not cliente_actual['success']:
                    return {
                        'success': False,
                        'message': f'Cliente con ID {cliente_id} no encontrado'
                    }
                
                # Combinar datos actuales con nuevos para validación
                datos_completos = cliente_actual['cliente'].copy()
                datos_completos.update(campos_actualizar)
                
                validation_result = self.validar_datos_cliente(
                    datos_completos.get('nombre_completo'),
                    datos_completos.get('numero_identificacion'),
                    datos_completos.get('contacto_telefono'),
                    datos_completos.get('contacto_email')
                )
                
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'message': f"Error de validación: {', '.join(validation_result['errors'])}"
                    }
            
            # Limpiar datos
            if 'nombre_completo' in campos_actualizar:
                campos_actualizar['nombre_completo'] = campos_actualizar['nombre_completo'].strip()
            if 'numero_identificacion' in campos_actualizar:
                campos_actualizar['numero_identificacion'] = campos_actualizar['numero_identificacion'].strip() if campos_actualizar['numero_identificacion'] else None
            if 'contacto_telefono' in campos_actualizar:
                campos_actualizar['contacto_telefono'] = campos_actualizar['contacto_telefono'].strip() if campos_actualizar['contacto_telefono'] else None
            if 'contacto_email' in campos_actualizar:
                campos_actualizar['contacto_email'] = campos_actualizar['contacto_email'].strip().lower() if campos_actualizar['contacto_email'] else None
            
            # Actualizar cliente
            resultado = self.cliente_model.actualizar_cliente(cliente_id, **campos_actualizar)
            
            if resultado['success']:
                return {
                    'success': True,
                    'message': 'Cliente actualizado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
                
        except Exception as e:
            logger.error(f"Error actualizando cliente {cliente_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def eliminar_cliente(self, cliente_id):
        """
        Eliminar un cliente con validaciones de negocio
        
        Args:
            cliente_id (int): ID del cliente a eliminar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validaciones adicionales de negocio
            if self.cliente_model.tiene_facturas(cliente_id):
                return {
                    'success': False,
                    'message': 'No se puede eliminar el cliente porque tiene facturas asociadas. '
                              'Considere desactivar el cliente en lugar de eliminarlo.'
                }
            
            # Eliminar cliente
            resultado = self.cliente_model.eliminar_cliente(cliente_id)
            
            if resultado['success']:
                return {
                    'success': True,
                    'message': 'Cliente eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
                
        except Exception as e:
            logger.error(f"Error eliminando cliente {cliente_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def buscar_clientes(self, termino_busqueda):
        """
        Buscar clientes por término de búsqueda
        
        Args:
            termino_busqueda (str): Término a buscar
            
        Returns:
            dict: Resultado con lista de clientes encontrados
        """
        try:
            if not termino_busqueda or not termino_busqueda.strip():
                return {
                    'success': True,
                    'data': [],
                    'message': 'Término de búsqueda vacío'
                }
            
            clientes = self.cliente_model.buscar_clientes(termino_busqueda.strip())
            
            # Formatear clientes para la vista
            clientes_formateados = [
                self._formatear_cliente_para_vista(cliente) 
                for cliente in clientes
            ]
            
            return {
                'success': True,
                'data': clientes_formateados,
                'total': len(clientes_formateados),
                'message': f'Se encontraron {len(clientes_formateados)} clientes'
            }
            
        except Exception as e:
            logger.error(f"Error buscando clientes: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': []
            }
    
    def obtener_historial_compras(self, cliente_id, limite=None):
        """
        Obtener historial de compras de un cliente
        
        Args:
            cliente_id (int): ID del cliente
            limite (int): Límite de registros
            
        Returns:
            dict: Resultado con historial de compras
        """
        try:
            historial = self.cliente_model.obtener_historial_compras(cliente_id, limite)
            
            # Formatear historial para la vista
            historial_formateado = []
            for factura in historial:
                factura_formateada = {
                    'id': factura['id'],
                    'numero_factura': factura['numero_factura'],
                    'fecha_factura': factura['fecha_factura'].strftime('%Y-%m-%d') if factura['fecha_factura'] else '',
                    'total_factura': NumberFormatter.format_currency(factura['total_factura']),
                    'total_factura_raw': float(factura['total_factura']),
                    'estado': factura['estado'],
                    'total_items': factura['total_items'],
                    'total_pagado': NumberFormatter.format_currency(factura['total_pagado']),
                    'total_pagado_raw': float(factura['total_pagado']),
                    'saldo_pendiente': NumberFormatter.format_currency(
                        float(factura['total_factura']) - float(factura['total_pagado'])
                    ),
                    'saldo_pendiente_raw': float(factura['total_factura']) - float(factura['total_pagado'])
                }
                historial_formateado.append(factura_formateada)
            
            return {
                'success': True,
                'data': historial_formateado,
                'total': len(historial_formateado)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de compras del cliente {cliente_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': []
            }
    
    def obtener_estadisticas_cliente(self, cliente_id):
        """
        Obtener estadísticas de un cliente
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            dict: Resultado con estadísticas del cliente
        """
        try:
            estadisticas = self.cliente_model.obtener_estadisticas_cliente(cliente_id)
            
            # Formatear estadísticas para la vista
            estadisticas_formateadas = {
                'total_facturas': estadisticas['total_facturas'],
                'total_compras': NumberFormatter.format_currency(estadisticas['total_compras']),
                'total_compras_raw': float(estadisticas['total_compras']),
                'total_pendiente': NumberFormatter.format_currency(estadisticas['total_pendiente']),
                'total_pendiente_raw': float(estadisticas['total_pendiente']),
                'promedio_compra': NumberFormatter.format_currency(estadisticas['promedio_compra']),
                'promedio_compra_raw': float(estadisticas['promedio_compra']),
                'ultima_compra': estadisticas['ultima_compra'].strftime('%Y-%m-%d') if estadisticas['ultima_compra'] else 'Sin compras'
            }
            
            return {
                'success': True,
                'data': estadisticas_formateadas
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del cliente {cliente_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': {}
            }
    
    def validar_datos_cliente(self, nombre_completo, numero_identificacion=None, 
                             contacto_telefono=None, contacto_email=None):
        """
        Validar datos del cliente usando el modelo
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Returns:
            dict: Resultado de validación con 'valid' (bool) y 'errors' (list)
        """
        try:
            return self.cliente_model.validate_cliente_data(
                nombre_completo, numero_identificacion, contacto_telefono, contacto_email
            )
        except Exception as e:
            logger.error(f"Error validando datos del cliente: {str(e)}")
            return {
                'valid': False,
                'errors': [f'Error de validación: {str(e)}']
            }
    
    def _formatear_cliente_para_vista(self, cliente):
        """
        Formatear datos del cliente para la vista
        
        Args:
            cliente (dict): Datos del cliente desde la base de datos
            
        Returns:
            dict: Cliente formateado para la vista
        """
        try:
            return {
                'id': cliente['id'],
                'tipo_identificacion': cliente.get('tipo_identificacion', 'CC'),  # Valor por defecto
                'numero_identificacion': cliente['numero_identificacion'] or '',
                'nombre': cliente['nombre_completo'],
                'email': cliente['contacto_email'] or '',
                'telefono': cliente['contacto_telefono'] or '',
                'ciudad': cliente.get('ciudad', ''),
                'fecha_creacion': cliente['fecha_creacion'].strftime('%Y-%m-%d %H:%M') if cliente['fecha_creacion'] else '',
                'fecha_actualizacion': cliente['fecha_actualizacion'].strftime('%Y-%m-%d %H:%M') if cliente['fecha_actualizacion'] else '',
                'fecha_creacion_raw': cliente['fecha_creacion'],
                'fecha_actualizacion_raw': cliente['fecha_actualizacion'],
                # Mantener también los nombres originales para compatibilidad
                'nombre_completo': cliente['nombre_completo'],
                'contacto_email': cliente['contacto_email'] or '',
                'contacto_telefono': cliente['contacto_telefono'] or ''
            }
        except Exception as e:
            logger.error(f"Error formateando cliente para vista: {str(e)}")
            return cliente
    
    def obtener_estadisticas_generales(self):
        """
        Obtener estadísticas generales de clientes
        
        Returns:
            dict: Estadísticas generales
        """
        try:
            # Obtener todos los clientes para calcular estadísticas
            resultado_clientes = self.listar_clientes()
            
            if not resultado_clientes['success']:
                return {
                    'success': False,
                    'message': 'Error obteniendo clientes para estadísticas'
                }
            
            total_clientes = resultado_clientes['total']
            
            # Calcular estadísticas adicionales si es necesario
            estadisticas = {
                'total_clientes': total_clientes,
                'clientes_activos': total_clientes,  # Por ahora todos son activos
                'nuevos_este_mes': 0,  # Placeholder por ahora
                'clientes_con_identificacion': 0,
                'clientes_con_telefono': 0,
                'clientes_con_email': 0
            }
            
            for cliente in resultado_clientes['data']:
                if cliente['numero_identificacion']:
                    estadisticas['clientes_con_identificacion'] += 1
                if cliente['contacto_telefono']:
                    estadisticas['clientes_con_telefono'] += 1
                if cliente['contacto_email']:
                    estadisticas['clientes_con_email'] += 1
            
            return {
                'success': True,
                'data': estadisticas
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas generales: {str(e)}")
            return {
                'success': False,
                'message': f'Error obteniendo estadísticas: {str(e)}'
            }
            logger.error(f"Error obteniendo estadísticas generales: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'data': {}
            }