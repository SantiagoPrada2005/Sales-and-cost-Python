"""
Pruebas unitarias para el controlador de facturas
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.factura_controller import FacturaController
from utils.exceptions import ValidationError, DatabaseError, FacturaError


class TestFacturaController(unittest.TestCase):
    """
    Pruebas para el controlador de facturas
    """
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.controller = FacturaController()
        
        # Mock de los modelos
        self.controller.factura_model = Mock()
        self.controller.cliente_model = Mock()
        self.controller.producto_model = Mock()
        
        # Mock de los formatters
        self.controller.currency_formatter = Mock()
        self.controller.date_formatter = Mock()
        
        # Configurar formatters mock
        self.controller.currency_formatter.format_currency.return_value = "$1,000.00"
        self.controller.date_formatter.format_date.return_value = "2024-01-15"
    
    def test_crear_factura_exitosa(self):
        """Prueba creación exitosa de factura"""
        # Configurar mocks
        self.controller.cliente_model.obtener_cliente_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'nombre': 'Cliente Test'}
        }
        
        self.controller.factura_model.crear_factura.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'numero_factura': 'F-001',
                'cliente_id': 1,
                'estado': 'borrador'
            }
        }
        
        # Ejecutar
        resultado = self.controller.crear_factura(cliente_id=1, observaciones="Test")
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertIn('F-001', resultado['message'])
        self.assertEqual(resultado['data']['numero_factura'], 'F-001')
        
        # Verificar llamadas
        self.controller.cliente_model.obtener_cliente_por_id.assert_called_once_with(1)
        self.controller.factura_model.crear_factura.assert_called_once_with(
            cliente_id=1, observaciones="Test"
        )
    
    def test_crear_factura_cliente_inexistente(self):
        """Prueba creación de factura con cliente inexistente"""
        # Configurar mock
        self.controller.cliente_model.obtener_cliente_por_id.return_value = {
            'success': False,
            'message': 'Cliente no encontrado'
        }
        
        # Ejecutar
        resultado = self.controller.crear_factura(cliente_id=999)
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'El cliente especificado no existe')
    
    def test_crear_factura_error_inesperado(self):
        """Prueba manejo de error inesperado en creación"""
        # Configurar mock para lanzar excepción
        self.controller.cliente_model.obtener_cliente_por_id.side_effect = Exception("Error de conexión")
        
        # Ejecutar
        resultado = self.controller.crear_factura(cliente_id=1)
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    def test_obtener_factura_exitosa(self):
        """Prueba obtención exitosa de factura"""
        # Configurar mocks
        factura_data = {
            'id': 1,
            'numero_factura': 'F-001',
            'cliente_id': 1,
            'estado': 'confirmada',
            'fecha_creacion': datetime.now(),
            'subtotal': 1000.0,
            'impuestos': 190.0,
            'total': 1190.0
        }
        
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': factura_data
        }
        
        detalles_data = [
            {
                'id': 1,
                'producto_id': 1,
                'producto_nombre': 'Producto Test',
                'cantidad': 2,
                'precio_unitario': 500.0,
                'subtotal': 1000.0
            }
        ]
        
        self.controller.factura_model.obtener_detalles_factura.return_value = {
            'success': True,
            'data': detalles_data
        }
        
        # Ejecutar
        resultado = self.controller.obtener_factura(1)
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertIn('detalles', resultado['data'])
        
        # Verificar llamadas
        self.controller.factura_model.obtener_factura_por_id.assert_called_once_with(1)
        self.controller.factura_model.obtener_detalles_factura.assert_called_once_with(1)
    
    def test_obtener_factura_inexistente(self):
        """Prueba obtención de factura inexistente"""
        # Configurar mock
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': False,
            'message': 'Factura no encontrada'
        }
        
        # Ejecutar
        resultado = self.controller.obtener_factura(999)
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'Factura no encontrada')
    
    def test_listar_facturas_exitosa(self):
        """Prueba listado exitoso de facturas"""
        # Configurar mock
        facturas_data = [
            {
                'id': 1,
                'numero_factura': 'F-001',
                'cliente_nombre': 'Cliente 1',
                'estado': 'confirmada',
                'total': 1000.0
            },
            {
                'id': 2,
                'numero_factura': 'F-002',
                'cliente_nombre': 'Cliente 2',
                'estado': 'borrador',
                'total': 500.0
            }
        ]
        
        self.controller.factura_model.obtener_todas_facturas.return_value = {
            'success': True,
            'data': facturas_data
        }
        
        # Ejecutar
        resultado = self.controller.listar_facturas()
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
        self.assertIn('Se encontraron 2 facturas', resultado['message'])
    
    def test_agregar_producto_a_factura_exitoso(self):
        """Prueba agregar producto a factura exitosamente"""
        # Configurar mocks
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador'}
        }
        
        self.controller.producto_model.obtener_producto_por_id.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 10
            }
        }
        
        self.controller.factura_model.agregar_detalle.return_value = {
            'success': True,
            'data': {'id': 1, 'subtotal': 500.0}
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=1, cantidad=5
        )
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertIn('Producto Test', resultado['message'])
        
        # Verificar llamadas
        self.controller.factura_model.agregar_detalle.assert_called_once_with(
            factura_id=1, producto_id=1, cantidad=5, precio_unitario=100.0
        )
    
    def test_agregar_producto_factura_confirmada(self):
        """Prueba agregar producto a factura ya confirmada"""
        # Configurar mock
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'confirmada'}
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=1, cantidad=5
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertIn('Solo se pueden modificar facturas en estado borrador', resultado['message'])
    
    def test_agregar_producto_inexistente(self):
        """Prueba agregar producto inexistente a factura"""
        # Configurar mocks
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador'}
        }
        
        self.controller.producto_model.obtener_producto_por_id.return_value = {
            'success': False,
            'message': 'Producto no encontrado'
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=999, cantidad=5
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'El producto especificado no existe')
    
    def test_agregar_producto_cantidad_invalida(self):
        """Prueba agregar producto con cantidad inválida"""
        # Configurar mocks
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador'}
        }
        
        self.controller.producto_model.obtener_producto_por_id.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 10
            }
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=1, cantidad=0
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'La cantidad debe ser mayor a cero')
    
    def test_agregar_producto_stock_insuficiente(self):
        """Prueba agregar producto con stock insuficiente"""
        # Configurar mocks
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador'}
        }
        
        self.controller.producto_model.obtener_producto_por_id.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 3
            }
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=1, cantidad=5
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertIn('Stock insuficiente', resultado['message'])
    
    def test_agregar_producto_precio_negativo(self):
        """Prueba agregar producto con precio negativo"""
        # Configurar mocks
        self.controller.factura_model.obtener_factura_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador'}
        }
        
        self.controller.producto_model.obtener_producto_por_id.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 10
            }
        }
        
        # Ejecutar
        resultado = self.controller.agregar_producto_a_factura(
            factura_id=1, producto_id=1, cantidad=5, precio_unitario=-10.0
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'El precio unitario no puede ser negativo')
    
    def test_actualizar_detalle_factura_exitoso(self):
        """Prueba actualización exitosa de detalle"""
        # Configurar mock
        self.controller.factura_model.actualizar_detalle.return_value = {
            'success': True,
            'data': {'id': 1, 'subtotal': 600.0}
        }
        
        # Ejecutar
        resultado = self.controller.actualizar_detalle_factura(
            detalle_id=1, cantidad=6, precio_unitario=100.0
        )
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['message'], 'Detalle actualizado exitosamente')
        
        # Verificar llamada
        self.controller.factura_model.actualizar_detalle.assert_called_once_with(
            detalle_id=1, cantidad=6, precio_unitario=100.0
        )
    
    def test_actualizar_detalle_cantidad_invalida(self):
        """Prueba actualización con cantidad inválida"""
        # Ejecutar
        resultado = self.controller.actualizar_detalle_factura(
            detalle_id=1, cantidad=0, precio_unitario=100.0
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'La cantidad debe ser mayor a cero')
    
    def test_actualizar_detalle_precio_negativo(self):
        """Prueba actualización con precio negativo"""
        # Ejecutar
        resultado = self.controller.actualizar_detalle_factura(
            detalle_id=1, cantidad=5, precio_unitario=-10.0
        )
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'El precio unitario no puede ser negativo')
    
    def test_eliminar_detalle_factura_exitoso(self):
        """Prueba eliminación exitosa de detalle"""
        # Configurar mock
        self.controller.factura_model.eliminar_detalle.return_value = {
            'success': True
        }
        
        # Ejecutar
        resultado = self.controller.eliminar_detalle_factura(1)
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['message'], 'Producto eliminado de la factura exitosamente')
        
        # Verificar llamada
        self.controller.factura_model.eliminar_detalle.assert_called_once_with(1)
    
    def test_eliminar_detalle_factura_error(self):
        """Prueba error al eliminar detalle"""
        # Configurar mock
        self.controller.factura_model.eliminar_detalle.return_value = {
            'success': False,
            'message': 'Detalle no encontrado'
        }
        
        # Ejecutar
        resultado = self.controller.eliminar_detalle_factura(999)
        
        # Verificar
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'Detalle no encontrado')
    
    def test_obtener_clientes_activos(self):
        """Prueba obtención de clientes activos"""
        # Configurar mock
        clientes_data = [
            {'id': 1, 'nombre': 'Cliente 1', 'activo': True},
            {'id': 2, 'nombre': 'Cliente 2', 'activo': True}
        ]
        
        self.controller.cliente_model.obtener_todos_clientes.return_value = {
            'success': True,
            'data': clientes_data
        }
        
        # Ejecutar
        resultado = self.controller.obtener_clientes_activos()
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
    
    def test_obtener_productos_disponibles(self):
        """Prueba obtención de productos disponibles"""
        # Configurar mock
        productos_data = [
            {'id': 1, 'nombre': 'Producto 1', 'stock_actual': 10},
            {'id': 2, 'nombre': 'Producto 2', 'stock_actual': 5}
        ]
        
        self.controller.producto_model.obtener_todos_productos.return_value = {
            'success': True,
            'data': productos_data
        }
        
        # Ejecutar
        resultado = self.controller.obtener_productos_disponibles()
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
    
    def test_buscar_productos(self):
        """Prueba búsqueda de productos"""
        # Configurar mock
        productos_data = [
            {
                'id': 1,
                'nombre': 'Producto Test',
                'precio_venta': 100.0,
                'stock_actual': 10
            }
        ]
        
        self.controller.producto_model.buscar_productos.return_value = {
            'success': True,
            'data': productos_data
        }
        
        # Ejecutar
        resultado = self.controller.buscar_productos("test")
        
        # Verificar
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 1)
        
        # Verificar llamada
        self.controller.producto_model.buscar_productos.assert_called_once_with("test")
    
    @patch('controllers.factura_controller.logger')
    def test_logging_en_operaciones(self, mock_logger):
        """Prueba que se registren logs en las operaciones"""
        # Configurar mocks para operación exitosa
        self.controller.cliente_model.obtener_cliente_por_id.return_value = {
            'success': True,
            'data': {'id': 1, 'nombre': 'Cliente Test'}
        }
        
        self.controller.factura_model.crear_factura.return_value = {
            'success': True,
            'data': {
                'id': 1,
                'numero_factura': 'F-001',
                'cliente_id': 1,
                'estado': 'borrador'
            }
        }
        
        # Ejecutar
        self.controller.crear_factura(cliente_id=1)
        
        # Verificar que se llamó al logger
        mock_logger.info.assert_called()
    
    def test_validar_datos_factura(self):
        """Prueba la validación de datos de factura"""
        # Datos válidos
        resultado = self.controller.validar_datos_factura(
            cliente_id=1,
            observaciones="Observaciones válidas"
        )
        self.assertTrue(resultado['valid'])
        self.assertEqual(resultado['errors'], [])
        
        # Datos inválidos - cliente inexistente
        resultado = self.controller.validar_datos_factura(
            cliente_id=999,
            observaciones="Observaciones válidas"
        )
        self.assertFalse(resultado['valid'])
        self.assertGreater(len(resultado['errors']), 0)


if __name__ == '__main__':
    unittest.main()