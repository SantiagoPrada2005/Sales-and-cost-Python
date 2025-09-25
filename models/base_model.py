"""
Clase base para todos los modelos del Sistema de Ventas y Costos
"""
from abc import ABC, abstractmethod
from config.database import DatabaseConnection
from utils.exceptions import DatabaseError, RecordNotFoundError
import logging

logger = logging.getLogger(__name__)

class BaseModel(ABC):
    """
    Clase base abstracta para todos los modelos
    Proporciona funcionalidades comunes como conexión a BD y operaciones CRUD básicas
    """
    
    def __init__(self):
        self.db = DatabaseConnection()
        self.table_name = self.get_table_name()
        self.primary_key = 'id'
    
    @abstractmethod
    def get_table_name(self):
        """
        Retorna el nombre de la tabla asociada al modelo
        
        Returns:
            str: Nombre de la tabla
        """
        pass
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """
        Ejecutar una consulta SQL
        
        Args:
            query (str): Consulta SQL
            params (tuple): Parámetros de la consulta
            fetch_one (bool): Retornar un solo registro
            fetch_all (bool): Retornar todos los registros
            
        Returns:
            dict|list|int: Resultado de la consulta
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params or ())
                    
                    if fetch_one:
                        return cursor.fetchone()
                    elif fetch_all:
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                        
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {query}, Error: {e}")
            raise DatabaseError(f"Error en la base de datos: {e}")
    
    def find_by_id(self, record_id):
        """
        Buscar un registro por ID
        
        Args:
            record_id (int): ID del registro
            
        Returns:
            dict: Registro encontrado o None
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = %s"
        return self.execute_query(query, (record_id,), fetch_one=True)
    
    def find_all(self, where_clause=None, params=None, order_by=None, limit=None):
        """
        Buscar todos los registros con filtros opcionales
        
        Args:
            where_clause (str): Cláusula WHERE
            params (tuple): Parámetros para la cláusula WHERE
            order_by (str): Campo de ordenamiento
            limit (int): Límite de registros
            
        Returns:
            list: Lista de registros
        """
        query = f"SELECT * FROM {self.table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, params, fetch_all=True)
    
    def count(self, where_clause=None, params=None):
        """
        Contar registros
        
        Args:
            where_clause (str): Cláusula WHERE
            params (tuple): Parámetros para la cláusula WHERE
            
        Returns:
            int: Número de registros
        """
        query = f"SELECT COUNT(*) as total FROM {self.table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        result = self.execute_query(query, params, fetch_one=True)
        return result['total'] if result else 0
    
    def exists(self, where_clause, params):
        """
        Verificar si existe un registro
        
        Args:
            where_clause (str): Cláusula WHERE
            params (tuple): Parámetros para la cláusula WHERE
            
        Returns:
            bool: True si existe, False en caso contrario
        """
        return self.count(where_clause, params) > 0
    
    def delete_by_id(self, record_id):
        """
        Eliminar un registro por ID
        
        Args:
            record_id (int): ID del registro a eliminar
            
        Returns:
            bool: True si se eliminó, False en caso contrario
        """
        # Verificar que el registro existe
        if not self.find_by_id(record_id):
            raise RecordNotFoundError(f"No se encontró el registro con ID {record_id}")
        
        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s"
        affected_rows = self.execute_query(query, (record_id,))
        return affected_rows > 0
    
    def build_insert_query(self, data):
        """
        Construir consulta INSERT
        
        Args:
            data (dict): Datos a insertar
            
        Returns:
            tuple: (query, values)
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(columns))
        
        query = f"""
        INSERT INTO {self.table_name} ({', '.join(columns)})
        VALUES ({placeholders})
        """
        
        return query, values
    
    def build_update_query(self, record_id, data):
        """
        Construir consulta UPDATE
        
        Args:
            record_id (int): ID del registro a actualizar
            data (dict): Datos a actualizar
            
        Returns:
            tuple: (query, values)
        """
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        values = list(data.values()) + [record_id]
        
        query = f"""
        UPDATE {self.table_name}
        SET {set_clause}
        WHERE {self.primary_key} = %s
        """
        
        return query, values
    
    def insert(self, data):
        """
        Insertar un nuevo registro
        
        Args:
            data (dict): Datos a insertar
            
        Returns:
            int: ID del registro insertado
        """
        query, values = self.build_insert_query(data)
        return self.execute_query(query, values)
    
    def update(self, record_id, data):
        """
        Actualizar un registro existente
        
        Args:
            record_id (int): ID del registro a actualizar
            data (dict): Datos a actualizar
            
        Returns:
            bool: True si se actualizó, False en caso contrario
        """
        # Verificar que el registro existe
        if not self.find_by_id(record_id):
            raise RecordNotFoundError(f"No se encontró el registro con ID {record_id}")
        
        query, values = self.build_update_query(record_id, data)
        affected_rows = self.execute_query(query, values)
        return affected_rows > 0
    
    def get_last_insert_id(self):
        """
        Obtener el último ID insertado
        
        Returns:
            int: Último ID insertado
        """
        query = "SELECT LAST_INSERT_ID() as last_id"
        result = self.execute_query(query, fetch_one=True)
        return result['last_id'] if result else None
    
    def begin_transaction(self):
        """Iniciar una transacción"""
        query = "START TRANSACTION"
        self.execute_query(query)
    
    def commit_transaction(self):
        """Confirmar una transacción"""
        query = "COMMIT"
        self.execute_query(query)
    
    def rollback_transaction(self):
        """Revertir una transacción"""
        query = "ROLLBACK"
        self.execute_query(query)