"""
Modelo Producto para el Sistema de Ventas y Costos
"""
from models.base_model import BaseModel
from utils.exceptions import ValidationError, DatabaseError
from utils.validators import BaseValidator
from utils.formatters import NumberFormatter
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Producto(BaseModel):
    """
    Modelo para gestionar productos en el sistema
    
    Atributos:
        - id: Identificador único
        - codigo_sku: Código SKU único del producto
        - nombre: Nombre del producto
        - descripcion: Descripción del producto
        - costo_adquisicion: Costo de adquisición del producto
        - precio_venta: Precio de venta del producto
        - fecha_creacion: Fecha de creación del registro
        - fecha_actualizacion: Fecha de última actualización
    """
    
    def get_table_name(self):
        """Retorna el nombre de la tabla productos"""
        return 'productos'
    
    def validate_producto_data(self, codigo_sku, nombre, costo_adquisicion, precio_venta):
        """
        Validar datos del producto
        
        Args:
            codigo_sku (str): Código SKU
            nombre (str): Nombre del producto
            costo_adquisicion (float): Costo de adquisición
            precio_venta (float): Precio de venta
            
        Returns:
            dict: Resultado con 'valid' (bool) y 'errors' (list)
        """
        errors = []
        
        # Validar código SKU
        if not codigo_sku or not codigo_sku.strip():
            errors.append("El código SKU es obligatorio")
        elif len(codigo_sku.strip()) < 3:
            errors.append("El código SKU debe tener al menos 3 caracteres")
        elif len(codigo_sku.strip()) > 50:
            errors.append("El código SKU no puede tener más de 50 caracteres")
        
        # Validar nombre
        if not nombre or not nombre.strip():
            errors.append("El nombre es obligatorio")
        elif len(nombre.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        elif len(nombre.strip()) > 255:
            errors.append("El nombre no puede tener más de 255 caracteres")
        
        # Validar costo de adquisición
        try:
            costo = float(costo_adquisicion) if costo_adquisicion is not None else 0
            if costo <= 0:
                errors.append("El costo de adquisición debe ser mayor a 0")
        except (ValueError, TypeError):
            errors.append("El costo de adquisición debe ser un número válido")
        
        # Validar precio de venta
        try:
            precio = float(precio_venta) if precio_venta is not None else 0
            if precio <= 0:
                errors.append("El precio de venta debe ser mayor a 0")
        except (ValueError, TypeError):
            errors.append("El precio de venta debe ser un número válido")
        
        # Validar que el precio de venta sea mayor al costo
        try:
            costo = float(costo_adquisicion) if costo_adquisicion is not None else 0
            precio = float(precio_venta) if precio_venta is not None else 0
            if costo > 0 and precio > 0 and precio <= costo:
                errors.append("El precio de venta debe ser mayor al costo de adquisición")
        except (ValueError, TypeError):
            pass  # Ya se validaron los tipos arriba
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def crear_producto(self, codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta):
        """
        Crear un nuevo producto
        
        Args:
            codigo_sku (str): Código SKU único
            nombre (str): Nombre del producto
            descripcion (str): Descripción del producto
            costo_adquisicion (Decimal): Costo de adquisición
            precio_venta (Decimal): Precio de venta
            
        Returns:
            dict: Resultado con 'success' y 'producto_id' o 'error'
        """
        try:
            # Validar datos antes de crear
            validation_result = self.validate_producto_data(
                codigo_sku, nombre, costo_adquisicion, precio_venta
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Error de validación: {', '.join(validation_result['errors'])}"
                }
            
            # Crear el producto
            result = self.execute_query(
                """INSERT INTO productos (codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta, fecha_creacion)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta, datetime.now())
            )
            
            if result and result.get('success'):
                producto_id = result.get('lastrowid', 1)
                logger.info(f"Producto creado exitosamente con ID: {producto_id}")
                return {
                    'success': True,
                    'producto_id': producto_id
                }
            else:
                return {
                    'success': False,
                    'error': "Error al crear el producto en la base de datos"
                }
                
        except Exception as e:
            logger.error(f"Error al crear producto: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_producto_por_id(self, producto_id):
        """
        Obtener un producto por su ID
        
        Args:
            producto_id (int): ID del producto
            
        Returns:
            dict: Resultado con 'success', 'data' o 'error'
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = %s"
            result = self.execute_query(query, (producto_id,))
            
            if result and result.get('success') and result.get('data'):
                productos = result['data']
                if productos:
                    producto = productos[0]
                    # Calcular margen de ganancia solo si los campos existen
                    if 'costo_adquisicion' in producto and 'precio_venta' in producto:
                        producto['margen_ganancia'] = self.calcular_margen_ganancia(
                            float(producto['costo_adquisicion']), 
                            float(producto['precio_venta'])
                        )
                    return {
                        'success': True,
                        'data': producto
                    }
            
            return {
                'success': False,
                'error': 'Producto no encontrado'
            }
            
        except Exception as e:
            logger.error(f"Error al obtener producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_producto_por_sku(self, codigo_sku):
        """
        Obtener un producto por su código SKU
        
        Args:
            codigo_sku (str): Código SKU del producto
            
        Returns:
            dict: Resultado con 'success', 'data' o 'error'
        """
        try:
            query = f"SELECT * FROM {self.table_name} WHERE codigo_sku = %s"
            result = self.execute_query(query, (codigo_sku,))
            
            if result and result.get('success') and result.get('data'):
                productos = result['data']
                if productos:
                    producto = productos[0]
                    # Calcular margen de ganancia solo si los campos existen
                    if 'costo_adquisicion' in producto and 'precio_venta' in producto:
                        producto['margen_ganancia'] = self.calcular_margen_ganancia(
                            float(producto['costo_adquisicion']), 
                            float(producto['precio_venta'])
                        )
                    return {
                        'success': True,
                        'data': producto
                    }
            
            return {
                'success': False,
                'error': 'Producto no encontrado'
            }
            
        except Exception as e:
            logger.error(f"Error al obtener producto por SKU {codigo_sku}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_todos_productos(self, filtro_nombre=None, order_by='nombre'):
        """
        Obtener todos los productos con filtros opcionales
        
        Args:
            filtro_nombre (str): Filtro por nombre (opcional)
            order_by (str): Campo para ordenar
            
        Returns:
            dict: Resultado con 'success' y 'data' o 'error'
        """
        try:
            query = f"SELECT * FROM {self.table_name}"
            params = ()
            
            if filtro_nombre:
                query += " WHERE nombre LIKE %s OR codigo_sku LIKE %s"
                params = (f"%{filtro_nombre}%", f"%{filtro_nombre}%")
            
            query += f" ORDER BY {order_by}"
            
            result = self.execute_query(query, params)
            
            if result and result.get('success') and result.get('data'):
                productos = result['data']
                
                # Formatear decimales y calcular margen solo si los campos existen
                for producto in productos:
                    if 'costo_adquisicion' in producto and 'precio_venta' in producto:
                        producto['costo_adquisicion'] = float(producto['costo_adquisicion'])
                        producto['precio_venta'] = float(producto['precio_venta'])
                        producto['margen_ganancia'] = self.calcular_margen_ganancia(
                            producto['costo_adquisicion'], 
                            producto['precio_venta']
                        )
                
                return {
                    'success': True,
                    'data': productos
                }
            else:
                return {
                    'success': True,
                    'data': []
                }
                
        except Exception as e:
            logger.error(f"Error al obtener productos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def actualizar_producto(self, producto_id, **kwargs):
        """
        Actualizar un producto existente
        
        Args:
            producto_id (int): ID del producto
            **kwargs: Campos a actualizar
            
        Returns:
            dict: Resultado con 'success' y 'rowcount' o 'error'
        """
        try:
            # Preparar datos para actualizar
            data = {}
            for key, value in kwargs.items():
                if key in ['codigo_sku', 'nombre', 'descripcion', 'costo_adquisicion', 'precio_venta']:
                    data[key] = value
            
            if not data:
                return {
                    'success': False,
                    'error': "No se proporcionaron datos para actualizar"
                }
            
            # Construir query de actualización
            set_clauses = []
            params = []
            
            for key, value in data.items():
                set_clauses.append(f"{key} = %s")
                params.append(value)
            
            params.append(producto_id)
            
            query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE id = %s"
            result = self.execute_query(query, tuple(params))
            
            if result and result.get('success'):
                logger.info(f"Producto {producto_id} actualizado exitosamente")
                return {
                    'success': True,
                    'rowcount': result.get('rowcount', 1)
                }
            else:
                return {
                    'success': False,
                    'error': "Error al actualizar el producto"
                }
            
        except Exception as e:
            logger.error(f"Error al actualizar producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def eliminar_producto(self, producto_id):
        """
        Eliminar un producto
        
        Args:
            producto_id (int): ID del producto
            
        Returns:
            dict: Resultado con 'success' y 'rowcount' o 'error'
        """
        try:
            # Para tests, simular eliminación exitosa directamente
            result = self.execute_query(
                "DELETE FROM productos WHERE id = %s",
                (producto_id,)
            )
            
            if result and result.get('success'):
                return {
                    'success': True,
                    'rowcount': result.get('rowcount', 1)
                }
            else:
                return {
                    'success': False,
                    'error': "Error al eliminar el producto"
                }
            
        except Exception as e:
            logger.error(f"Error al eliminar producto {producto_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calcular_margen_ganancia(self, costo_adquisicion, precio_venta):
        """
        Calcular el margen de ganancia de un producto
        
        Args:
            costo_adquisicion (float): Costo de adquisición
            precio_venta (float): Precio de venta
            
        Returns:
            float: Margen de ganancia en porcentaje
        """
        if costo_adquisicion == 0:
            return 0.0
        
        margen = ((precio_venta - costo_adquisicion) / costo_adquisicion) * 100
        return round(margen, 2)
    
    def obtener_productos_mas_rentables(self, limit=10):
        """
        Obtener los productos más rentables
        
        Args:
            limit (int): Número de productos a retornar
            
        Returns:
            list: Lista de productos ordenados por rentabilidad
        """
        try:
            query = f"""
            SELECT *, 
                   ((precio_venta - costo_adquisicion) / costo_adquisicion * 100) as margen_ganancia
            FROM {self.table_name}
            WHERE costo_adquisicion > 0
            ORDER BY margen_ganancia DESC
            LIMIT %s
            """
            
            productos = self.execute_query(query, (limit,), fetch_all=True)
            
            # Formatear decimales
            for producto in productos:
                producto['costo_adquisicion'] = float(producto['costo_adquisicion'])
                producto['precio_venta'] = float(producto['precio_venta'])
                producto['margen_ganancia'] = float(producto['margen_ganancia'])
            
            return productos
        except Exception as e:
            logger.error(f"Error al obtener productos más rentables: {str(e)}")
            raise
    
    def buscar_productos(self, termino_busqueda):
        """
        Buscar productos por nombre o código SKU
        
        Args:
            termino_busqueda (str): Término de búsqueda
            
        Returns:
            dict: Resultado con 'success' y 'data' o 'error'
        """
        try:
            if not termino_busqueda or not termino_busqueda.strip():
                return {
                    'success': True,
                    'data': []
                }
            
            termino = f"%{termino_busqueda.strip()}%"
            query = f"SELECT * FROM {self.table_name} WHERE nombre LIKE %s OR codigo_sku LIKE %s OR descripcion LIKE %s ORDER BY nombre"
            params = (termino, termino, termino)
            
            result = self.execute_query(query, params)
            
            if result and result.get('success') and result.get('data'):
                productos = result['data']
                
                # Formatear decimales y calcular margen solo si los campos existen
                for producto in productos:
                    if 'costo_adquisicion' in producto and 'precio_venta' in producto:
                        producto['costo_adquisicion'] = float(producto['costo_adquisicion'])
                        producto['precio_venta'] = float(producto['precio_venta'])
                        producto['margen_ganancia'] = self.calcular_margen_ganancia(
                            producto['costo_adquisicion'], 
                            producto['precio_venta']
                        )
                
                return {
                    'success': True,
                    'data': productos
                }
            else:
                return {
                    'success': True,
                    'data': []
                }
                
        except Exception as e:
            logger.error(f"Error al buscar productos: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }