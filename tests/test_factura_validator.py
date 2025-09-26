"""
Pruebas unitarias para el validador de facturas
"""
import unittest
from decimal import Decimal
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.validators import FacturaValidator
from utils.exceptions import ValidationError
from config.settings import VALIDATION_CONFIG


class TestFacturaValidator(unittest.TestCase):
    """
    Pruebas para el validador de facturas
    """
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.validator = FacturaValidator()
    
    def test_validar_factura_completa_exitosa(self):
        """Prueba validación exitosa de factura completa"""
        detalles = [
            {
                'cantidad': 2,
                'precio_unitario': Decimal('100.00'),
                'producto_id': 1
            },
            {
                'cantidad': 1,
                'precio_unitario': Decimal('50.00'),
                'producto_id': 2
            }
        ]
        
        # No debe lanzar excepción
        try:
            self.validator.validar_factura_completa(
                cliente_id=1,
                observaciones="Factura de prueba",
                detalles=detalles
            )
        except ValidationError:
            self.fail("validar_factura_completa lanzó ValidationError inesperadamente")
    
    def test_validar_factura_completa_cliente_requerido(self):
        """Prueba validación con cliente faltante"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(cliente_id=None)
        
        self.assertIn("Cliente", str(context.exception))
    
    def test_validar_factura_completa_cliente_id_invalido(self):
        """Prueba validación con cliente ID inválido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(cliente_id=0)
        
        self.assertIn("Cliente ID", str(context.exception))
    
    def test_validar_factura_completa_observaciones_largas(self):
        """Prueba validación con observaciones muy largas"""
        observaciones_largas = "x" * (VALIDATION_CONFIG['max_description_length'] + 1)
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(
                cliente_id=1,
                observaciones=observaciones_largas
            )
        
        self.assertIn("Observaciones", str(context.exception))
    
    def test_validar_factura_completa_sin_detalles(self):
        """Prueba validación con lista de detalles vacía"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(
                cliente_id=1,
                detalles=[]
            )
        
        self.assertIn("al menos un producto", str(context.exception))
    
    def test_validar_factura_completa_detalle_invalido(self):
        """Prueba validación con detalle inválido"""
        detalles = [
            {
                'cantidad': 0,  # Cantidad inválida
                'precio_unitario': Decimal('100.00'),
                'producto_id': 1
            }
        ]
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(
                cliente_id=1,
                detalles=detalles
            )
        
        self.assertIn("Error en producto 1", str(context.exception))
    
    def test_validar_detalle_factura_exitoso(self):
        """Prueba validación exitosa de detalle"""
        # No debe lanzar excepción
        try:
            self.validator.validar_detalle_factura(
                cantidad=5,
                precio_unitario=Decimal('100.00'),
                producto_id=1
            )
        except ValidationError:
            self.fail("validar_detalle_factura lanzó ValidationError inesperadamente")
    
    def test_validar_detalle_factura_cantidad_cero(self):
        """Prueba validación con cantidad cero"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=0,
                precio_unitario=Decimal('100.00')
            )
        
        self.assertIn("Cantidad", str(context.exception))
    
    def test_validar_detalle_factura_cantidad_negativa(self):
        """Prueba validación con cantidad negativa"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=-1,
                precio_unitario=Decimal('100.00')
            )
        
        self.assertIn("Cantidad", str(context.exception))
    
    def test_validar_detalle_factura_cantidad_excesiva(self):
        """Prueba validación con cantidad excesiva"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=VALIDATION_CONFIG['max_quantity'] + 1,
                precio_unitario=Decimal('100.00')
            )
        
        self.assertIn("Cantidad", str(context.exception))
    
    def test_validar_detalle_factura_precio_cero(self):
        """Prueba validación con precio cero"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=Decimal('0.00')
            )
        
        self.assertIn("Precio unitario", str(context.exception))
    
    def test_validar_detalle_factura_precio_negativo(self):
        """Prueba validación con precio negativo"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=Decimal('-10.00')
            )
        
        self.assertIn("Precio unitario", str(context.exception))
    
    def test_validar_detalle_factura_precio_excesivo(self):
        """Prueba validación con precio excesivo"""
        precio_excesivo = Decimal(str(VALIDATION_CONFIG['max_price'] + 1))
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=precio_excesivo
            )
        
        self.assertIn("Precio unitario", str(context.exception))
    
    def test_validar_detalle_factura_producto_id_invalido(self):
        """Prueba validación con producto ID inválido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=Decimal('100.00'),
                producto_id=0
            )
        
        self.assertIn("Producto ID", str(context.exception))
    
    def test_validar_numero_factura_exitoso(self):
        """Prueba validación exitosa de número de factura"""
        numeros_validos = ["F-001", "FAC-2024-001", "INV001", "F001"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_numero_factura(numero)
            except ValidationError:
                self.fail(f"validar_numero_factura falló con número válido: {numero}")
    
    def test_validar_numero_factura_vacio(self):
        """Prueba validación con número de factura vacío"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_numero_factura("")
        
        self.assertIn("requerido", str(context.exception))
    
    def test_validar_numero_factura_muy_corto(self):
        """Prueba validación de número de factura muy corto"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_numero_factura("AB")
        self.assertIn("debe tener al menos", str(context.exception))
    
    def test_validar_numero_factura_muy_largo(self):
        """Prueba validación de número de factura muy largo"""
        numero_largo = "A" * 25  # Más de 20 caracteres
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_numero_factura(numero_largo)
        self.assertIn("no puede exceder", str(context.exception))
    
    def test_validar_numero_factura_caracteres_invalidos(self):
        """Prueba validación con caracteres inválidos"""
        numeros_invalidos = ["F@001", "F 001", "F.001", "F_001"]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError) as context:
                self.validator.validar_numero_factura(numero)
            
            self.assertIn("solo puede contener", str(context.exception))
    
    def test_validar_estado_factura_validos(self):
        """Prueba validación con estados válidos"""
        estados_validos = ['borrador', 'confirmada', 'anulada']
        
        for estado in estados_validos:
            try:
                self.validator.validar_estado_factura(estado)
            except ValidationError:
                self.fail(f"validar_estado_factura falló con estado válido: {estado}")
    
    def test_validar_estado_factura_invalido(self):
        """Prueba validación con estado inválido"""
        estados_invalidos = ['pendiente', 'pagada', 'vencida', 'cancelada']
        
        for estado in estados_invalidos:
            with self.assertRaises(ValidationError) as context:
                self.validator.validar_estado_factura(estado)
            
            self.assertIn("Estado de factura inválido", str(context.exception))
    
    def test_validar_totales_factura_correctos(self):
        """Prueba validación con totales correctos"""
        subtotal = Decimal('1000.00')
        impuestos = Decimal('190.00')
        total = Decimal('1190.00')
        
        # No debe lanzar excepción
        try:
            self.validator.validar_totales_factura(subtotal, impuestos, total)
        except ValidationError:
            self.fail("validar_totales_factura lanzó ValidationError inesperadamente")
    
    def test_validar_totales_factura_subtotal_negativo(self):
        """Prueba validación con subtotal negativo"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_totales_factura(
                Decimal('-100.00'),
                Decimal('19.00'),
                Decimal('-81.00')
            )
        
        self.assertIn("Subtotal", str(context.exception))
    
    def test_validar_totales_factura_impuestos_negativos(self):
        """Prueba validación con impuestos negativos"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_totales_factura(
                Decimal('100.00'),
                Decimal('-19.00'),
                Decimal('81.00')
            )
        
        self.assertIn("Impuestos", str(context.exception))
    
    def test_validar_totales_factura_total_negativo(self):
        """Prueba validación con total negativo"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_totales_factura(
                Decimal('100.00'),
                Decimal('19.00'),
                Decimal('-119.00')
            )
        
        self.assertIn("Total", str(context.exception))
    
    def test_validar_totales_factura_suma_incorrecta(self):
        """Prueba validación con suma incorrecta"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_totales_factura(
                Decimal('1000.00'),
                Decimal('190.00'),
                Decimal('1000.00')  # Total incorrecto
            )
        
        self.assertIn("no coincide", str(context.exception))
    
    def test_validar_totales_factura_diferencia_redondeo(self):
        """Prueba validación con diferencia mínima por redondeo"""
        # Diferencia de 0.01 debe ser aceptable
        subtotal = Decimal('100.00')
        impuestos = Decimal('19.00')
        total = Decimal('119.01')  # Diferencia de 0.01
        
        # No debe lanzar excepción
        try:
            self.validator.validar_totales_factura(subtotal, impuestos, total)
        except ValidationError:
            self.fail("validar_totales_factura no debe fallar con diferencia mínima")
    
    def test_validar_observaciones_validas(self):
        """Prueba validación con observaciones válidas"""
        observaciones_validas = [
            "Factura de prueba",
            "Cliente preferencial - descuento aplicado",
            "Entrega urgente solicitada",
            ""  # Observaciones vacías deben ser válidas
        ]
        
        for obs in observaciones_validas:
            try:
                self.validator.validar_observaciones(obs)
            except ValidationError:
                self.fail(f"validar_observaciones falló con observación válida: {obs}")
    
    def test_validar_observaciones_muy_largas(self):
        """Prueba validación con observaciones muy largas"""
        observaciones_largas = "x" * (VALIDATION_CONFIG['max_description_length'] + 1)
        
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_observaciones(observaciones_largas)
        
        self.assertIn("Observaciones", str(context.exception))
    
    def test_validar_stock_disponible_suficiente(self):
        """Prueba validación con stock suficiente"""
        # No debe lanzar excepción
        try:
            self.validator.validar_stock_disponible(
                producto_id=1,
                cantidad_solicitada=5,
                stock_actual=10
            )
        except ValidationError:
            self.fail("validar_stock_disponible lanzó ValidationError inesperadamente")
    
    def test_validar_stock_disponible_insuficiente(self):
        """Prueba validación con stock insuficiente"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_stock_disponible(
                producto_id=1,
                cantidad_solicitada=10,
                stock_actual=5
            )
        
        self.assertIn("Stock insuficiente", str(context.exception))
        self.assertIn("Disponible: 5", str(context.exception))
        self.assertIn("Solicitado: 10", str(context.exception))
    
    def test_validar_stock_disponible_exacto(self):
        """Prueba validación con stock exacto"""
        # No debe lanzar excepción
        try:
            self.validator.validar_stock_disponible(
                producto_id=1,
                cantidad_solicitada=5,
                stock_actual=5
            )
        except ValidationError:
            self.fail("validar_stock_disponible lanzó ValidationError inesperadamente")
    
    def test_validar_actualizacion_detalle_exitosa(self):
        """Prueba validación exitosa de actualización de detalle"""
        # No debe lanzar excepción
        try:
            self.validator.validar_actualizacion_detalle(
                detalle_id=1,
                nueva_cantidad=10,
                nuevo_precio=Decimal('150.00')
            )
        except ValidationError:
            self.fail("validar_actualizacion_detalle lanzó ValidationError inesperadamente")
    
    def test_validar_actualizacion_detalle_id_invalido(self):
        """Prueba validación con ID de detalle inválido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_actualizacion_detalle(detalle_id=0)
        
        self.assertIn("ID del detalle", str(context.exception))
    
    def test_validar_actualizacion_detalle_cantidad_invalida(self):
        """Prueba validación con nueva cantidad inválida"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_actualizacion_detalle(
                detalle_id=1,
                nueva_cantidad=0
            )
        
        self.assertIn("Nueva cantidad", str(context.exception))
    
    def test_validar_actualizacion_detalle_precio_invalido(self):
        """Prueba validación con nuevo precio inválido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_actualizacion_detalle(
                detalle_id=1,
                nuevo_precio=Decimal('-10.00')
            )
        
        self.assertIn("Nuevo precio", str(context.exception))
    
    def test_validar_actualizacion_detalle_solo_cantidad(self):
        """Prueba validación actualizando solo cantidad"""
        # No debe lanzar excepción
        try:
            self.validator.validar_actualizacion_detalle(
                detalle_id=1,
                nueva_cantidad=5
            )
        except ValidationError:
            self.fail("validar_actualizacion_detalle lanzó ValidationError inesperadamente")
    
    def test_validar_actualizacion_detalle_solo_precio(self):
        """Prueba validación actualizando solo precio"""
        # No debe lanzar excepción
        try:
            self.validator.validar_actualizacion_detalle(
                detalle_id=1,
                nuevo_precio=Decimal('200.00')
            )
        except ValidationError:
            self.fail("validar_actualizacion_detalle lanzó ValidationError inesperadamente")
    
    def test_validar_actualizacion_detalle_sin_cambios(self):
        """Prueba validación sin especificar cambios"""
        # No debe lanzar excepción
        try:
            self.validator.validar_actualizacion_detalle(detalle_id=1)
        except ValidationError:
            self.fail("validar_actualizacion_detalle lanzó ValidationError inesperadamente")


if __name__ == '__main__':
    unittest.main()