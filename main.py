#!/usr/bin/env python3
"""
Sistema de Ventas y Costos
Punto de entrada principal de la aplicación

Autor: Equipo de Desarrollo
Versión: 1.0.0
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import APP_CONFIG, LOGGING_CONFIG, UI_CONFIG
from config.database import DatabaseConnection
from utils.exceptions import ConfigurationError, DatabaseError

def setup_logging():
    """Configurar el sistema de logging"""
    try:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(LOGGING_CONFIG['file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG['level']),
            format=LOGGING_CONFIG['format'],
            handlers=[
                logging.FileHandler(LOGGING_CONFIG['file'], encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Iniciando {APP_CONFIG['name']} v{APP_CONFIG['version']}")
        return logger
        
    except Exception as e:
        print(f"Error configurando logging: {e}")
        # Configuración básica de fallback
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

def check_database_connection():
    """Verificar la conexión a la base de datos"""
    try:
        db = DatabaseConnection()
        if db.test_connection():
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error verificando conexión a BD: {e}")
        return False

def show_error_dialog(title, message):
    """Mostrar diálogo de error"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

def create_splash_screen():
    """Crear pantalla de carga"""
    # Crear un pixmap simple para la pantalla de carga
    pixmap = QPixmap(400, 300)
    pixmap.fill(Qt.white)
    
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
    
    # Mostrar mensaje en la pantalla de carga
    splash.showMessage(
        f"Cargando {APP_CONFIG['name']}...\nVersión {APP_CONFIG['version']}",
        Qt.AlignCenter | Qt.AlignBottom,
        Qt.black
    )
    
    return splash

def setup_application():
    """Configurar la aplicación PyQt5"""
    app = QApplication(sys.argv)
    
    # Configurar propiedades de la aplicación
    app.setApplicationName(APP_CONFIG['name'])
    app.setApplicationVersion(APP_CONFIG['version'])
    app.setOrganizationName(APP_CONFIG['author'])
    
    # Configurar fuente por defecto
    font = QFont()
    font.setPointSize(UI_CONFIG['default_font_size'])
    app.setFont(font)
    
    return app

def main():
    """Función principal"""
    logger = setup_logging()
    
    try:
        # Crear aplicación PyQt5
        app = setup_application()
        
        # Mostrar pantalla de carga
        splash = create_splash_screen()
        splash.show()
        app.processEvents()
        
        # Simular tiempo de carga
        QTimer.singleShot(2000, splash.close)
        
        logger.info("Aplicación PyQt5 configurada correctamente")
        
        # Verificar conexión a base de datos
        logger.info("Verificando conexión a la base de datos...")
        if not check_database_connection():
            error_msg = """
            No se pudo conectar a la base de datos.
            
            Verifique:
            1. Que MySQL esté ejecutándose
            2. Las credenciales en el archivo .env
            3. Que la base de datos exista
            
            Consulte la documentación para más información.
            """
            logger.error("Fallo en la conexión a la base de datos")
            show_error_dialog("Error de Conexión", error_msg)
            return 1
        
        logger.info("Conexión a la base de datos exitosa")
        
        # Importar y mostrar ventana principal
        from views.main_window import MainWindow
        
        # Cerrar pantalla de carga
        splash.finish(None)
        
        # Crear y mostrar ventana principal
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Ventana principal mostrada exitosamente")
        
        # Ejecutar el bucle principal de la aplicación
        return app.exec_()
        
    except ConfigurationError as e:
        logger.error(f"Error de configuración: {e}")
        show_error_dialog("Error de Configuración", str(e))
        return 1
        
    except DatabaseError as e:
        logger.error(f"Error de base de datos: {e}")
        show_error_dialog("Error de Base de Datos", str(e))
        return 1
        
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        show_error_dialog("Error Inesperado", f"Ha ocurrido un error inesperado:\n{e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())