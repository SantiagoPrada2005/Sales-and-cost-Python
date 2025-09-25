#!/usr/bin/env python3
"""
Script para configurar las tablas de la base de datos
"""

import sys
import os
import logging

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import DatabaseConnection
from utils.exceptions import DatabaseError

def setup_logging():
    """Configurar logging básico"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_tables():
    """Crear las tablas necesarias en la base de datos"""
    logger = setup_logging()
    
    # SQL para crear las tablas
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS productos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            codigo_sku VARCHAR(50) UNIQUE NOT NULL,
            nombre VARCHAR(255) NOT NULL,
            descripcion TEXT,
            costo_adquisicion DECIMAL(10,2) NOT NULL,
            precio_venta DECIMAL(10,2) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        """
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_completo VARCHAR(255) NOT NULL,
            numero_identificacion VARCHAR(50),
            contacto_telefono VARCHAR(50),
            contacto_email VARCHAR(255),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        """
        CREATE TABLE IF NOT EXISTS facturas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            numero_factura VARCHAR(50) UNIQUE NOT NULL,
            cliente_id INT NOT NULL,
            fecha_factura DATE NOT NULL,
            subtotal_factura DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            impuestos_factura DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            total_factura DECIMAL(10,2) NOT NULL,
            estado ENUM('borrador', 'confirmada', 'anulada') DEFAULT 'borrador',
            observaciones TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        """
        CREATE TABLE IF NOT EXISTS factura_detalles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            factura_id INT NOT NULL,
            producto_id INT NOT NULL,
            cantidad INT NOT NULL,
            precio_unitario DECIMAL(10,2) NOT NULL,
            subtotal DECIMAL(10,2) NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]
    
    # Datos de ejemplo
    sample_data_sql = [
        """
        INSERT IGNORE INTO productos (codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta) VALUES
        ('PROD001', 'Producto Ejemplo 1', 'Descripción del producto ejemplo 1', 100.00, 150.00),
        ('PROD002', 'Producto Ejemplo 2', 'Descripción del producto ejemplo 2', 200.00, 280.00),
        ('PROD003', 'Producto Ejemplo 3', 'Descripción del producto ejemplo 3', 50.00, 75.00)
        """,
        
        """
        INSERT IGNORE INTO clientes (nombre_completo, numero_identificacion, contacto_telefono, contacto_email) VALUES
        ('Cliente Ejemplo 1', '12345678', '555-0001', 'cliente1@example.com'),
        ('Cliente Ejemplo 2', '87654321', '555-0002', 'cliente2@example.com'),
        ('Cliente Ejemplo 3', '11223344', '555-0003', 'cliente3@example.com')
        """
    ]
    
    try:
        db = DatabaseConnection()
        
        # Verificar conexión
        if not db.test_connection():
            logger.error("No se pudo conectar a la base de datos")
            return False
        
        logger.info("Conexión a la base de datos exitosa")
        
        # Crear tablas
        logger.info("Creando tablas...")
        with db.get_cursor() as cursor:
            for i, sql in enumerate(tables_sql, 1):
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {i} creada exitosamente")
                except Exception as e:
                    logger.error(f"Error creando tabla {i}: {e}")
                    return False
        
        # Insertar datos de ejemplo
        logger.info("Insertando datos de ejemplo...")
        with db.get_cursor() as cursor:
            for i, sql in enumerate(sample_data_sql, 1):
                try:
                    cursor.execute(sql)
                    logger.info(f"Datos de ejemplo {i} insertados exitosamente")
                except Exception as e:
                    logger.warning(f"Advertencia insertando datos de ejemplo {i}: {e}")
        
        logger.info("¡Base de datos configurada exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"Error configurando la base de datos: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)