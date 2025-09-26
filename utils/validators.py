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
    
    def validar_cliente_completo(self, tipo_identificacion, numero_identificacion, nombre, 
                                email=None, telefono=None, direccion=None, ciudad=None, fecha_nacimiento=None):
        """Validar todos los campos de un cliente de forma completa"""
        # Validar tipo de identificación
        self.validate_required(tipo_identificacion, "Tipo de identificación")
        self.validar_tipo_identificacion(tipo_identificacion)
        
        # Validar número de identificación
        self.validate_required(numero_identificacion, "Número de identificación")
        self.validar_identificacion_por_tipo(numero_identificacion, tipo_identificacion)
        
        # Validar nombre
        self.validate_required(nombre, "Nombre")
        self.validate_length(nombre, "Nombre", VALIDATION_CONFIG['max_client_name_length'], 2)
        self.validar_nombre_format(nombre)
        
        # Validar email si se proporciona
        if email and email.strip():
            self.validar_email(email)
        
        # Validar teléfono si se proporciona
        if telefono and telefono.strip():
            self.validar_telefono(telefono)
        
        # Validar dirección si se proporciona
        if direccion and direccion.strip():
            self.validate_length(direccion, "Dirección", 255)
        
        # Validar ciudad si se proporciona
        if ciudad and ciudad.strip():
            self.validate_length(ciudad, "Ciudad", 50)
            self.validar_ciudad_format(ciudad)
        
        # Validar fecha de nacimiento si se proporciona
        if fecha_nacimiento:
            self.validar_fecha_nacimiento(fecha_nacimiento)
    
    def validar_cliente(self, nombre, identificacion, email=None, telefono=None):
        """Validar campos básicos de un cliente (mantenido por compatibilidad)"""
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
    
    def validar_tipo_identificacion(self, tipo_identificacion):
        """Validar que el tipo de identificación sea válido"""
        tipos_validos = [
            "Cédula de Ciudadanía",
            "Cédula de Extranjería", 
            "NIT",
            "Pasaporte",
            "Tarjeta de Identidad"
        ]
        if tipo_identificacion not in tipos_validos:
            raise ValidationError(f"Tipo de identificación inválido. Tipos válidos: {', '.join(tipos_validos)}")
    
    def validar_identificacion_por_tipo(self, numero_identificacion, tipo_identificacion):
        """Validar formato de identificación según el tipo"""
        numero_clean = numero_identificacion.replace('-', '').replace(' ', '')
        
        if tipo_identificacion == "Cédula de Ciudadanía":
            if not re.match(r'^\d{6,10}$', numero_clean):
                raise ValidationError("La cédula de ciudadanía debe tener entre 6 y 10 dígitos")
        
        elif tipo_identificacion == "Cédula de Extranjería":
            if not re.match(r'^\d{6,12}$', numero_clean):
                raise ValidationError("La cédula de extranjería debe tener entre 6 y 12 dígitos")
        
        elif tipo_identificacion == "NIT":
            if not re.match(r'^\d{9,15}$', numero_clean):
                raise ValidationError("El NIT debe tener entre 9 y 15 dígitos")
        
        elif tipo_identificacion == "Pasaporte":
            if not re.match(r'^[A-Za-z0-9]{6,12}$', numero_identificacion.replace('-', '').replace(' ', '')):
                raise ValidationError("El pasaporte debe tener entre 6 y 12 caracteres alfanuméricos")
        
        elif tipo_identificacion == "Tarjeta de Identidad":
            if not re.match(r'^\d{8,15}$', numero_clean):
                raise ValidationError("La tarjeta de identidad debe tener entre 8 y 15 dígitos")
    
    def validar_identificacion_format(self, identificacion):
        """Validar formato de identificación (solo números) - método legacy"""
        if not re.match(r'^\d+$', identificacion):
            raise ValidationError("La identificación solo puede contener números")
        
        if len(identificacion) < 6 or len(identificacion) > 15:
            raise ValidationError("La identificación debe tener entre 6 y 15 dígitos")
    
    def validar_nombre_format(self, nombre):
        """Validar formato del nombre (solo letras, espacios y algunos caracteres especiales)"""
        if not re.match(r'^[A-Za-zÀ-ÿ\u00f1\u00d1\s\.\-\']+$', nombre):
            raise ValidationError("El nombre solo puede contener letras, espacios, puntos, guiones y apostrofes")
    
    def validar_email(self, email):
        """Validar formato de email"""
        try:
            # Usar check_deliverability=False para evitar verificación de dominio en pruebas
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise ValidationError("El formato del email no es válido")
        
        # Validación adicional de longitud
        self.validate_length(email, "Email", 100)
    
    def validar_telefono(self, telefono):
        """Validar formato de teléfono"""
        # Remover espacios y caracteres especiales para validación
        telefono_clean = re.sub(r'[^\d+]', '', telefono)
        
        if not re.match(r'^[\+]?[\d\s\-\(\)]{7,20}$', telefono):
            raise ValidationError("El formato del teléfono no es válido")
        
        # Validar que tenga al menos 7 dígitos
        if len(telefono_clean) < 7:
            raise ValidationError("El teléfono debe tener al menos 7 dígitos")
    
    def validar_ciudad_format(self, ciudad):
        """Validar formato de la ciudad"""
        if not re.match(r'^[A-Za-zÀ-ÿ\u00f1\u00d1\s\.\-]+$', ciudad):
            raise ValidationError("La ciudad solo puede contener letras, espacios, puntos y guiones")
    
    def validar_fecha_nacimiento(self, fecha_nacimiento):
        """Validar fecha de nacimiento"""
        if isinstance(fecha_nacimiento, str):
            try:
                fecha_obj = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Formato de fecha de nacimiento inválido. Use YYYY-MM-DD")
        else:
            fecha_obj = fecha_nacimiento
        
        # Validar que no sea futura
        if fecha_obj > datetime.now():
            raise ValidationError("La fecha de nacimiento no puede ser futura")
        
        # Validar edad mínima (por ejemplo, 0 años) y máxima (por ejemplo, 120 años)
        edad_anos = (datetime.now() - fecha_obj).days / 365.25
        if edad_anos < 0:
            raise ValidationError("La fecha de nacimiento no es válida")
        if edad_anos > 120:
            raise ValidationError("La fecha de nacimiento indica una edad no válida")
    
    def validar_actualizacion_cliente(self, **campos):
        """Validar campos para actualización de cliente (campos opcionales)"""
        if 'nombre' in campos and campos['nombre']:
            self.validate_length(campos['nombre'], "Nombre", VALIDATION_CONFIG['max_client_name_length'], 2)
            self.validar_nombre_format(campos['nombre'])
        
        if 'email' in campos and campos['email']:
            self.validar_email(campos['email'])
        
        if 'telefono' in campos and campos['telefono']:
            self.validar_telefono(campos['telefono'])
        
        if 'direccion' in campos and campos['direccion']:
            self.validate_length(campos['direccion'], "Dirección", 255)
        
        if 'ciudad' in campos and campos['ciudad']:
            self.validate_length(campos['ciudad'], "Ciudad", 50)
            self.validar_ciudad_format(campos['ciudad'])
        
        if 'fecha_nacimiento' in campos and campos['fecha_nacimiento']:
            self.validar_fecha_nacimiento(campos['fecha_nacimiento'])

