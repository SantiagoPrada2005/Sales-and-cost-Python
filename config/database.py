"""
Configuración y manejo de conexiones a la base de datos MySQL
"""
import pymysql
import logging
from contextlib import contextmanager
from config.settings import DATABASE_CONFIG

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Clase para manejar conexiones a la base de datos MySQL
    """
    
    def __init__(self):
        self.config = DATABASE_CONFIG
        self._connection = None
    
    def get_connection(self):
        """
        Obtener una conexión a la base de datos
        
        Returns:
            pymysql.Connection: Conexión a la base de datos
        """
        try:
            connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config['charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            logger.info("Conexión a la base de datos establecida exitosamente")
            return connection
        except pymysql.Error as e:
            logger.error(f"Error al conectar a la base de datos: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager para obtener un cursor de base de datos
        
        Yields:
            pymysql.cursors.DictCursor: Cursor de la base de datos
        """
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                yield cursor
                connection.commit()
        except Exception as e:
            connection.rollback()
            logger.error(f"Error en la transacción: {e}")
            raise
        finally:
            connection.close()
    
    def test_connection(self):
        """
        Probar la conexión a la base de datos
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Error al probar la conexión: {e}")
            return False
    
    def create_database_if_not_exists(self):
        """
        Crear la base de datos si no existe
        """
        try:
            # Conectar sin especificar base de datos
            temp_config = self.config.copy()
            temp_config.pop('database')
            
            connection = pymysql.connect(
                **temp_config,
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config['database']}")
                connection.commit()
                logger.info(f"Base de datos '{self.config['database']}' creada o ya existe")
            
            connection.close()
            
        except pymysql.Error as e:
            logger.error(f"Error al crear la base de datos: {e}")
            raise
    
    def execute_script(self, script_path):
        """
        Ejecutar un script SQL desde un archivo
        
        Args:
            script_path (str): Ruta al archivo SQL
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as file:
                script = file.read()
            
            # Dividir el script en declaraciones individuales
            statements = [stmt.strip() for stmt in script.split(';') if stmt.strip()]
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for statement in statements:
                        if statement:
                            cursor.execute(statement)
                    conn.commit()
                    logger.info(f"Script {script_path} ejecutado exitosamente")
        
        except Exception as e:
            logger.error(f"Error al ejecutar el script {script_path}: {e}")
            raise

# Instancia global de la conexión
db_connection = DatabaseConnection()