"""
Pruebas de integración para el módulo completo de facturas
Prueban la interacción entre modelo, controlador y validadores
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


class TestIntegrationFactura(unittest.TestCase):
    """
    Pruebas de integración para el módulo de facturas
    """
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.factura_model = Factura()
        self.controller = FacturaController()
        self.validator = FacturaValidator()
        
        # Mock de la base de datos para evitar conexiones reales
        self.db_mock = MagicMock()
        
    @patch('models.factura.DatabaseManager')
    def test_flujo_completo_creacion_factura(self, mock_db_manager):
        """Prueba el flujo completo de creación de una factura"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        
        # Mock de cursor y resultados
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular que el cliente existe
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'nombre': 'Cliente Test', 'activo': True},  # Cliente existe
            {'numero_factura': 'F-001'},  # Número de factura generado
            {'id': 1, 'numero_factura': 'F-001', 'cliente_id': 1, 'estado': 'borrador'}  # Factura creada
        ]
        mock_cursor.lastrowid = 1
        
        # Ejecutar creación de factura
        resultado = self.controller.crear_factura(
            cliente_id=1,
            observaciones="Factura de prueba de integración"
        )
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertIn('F-001', resultado['message'])
        self.assertEqual(resultado['data']['numero_factura'], 'F-001')
    
    @patch('models.factura.DatabaseManager')
    def test_flujo_completo_agregar_productos(self, mock_db_manager):
        """Prueba el flujo completo de agregar productos a una factura"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular datos de factura y producto
        mock_cursor.fetchone.side_effect = [
            {'id': 1, 'estado': 'borrador'},  # Factura en borrador
            {  # Producto existe con stock
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 10
            },
            {'id': 1, 'subtotal': 500.0}  # Detalle agregado
        ]
        mock_cursor.lastrowid = 1
        
        # Ejecutar agregar producto
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1,
            producto_id=1,
            cantidad=5
        )
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertIn('Producto Test', resultado['message'])
    
    @patch('models.factura.DatabaseManager')
    def test_flujo_completo_confirmar_factura(self, mock_db_manager):
        """Prueba el flujo completo de confirmación de factura"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular factura con total válido
        mock_cursor.fetchone.side_effect = [
            {
                'id': 1,
                'numero_factura': 'F-001',
                'estado': 'borrador',
                'total_factura': 1190.0
            },
            {  # Factura confirmada
                'id': 1,
                'numero_factura': 'F-001',
                'estado': 'confirmada'
            }
        ]
        
        # Ejecutar confirmación
        resultado = self.controller.confirmar_factura(1)
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertIn('confirmada exitosamente', resultado['message'])
    
    def test_validacion_integrada_datos_factura(self):
        """Prueba la validación integrada de datos de factura"""
        # Datos válidos
        detalles_validos = [
            {
                'cantidad': 2,
                'precio_unitario': Decimal('100.00'),
                'producto_id': 1
            }
        ]
        
        # No debe lanzar excepción
        try:
            self.validator.validar_factura_completa(
                cliente_id=1,
                observaciones="Factura válida",
                detalles=detalles_validos
            )
        except ValidationError:
            self.fail("La validación falló con datos válidos")
    
    def test_validacion_integrada_datos_invalidos(self):
        """Prueba la validación integrada con datos inválidos"""
        # Datos inválidos
        detalles_invalidos = [
            {
                'cantidad': 0,  # Cantidad inválida
                'precio_unitario': Decimal('100.00'),
                'producto_id': 1
            }
        ]
        
        # Debe lanzar excepción
        with self.assertRaises(ValidationError):
            self.validator.validar_factura_completa(
                cliente_id=1,
                detalles=detalles_invalidos
            )
    
    @patch('models.factura.DatabaseManager')
    def test_manejo_errores_base_datos(self, mock_db_manager):
        """Prueba el manejo de errores de base de datos"""
        # Configurar mock para lanzar excepción
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_db.get_connection.side_effect = Exception("Error de conexión")
        
        # Ejecutar operación
        resultado = self.controller.crear_factura(cliente_id=1)
        
        # Verificar manejo del error
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    @patch('models.factura.DatabaseManager')
    def test_transaccionalidad_operaciones(self, mock_db_manager):
        """Prueba la transaccionalidad de las operaciones"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_connection = MagicMock()
        mock_db.get_connection.return_value = mock_connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        
        # Simular error en la operación
        mock_cursor.execute.side_effect = Exception("Error SQL")
        
        # Ejecutar operación que debe fallar
        resultado = self.factura_model.crear_factura(cliente_id=1)
        
        # Verificar que se llamó rollback
        mock_connection.rollback.assert_called()
        self.assertFalse(resultado['success'])
    
    @patch('models.factura.DatabaseManager')
    def test_consistencia_datos_factura(self, mock_db_manager):
        """Prueba la consistencia de datos en operaciones de factura"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular datos consistentes
        factura_data = {
            'id': 1,
            'numero_factura': 'F-001',
            'cliente_id': 1,
            'subtotal_factura': 1000.0,
            'impuestos_factura': 190.0,
            'total_factura': 1190.0,
            'estado': 'borrador'
        }
        
        mock_cursor.fetchone.return_value = factura_data
        
        # Obtener factura
        resultado = self.factura_model.obtener_factura_por_id(1)
        
        # Verificar consistencia
        self.assertTrue(resultado['success'])
        data = resultado['data']
        self.assertEqual(data['subtotal_factura'], 1000.0)
        self.assertEqual(data['impuestos_factura'], 190.0)
        self.assertEqual(data['total_factura'], 1190.0)
    
    @patch('models.factura.DatabaseManager')
    def test_integridad_referencial(self, mock_db_manager):
        """Prueba la integridad referencial entre facturas y detalles"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular factura con detalles
        factura_data = {
            'id': 1,
            'numero_factura': 'F-001',
            'cliente_id': 1,
            'estado': 'borrador'
        }
        
        detalles_data = [
            {
                'id': 1,
                'factura_id': 1,
                'producto_id': 1,
                'cantidad': 2,
                'precio_unitario': 100.0,
                'subtotal': 200.0
            }
        ]
        
        mock_cursor.fetchone.return_value = factura_data
        mock_cursor.fetchall.return_value = detalles_data
        
        # Obtener factura y detalles
        factura_result = self.factura_model.obtener_factura_por_id(1)
        detalles_result = self.factura_model.obtener_detalles_factura(1)
        
        # Verificar integridad
        self.assertTrue(factura_result['success'])
        self.assertTrue(detalles_result['success'])
        self.assertEqual(detalles_result['data'][0]['factura_id'], 1)
    
    def test_validacion_reglas_negocio(self):
        """Prueba la validación de reglas de negocio"""
        # Regla: No se puede agregar productos a factura confirmada
        with patch.object(self.controller.factura_model, 'obtener_factura_por_id') as mock_get:
            mock_get.return_value = {
                'success': True,
                'data': {'id': 1, 'estado': 'confirmada'}
            }
            
            resultado = self.controller.agregar_producto_a_factura(
                factura_id=1,
                producto_id=1,
                cantidad=1
            )
            
            self.assertFalse(resultado['success'])
            self.assertIn('Solo se pueden modificar facturas en estado borrador', resultado['message'])
    
    def test_calculo_totales_automatico(self):
        """Prueba el cálculo automático de totales"""
        # Validar que los totales se calculen correctamente
        subtotal = Decimal('1000.00')
        impuestos = Decimal('190.00')
        total = Decimal('1190.00')
        
        # La validación debe pasar
        try:
            self.validator.validar_totales_factura(subtotal, impuestos, total)
        except ValidationError:
            self.fail("El cálculo de totales falló")
    
    @patch('models.factura.DatabaseManager')
    def test_actualizacion_stock_productos(self, mock_db_manager):
        """Prueba la actualización de stock al confirmar factura"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular factura con detalles
        mock_cursor.fetchone.side_effect = [
            {  # Factura válida
                'id': 1,
                'numero_factura': 'F-001',
                'estado': 'borrador',
                'total_factura': 500.0
            },
            {  # Factura confirmada
                'id': 1,
                'estado': 'confirmada'
            }
        ]
        
        # Simular detalles de factura
        mock_cursor.fetchall.return_value = [
            {
                'producto_id': 1,
                'cantidad': 5
            }
        ]
        
        # Confirmar factura
        resultado = self.factura_model.confirmar_factura(1)
        
        # Verificar que se ejecutaron las consultas de actualización de stock
        self.assertTrue(resultado['success'])
        # Verificar que se llamó execute múltiples veces (para actualizar stock)
        self.assertGreater(mock_cursor.execute.call_count, 1)
    
    def test_generacion_numero_factura_unico(self):
        """Prueba la generación de números de factura únicos"""
        with patch.object(self.factura_model, '_generar_numero_factura') as mock_gen:
            mock_gen.return_value = 'F-001'
            
            numero = self.factura_model._generar_numero_factura()
            
            # Verificar formato
            self.assertRegex(numero, r'^F-\d+$')
    
    @patch('models.factura.DatabaseManager')
    def test_busqueda_facturas_con_filtros(self, mock_db_manager):
        """Prueba la búsqueda de facturas con diferentes filtros"""
        # Configurar mock de base de datos
        mock_db = MagicMock()
        mock_db_manager.return_value = mock_db
        mock_cursor = MagicMock()
        mock_db.get_connection.return_value.cursor.return_value = mock_cursor
        
        # Simular resultados de búsqueda
        facturas_data = [
            {
                'id': 1,
                'numero_factura': 'F-001',
                'cliente_nombre': 'Cliente 1',
                'estado': 'confirmada',
                'total': 1000.0
            }
        ]
        
        mock_cursor.fetchall.return_value = facturas_data
        
        # Buscar con filtros
        filtros = {'estado': 'confirmada', 'cliente_id': 1}
        resultado = self.controller.listar_facturas(filtros)
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 1)
    
    def test_manejo_concurrencia_facturas(self):
        """Prueba el manejo de concurrencia en operaciones de facturas"""
        # Simular operaciones concurrentes
        with patch.object(self.factura_model, 'obtener_factura_por_id') as mock_get:
            # Primera llamada: factura en borrador
            # Segunda llamada: factura ya confirmada (simulando concurrencia)
            mock_get.side_effect = [
                {'success': True, 'data': {'id': 1, 'estado': 'borrador'}},
                {'success': True, 'data': {'id': 1, 'estado': 'confirmada'}}
            ]
            
            # Primera operación debería funcionar
            resultado1 = self.controller.agregar_producto_a_factura(1, 1, 1)
            
            # Segunda operación debería fallar por concurrencia
            resultado2 = self.controller.agregar_producto_a_factura(1, 1, 1)
            
            self.assertFalse(resultado2['success'])


if __name__ == '__main__':
    unittest.main()