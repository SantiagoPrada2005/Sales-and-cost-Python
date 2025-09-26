"""
Pruebas de casos límite y manejo de errores para el módulo de facturas
Cubre escenarios extremos y situaciones de error
"""
import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.factura import Factura
from controllers.factura_controller import FacturaController
from utils.validators import FacturaValidator
from utils.exceptions import ValidationError, DatabaseError, FacturaError


class TestEdgeCasesFactura(unittest.TestCase):
    """
    Pruebas de casos límite y manejo de errores para el módulo de facturas
    """
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.factura_model = Factura()
        self.controller = FacturaController()
        self.validator = FacturaValidator()
    
    # ==================== CASOS LÍMITE DE DATOS ====================
    
    def test_observaciones_maxima_longitud(self):
        """Prueba observaciones en el límite máximo de caracteres"""
        observaciones_limite = "A" * 500  # Límite máximo
        
        # No debe lanzar excepción
        try:
            self.validator.validar_observaciones(observaciones_limite)
        except ValidationError:
            self.fail("Falló con observaciones en el límite máximo")
    
    def test_observaciones_excede_limite(self):
        """Prueba observaciones que exceden el límite máximo"""
        observaciones_excesivas = "A" * 501  # Excede el límite
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_observaciones(observaciones_excesivas)
        
        self.assertIn("demasiado largas", str(context.exception))
    
    def test_cantidad_maxima_permitida(self):
        """Prueba cantidad en el límite máximo permitido"""
        cantidad_limite = 999999  # Límite máximo
        
        # No debe lanzar excepción
        try:
            self.validator.validar_detalle_factura(
                cantidad=cantidad_limite,
                precio_unitario=Decimal('1.00'),
                producto_id=1
            )
        except ValidationError:
            self.fail("Falló con cantidad en el límite máximo")
    
    def test_cantidad_excede_limite(self):
        """Prueba cantidad que excede el límite máximo"""
        cantidad_excesiva = 1000000  # Excede el límite
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=cantidad_excesiva,
                precio_unitario=Decimal('1.00'),
                producto_id=1
            )
        
        self.assertIn("no puede ser mayor", str(context.exception))
    
    def test_precio_maximo_permitido(self):
        """Prueba precio en el límite máximo permitido"""
        precio_limite = Decimal('999999.99')  # Límite máximo
        
        # No debe lanzar excepción
        try:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=precio_limite,
                producto_id=1
            )
        except ValidationError:
            self.fail("Falló con precio en el límite máximo")
    
    def test_precio_excede_limite(self):
        """Prueba precio que excede el límite máximo"""
        precio_excesivo = Decimal('1000000.00')  # Excede el límite
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_detalle_factura(
                cantidad=1,
                precio_unitario=precio_excesivo,
                producto_id=1
            )
        
        self.assertIn("no puede ser mayor", str(context.exception))
    
    def test_numero_factura_caracteres_especiales(self):
        """Prueba número de factura con caracteres especiales"""
        numeros_invalidos = [
            "F-001@",
            "F-001#",
            "F-001$",
            "F-001%",
            "F-001&",
            "F 001",  # Espacio
            "F-001ñ",  # Carácter especial
            "F-001á"   # Acento
        ]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_numero_factura(numero)
    
    def test_precision_decimal_extrema(self):
        """Prueba precisión decimal extrema en precios"""
        # Precios con muchos decimales
        precios_extremos = [
            Decimal('0.001'),      # Muy pequeño
            Decimal('0.999'),      # Casi 1
            Decimal('99999.999'),  # Muchos decimales
            Decimal('1.123456789') # Muchos decimales
        ]
        
        for precio in precios_extremos:
            try:
                self.validator.validar_detalle_factura(
                    cantidad=1,
                    precio_unitario=precio,
                    producto_id=1
                )
            except ValidationError:
                self.fail(f"Falló con precio decimal extremo: {precio}")
    
    # ==================== CASOS LÍMITE DE STOCK ====================
    
    def test_stock_exacto_disponible(self):
        """Prueba cuando se solicita exactamente el stock disponible"""
        stock_disponible = 10
        cantidad_solicitada = 10
        
        # No debe lanzar excepción
        try:
            self.validator.validar_stock_disponible(cantidad_solicitada, stock_disponible)
        except ValidationError:
            self.fail("Falló con stock exacto disponible")
    
    def test_stock_insuficiente_por_uno(self):
        """Prueba cuando falta una unidad de stock"""
        stock_disponible = 10
        cantidad_solicitada = 11
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_stock_disponible(cantidad_solicitada, stock_disponible)
        
        self.assertIn("Stock insuficiente", str(context.exception))
    
    def test_stock_cero_disponible(self):
        """Prueba cuando no hay stock disponible"""
        stock_disponible = 0
        cantidad_solicitada = 1
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_stock_disponible(cantidad_solicitada, stock_disponible)
        
        self.assertIn("Stock insuficiente", str(context.exception))
    
    # ==================== MANEJO DE ERRORES DE BASE DE DATOS ====================
    
    @patch('models.factura.DatabaseManager')
    def test_error_conexion_base_datos(self, mock_db_manager):
        """Prueba manejo de error de conexión a base de datos"""
        # Simular error de conexión
        mock_db_manager.return_value.get_connection.side_effect = Exception("Connection failed")
        
        resultado = self.factura_model.crear_factura(cliente_id=1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    @patch('models.factura.DatabaseManager')
    def test_error_sql_sintaxis(self, mock_db_manager):
        """Prueba manejo de error de sintaxis SQL"""
        # Configurar mock para error SQL
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular error de sintaxis SQL
        mock_cursor.execute.side_effect = Exception("SQL syntax error")
        
        resultado = self.factura_model.crear_factura(cliente_id=1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    @patch('models.factura.DatabaseManager')
    def test_timeout_base_datos(self, mock_db_manager):
        """Prueba manejo de timeout de base de datos"""
        # Simular timeout
        mock_db_manager.return_value.get_connection.side_effect = TimeoutError("Database timeout")
        
        resultado = self.factura_model.obtener_factura_por_id(1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    @patch('models.factura.DatabaseManager')
    def test_rollback_transaccion_error(self, mock_db_manager):
        """Prueba rollback cuando ocurre error en transacción"""
        # Configurar mock
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_connection = MagicMock()
        mock_db.get_connection.return_value = mock_connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Simular error después de comenzar transacción
        mock_cursor.execute.side_effect = Exception("Error en transacción")
        
        resultado = self.factura_model.crear_factura(cliente_id=1)
        
        # Verificar que se llamó rollback
        mock_connection.rollback.assert_called()
        self.assertFalse(resultado['success'])
    
    # ==================== CASOS LÍMITE DE CONCURRENCIA ====================
    
    @patch('models.factura.DatabaseManager')
    def test_modificacion_concurrente_factura(self, mock_db_manager):
        """Prueba modificación concurrente de la misma factura"""
        # Configurar mock
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Primera consulta: factura en borrador
        # Segunda consulta: factura ya confirmada (modificada por otro proceso)
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'estado': 'borrador'},
            {'id': 1, 'estado': 'confirmada'}
        ]
        
        # Intentar agregar producto
        resultado = self.controller.agregar_producto_a_factura(1, 1, 1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Solo se pueden modificar facturas en estado borrador', resultado['message'])
    
    # ==================== CASOS LÍMITE DE MEMORIA ====================
    
    @patch('models.factura.DatabaseManager')
    def test_factura_con_muchos_detalles(self, mock_db_manager):
        """Prueba factura con gran cantidad de detalles"""
        # Configurar mock
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular muchos detalles (1000)
        detalles_muchos = []
        for i in range(1000):
            detalles_muchos.append({
                'id': i + 1,
                'factura_id': 1,
                'producto_id': i + 1,
                'cantidad': 1,
                'precio_unitario': 10.0,
                'subtotal': 10.0
            })
        
        mock_cursor.fetchall.return_value = detalles_muchos
        
        resultado = self.factura_model.obtener_detalles_factura(1)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 1000)
    
    # ==================== CASOS LÍMITE DE VALIDACIÓN ====================
    
    def test_validacion_cliente_id_extremos(self):
        """Prueba validación con IDs de cliente extremos"""
        ids_extremos = [
            -1,        # Negativo
            0,         # Cero
            999999999, # Muy grande
            None,      # Nulo
        ]
        
        for cliente_id in ids_extremos:
            if cliente_id is None or cliente_id <= 0:
                with self.assertRaises(ValidationError):
                    self.validator.validar_factura_completa(
                        cliente_id=cliente_id,
                        detalles=[{
                            'cantidad': 1,
                            'precio_unitario': Decimal('10.00'),
                            'producto_id': 1
                        }]
                    )
    
    def test_validacion_producto_id_extremos(self):
        """Prueba validación con IDs de producto extremos"""
        ids_extremos = [
            -1,        # Negativo
            0,         # Cero
            999999999, # Muy grande
        ]
        
        for producto_id in ids_extremos:
            if producto_id <= 0:
                with self.assertRaises(ValidationError):
                    self.validator.validar_detalle_factura(
                        cantidad=1,
                        precio_unitario=Decimal('10.00'),
                        producto_id=producto_id
                    )
    
    # ==================== CASOS LÍMITE DE CÁLCULOS ====================
    
    def test_calculo_totales_precision_extrema(self):
        """Prueba cálculo de totales con precisión extrema"""
        # Valores que pueden causar problemas de redondeo
        subtotal = Decimal('999999.999')
        impuestos = Decimal('189999.99981')  # 19% de subtotal
        total = subtotal + impuestos
        
        # Debe manejar la precisión correctamente
        try:
            self.validator.validar_totales_factura(subtotal, impuestos, total)
        except ValidationError:
            self.fail("Falló con cálculos de precisión extrema")
    
    def test_calculo_totales_redondeo_limite(self):
        """Prueba cálculo con diferencias de redondeo en el límite"""
        subtotal = Decimal('100.00')
        impuestos = Decimal('19.00')
        total = Decimal('119.01')  # Diferencia de 0.01 (en el límite)
        
        # Debe aceptar diferencias menores a 0.01
        try:
            self.validator.validar_totales_factura(subtotal, impuestos, total)
        except ValidationError:
            self.fail("Falló con diferencia de redondeo en el límite")
    
    def test_calculo_totales_redondeo_excede(self):
        """Prueba cálculo con diferencias de redondeo que exceden el límite"""
        subtotal = Decimal('100.00')
        impuestos = Decimal('19.00')
        total = Decimal('119.02')  # Diferencia de 0.02 (excede el límite)
        
        # Debe rechazar diferencias mayores a 0.01
        with self.assertRaises(ValidationError):
            self.validator.validar_totales_factura(subtotal, impuestos, total)
    
    # ==================== CASOS LÍMITE DE ESTADOS ====================
    
    def test_transiciones_estado_invalidas(self):
        """Prueba transiciones de estado inválidas"""
        estados_invalidos = [
            'BORRADOR',    # Mayúsculas
            'Confirmada',  # Capitalizado
            'cancelada',   # Minúsculas
            'pendiente',   # Estado inexistente
            'procesando',  # Estado inexistente
            '',            # Vacío
            None,          # Nulo
            123,           # Número
        ]
        
        for estado in estados_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_estado_factura(estado)
    
    # ==================== CASOS LÍMITE DE ENTRADA DE USUARIO ====================
    
    def test_entrada_usuario_caracteres_unicode(self):
        """Prueba entrada con caracteres Unicode especiales"""
        observaciones_unicode = "Factura con émojis 🧾💰 y caracteres especiales ñáéíóú"
        
        # Debe manejar Unicode correctamente
        try:
            self.validator.validar_observaciones(observaciones_unicode)
        except ValidationError:
            self.fail("Falló con caracteres Unicode")
    
    def test_entrada_usuario_sql_injection(self):
        """Prueba entrada que podría ser SQL injection"""
        observaciones_maliciosas = [
            "'; DROP TABLE facturas; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM usuarios",
            "<script>alert('xss')</script>",
        ]
        
        for observacion in observaciones_maliciosas:
            # Debe validar normalmente (la protección SQL está en el modelo)
            try:
                if len(observacion) <= 500:  # Si está dentro del límite
                    self.validator.validar_observaciones(observacion)
            except ValidationError:
                # Es aceptable que falle por otros motivos de validación
                pass
    
    # ==================== CASOS LÍMITE DE RECURSOS ====================
    
    @patch('models.factura.DatabaseManager')
    def test_memoria_insuficiente_simulada(self, mock_db_manager):
        """Prueba manejo cuando se simula memoria insuficiente"""
        # Simular error de memoria
        mock_db_manager.return_value.get_connection.side_effect = MemoryError("Out of memory")
        
        resultado = self.factura_model.listar_facturas()
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    def test_validacion_lista_detalles_vacia(self):
        """Prueba validación con lista de detalles vacía"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_factura_completa(
                cliente_id=1,
                detalles=[]  # Lista vacía
            )
        
        self.assertIn("debe tener al menos un detalle", str(context.exception))
    
    def test_validacion_detalles_none(self):
        """Prueba validación con detalles None"""
        with self.assertRaises(ValidationError):
            self.validator.validar_factura_completa(
                cliente_id=1,
                detalles=None  # None en lugar de lista
            )


if __name__ == '__main__':
    unittest.main()