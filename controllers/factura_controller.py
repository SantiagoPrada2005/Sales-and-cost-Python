"""
Controlador para el módulo de Facturas
Maneja la lógica de negocio entre la vista y el modelo
"""
from models.factura import Factura
from models.cliente import Cliente
from models.producto import Producto
from utils.exceptions import ValidationError, DatabaseError, FacturaError
from utils.formatters import CurrencyFormatter, NumberFormatter, DateFormatter
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class FacturaController:
    """
    Controlador para gestionar la lógica de negocio de facturas
    """
    
    def __init__(self):
        self.factura_model = Factura()
        self.cliente_model = Cliente()
        self.producto_model = Producto()
        self.currency_formatter = CurrencyFormatter()
        self.date_formatter = DateFormatter()
    
    def crear_factura(self, cliente_id, observaciones=None):
        """
        Crear una nueva factura con validaciones de negocio
        
        Args:
            cliente_id (int): ID del cliente
            observaciones (str): Observaciones opcionales
            
        Returns:
            dict: Resultado de la operación con éxito/error y mensaje
        """
        try:
            # Validar que el cliente existe y está activo
            cliente_result = self.cliente_model.obtener_cliente_por_id(cliente_id)
            if not cliente_result['success']:
                return {
                    'success': False,
                    'message': 'El cliente especificado no existe'
                }
            
            # Crear factura
            resultado = self.factura_model.crear_factura(
                cliente_id=cliente_id,
                observaciones=observaciones
            )
            
            if resultado['success']:
                logger.info(f"Factura creada exitosamente: {resultado['data']['numero_factura']}")
                return {
                    'success': True,
                    'message': f'Factura {resultado["data"]["numero_factura"]} creada exitosamente',
                    'data': resultado['data']
                }
            else:
                return resultado
            
        except Exception as e:
            logger.error(f"Error inesperado al crear factura: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_factura(self, factura_id):
        """
        Obtener una factura por ID con formato para la vista
        
        Args:
            factura_id (int): ID de la factura
            
        Returns:
            dict: Resultado con datos de la factura formateados
        """
        try:
            resultado = self.factura_model.obtener_factura_por_id(factura_id)
            
            if resultado['success']:
                # Formatear datos para la vista
                factura_formateada = self._formatear_factura_para_vista(resultado['data'])
                
                # Obtener detalles de la factura
                detalles_result = self.factura_model.obtener_detalles_factura(factura_id)
                if detalles_result['success']:
                    factura_formateada['detalles'] = [
                        self._formatear_detalle_para_vista(detalle) 
                        for detalle in detalles_result['data']
                    ]
                
                return {
                    'success': True,
                    'data': factura_formateada
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al obtener factura: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def listar_facturas(self, filtros=None):
        """
        Obtener lista de facturas con filtros y formato para la vista
        
        Args:
            filtros (dict): Filtros opcionales
            
        Returns:
            dict: Resultado con lista de facturas formateadas
        """
        try:
            resultado = self.factura_model.obtener_todas_facturas(filtros)
            
            if resultado['success']:
                # Formatear facturas para la vista
                facturas_formateadas = [
                    self._formatear_factura_para_lista(factura) 
                    for factura in resultado['data']
                ]
                
                return {
                    'success': True,
                    'data': facturas_formateadas,
                    'message': f'Se encontraron {len(facturas_formateadas)} facturas'
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al listar facturas: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def agregar_producto_a_factura(self, factura_id, producto_id, cantidad, precio_unitario=None):
        """
        Agregar un producto a una factura con validaciones de negocio
        
        Args:
            factura_id (int): ID de la factura
            producto_id (int): ID del producto
            cantidad (int): Cantidad del producto
            precio_unitario (float): Precio unitario opcional
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar que la factura existe y está en borrador
            factura_result = self.factura_model.obtener_factura_por_id(factura_id)
            if not factura_result['success']:
                return factura_result
            
            if factura_result['data']['estado'] != 'borrador':
                return {
                    'success': False,
                    'message': 'Solo se pueden modificar facturas en estado borrador'
                }
            
            # Validar que el producto existe
            producto_result = self.producto_model.obtener_producto_por_id(producto_id)
            if not producto_result['success']:
                return {
                    'success': False,
                    'message': 'El producto especificado no existe'
                }
            
            producto = producto_result['data']
            
            # Validar cantidad
            if cantidad <= 0:
                return {
                    'success': False,
                    'message': 'La cantidad debe ser mayor a cero'
                }
            
            # Validar stock disponible
            if producto['stock_actual'] < cantidad:
                return {
                    'success': False,
                    'message': f'Stock insuficiente. Disponible: {producto["stock_actual"]}'
                }
            
            # Usar precio del producto si no se especifica
            if precio_unitario is None:
                precio_unitario = float(producto['precio_venta'])
            else:
                precio_unitario = float(precio_unitario)
                
                # Validar que el precio no sea negativo
                if precio_unitario < 0:
                    return {
                        'success': False,
                        'message': 'El precio unitario no puede ser negativo'
                    }
            
            # Agregar producto a la factura
            resultado = self.factura_model.agregar_detalle(
                factura_id=factura_id,
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
            
            if resultado['success']:
                logger.info(f"Producto agregado a factura {factura_id}: {producto['nombre']} x{cantidad}")
                return {
                    'success': True,
                    'message': f'Producto "{producto["nombre"]}" agregado exitosamente',
                    'data': resultado['data']
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al agregar producto a factura: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def actualizar_detalle_factura(self, detalle_id, cantidad, precio_unitario):
        """
        Actualizar un detalle de factura
        
        Args:
            detalle_id (int): ID del detalle
            cantidad (int): Nueva cantidad
            precio_unitario (float): Nuevo precio unitario
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar datos
            if cantidad <= 0:
                return {
                    'success': False,
                    'message': 'La cantidad debe ser mayor a cero'
                }
            
            if precio_unitario < 0:
                return {
                    'success': False,
                    'message': 'El precio unitario no puede ser negativo'
                }
            
            # Actualizar detalle
            resultado = self.factura_model.actualizar_detalle(
                detalle_id=detalle_id,
                cantidad=cantidad,
                precio_unitario=float(precio_unitario)
            )
            
            if resultado['success']:
                logger.info(f"Detalle actualizado: ID {detalle_id}")
                return {
                    'success': True,
                    'message': 'Detalle actualizado exitosamente',
                    'data': resultado['data']
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al actualizar detalle: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def eliminar_detalle_factura(self, detalle_id):
        """
        Eliminar un detalle de factura
        
        Args:
            detalle_id (int): ID del detalle
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            resultado = self.factura_model.eliminar_detalle(detalle_id)
            
            if resultado['success']:
                logger.info(f"Detalle eliminado: ID {detalle_id}")
                return {
                    'success': True,
                    'message': 'Producto eliminado de la factura exitosamente'
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al eliminar detalle: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def confirmar_factura(self, factura_id):
        """
        Confirmar una factura (cambiar de borrador a confirmada)
        
        Args:
            factura_id (int): ID de la factura
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validaciones adicionales de negocio
            factura_result = self.factura_model.obtener_factura_por_id(factura_id)
            if not factura_result['success']:
                return factura_result
            
            factura = factura_result['data']
            
            # Validar que la factura tenga un total mayor a cero
            if factura['total_factura'] <= 0:
                return {
                    'success': False,
                    'message': 'La factura debe tener un total mayor a cero'
                }
            
            # Confirmar factura
            resultado = self.factura_model.confirmar_factura(factura_id)
            
            if resultado['success']:
                logger.info(f"Factura confirmada: {factura['numero_factura']}")
                return {
                    'success': True,
                    'message': f'Factura {factura["numero_factura"]} confirmada exitosamente'
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al confirmar factura: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def anular_factura(self, factura_id, motivo=None):
        """
        Anular una factura
        
        Args:
            factura_id (int): ID de la factura
            motivo (str): Motivo de anulación
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar motivo si se proporciona
            if motivo and len(motivo.strip()) == 0:
                motivo = None
            
            resultado = self.factura_model.anular_factura(factura_id, motivo)
            
            if resultado['success']:
                factura_result = self.factura_model.obtener_factura_por_id(factura_id)
                numero_factura = factura_result['data']['numero_factura'] if factura_result['success'] else factura_id
                
                logger.info(f"Factura anulada: {numero_factura}")
                return {
                    'success': True,
                    'message': f'Factura {numero_factura} anulada exitosamente'
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al anular factura: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_clientes_activos(self):
        """
        Obtener lista de clientes activos para selección en facturas
        
        Returns:
            dict: Resultado con lista de clientes
        """
        try:
            resultado = self.cliente_model.obtener_todos_clientes()
            
            if resultado['success']:
                # Formatear clientes para combo box
                clientes_formateados = [
                    {
                        'id': cliente['id'],
                        'nombre': cliente['nombre_completo'],
                        'identificacion': cliente.get('numero_identificacion', ''),
                        'display_text': f"{cliente['nombre_completo']} - {cliente.get('numero_identificacion', 'Sin ID')}"
                    }
                    for cliente in resultado['data']
                ]
                
                return {
                    'success': True,
                    'data': clientes_formateados
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al obtener clientes: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_productos_disponibles(self):
        """
        Obtener lista de productos disponibles para agregar a facturas
        
        Returns:
            dict: Resultado con lista de productos
        """
        try:
            resultado = self.producto_model.listar_productos()
            
            if resultado['success']:
                # Filtrar productos con stock disponible
                productos_disponibles = [
                    {
                        'id': producto['id'],
                        'codigo_sku': producto['codigo_sku'],
                        'nombre': producto['nombre'],
                        'precio_venta': float(producto['precio_venta']),
                        'stock_actual': producto['stock_actual'],
                        'display_text': f"{producto['codigo_sku']} - {producto['nombre']} (Stock: {producto['stock_actual']})"
                    }
                    for producto in resultado['data']
                    if producto['stock_actual'] > 0
                ]
                
                return {
                    'success': True,
                    'data': productos_disponibles
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al obtener productos: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def buscar_productos(self, termino_busqueda):
        """
        Buscar productos por código SKU o nombre
        
        Args:
            termino_busqueda (str): Término de búsqueda
            
        Returns:
            dict: Resultado con productos encontrados
        """
        try:
            if not termino_busqueda or len(termino_busqueda.strip()) < 2:
                return {
                    'success': False,
                    'message': 'El término de búsqueda debe tener al menos 2 caracteres'
                }
            
            # Buscar por SKU primero
            resultado_sku = self.producto_model.obtener_producto_por_sku(termino_busqueda.strip())
            if resultado_sku['success']:
                producto = resultado_sku['data']
                if producto['stock_actual'] > 0:
                    return {
                        'success': True,
                        'data': [self._formatear_producto_para_busqueda(producto)]
                    }
            
            # Buscar por nombre
            resultado_nombre = self.producto_model.buscar_productos(termino_busqueda)
            if resultado_nombre['success']:
                productos_disponibles = [
                    self._formatear_producto_para_busqueda(producto)
                    for producto in resultado_nombre['data']
                    if producto['stock_actual'] > 0
                ]
                
                return {
                    'success': True,
                    'data': productos_disponibles
                }
            
            return {
                'success': True,
                'data': [],
                'message': 'No se encontraron productos disponibles'
            }
            
        except Exception as e:
            logger.error(f"Error al buscar productos: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_estadisticas_ventas(self, fecha_desde=None, fecha_hasta=None):
        """
        Obtener estadísticas de ventas formateadas para la vista
        
        Args:
            fecha_desde (date): Fecha de inicio
            fecha_hasta (date): Fecha de fin
            
        Returns:
            dict: Resultado con estadísticas formateadas
        """
        try:
            resultado = self.factura_model.obtener_estadisticas_ventas(fecha_desde, fecha_hasta)
            
            if resultado['success']:
                stats = resultado['data']
                
                # Formatear estadísticas para la vista
                estadisticas_formateadas = {
                    'total_facturas': stats['total_facturas'],
                    'facturas_confirmadas': stats['facturas_confirmadas'],
                    'facturas_borrador': stats['facturas_borrador'],
                    'facturas_anuladas': stats['facturas_anuladas'],
                    'total_ventas': self.currency_formatter.format_currency(stats['total_ventas']),
                    'total_ventas_raw': float(stats['total_ventas']),
                    'promedio_venta': self.currency_formatter.format_currency(stats['promedio_venta']),
                    'promedio_venta_raw': float(stats['promedio_venta']),
                    'periodo': {
                        'desde': fecha_desde.strftime('%d/%m/%Y') if fecha_desde else 'Inicio',
                        'hasta': fecha_hasta.strftime('%d/%m/%Y') if fecha_hasta else 'Hoy'
                    }
                }
                
                return {
                    'success': True,
                    'data': estadisticas_formateadas
                }
            else:
                return resultado
                
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def _formatear_factura_para_vista(self, factura):
        """Formatear factura para mostrar en la vista detallada"""
        return {
            'id': factura['id'],
            'numero_factura': factura['numero_factura'],
            'cliente_id': factura['cliente_id'],
            'cliente_nombre': factura['cliente_nombre'],
            'fecha_factura': self.date_formatter.format_date(factura['fecha_factura']),
            'fecha_factura_raw': factura['fecha_factura'],
            'subtotal_factura': self.currency_formatter.format_currency(factura['subtotal_factura']),
            'subtotal_factura_raw': float(factura['subtotal_factura']),
            'impuestos_factura': self.currency_formatter.format_currency(factura['impuestos_factura']),
            'impuestos_factura_raw': float(factura['impuestos_factura']),
            'total_factura': self.currency_formatter.format_currency(factura['total_factura']),
            'total_factura_raw': float(factura['total_factura']),
            'estado': factura['estado'],
            'estado_display': self._get_estado_display(factura['estado']),
            'observaciones': factura.get('observaciones', ''),
            'detalles': []  # Se llena por separado
        }
    
    def _formatear_factura_para_lista(self, factura):
        """Formatear factura para mostrar en la lista/tabla"""
        return {
            'id': factura['id'],
            'numero_factura': factura['numero_factura'],
            'cliente_nombre': factura['cliente_nombre'],
            'fecha_factura': self.date_formatter.format_date(factura['fecha_factura']),
            'total_factura': self.currency_formatter.format_currency(factura['total_factura']),
            'total_factura_raw': float(factura['total_factura']),
            'estado': factura['estado'],
            'estado_display': self._get_estado_display(factura['estado'])
        }
    
    def _formatear_detalle_para_vista(self, detalle):
        """Formatear detalle de factura para la vista"""
        subtotal = float(detalle['subtotal'])
        precio_unitario = float(detalle['precio_unitario'])
        
        return {
            'id': detalle['id'],
            'producto_id': detalle['producto_id'],
            'producto_codigo': detalle['producto_codigo'],
            'producto_nombre': detalle['producto_nombre'],
            'cantidad': detalle['cantidad'],
            'precio_unitario': self.currency_formatter.format_currency(precio_unitario),
            'precio_unitario_raw': float(precio_unitario),
            'subtotal': self.currency_formatter.format_currency(subtotal),
            'subtotal_raw': subtotal
        }
    
    def _formatear_producto_para_busqueda(self, producto):
        """Formatear producto para resultados de búsqueda"""
        return {
            'id': producto['id'],
            'codigo_sku': producto['codigo_sku'],
            'nombre': producto['nombre'],
            'precio_venta': float(producto['precio_venta']),
            'precio_venta_formatted': self.currency_formatter.format_currency(producto['precio_venta']),
            'stock_actual': producto['stock_actual'],
            'display_text': f"{producto['codigo_sku']} - {producto['nombre']} - {self.currency_formatter.format_currency(producto['precio_venta'])} (Stock: {producto['stock_actual']})"
        }
    
    def _get_estado_display(self, estado):
        """Obtener texto de display para el estado de la factura"""
        estados = {
            'borrador': 'Borrador',
            'confirmada': 'Confirmada',
            'pagada': 'Pagada',
            'anulada': 'Anulada'
        }
        return estados.get(estado, estado.title())
    
    def validar_datos_factura(self, cliente_id, observaciones=None):
        """
        Validar datos básicos de una factura
        
        Args:
            cliente_id (int): ID del cliente
            observaciones (str): Observaciones opcionales
            
        Returns:
            dict: Resultado de validación
        """
        errors = []
        
        # Validar cliente_id
        if not cliente_id or cliente_id <= 0:
            errors.append("Debe seleccionar un cliente válido")
        
        # Validar observaciones si se proporcionan
        if observaciones and len(observaciones) > 500:
            errors.append("Las observaciones no pueden exceder 500 caracteres")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }