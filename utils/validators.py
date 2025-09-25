"""
Validadores para el Sistema de Ventas y Costos
"""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from utils.exceptions import ValidationError
from config.settings import VALIDATION_CONFIG

class BaseValidator:
    """Clase base para validadores"""
    
    @staticmethod
    def validate_required(value, field_name):
        """Validar que un campo requerido no esté vacío"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"El campo '{field_name}' es requerido")
    
    @staticmethod
    def validate_length(value, field_name, max_length, min_length=1):
        """Validar la longitud de un campo de texto"""
        if value and len(value) > max_length:
            raise ValidationError(f"El campo '{field_name}' no puede exceder {max_length} caracteres")
        if value and len(value) < min_length:
            raise ValidationError(f"El campo '{field_name}' debe tener al menos {min_length} caracteres")
    
    @staticmethod
    def validate_decimal(value, field_name, min_value=None, max_value=None):
        """Validar que un valor sea un decimal válido"""
        try:
            decimal_value = Decimal(str(value))
            if min_value is not None and decimal_value < Decimal(str(min_value)):
                raise ValidationError(f"El campo '{field_name}' debe ser mayor o igual a {min_value}")
            if max_value is not None and decimal_value > Decimal(str(max_value)):
                raise ValidationError(f"El campo '{field_name}' debe ser menor o igual a {max_value}")
            return decimal_value
        except (InvalidOperation, ValueError):
            raise ValidationError(f"El campo '{field_name}' debe ser un número válido")
    
    @staticmethod
    def validate_integer(value, field_name, min_value=None, max_value=None):
        """Validar que un valor sea un entero válido"""
        try:
            int_value = int(value)
            if min_value is not None and int_value < min_value:
                raise ValidationError(f"El campo '{field_name}' debe ser mayor o igual a {min_value}")
            if max_value is not None and int_value > max_value:
                raise ValidationError(f"El campo '{field_name}' debe ser menor o igual a {max_value}")
            return int_value
        except (ValueError, TypeError):
            raise ValidationError(f"El campo '{field_name}' debe ser un número entero válido")

class ProductoValidator(BaseValidator):
    """Validador para productos"""
    
    def validar_producto(self, codigo_sku, nombre, costo_adquisicion, precio_venta):
        """Validar todos los campos de un producto"""
        # Validar SKU
        self.validate_required(codigo_sku, "Código SKU")
        self.validate_length(codigo_sku, "Código SKU", 50)
        self.validar_sku_format(codigo_sku)
        
        # Validar nombre
        self.validate_required(nombre, "Nombre")
        self.validate_length(nombre, "Nombre", VALIDATION_CONFIG['max_product_name_length'])
        
        # Validar precios
        self.validate_decimal(
            costo_adquisicion, 
            "Costo de adquisición", 
            VALIDATION_CONFIG['min_price'], 
            VALIDATION_CONFIG['max_price']
        )
        self.validate_decimal(
            precio_venta, 
            "Precio de venta", 
            VALIDATION_CONFIG['min_price'], 
            VALIDATION_CONFIG['max_price']
        )
        
        # Validar que el precio de venta sea mayor al costo
        if Decimal(str(precio_venta)) <= Decimal(str(costo_adquisicion)):
            raise ValidationError("El precio de venta debe ser mayor al costo de adquisición")
    
    def validar_sku_format(self, sku):
        """Validar formato del SKU (alfanumérico, guiones y guiones bajos permitidos)"""
        if not re.match(r'^[A-Za-z0-9_-]+$', sku):
            raise ValidationError("El SKU solo puede contener letras, números, guiones y guiones bajos")
    
    def validar_stock(self, cantidad):
        """Validar cantidad de stock"""
        return self.validate_integer(
            cantidad, 
            "Cantidad", 
            0, 
            VALIDATION_CONFIG['max_quantity']
        )

class ClienteValidator(BaseValidator):
    """Validador para clientes"""
    
    def validar_cliente(self, nombre, identificacion, email=None, telefono=None):
        """Validar todos los campos de un cliente"""
        # Validar nombre
        self.validate_required(nombre, "Nombre")
        self.validate_length(nombre, "Nombre", VALIDATION_CONFIG['max_client_name_length'])
        
        # Validar identificación
        self.validate_required(identificacion, "Identificación")
        self.validar_identificacion_format(identificacion)
        
        # Validar email si se proporciona
        if email:
            self.validar_email(email)
        
        # Validar teléfono si se proporciona
        if telefono:
            self.validar_telefono(telefono)
    
    def validar_identificacion_format(self, identificacion):
        """Validar formato de identificación (solo números)"""
        if not re.match(r'^\d+$', identificacion):
            raise ValidationError("La identificación solo puede contener números")
        
        if len(identificacion) < 6 or len(identificacion) > 15:
            raise ValidationError("La identificación debe tener entre 6 y 15 dígitos")
    
    def validar_email(self, email):
        """Validar formato de email"""
        try:
            validate_email(email)
        except EmailNotValidError:
            raise ValidationError("El formato del email no es válido")
    
    def validar_telefono(self, telefono):
        """Validar formato de teléfono"""
        # Remover espacios y caracteres especiales para validación
        telefono_clean = re.sub(r'[^\d+]', '', telefono)
        
        if not re.match(r'^[\+]?[\d\s\-\(\)]{7,15}$', telefono):
            raise ValidationError("El formato del teléfono no es válido")

class FacturaValidator(BaseValidator):
    """Validador para facturas"""
    
    def validar_detalle_factura(self, cantidad, precio_unitario):
        """Validar detalle de factura"""
        # Validar cantidad
        self.validate_integer(cantidad, "Cantidad", 1, VALIDATION_CONFIG['max_quantity'])
        
        # Validar precio unitario
        self.validate_decimal(
            precio_unitario, 
            "Precio unitario", 
            VALIDATION_CONFIG['min_price'], 
            VALIDATION_CONFIG['max_price']
        )
    
    def validar_observaciones(self, observaciones):
        """Validar observaciones de factura"""
        if observaciones:
            self.validate_length(observaciones, "Observaciones", VALIDATION_CONFIG['max_description_length'])

class PagoValidator(BaseValidator):
    """Validador para pagos"""
    
    def validar_pago(self, monto, metodo_pago, referencia=None):
        """Validar datos de pago"""
        # Validar monto
        self.validate_decimal(
            monto, 
            "Monto", 
            VALIDATION_CONFIG['min_price'], 
            VALIDATION_CONFIG['max_price']
        )
        
        # Validar método de pago
        self.validate_required(metodo_pago, "Método de pago")
        self.validar_metodo_pago(metodo_pago)
        
        # Validar referencia si se proporciona
        if referencia:
            self.validate_length(referencia, "Referencia", 100)
    
    def validar_metodo_pago(self, metodo_pago):
        """Validar que el método de pago sea válido"""
        metodos_validos = ['efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'cheque']
        if metodo_pago.lower() not in metodos_validos:
            raise ValidationError(f"Método de pago inválido. Métodos válidos: {', '.join(metodos_validos)}")
    
    def validar_fecha_pago(self, fecha_pago):
        """Validar que la fecha de pago no sea futura"""
        if isinstance(fecha_pago, str):
            try:
                fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD")
        
        if fecha_pago > datetime.now():
            raise ValidationError("La fecha de pago no puede ser futura")