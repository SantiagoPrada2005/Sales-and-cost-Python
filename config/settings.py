"""
Configuraciones generales del Sistema de Ventas y Costos
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'sales_cost_system'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Configuración de la aplicación
APP_CONFIG = {
    'name': 'Sistema de Ventas y Costos',
    'version': '1.0.0',
    'author': 'Equipo de Desarrollo',
    'description': 'Sistema integral para gestión de ventas y control de costos'
}

# Configuración de impuestos
TAX_CONFIG = {
    'iva_rate': 0.19,  # 19% IVA
    'currency': 'COP',
    'currency_symbol': '$'
}

# Configuración de validaciones
VALIDATION_CONFIG = {
    'max_product_name_length': 100,
    'max_client_name_length': 100,
    'max_description_length': 500,
    'min_price': 0.01,
    'max_price': 999999999.99,
    'max_quantity': 999999
}

# Configuración de la interfaz
UI_CONFIG = {
    'window_width': 1200,
    'window_height': 800,
    'table_row_height': 30,
    'default_font_size': 10
}

# Configuración de logging
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/app.log'
}

# Estados de factura
INVOICE_STATES = {
    'DRAFT': 'borrador',
    'CONFIRMED': 'confirmada',
    'PAID': 'pagada',
    'CANCELLED': 'anulada'
}

# Estados de cuenta pendiente
PENDING_ACCOUNT_STATES = {
    'PENDING': 'pendiente',
    'PARTIAL': 'parcial',
    'PAID': 'pagada',
    'OVERDUE': 'vencida'
}