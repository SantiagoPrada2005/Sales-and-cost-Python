#!/usr/bin/env python3
"""
Script de prueba para verificar las clases de utilidades
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.exceptions import *
from utils.validators import *
from utils.formatters import *

def test_exceptions():
    """Prueba las excepciones personalizadas"""
    print("🔍 Probando excepciones personalizadas...")
    
    try:
        # Probar excepción base
        try:
            raise SalesSystemError("Error de prueba")
        except SalesSystemError as e:
            print(f"✅ SalesSystemError: {e}")
        
        # Probar excepción de validación
        try:
            raise ValidationError("Error de validación")
        except ValidationError as e:
            print(f"✅ ValidationError: {e}")
        
        # Probar excepción de producto
        try:
            raise ProductoError("Error de producto")
        except ProductoError as e:
            print(f"✅ ProductoError: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de excepciones: {e}")
        return False

def test_validators():
    """Prueba los validadores"""
    print("\n🔍 Probando validadores...")
    
    try:
        # Probar BaseValidator
        print("📋 Probando BaseValidator...")
        
        # Validación de campos requeridos
        BaseValidator.validate_required("test", "campo_test")
        print("✅ validate_required funciona")
        
        # Validación de longitud
        BaseValidator.validate_length("test", "campo_test", min_length=2, max_length=10)
        print("✅ validate_length funciona")
        
        # Validación de decimal
        BaseValidator.validate_decimal(Decimal("10.50"), "precio")
        print("✅ validate_decimal funciona")
        
        # Validación de entero
        BaseValidator.validate_integer(100, "cantidad")
        print("✅ validate_integer funciona")
        
        # Probar ProductoValidator
        print("📋 Probando ProductoValidator...")
        validator = ProductoValidator()
        validator.validar_producto('TEST001', 'Producto Test', Decimal('50.00'), Decimal('100.00'))
        print("✅ ProductoValidator.validar_producto funciona")
        
        # Probar ClienteValidator
        print("📋 Probando ClienteValidator...")
        validator = ClienteValidator()
        validator.validar_cliente('Cliente Test', '12345678', 'user@gmail.com', '1234567890')
        print("✅ ClienteValidator.validar_cliente funciona")
        
        # Probar FacturaValidator
        print("📋 Probando FacturaValidator...")
        validator = FacturaValidator()
        validator.validar_detalle_factura(5, Decimal('100.00'))
        print("✅ FacturaValidator.validar_detalle_factura funciona")
        
        # Probar PagoValidator
        print("📋 Probando PagoValidator...")
        validator = PagoValidator()
        validator.validar_pago(Decimal('100.00'), 'efectivo')
        print("✅ PagoValidator.validar_pago funciona")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de validadores: {e}")
        return False

def test_formatters():
    """Prueba los formateadores"""
    print("\n🔍 Probando formateadores...")
    
    try:
        # Probar CurrencyFormatter
        print("📋 Probando CurrencyFormatter...")
        formatted = CurrencyFormatter.format_currency(Decimal('1234.56'))
        print(f"✅ Formato de moneda: {formatted}")
        
        parsed = CurrencyFormatter.parse_currency("$1,234.56")
        print(f"✅ Parse de moneda: {parsed}")
        
        # Probar DateFormatter
        print("📋 Probando DateFormatter...")
        now = datetime.now()
        formatted_date = DateFormatter.format_date(now.date())
        print(f"✅ Formato de fecha: {formatted_date}")
        
        formatted_datetime = DateFormatter.format_datetime(now)
        print(f"✅ Formato de fecha y hora: {formatted_datetime}")
        
        # Probar NumberFormatter
        print("📋 Probando NumberFormatter...")
        formatted_decimal = NumberFormatter.format_decimal(Decimal('1234.567'), 2)
        print(f"✅ Formato decimal: {formatted_decimal}")
        
        formatted_percent = NumberFormatter.format_percentage(Decimal('0.15'))
        print(f"✅ Formato porcentaje: {formatted_percent}")
        
        # Probar TextFormatter
        print("📋 Probando TextFormatter...")
        capitalized = TextFormatter.capitalize_words("hola mundo")
        print(f"✅ Capitalizar palabras: {capitalized}")
        
        cleaned = TextFormatter.clean_text("  Texto con espacios  ")
        print(f"✅ Limpiar texto: '{cleaned}'")
        
        # Probar InvoiceFormatter
        print("📋 Probando InvoiceFormatter...")
        invoice_number = InvoiceFormatter.format_invoice_number(123)
        print(f"✅ Número de factura: {invoice_number}")
        
        state_text = InvoiceFormatter.format_invoice_state("pendiente")
        print(f"✅ Estado de factura: {state_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de formateadores: {e}")
        return False

def test_validation_errors():
    """Prueba que las validaciones fallen correctamente"""
    print("\n🔍 Probando errores de validación...")
    
    try:
        # Probar validación que debe fallar
        try:
            BaseValidator.validate_required("", "campo_vacio")
            print("❌ validate_required debería haber fallado")
            return False
        except ValidationError:
            print("✅ validate_required falla correctamente con campo vacío")
        
        # Probar longitud que debe fallar
        try:
            BaseValidator.validate_length("a", "campo_corto", max_length=10, min_length=5)
            print("❌ validate_length debería haber fallado")
            return False
        except ValidationError:
            print("✅ validate_length falla correctamente con texto corto")
        
        # Probar email inválido
        try:
            validator = ClienteValidator()
            validator.validar_cliente('Cliente Test', '12345678', 'email_invalido', '1234567890')
            print("❌ ClienteValidator debería haber fallado con email inválido")
            return False
        except ValidationError:
            print("✅ ClienteValidator falla correctamente con email inválido")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en prueba de errores de validación: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBAS DE UTILIDADES")
    print("=" * 60)
    
    success = True
    
    if not test_exceptions():
        success = False
    
    if not test_validators():
        success = False
    
    if not test_formatters():
        success = False
    
    if not test_validation_errors():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODAS LAS PRUEBAS DE UTILIDADES PASARON")
    else:
        print("💥 ALGUNAS PRUEBAS FALLARON")
    print("=" * 60)
    
    sys.exit(0 if success else 1)