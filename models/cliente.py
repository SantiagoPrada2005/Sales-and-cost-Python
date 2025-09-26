"""
Modelo Cliente para el Sistema de Ventas y Costos
"""
from models.base_model import BaseModel
from utils.exceptions import ValidationError, DatabaseError, ClienteError, DuplicateRecordError
from utils.validators import BaseValidator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Cliente(BaseModel):
    """
    Modelo para gestionar clientes en el sistema
    
    Atributos:
        - id: Identificador único
        - nombre_completo: Nombre completo del cliente
        - numero_identificacion: Número de identificación (opcional)
        - contacto_telefono: Teléfono de contacto (opcional)
        - contacto_email: Email de contacto (opcional)
        - fecha_creacion: Fecha de creación del registro
        - fecha_actualizacion: Fecha de última actualización
    """
    
    def get_table_name(self):
        """Retorna el nombre de la tabla clientes"""
        return 'clientes'
    
    def validate_cliente_data(self, nombre_completo, numero_identificacion=None, 
                             contacto_telefono=None, contacto_email=None):
        """
        Validar datos del cliente
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Returns:
            dict: Resultado con 'valid' (bool) y 'errors' (list)
        """
        errors = []
        
        # Validar nombre completo (obligatorio)
        if not nombre_completo or not nombre_completo.strip():
            errors.append("El nombre completo es obligatorio")
        elif len(nombre_completo.strip()) < 2:
            errors.append("El nombre completo debe tener al menos 2 caracteres")
        elif len(nombre_completo.strip()) > 100:
            errors.append("El nombre completo no puede exceder 100 caracteres")
        
        # Validar número de identificación (opcional)
        if numero_identificacion:
            numero_identificacion = numero_identificacion.strip()
            if len(numero_identificacion) < 5:
                errors.append("El número de identificación debe tener al menos 5 caracteres")
            elif len(numero_identificacion) > 20:
                errors.append("El número de identificación no puede exceder 20 caracteres")
        
        # Validar teléfono (opcional)
        if contacto_telefono:
            contacto_telefono = contacto_telefono.strip()
            if len(contacto_telefono) < 7:
                errors.append("El teléfono debe tener al menos 7 caracteres")
            elif len(contacto_telefono) > 15:
                errors.append("El teléfono no puede exceder 15 caracteres")
        
        # Validar email (opcional)
        if contacto_email:
            contacto_email = contacto_email.strip()
            if '@' not in contacto_email or '.' not in contacto_email:
                errors.append("El email debe tener un formato válido")
            elif len(contacto_email) > 100:
                errors.append("El email no puede exceder 100 caracteres")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def crear_cliente(self, nombre_completo, numero_identificacion=None, 
                     contacto_telefono=None, contacto_email=None):
        """
        Crear un nuevo cliente
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Returns:
            dict: Resultado con 'success' (bool), 'cliente_id' (int) y 'message' (str)
        """
        try:
            # Validar datos de entrada
            validation = self.validate_cliente_data(nombre_completo, numero_identificacion, 
                                                   contacto_telefono, contacto_email)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'cliente_id': None,
                    'message': '; '.join(validation['errors'])
                }
            
            # Limpiar datos
            nombre_completo = nombre_completo.strip()
            numero_identificacion = numero_identificacion.strip() if numero_identificacion else None
            contacto_telefono = contacto_telefono.strip() if contacto_telefono else None
            contacto_email = contacto_email.strip().lower() if contacto_email else None
            
            # Verificar que la identificación no exista (si se proporciona)
            if numero_identificacion and self.existe_identificacion(numero_identificacion):
                return {
                    'success': False,
                    'cliente_id': None,
                    'message': f"Ya existe un cliente con la identificación '{numero_identificacion}'"
                }
            
            # Verificar que el email no exista (si se proporciona)
            if contacto_email and self.existe_email(contacto_email):
                return {
                    'success': False,
                    'cliente_id': None,
                    'message': f"Ya existe un cliente con el email '{contacto_email}'"
                }
            
            # Insertar cliente
            data = {
                'nombre_completo': nombre_completo,
                'numero_identificacion': numero_identificacion,
                'contacto_telefono': contacto_telefono,
                'contacto_email': contacto_email
            }
            
            cliente_id = self.insert(data)
            
            logger.info(f"Cliente creado exitosamente con ID: {cliente_id}")
            
            return {
                'success': True,
                'cliente_id': cliente_id,
                'message': 'Cliente creado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error creando cliente: {e}")
            return {
                'success': False,
                'cliente_id': None,
                'message': f'Error interno: {str(e)}'
            }
    
    def obtener_cliente_por_id(self, cliente_id):
        """
        Obtener cliente por ID
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            dict: Resultado con 'success' (bool), 'cliente' (dict) y 'message' (str)
        """
        try:
            cliente = self.find_by_id(cliente_id)
            
            if cliente:
                return {
                    'success': True,
                    'cliente': cliente,
                    'message': 'Cliente encontrado'
                }
            else:
                return {
                    'success': False,
                    'cliente': None,
                    'message': f'Cliente con ID {cliente_id} no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo cliente por ID {cliente_id}: {e}")
            return {
                'success': False,
                'cliente': None,
                'message': f'Error interno: {str(e)}'
            }
    
    def obtener_cliente_por_identificacion(self, numero_identificacion):
        """
        Obtener cliente por número de identificación
        
        Args:
            numero_identificacion (str): Número de identificación
            
        Returns:
            dict: Resultado con 'success' (bool), 'cliente' (dict) y 'message' (str)
        """
        try:
            cliente = self.execute_query(
                "SELECT * FROM clientes WHERE numero_identificacion = %s",
                (numero_identificacion,),
                fetch_one=True
            )
            
            if cliente:
                return {
                    'success': True,
                    'cliente': cliente,
                    'message': 'Cliente encontrado'
                }
            else:
                return {
                    'success': False,
                    'cliente': None,
                    'message': f'Cliente con identificación {numero_identificacion} no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo cliente por identificación {numero_identificacion}: {e}")
            return {
                'success': False,
                'cliente': None,
                'message': f'Error interno: {str(e)}'
            }
    
    def obtener_todos_clientes(self, filtro_nombre=None, order_by='nombre_completo'):
        """
        Obtener lista de clientes con filtros opcionales
        
        Args:
            filtro_nombre (str): Filtro de búsqueda por nombre, identificación o email
            order_by (str): Campo de ordenamiento
            
        Returns:
            list: Lista de clientes
        """
        try:
            if filtro_nombre:
                where_clause = """
                nombre_completo LIKE %s 
                OR numero_identificacion LIKE %s 
                OR contacto_email LIKE %s
                """
                filtro_param = f"%{filtro_nombre}%"
                params = (filtro_param, filtro_param, filtro_param)
                
                return self.find_all(where_clause=where_clause, params=params, order_by=order_by)
            else:
                return self.find_all(order_by=order_by)
                
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {e}")
            return []
    
    def actualizar_cliente(self, cliente_id, **kwargs):
        """
        Actualizar cliente existente
        
        Args:
            cliente_id (int): ID del cliente
            **kwargs: Campos a actualizar
            
        Returns:
            dict: Resultado con 'success' (bool) y 'message' (str)
        """
        try:
            # Verificar que el cliente existe
            cliente_actual = self.find_by_id(cliente_id)
            if not cliente_actual:
                return {
                    'success': False,
                    'message': f'Cliente con ID {cliente_id} no encontrado'
                }
            
            # Campos permitidos para actualización
            campos_permitidos = ['nombre_completo', 'numero_identificacion', 
                               'contacto_telefono', 'contacto_email']
            
            campos_actualizar = {k: v for k, v in kwargs.items() if k in campos_permitidos}
            
            if not campos_actualizar:
                return {
                    'success': False,
                    'message': 'No hay campos válidos para actualizar'
                }
            
            # Validar datos si se están actualizando
            if any(campo in campos_actualizar for campo in ['nombre_completo', 'numero_identificacion', 
                                                           'contacto_telefono', 'contacto_email']):
                # Obtener valores actuales o nuevos
                nombre_completo = campos_actualizar.get('nombre_completo', cliente_actual['nombre_completo'])
                numero_identificacion = campos_actualizar.get('numero_identificacion', cliente_actual['numero_identificacion'])
                contacto_telefono = campos_actualizar.get('contacto_telefono', cliente_actual['contacto_telefono'])
                contacto_email = campos_actualizar.get('contacto_email', cliente_actual['contacto_email'])
                
                validation = self.validate_cliente_data(nombre_completo, numero_identificacion, 
                                                       contacto_telefono, contacto_email)
                
                if not validation['valid']:
                    return {
                        'success': False,
                        'message': '; '.join(validation['errors'])
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
            
            # Validar identificación única si se está actualizando
            if 'numero_identificacion' in campos_actualizar and campos_actualizar['numero_identificacion']:
                if self.existe_identificacion(campos_actualizar['numero_identificacion'], excluir_id=cliente_id):
                    return {
                        'success': False,
                        'message': f"Ya existe un cliente con la identificación '{campos_actualizar['numero_identificacion']}'"
                    }
            
            # Validar email único si se está actualizando
            if 'contacto_email' in campos_actualizar and campos_actualizar['contacto_email']:
                if self.existe_email(campos_actualizar['contacto_email'], excluir_id=cliente_id):
                    return {
                        'success': False,
                        'message': f"Ya existe un cliente con el email '{campos_actualizar['contacto_email']}'"
                    }
            
            # Actualizar cliente
            rows_affected = self.update(cliente_id, campos_actualizar)
            
            if rows_affected > 0:
                logger.info(f"Cliente {cliente_id} actualizado exitosamente")
                return {
                    'success': True,
                    'message': 'Cliente actualizado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo actualizar el cliente'
                }
                
        except Exception as e:
            logger.error(f"Error actualizando cliente {cliente_id}: {e}")
            return {
                'success': False,
                'message': f'Error interno: {str(e)}'
            }
    
    def eliminar_cliente(self, cliente_id):
        """
        Eliminar cliente con validación de dependencias
        
        Args:
            cliente_id (int): ID del cliente a eliminar
            
        Returns:
            dict: Resultado con 'success' (bool) y 'message' (str)
        """
        try:
            # Verificar que el cliente existe
            if not self.find_by_id(cliente_id):
                return {
                    'success': False,
                    'message': f'Cliente con ID {cliente_id} no encontrado'
                }
            
            # Verificar si el cliente tiene facturas
            if self.tiene_facturas(cliente_id):
                return {
                    'success': False,
                    'message': 'No se puede eliminar el cliente porque tiene facturas asociadas'
                }
            
            # Eliminar cliente
            rows_affected = self.delete_by_id(cliente_id)
            
            if rows_affected > 0:
                logger.info(f"Cliente {cliente_id} eliminado exitosamente")
                return {
                    'success': True,
                    'message': 'Cliente eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo eliminar el cliente'
                }
                
        except Exception as e:
            logger.error(f"Error eliminando cliente {cliente_id}: {e}")
            return {
                'success': False,
                'message': f'Error interno: {str(e)}'
            }
    
    def existe_identificacion(self, numero_identificacion, excluir_id=None):
        """
        Verificar si existe una identificación
        
        Args:
            numero_identificacion (str): Número de identificación
            excluir_id (int): ID a excluir de la búsqueda
            
        Returns:
            bool: True si existe, False si no
        """
        try:
            where_clause = "numero_identificacion = %s"
            params = [numero_identificacion]
            
            if excluir_id:
                where_clause += " AND id != %s"
                params.append(excluir_id)
            
            count = self.count(where_clause=where_clause, params=tuple(params))
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando identificación {numero_identificacion}: {e}")
            return False
    
    def existe_email(self, contacto_email, excluir_id=None):
        """
        Verificar si existe un email
        
        Args:
            contacto_email (str): Email de contacto
            excluir_id (int): ID a excluir de la búsqueda
            
        Returns:
            bool: True si existe, False si no
        """
        try:
            where_clause = "contacto_email = %s"
            params = [contacto_email.lower()]
            
            if excluir_id:
                where_clause += " AND id != %s"
                params.append(excluir_id)
            
            count = self.count(where_clause=where_clause, params=tuple(params))
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando email {contacto_email}: {e}")
            return False
    
    def tiene_facturas(self, cliente_id):
        """
        Verificar si el cliente tiene facturas asociadas
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            bool: True si tiene facturas, False si no
        """
        try:
            count = self.execute_query(
                "SELECT COUNT(*) as count FROM facturas WHERE cliente_id = %s",
                (cliente_id,),
                fetch_one=True
            )
            return count['count'] > 0 if count else False
            
        except Exception as e:
            logger.error(f"Error verificando facturas del cliente {cliente_id}: {e}")
            return False
    
    def obtener_historial_compras(self, cliente_id, limite=None):
        """
        Obtener historial de compras del cliente
        
        Args:
            cliente_id (int): ID del cliente
            limite (int): Límite de registros a obtener
            
        Returns:
            list: Lista de facturas del cliente
        """
        try:
            query = """
            SELECT f.id, f.numero_factura, f.fecha_factura, f.total_factura, f.estado,
                   COUNT(fd.id) as total_items,
                   COALESCE(SUM(p.monto_pago), 0) as total_pagado
            FROM facturas f
            LEFT JOIN factura_detalles fd ON f.id = fd.factura_id
            LEFT JOIN pagos p ON f.id = p.factura_id
            WHERE f.cliente_id = %s
            GROUP BY f.id
            ORDER BY f.fecha_factura DESC
            """
            
            params = [cliente_id]
            if limite:
                query += " LIMIT %s"
                params.append(limite)
            
            return self.execute_query(query, tuple(params), fetch_all=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo historial de compras del cliente {cliente_id}: {e}")
            return []
    
    def obtener_estadisticas_cliente(self, cliente_id):
        """
        Obtener estadísticas del cliente
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            dict: Estadísticas del cliente
        """
        try:
            estadisticas = self.execute_query("""
            SELECT 
                COUNT(f.id) as total_facturas,
                COALESCE(SUM(f.total_factura), 0) as total_compras,
                COALESCE(SUM(CASE WHEN f.estado = 'pendiente_pago' THEN f.total_factura ELSE 0 END), 0) as total_pendiente,
                COALESCE(AVG(f.total_factura), 0) as promedio_compra,
                MAX(f.fecha_factura) as ultima_compra
            FROM facturas f
            WHERE f.cliente_id = %s
            """, (cliente_id,), fetch_one=True)
            
            return estadisticas if estadisticas else {
                'total_facturas': 0,
                'total_compras': 0,
                'total_pendiente': 0,
                'promedio_compra': 0,
                'ultima_compra': None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del cliente {cliente_id}: {e}")
            return {
                'total_facturas': 0,
                'total_compras': 0,
                'total_pendiente': 0,
                'promedio_compra': 0,
                'ultima_compra': None
            }
    
    def buscar_clientes(self, termino_busqueda):
        """
        Buscar clientes por término de búsqueda
        
        Args:
            termino_busqueda (str): Término a buscar
            
        Returns:
            list: Lista de clientes que coinciden con la búsqueda
        """
        try:
            if not termino_busqueda or not termino_busqueda.strip():
                return []
            
            termino = f"%{termino_busqueda.strip()}%"
            
            return self.execute_query("""
            SELECT * FROM clientes 
            WHERE nombre_completo LIKE %s 
            OR numero_identificacion LIKE %s 
            OR contacto_telefono LIKE %s 
            OR contacto_email LIKE %s
            ORDER BY nombre_completo
            """, (termino, termino, termino, termino), fetch_all=True)
            
        except Exception as e:
            logger.error(f"Error buscando clientes con término '{termino_busqueda}': {e}")
            return []