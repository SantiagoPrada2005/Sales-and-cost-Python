"""
Modelo Factura para el Sistema de Ventas y Costos
"""
from models.base_model import BaseModel
from utils.exceptions import ValidationError, DatabaseError, FacturaError
from utils.validators import FacturaValidator
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Factura(BaseModel):
    """
    Modelo para gestionar facturas en el sistema
    
    Atributos:
        - id: Identificador único
        - numero_factura: Número único de factura
        - cliente_id: ID del cliente
        - fecha_factura: Fecha de creación de la factura
        - subtotal_factura: Subtotal sin impuestos
        - impuestos_factura: Valor de impuestos
        - total_factura: Total de la factura
        - estado: Estado de la factura (borrador, confirmada, pagada, anulada)
        - observaciones: Observaciones adicionales
        - fecha_creacion: Fecha de creación del registro
        - fecha_actualizacion: Fecha de última actualización
    """
    
    def __init__(self):
        super().__init__()
        self.validator = FacturaValidator()
    
    def get_table_name(self):
        """Retorna el nombre de la tabla facturas"""
        return 'facturas'
    
    def crear_factura(self, cliente_id, observaciones=None):
        """
        Crear una nueva factura en estado borrador
        
        Args:
            cliente_id (int): ID del cliente
            observaciones (str): Observaciones opcionales
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            # Validar que el cliente existe
            if not self.cliente_existe(cliente_id):
                return {
                    'success': False,
                    'message': 'El cliente especificado no existe',
                    'data': None
                }
            
            # Generar número de factura
            numero_factura = self.generar_numero_factura()
            
            # Validar observaciones si se proporcionan
            if observaciones:
                self.validator.validar_observaciones(observaciones)
            
            query = """
            INSERT INTO facturas (numero_factura, cliente_id, fecha_factura, 
                                subtotal_factura, impuestos_factura, total_factura, 
                                estado, observaciones, fecha_creacion, fecha_actualizacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            fecha_actual = datetime.now()
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        numero_factura, cliente_id, fecha_actual,
                        Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
                        'borrador', observaciones, fecha_actual, fecha_actual
                    ))
                    conn.commit()
                    factura_id = cursor.lastrowid
                    
                    logger.info(f"Factura creada exitosamente: ID {factura_id}, Número {numero_factura}")
                    
                    return {
                        'success': True,
                        'message': 'Factura creada exitosamente',
                        'data': {
                            'id': factura_id,
                            'numero_factura': numero_factura,
                            'cliente_id': cliente_id,
                            'estado': 'borrador'
                        }
                    }
                    
        except ValidationError as e:
            logger.error(f"Error de validación al crear factura: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except DatabaseError as e:
            logger.error(f"Error de base de datos al crear factura: {str(e)}")
            return {
                'success': False,
                'message': 'Error al crear la factura en la base de datos',
                'data': None
            }
        except Exception as e:
            logger.error(f"Error inesperado al crear factura: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al crear la factura',
                'data': None
            }
    
    def agregar_detalle(self, factura_id, producto_id, cantidad, precio_unitario=None):
        """
        Agregar un producto a la factura
        
        Args:
            factura_id (int): ID de la factura
            producto_id (int): ID del producto
            cantidad (int): Cantidad del producto
            precio_unitario (Decimal): Precio unitario (opcional, toma del producto si no se especifica)
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            # Validar que la factura existe y está en borrador
            factura = self.obtener_factura_por_id(factura_id)
            if not factura['success']:
                return factura
            
            if factura['data']['estado'] != 'borrador':
                return {
                    'success': False,
                    'message': 'Solo se pueden modificar facturas en estado borrador',
                    'data': None
                }
            
            # Obtener información del producto
            producto = self.obtener_producto(producto_id)
            if not producto:
                return {
                    'success': False,
                    'message': 'El producto especificado no existe',
                    'data': None
                }
            
            # Usar precio del producto si no se especifica
            if precio_unitario is None:
                precio_unitario = producto['precio_venta']
            
            # Validar cantidad y precio
            self.validator.validar_detalle_factura(cantidad, precio_unitario)
            
            # Verificar stock disponible
            if producto['stock_actual'] < cantidad:
                return {
                    'success': False,
                    'message': f'Stock insuficiente. Disponible: {producto["stock_actual"]}',
                    'data': None
                }
            
            # Verificar si el producto ya está en la factura
            detalle_existente = self.obtener_detalle_producto(factura_id, producto_id)
            
            if detalle_existente:
                # Actualizar cantidad existente
                nueva_cantidad = detalle_existente['cantidad'] + cantidad
                return self.actualizar_detalle(detalle_existente['id'], nueva_cantidad, precio_unitario)
            else:
                # Crear nuevo detalle
                query = """
                INSERT INTO factura_detalles (factura_id, producto_id, cantidad, 
                                            precio_unitario, subtotal, fecha_creacion, fecha_actualizacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                subtotal = Decimal(str(cantidad)) * Decimal(str(precio_unitario))
                fecha_actual = datetime.now()
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(query, (factura_id, producto_id, cantidad, 
                                             precio_unitario, subtotal, fecha_actual, fecha_actual))
                        conn.commit()
                        detalle_id = cursor.lastrowid
                
                # Recalcular totales de la factura
                self.recalcular_totales(factura_id)
                
                logger.info(f"Detalle agregado a factura {factura_id}: Producto {producto_id}, Cantidad {cantidad}")
                
                return {
                    'success': True,
                    'message': 'Producto agregado a la factura exitosamente',
                    'data': {
                        'detalle_id': detalle_id,
                        'factura_id': factura_id,
                        'producto_id': producto_id,
                        'cantidad': cantidad,
                        'precio_unitario': precio_unitario,
                        'subtotal': subtotal
                    }
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación al agregar detalle: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error inesperado al agregar detalle: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al agregar el producto',
                'data': None
            }
    
    def actualizar_detalle(self, detalle_id, cantidad, precio_unitario):
        """
        Actualizar un detalle de factura existente
        
        Args:
            detalle_id (int): ID del detalle
            cantidad (int): Nueva cantidad
            precio_unitario (Decimal): Nuevo precio unitario
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            # Validar datos
            self.validator.validar_detalle_factura(cantidad, precio_unitario)
            
            # Obtener información del detalle
            detalle = self.obtener_detalle_por_id(detalle_id)
            if not detalle:
                return {
                    'success': False,
                    'message': 'El detalle de factura no existe',
                    'data': None
                }
            
            # Validar que la factura esté en borrador
            factura = self.obtener_factura_por_id(detalle['factura_id'])
            if factura['data']['estado'] != 'borrador':
                return {
                    'success': False,
                    'message': 'Solo se pueden modificar facturas en estado borrador',
                    'data': None
                }
            
            subtotal = Decimal(str(cantidad)) * Decimal(str(precio_unitario))
            
            query = """
            UPDATE factura_detalles 
            SET cantidad = %s, precio_unitario = %s, subtotal = %s, fecha_actualizacion = %s
            WHERE id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (cantidad, precio_unitario, subtotal, datetime.now(), detalle_id))
                    conn.commit()
            
            # Recalcular totales
            self.recalcular_totales(detalle['factura_id'])
            
            logger.info(f"Detalle actualizado: ID {detalle_id}, Cantidad {cantidad}")
            
            return {
                'success': True,
                'message': 'Detalle actualizado exitosamente',
                'data': {
                    'detalle_id': detalle_id,
                    'cantidad': cantidad,
                    'precio_unitario': precio_unitario,
                    'subtotal': subtotal
                }
            }
            
        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error al actualizar detalle: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al actualizar el detalle',
                'data': None
            }
    
    def eliminar_detalle(self, detalle_id):
        """
        Eliminar un detalle de factura
        
        Args:
            detalle_id (int): ID del detalle a eliminar
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            # Obtener información del detalle para validaciones
            detalle = self.obtener_detalle_por_id(detalle_id)
            if not detalle:
                return {
                    'success': False,
                    'message': 'El detalle de factura no existe',
                    'data': None
                }
            
            # Validar que la factura esté en borrador
            factura = self.obtener_factura_por_id(detalle['factura_id'])
            if factura['data']['estado'] != 'borrador':
                return {
                    'success': False,
                    'message': 'Solo se pueden modificar facturas en estado borrador',
                    'data': None
                }
            
            query = "DELETE FROM factura_detalles WHERE id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (detalle_id,))
                    conn.commit()
            
            # Recalcular totales
            self.recalcular_totales(detalle['factura_id'])
            
            logger.info(f"Detalle eliminado: ID {detalle_id}")
            
            return {
                'success': True,
                'message': 'Detalle eliminado exitosamente',
                'data': {'detalle_id': detalle_id}
            }
            
        except Exception as e:
            logger.error(f"Error al eliminar detalle: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al eliminar el detalle',
                'data': None
            }
    
    def recalcular_totales(self, factura_id):
        """
        Recalcular los totales de una factura basado en sus detalles
        
        Args:
            factura_id (int): ID de la factura
        """
        try:
            # Obtener suma de subtotales
            query = """
            SELECT COALESCE(SUM(subtotal), 0) as subtotal_total
            FROM factura_detalles
            WHERE factura_id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (factura_id,))
                    result = cursor.fetchone()
                    subtotal = result['subtotal_total']
            
            # Calcular impuestos (19% IVA por defecto)
            tasa_impuesto = Decimal('0.19')
            impuestos = subtotal * tasa_impuesto
            total = subtotal + impuestos
            
            # Actualizar factura
            update_query = """
            UPDATE facturas 
            SET subtotal_factura = %s, impuestos_factura = %s, total_factura = %s, fecha_actualizacion = %s
            WHERE id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(update_query, (subtotal, impuestos, total, datetime.now(), factura_id))
                    conn.commit()
                    
            logger.debug(f"Totales recalculados para factura {factura_id}: Subtotal {subtotal}, Total {total}")
            
        except Exception as e:
            logger.error(f"Error al recalcular totales de factura {factura_id}: {str(e)}")
            raise
    
    def confirmar_factura(self, factura_id):
        """
        Confirmar una factura (cambiar de borrador a confirmada)
        
        Args:
            factura_id (int): ID de la factura
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            factura_result = self.obtener_factura_por_id(factura_id)
            if not factura_result['success']:
                return factura_result
            
            factura = factura_result['data']
            
            if factura['estado'] != 'borrador':
                return {
                    'success': False,
                    'message': 'Solo se pueden confirmar facturas en estado borrador',
                    'data': None
                }
            
            # Validar que tenga al menos un detalle
            detalles = self.obtener_detalles_factura(factura_id)
            if not detalles['success'] or not detalles['data']:
                return {
                    'success': False,
                    'message': 'La factura debe tener al menos un producto',
                    'data': None
                }
            
            # Validar stock para todos los productos
            for detalle in detalles['data']:
                producto = self.obtener_producto(detalle['producto_id'])
                if producto['stock_actual'] < detalle['cantidad']:
                    return {
                        'success': False,
                        'message': f'Stock insuficiente para {producto["nombre"]}',
                        'data': None
                    }
            
            # Actualizar stock de productos
            for detalle in detalles['data']:
                self.actualizar_stock_producto(detalle['producto_id'], -detalle['cantidad'])
            
            # Cambiar estado de la factura
            query = "UPDATE facturas SET estado = 'confirmada', fecha_actualizacion = %s WHERE id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (datetime.now(), factura_id))
                    conn.commit()
            
            logger.info(f"Factura confirmada: ID {factura_id}")
            
            return {
                'success': True,
                'message': 'Factura confirmada exitosamente',
                'data': {'factura_id': factura_id, 'estado': 'confirmada'}
            }
            
        except Exception as e:
            logger.error(f"Error al confirmar factura: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al confirmar la factura',
                'data': None
            }
    
    def anular_factura(self, factura_id, motivo=None):
        """
        Anular una factura
        
        Args:
            factura_id (int): ID de la factura
            motivo (str): Motivo de anulación
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            factura_result = self.obtener_factura_por_id(factura_id)
            if not factura_result['success']:
                return factura_result
            
            factura = factura_result['data']
            
            if factura['estado'] == 'anulada':
                return {
                    'success': False,
                    'message': 'La factura ya está anulada',
                    'data': None
                }
            
            # Si la factura estaba confirmada, devolver stock
            if factura['estado'] == 'confirmada':
                detalles = self.obtener_detalles_factura(factura_id)
                if detalles['success']:
                    for detalle in detalles['data']:
                        self.actualizar_stock_producto(detalle['producto_id'], detalle['cantidad'])
            
            # Actualizar estado
            query = """
            UPDATE facturas 
            SET estado = 'anulada', observaciones = CONCAT(COALESCE(observaciones, ''), %s), fecha_actualizacion = %s
            WHERE id = %s
            """
            
            motivo_texto = f"\n[ANULADA] {motivo}" if motivo else "\n[ANULADA]"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (motivo_texto, datetime.now(), factura_id))
                    conn.commit()
            
            logger.info(f"Factura anulada: ID {factura_id}, Motivo: {motivo}")
            
            return {
                'success': True,
                'message': 'Factura anulada exitosamente',
                'data': {'factura_id': factura_id, 'estado': 'anulada'}
            }
            
        except Exception as e:
            logger.error(f"Error al anular factura: {str(e)}")
            return {
                'success': False,
                'message': 'Error inesperado al anular la factura',
                'data': None
            }
    
    def obtener_factura_por_id(self, factura_id):
        """
        Obtener factura por ID
        
        Args:
            factura_id (int): ID de la factura
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            query = """
            SELECT f.*, c.nombre_completo as cliente_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (factura_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        return {
                            'success': True,
                            'message': 'Factura encontrada',
                            'data': result
                        }
                    else:
                        return {
                            'success': False,
                            'message': 'Factura no encontrada',
                            'data': None
                        }
                        
        except Exception as e:
            logger.error(f"Error al obtener factura por ID: {str(e)}")
            return {
                'success': False,
                'message': 'Error al obtener la factura',
                'data': None
            }
    
    def obtener_todas_facturas(self, filtros=None):
        """
        Obtener lista de facturas con filtros opcionales
        
        Args:
            filtros (dict): Filtros opcionales (cliente_id, estado, fecha_desde, fecha_hasta, numero_factura)
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (list) y 'message' (str)
        """
        try:
            base_query = """
            SELECT f.*, c.nombre_completo as cliente_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE 1=1
            """
            
            params = []
            
            if filtros:
                if filtros.get('cliente_id'):
                    base_query += " AND f.cliente_id = %s"
                    params.append(filtros['cliente_id'])
                
                if filtros.get('estado'):
                    base_query += " AND f.estado = %s"
                    params.append(filtros['estado'])
                
                if filtros.get('fecha_desde'):
                    base_query += " AND f.fecha_factura >= %s"
                    params.append(filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    base_query += " AND f.fecha_factura <= %s"
                    params.append(filtros['fecha_hasta'])
                
                if filtros.get('numero_factura'):
                    base_query += " AND f.numero_factura LIKE %s"
                    params.append(f"%{filtros['numero_factura']}%")
            
            base_query += " ORDER BY f.fecha_factura DESC, f.id DESC"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(base_query, params)
                    results = cursor.fetchall()
                    
                    return {
                        'success': True,
                        'message': f'Se encontraron {len(results)} facturas',
                        'data': results
                    }
                    
        except Exception as e:
            logger.error(f"Error al obtener facturas: {str(e)}")
            return {
                'success': False,
                'message': 'Error al obtener las facturas',
                'data': []
            }
    
    def obtener_detalles_factura(self, factura_id):
        """
        Obtener detalles de una factura
        
        Args:
            factura_id (int): ID de la factura
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (list) y 'message' (str)
        """
        try:
            query = """
            SELECT fd.*, p.nombre as producto_nombre, p.codigo_sku as producto_codigo
            FROM factura_detalles fd
            JOIN productos p ON fd.producto_id = p.id
            WHERE fd.factura_id = %s
            ORDER BY fd.id
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (factura_id,))
                    results = cursor.fetchall()
                    
                    return {
                        'success': True,
                        'message': f'Se encontraron {len(results)} detalles',
                        'data': results
                    }
                    
        except Exception as e:
            logger.error(f"Error al obtener detalles de factura: {str(e)}")
            return {
                'success': False,
                'message': 'Error al obtener los detalles de la factura',
                'data': []
            }
    
    def obtener_detalle_por_id(self, detalle_id):
        """Obtener un detalle específico por ID"""
        try:
            query = "SELECT * FROM factura_detalles WHERE id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (detalle_id,))
                    return cursor.fetchone()
                    
        except Exception as e:
            logger.error(f"Error al obtener detalle por ID: {str(e)}")
            return None
    
    def obtener_detalle_producto(self, factura_id, producto_id):
        """Obtener detalle de un producto específico en una factura"""
        try:
            query = """
            SELECT * FROM factura_detalles 
            WHERE factura_id = %s AND producto_id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (factura_id, producto_id))
                    return cursor.fetchone()
                    
        except Exception as e:
            logger.error(f"Error al obtener detalle de producto: {str(e)}")
            return None
    
    def generar_numero_factura(self):
        """Generar número de factura único"""
        try:
            query = """
            SELECT COALESCE(MAX(CAST(SUBSTRING(numero_factura, 2) AS UNSIGNED)), 0) + 1 as siguiente
            FROM facturas 
            WHERE numero_factura REGEXP '^F[0-9]+$'
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    return f"F{result['siguiente']:06d}"
                    
        except Exception as e:
            logger.error(f"Error al generar número de factura: {str(e)}")
            # Fallback: usar timestamp
            return f"F{int(datetime.now().timestamp())}"
    
    def cliente_existe(self, cliente_id):
        """Verificar si un cliente existe"""
        try:
            query = "SELECT COUNT(*) as count FROM clientes WHERE id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (cliente_id,))
                    result = cursor.fetchone()
                    return result['count'] > 0
                    
        except Exception as e:
            logger.error(f"Error al verificar existencia de cliente: {str(e)}")
            return False
    
    def obtener_producto(self, producto_id):
        """Obtener información de un producto"""
        try:
            query = "SELECT * FROM productos WHERE id = %s"
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (producto_id,))
                    return cursor.fetchone()
                    
        except Exception as e:
            logger.error(f"Error al obtener producto: {str(e)}")
            return None
    
    def actualizar_stock_producto(self, producto_id, cambio_cantidad):
        """
        Actualizar stock de un producto
        
        Args:
            producto_id (int): ID del producto
            cambio_cantidad (int): Cantidad a sumar/restar (negativo para restar)
        """
        try:
            query = """
            UPDATE productos 
            SET stock_actual = stock_actual + %s, fecha_actualizacion = %s
            WHERE id = %s
            """
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (cambio_cantidad, datetime.now(), producto_id))
                    conn.commit()
                    
            logger.debug(f"Stock actualizado para producto {producto_id}: {cambio_cantidad}")
            
        except Exception as e:
            logger.error(f"Error al actualizar stock: {str(e)}")
            raise
    
    def obtener_estadisticas_ventas(self, fecha_desde=None, fecha_hasta=None):
        """
        Obtener estadísticas de ventas
        
        Args:
            fecha_desde (datetime): Fecha de inicio (opcional)
            fecha_hasta (datetime): Fecha de fin (opcional)
            
        Returns:
            dict: Resultado con 'success' (bool), 'data' (dict) y 'message' (str)
        """
        try:
            base_query = """
            SELECT 
                COUNT(*) as total_facturas,
                COUNT(CASE WHEN estado = 'confirmada' THEN 1 END) as facturas_confirmadas,
                COUNT(CASE WHEN estado = 'borrador' THEN 1 END) as facturas_borrador,
                COUNT(CASE WHEN estado = 'anulada' THEN 1 END) as facturas_anuladas,
                COALESCE(SUM(CASE WHEN estado = 'confirmada' THEN total_factura ELSE 0 END), 0) as total_ventas,
                COALESCE(AVG(CASE WHEN estado = 'confirmada' THEN total_factura ELSE NULL END), 0) as promedio_venta
            FROM facturas
            WHERE 1=1
            """
            
            params = []
            
            if fecha_desde:
                base_query += " AND fecha_factura >= %s"
                params.append(fecha_desde)
            
            if fecha_hasta:
                base_query += " AND fecha_factura <= %s"
                params.append(fecha_hasta)
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(base_query, params)
                    result = cursor.fetchone()
                    
                    return {
                        'success': True,
                        'message': 'Estadísticas obtenidas exitosamente',
                        'data': result
                    }
                    
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {str(e)}")
            return {
                'success': False,
                'message': 'Error al obtener las estadísticas',
                'data': None
            }