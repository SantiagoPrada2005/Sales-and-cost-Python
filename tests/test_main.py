#!/usr/bin/env python3
"""
Pruebas para el punto de entrada main.py
"""

import sys
import os
from unittest.mock import Mock, patch

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_main_imports():
    """Probar que main.py puede importar todas sus dependencias"""
    print("\n🔍 Probando importaciones de main.py...")
    
    try:
        # Probar importaciones individuales
        import config.settings
        print("✅ config.settings importado")
        
        import config.database
        print("✅ config.database importado")
        
        import utils.exceptions
        print("✅ utils.exceptions importado")
        
        # Verificar que las configuraciones están disponibles
        if hasattr(config.settings, 'APP_CONFIG'):
            print("✅ APP_CONFIG disponible")
        
        if hasattr(config.settings, 'DATABASE_CONFIG'):
            print("✅ DATABASE_CONFIG disponible")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_main_structure():
    """Probar la estructura del archivo main.py"""
    print("\n🔍 Probando estructura de main.py...")
    
    try:
        # Leer el archivo main.py
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar elementos clave
        required_elements = [
            'import logging',
            'import sys',
            'from PyQt5.QtWidgets import QApplication',
            'def setup_logging',
            'def check_database_connection',
            'def main',
            'if __name__ == "__main__"'
        ]
        
        for element in required_elements:
            if element in content:
                print(f"✅ {element} encontrado")
            else:
                print(f"❌ {element} no encontrado")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo main.py: {e}")
        return False

def test_logging_setup():
    """Probar la configuración de logging"""
    print("\n🔍 Probando configuración de logging...")
    
    try:
        # Mock de la configuración
        with patch('config.settings.APP_CONFIG', {'debug': True, 'log_level': 'INFO'}):
            # Importar la función después del mock
            from main import setup_logging
            
            # Probar que la función existe y es callable
            if callable(setup_logging):
                print("✅ setup_logging es callable")
            else:
                print("❌ setup_logging no es callable")
                return False
            
            # Intentar ejecutar (con mock para evitar crear archivos)
            with patch('logging.basicConfig'):
                setup_logging()
                print("✅ setup_logging ejecuta sin errores")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración de logging: {e}")
        return False

def test_database_connection_function():
    """Probar la función de prueba de conexión a base de datos"""
    print("\n🔍 Probando función de conexión a base de datos...")
    
    try:
        # Mock de la base de datos
        with patch('config.database.DatabaseConnection') as mock_db:
            mock_db_instance = Mock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.test_connection.return_value = True
            
            # Importar la función después del mock
            from main import check_database_connection
            
            # Probar que la función existe
            if callable(check_database_connection):
                print("✅ check_database_connection es callable")
            else:
                print("❌ check_database_connection no es callable")
                return False
            
            # Intentar ejecutar
            result = check_database_connection()
            print("✅ check_database_connection ejecuta sin errores")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en función de conexión: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS DEL PUNTO DE ENTRADA MAIN.PY")
    print("=" * 60)
    
    success = True
    
    if not test_main_imports():
        success = False
    
    if not test_main_structure():
        success = False
    
    if not test_logging_setup():
        success = False
    
    if not test_database_connection_function():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODAS LAS PRUEBAS DE MAIN.PY PASARON")
    else:
        print("💥 ALGUNAS PRUEBAS DE MAIN.PY FALLARON")
    print("=" * 60)
    
    sys.exit(0 if success else 1)