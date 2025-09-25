"""
Excepciones personalizadas del Sistema de Ventas y Costos
"""

class SalesSystemError(Exception):
    """Excepción base para el sistema de ventas"""
    pass

class ValidationError(SalesSystemError):
    """Excepción para errores de validación de datos"""
    pass

class ProductoError(SalesSystemError):
    """Excepción específica para errores relacionados con productos"""
    pass

class ClienteError(SalesSystemError):
    """Excepción específica para errores relacionados con clientes"""
    pass

class FacturaError(SalesSystemError):
    """Excepción específica para errores relacionados con facturas"""
    pass

class PagoError(SalesSystemError):
    """Excepción específica para errores relacionados con pagos"""
    pass

class DatabaseError(SalesSystemError):
    """Excepción para errores de base de datos"""
    pass

class ConfigurationError(SalesSystemError):
    """Excepción para errores de configuración"""
    pass

class BusinessRuleError(SalesSystemError):
    """Excepción para violaciones de reglas de negocio"""
    pass

class InsufficientStockError(ProductoError):
    """Excepción para casos de stock insuficiente"""
    pass

class DuplicateRecordError(SalesSystemError):
    """Excepción para registros duplicados"""
    pass

class RecordNotFoundError(SalesSystemError):
    """Excepción para registros no encontrados"""
    pass

class InvalidStateError(SalesSystemError):
    """Excepción para estados inválidos de entidades"""
    pass