class FacturaValidator(BaseValidator):
    """Validador para facturas"""
    
    def validar_factura_completa(self, cliente_id, observaciones=None, detalles=None):
        """Validar datos completos de una factura"""
        # Validar cliente
        self.validate_required(cliente_id, "Cliente")
        self.validate_integer(cliente_id, "Cliente ID", 1)
        
        # Validar observaciones
        if observaciones:
            self.validar_observaciones(observaciones)
        
        # Validar que tenga al menos un detalle
        if detalles is not None:
            if not detalles or len(detalles) == 0:
                raise ValidationError("La factura debe tener al menos un producto")
            
            # Validar cada detalle
            for i, detalle in enumerate(detalles):
                try:
                    self.validar_detalle_factura(
                        detalle.get('cantidad'),
                        detalle.get('precio_unitario'),
                        detalle.get('producto_id')
                    )
                except ValidationError as e:
                    raise ValidationError(f"Error en producto {i+1}: {str(e)}")
    
    def validar_detalle_factura(self, cantidad, precio_unitario, producto_id=None):
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
        
        # Validar producto ID si se proporciona
        if producto_id is not None:
            self.validate_integer(producto_id, "Producto ID", 1)
    
    def validar_numero_factura(self, numero_factura):
        """Validar formato del número de factura"""
        self.validate_required(numero_factura, "Número de factura")
        self.validate_length(numero_factura, "Número de factura", 20, 3)
        
        # Validar formato (letras, números y guiones)
        if not re.match(r'^[A-Za-z0-9-]+$', numero_factura):
            raise ValidationError("El número de factura solo puede contener letras, números y guiones")
    
    def validar_estado_factura(self, estado):
        """Validar que el estado de la factura sea válido"""
        estados_validos = ['borrador', 'confirmada', 'anulada']
        if estado not in estados_validos:
            raise ValidationError(f"Estado de factura inválido. Estados válidos: {', '.join(estados_validos)}")
    
    def validar_cambio_estado(self, estado_actual, nuevo_estado):
        """Validar que el cambio de estado sea válido"""
        transiciones_validas = {
            'borrador': ['confirmada', 'anulada'],
            'confirmada': ['anulada'],
            'anulada': []  # No se puede cambiar desde anulada
        }
        
        if nuevo_estado not in transiciones_validas.get(estado_actual, []):
            raise ValidationError(f"No se puede cambiar de estado '{estado_actual}' a '{nuevo_estado}'")
    
    def validar_totales_factura(self, subtotal, impuestos, total):
        """Validar que los totales de la factura sean correctos"""
        # Validar que sean números positivos
        self.validate_decimal(subtotal, "Subtotal", 0)
        self.validate_decimal(impuestos, "Impuestos", 0)
        self.validate_decimal(total, "Total", 0)
        
        # Validar que el total sea la suma del subtotal e impuestos
        subtotal_decimal = Decimal(str(subtotal))
        impuestos_decimal = Decimal(str(impuestos))
        total_decimal = Decimal(str(total))
        
        total_calculado = subtotal_decimal + impuestos_decimal
        
        # Permitir una pequeña diferencia por redondeo
        diferencia = abs(total_decimal - total_calculado)
        if diferencia > Decimal('0.01'):
            raise ValidationError("El total no coincide con la suma del subtotal e impuestos")
    
    def validar_observaciones(self, observaciones):
        """Validar observaciones de factura"""
        if observaciones:
            self.validate_length(observaciones, "Observaciones", VALIDATION_CONFIG['max_description_length'])
    
    def validar_stock_disponible(self, producto_id, cantidad_solicitada, stock_actual):
        """Validar que hay suficiente stock para la cantidad solicitada"""
        if stock_actual < cantidad_solicitada:
            raise ValidationError(f"Stock insuficiente. Disponible: {stock_actual}, Solicitado: {cantidad_solicitada}")
    
    def validar_actualizacion_detalle(self, detalle_id, nueva_cantidad=None, nuevo_precio=None):
        """Validar actualización de detalle de factura"""
        self.validate_integer(detalle_id, "ID del detalle", 1)
        
        if nueva_cantidad is not None:
            self.validate_integer(nueva_cantidad, "Nueva cantidad", 1, VALIDATION_CONFIG['max_quantity'])
        
        if nuevo_precio is not None:
            self.validate_decimal(
                nuevo_precio, 
                "Nuevo precio", 
                VALIDATION_CONFIG['min_price'], 
                VALIDATION_CONFIG['max_price']
            )

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