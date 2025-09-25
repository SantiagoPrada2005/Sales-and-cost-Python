#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de la base de datos
"""

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import DatabaseConnection
from config.settings import DATABASE_CONFIG
from utils.exceptions import DatabaseError

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("🔍 Probando configuración de base de datos...")
    
    # Mostrar configuración (sin password)
    print(f"📋 Configuración:")
    print(f"   Host: {DATABASE_CONFIG['host']}")
    print(f"   Puerto: {DATABASE_CONFIG['port']}")
    print(f"   Usuario: {DATABASE_CONFIG['user']}")
    print(f"   Base de datos: {DATABASE_CONFIG['database']}")
    
    try:
        # Crear instancia de conexión
        db = DatabaseConnection()
        print("✅ Instancia de DatabaseConnection creada correctamente")
        
        # Probar conexión
        print("🔌 Probando conexión...")
        if db.test_connection():
            print("✅ Conexión a MySQL exitosa")
        else:
            print("❌ No se pudo conectar a MySQL")
            return False
            
        # Probar obtener conexión
        print("🔗 Probando obtener conexión...")
        conn = db.get_connection()
        if conn:
            print("✅ Conexión obtenida correctamente")
            conn.close()
        else:
            print("❌ No se pudo obtener conexión")
            return False
            
        # Probar context manager
        print("🔄 Probando context manager...")
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print("✅ Context manager funcionando correctamente")
            else:
                print("❌ Error en context manager")
                return False
                
        return True
        
    except DatabaseError as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_database_creation():
    """Prueba la creación de la base de datos"""
    print("\n🏗️  Probando creación de base de datos...")
    
    try:
        db = DatabaseConnection()
        
        # Intentar crear la base de datos
        if db.create_database_if_not_exists():
            print("✅ Base de datos verificada/creada correctamente")
            return True
        else:
            print("❌ Error al crear/verificar base de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error al crear base de datos: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS DE CONFIGURACIÓN DE BASE DE DATOS")
    print("=" * 60)
    
    # Verificar variables de entorno
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("💡 Asegúrate de crear el archivo .env con las variables necesarias")
        sys.exit(1)
    
    # Ejecutar pruebas
    success = True
    
    if not test_database_connection():
        success = False
    
    if not test_database_creation():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODAS LAS PRUEBAS DE BASE DE DATOS PASARON")
    else:
        print("💥 ALGUNAS PRUEBAS FALLARON")
        print("💡 Verifica tu configuración de MySQL y las variables de entorno")
    print("=" * 60)
    
    sys.exit(0 if success else 1)