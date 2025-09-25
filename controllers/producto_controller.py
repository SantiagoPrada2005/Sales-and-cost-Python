"""
Controlador para el módulo de Productos
Maneja la lógica de negocio entre la vista y el modelo
"""
from models.producto import Producto
from utils.exceptions import ValidationError, DatabaseError, RecordNotFoundError
from utils.formatters import CurrencyFormatter, NumberFormatter
import logging

logger = logging.getLogger(__name__)

class ProductoController:
    """
    Controlador para gestionar la lógica de negocio de productos
    """
    
    def __init__(self):
        self.producto_model = Producto()
    
    def crear_producto(self, codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta):
        """
        Crear un nuevo producto con validaciones de negocio
        
        Args:
            codigo_sku (str): Código SKU único
            nombre (str): Nombre del producto
            descripcion (str): Descripción del producto
            costo_adquisicion (float): Costo de adquisición
            precio_venta (float): Precio de venta
            
        Returns:
            dict: Resultado de la operación con éxito/error y mensaje
        """
        try:
            # Validar datos de entrada
            validation_result = self.validar_datos_producto(
                codigo_sku, nombre, costo_adquisicion, precio_venta
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"Error de validación: {', '.join(validation_result['errors'])}"
                }
            
            # Validaciones adicionales de negocio
            if precio_venta < costo_adquisicion:
                logger.warning(f"Producto {codigo_sku}: precio de venta menor al costo de adquisición")
            
            # Crear producto
            resultado = self.producto_model.crear_producto(
                codigo_sku=codigo_sku.strip().upper(),
                nombre=nombre.strip(),
                descripcion=descripcion.strip() if descripcion else None,
                costo_adquisicion=float(costo_adquisicion),
                precio_venta=float(precio_venta)
            )
            
            if resultado['success']:
                return {
                    'success': True,
                    'message': f'Producto creado exitosamente con ID: {resultado["producto_id"]}',
                    'producto_id': resultado['producto_id']
                }
            else:
                return {
                    'success': False,
                    'message': resultado['error']
                }
            
        except Exception as e:
            logger.error(f"Error inesperado al crear producto: {str(e)}")
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}'
            }
    
    def obtener_producto(self, producto_id):
        """
        Obtener un producto por ID con formato para la vista
        
        Args:
            producto_id (int): ID del producto
            
        Returns:
            dict: Resultado con datos del producto formateados
        """
        try:
            resultado = self.producto_model.obtener_producto_por_id(producto_id)
            
            if resultado['success']:
                # Formatear datos para la vista
                producto_formateado = self._formatear_producto_para_vista(resultado['data'])
                
                return {
                    'success': True,
                    'data': producto_formateado
                }
            else:
                return {
                    'success': False,
                    'error': resultado['error']
                }
                
        except Exception as e:
            logger.error(f"Error al obtener producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'error': f'Error al obtener producto: {str(e)}'
            }
    
    def obtener_producto_por_sku(self, codigo_sku):
        """
        Obtener un producto por código SKU
        
        Args:
            codigo_sku (str): Código SKU del producto
            
        Returns:
            dict: Resultado con datos del producto
        """
        try:
            producto = self.producto_model.obtener_producto_por_sku(codigo_sku.strip().upper())
            
            if producto:
                producto_formateado = self._formatear_producto_para_vista(producto)
                return {
                    'success': True,
                    'message': 'Producto encontrado',
                    'data': producto_formateado
                }
            else:
                return {
                    'success': False,
                    'message': f'Producto con SKU {codigo_sku} no encontrado',
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"Error al obtener producto por SKU {codigo_sku}: {str(e)}")
            return {
                'success': False,
                'message': f'Error al obtener producto: {str(e)}',
                'data': None
            }
    
    def listar_productos(self, filtro_nombre=None, orden='nombre'):
        """
        Listar todos los productos con filtros opcionales
        
        Args:
            filtro_nombre (str): Filtro por nombre (opcional)
            orden (str): Campo para ordenar
            
        Returns:
            dict: Resultado con lista de productos formateados
        """
        try:
            resultado = self.producto_model.obtener_todos_productos(
                filtro_nombre=filtro_nombre,
                order_by=orden
            )
            
            if resultado['success']:
                # Formatear productos para la vista
                productos_formateados = []
                for producto in resultado['data']:
                    productos_formateados.append(self._formatear_producto_para_vista(producto))
                
                return {
                    'success': True,
                    'data': productos_formateados
                }
            else:
                return {
                    'success': False,
                    'error': resultado['error']
                }
            
        except Exception as e:
            logger.error(f"Error al listar productos: {str(e)}")
            return {
                'success': False,
                'error': f'Error al listar productos: {str(e)}'
            }
    
    def actualizar_producto(self, producto_id, **kwargs):
        """
        Actualizar un producto existente
        
        Args:
            producto_id (int): ID del producto
            **kwargs: Campos a actualizar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Procesar y limpiar datos
            datos_actualizacion = {}
            
            if 'codigo_sku' in kwargs and kwargs['codigo_sku']:
                datos_actualizacion['codigo_sku'] = kwargs['codigo_sku'].strip().upper()
            
            if 'nombre' in kwargs and kwargs['nombre']:
                datos_actualizacion['nombre'] = kwargs['nombre'].strip()
            
            if 'descripcion' in kwargs:
                datos_actualizacion['descripcion'] = kwargs['descripcion'].strip() if kwargs['descripcion'] else None
            
            if 'costo_adquisicion' in kwargs and kwargs['costo_adquisicion'] is not None:
                datos_actualizacion['costo_adquisicion'] = float(kwargs['costo_adquisicion'])
            
            if 'precio_venta' in kwargs and kwargs['precio_venta'] is not None:
                datos_actualizacion['precio_venta'] = float(kwargs['precio_venta'])
            
            # Validación de negocio: precio vs costo
            if ('precio_venta' in datos_actualizacion and 'costo_adquisicion' in datos_actualizacion):
                if datos_actualizacion['precio_venta'] < datos_actualizacion['costo_adquisicion']:
                    logger.warning(f"Producto {producto_id}: precio de venta menor al costo de adquisición")
            
            # Actualizar producto
            resultado = self.producto_model.actualizar_producto(producto_id, **datos_actualizacion)
            
            if resultado:
                return {
                    'success': True,
                    'message': 'Producto actualizado exitosamente',
                    'data': {'id': producto_id}
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo actualizar el producto',
                    'data': None
                }
                
        except ValidationError as e:
            return {
                'success': False,
                'message': f'Error de validación: {str(e)}',
                'data': None
            }
        except RecordNotFoundError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error al actualizar producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error al actualizar producto: {str(e)}',
                'data': None
            }
    
    def eliminar_producto(self, producto_id):
        """
        Eliminar un producto
        
        Args:
            producto_id (int): ID del producto
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            resultado = self.producto_model.eliminar_producto(producto_id)
            
            if resultado:
                return {
                    'success': True,
                    'message': 'Producto eliminado exitosamente',
                    'data': {'id': producto_id}
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo eliminar el producto',
                    'data': None
                }
                
        except RecordNotFoundError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except DatabaseError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error al eliminar producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error al eliminar producto: {str(e)}',
                'data': None
            }
    
    def buscar_productos(self, termino_busqueda):
        """
        Buscar productos por término de búsqueda
        
        Args:
            termino_busqueda (str): Término de búsqueda
            
        Returns:
            dict: Resultado con productos encontrados
        """
        try:
            if not termino_busqueda or not termino_busqueda.strip():
                return {
                    'success': True,
                    'message': 'Término de búsqueda vacío',
                    'data': []
                }
            
            resultado = self.producto_model.buscar_productos(termino_busqueda.strip())
            
            if resultado.get('success'):
                productos = resultado.get('data', [])
                
                # Formatear productos para la vista
                productos_formateados = []
                for producto in productos:
                    productos_formateados.append(self._formatear_producto_para_vista(producto))
                
                return {
                    'success': True,
                    'message': f'Se encontraron {len(productos_formateados)} producto(s)',
                    'data': productos_formateados
                }
            else:
                return {
                    'success': False,
                    'message': resultado.get('error', 'Error en la búsqueda'),
                    'data': []
                }
            
        except Exception as e:
            logger.error(f"Error al buscar productos: {str(e)}")
            return {
                'success': False,
                'message': f'Error en la búsqueda: {str(e)}',
                'data': []
            }
    
    def obtener_productos_rentables(self, limite=10):
        """
        Obtener los productos más rentables
        
        Args:
            limite (int): Número de productos a retornar
            
        Returns:
            dict: Resultado con productos más rentables
        """
        try:
            productos = self.producto_model.obtener_productos_mas_rentables(limite)
            
            # Formatear productos para la vista
            productos_formateados = []
            for producto in productos:
                productos_formateados.append(self._formatear_producto_para_vista(producto))
            
            return {
                'success': True,
                'message': f'Top {len(productos_formateados)} productos más rentables',
                'data': productos_formateados
            }
            
        except Exception as e:
            logger.error(f"Error al obtener productos rentables: {str(e)}")
            return {
                'success': False,
                'message': f'Error al obtener productos rentables: {str(e)}',
                'data': []
            }
    
    def validar_datos_producto(self, codigo_sku, nombre, costo_adquisicion, precio_venta):
        """
        Validar datos de producto antes de crear/actualizar
        
        Args:
            codigo_sku (str): Código SKU
            nombre (str): Nombre del producto
            costo_adquisicion (float): Costo de adquisición
            precio_venta (float): Precio de venta
            
        Returns:
            dict: Resultado de la validación
        """
        errores = []
        
        # Validar código SKU
        if not codigo_sku or not codigo_sku.strip():
            errores.append("El código SKU es requerido")
        elif len(codigo_sku.strip()) > 50:
            errores.append("El código SKU no puede exceder 50 caracteres")
        
        # Validar nombre
        if not nombre or not nombre.strip():
            errores.append("El nombre del producto es requerido")
        elif len(nombre.strip()) > 255:
            errores.append("El nombre no puede exceder 255 caracteres")
        
        # Validar costo de adquisición
        try:
            costo = float(costo_adquisicion)
            if costo < 0:
                errores.append("El costo de adquisición debe ser positivo")
        except (ValueError, TypeError):
            errores.append("El costo de adquisición debe ser un número válido")
        
        # Validar precio de venta
        try:
            precio = float(precio_venta)
            if precio < 0:
                errores.append("El precio de venta debe ser positivo")
        except (ValueError, TypeError):
            errores.append("El precio de venta debe ser un número válido")
        
        # Validar relación precio-costo
        try:
            if float(precio_venta) < float(costo_adquisicion):
                errores.append("Advertencia: El precio de venta es menor al costo de adquisición")
        except (ValueError, TypeError):
            pass
        
        return {
            'valid': len(errores) == 0,
            'errors': errores
        }
    
    def _formatear_producto_para_vista(self, producto):
        """
        Formatear datos del producto para mostrar en la vista
        
        Args:
            producto (dict): Datos del producto
            
        Returns:
            dict: Producto formateado
        """
        if not producto:
            return None
        
        return {
            'id': producto.get('id'),
            'codigo_sku': producto.get('codigo_sku'),
            'nombre': producto.get('nombre'),
            'descripcion': producto.get('descripcion', ''),
            'costo_adquisicion': producto.get('costo_adquisicion'),
            'precio_venta': producto.get('precio_venta'),
            'margen_ganancia': producto.get('margen_ganancia', 0),
            'costo_adquisicion_formatted': CurrencyFormatter.format_currency(producto.get('costo_adquisicion', 0)),
            'precio_venta_formatted': CurrencyFormatter.format_currency(producto.get('precio_venta', 0)),
            'margen_ganancia_formatted': NumberFormatter.format_percentage(producto.get('margen_ganancia', 0)),
            'fecha_creacion': producto.get('fecha_creacion'),
            'fecha_actualizacion': producto.get('fecha_actualizacion')
        }
    
    def obtener_estadisticas_productos(self):
        """
        Obtener estadísticas generales de productos
        
        Returns:
            dict: Estadísticas de productos
        """
        try:
            # Obtener todos los productos
            resultado = self.listar_productos()
            
            if not resultado['success']:
                return resultado
            
            productos = resultado['data']
            
            if not productos:
                return {
                    'success': True,
                    'message': 'No hay productos registrados',
                    'data': {
                        'total_productos': 0,
                        'costo_total_inventario': 0,
                        'valor_total_inventario': 0,
                        'margen_promedio': 0,
                        'producto_mas_rentable': None,
                        'producto_menos_rentable': None
                    }
                }
            
            # Calcular estadísticas
            total_productos = len(productos)
            costo_total = sum(p['costo_adquisicion'] for p in productos)
            valor_total = sum(p['precio_venta'] for p in productos)
            margen_promedio = sum(p['margen_ganancia'] for p in productos) / total_productos
            
            # Producto más y menos rentable
            productos_ordenados = sorted(productos, key=lambda x: x['margen_ganancia'])
            producto_menos_rentable = productos_ordenados[0] if productos_ordenados else None
            producto_mas_rentable = productos_ordenados[-1] if productos_ordenados else None
            
            return {
                'success': True,
                'message': 'Estadísticas calculadas exitosamente',
                'data': {
                    'total_productos': total_productos,
                    'costo_total_inventario': costo_total,
                    'valor_total_inventario': valor_total,
                    'valor_total': valor_total,  # Alias para compatibilidad con tests
                    'margen_promedio': round(margen_promedio, 2),
                    'costo_total_formatted': CurrencyFormatter.format_currency(costo_total),
            'valor_total_formatted': CurrencyFormatter.format_currency(valor_total),
            'margen_promedio_formatted': NumberFormatter.format_percentage(margen_promedio),
                    'producto_mas_rentable': producto_mas_rentable,
                    'producto_menos_rentable': producto_menos_rentable
                }
            }
            
        except Exception as e:
            logger.error(f"Error al calcular estadísticas de productos: {str(e)}")
            return {
                'success': False,
                'message': f'Error al calcular estadísticas: {str(e)}',
                'data': None
            }