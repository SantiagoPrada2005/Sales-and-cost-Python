"""
Tests unitarios para el módulo de productos
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.producto import Producto
from controllers.producto_controller import ProductoController
from utils.exceptions import ValidationError, DatabaseError

class TestProducto(unittest.TestCase):
    """Tests para el modelo Producto"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.producto = Producto()
        
        # Datos de prueba válidos
        self.datos_validos = {
            'codigo_sku': 'PROD-001',
            'nombre': 'Producto de Prueba',
            'descripcion': 'Descripción del producto de prueba',
            'costo_adquisicion': Decimal('100.00'),
            'precio_venta': Decimal('150.00')
        }
        
        # Datos de prueba inválidos
        self.datos_invalidos = {
            'codigo_sku': '',
            'nombre': '',
            'descripcion': 'Descripción',
            'costo_adquisicion': Decimal('-10.00'),
            'precio_venta': Decimal('-5.00')
        }
    
    def test_get_table_name(self):
        """Test para obtener el nombre de la tabla"""
        self.assertEqual(self.producto.get_table_name(), 'productos')
    
    def test_validate_producto_data_valid(self):
        """Test para validación de datos válidos"""
        result = self.producto.validate_producto_data(
            self.datos_validos['codigo_sku'],
            self.datos_validos['nombre'],
            self.datos_validos['costo_adquisicion'],
            self.datos_validos['precio_venta']
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_producto_data_invalid(self):
        """Test para validación de datos inválidos"""
        result = self.producto.validate_producto_data(
            self.datos_invalidos['codigo_sku'],
            self.datos_invalidos['nombre'],
            self.datos_invalidos['costo_adquisicion'],
            self.datos_invalidos['precio_venta']
        )
        
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
        
        # Verificar errores específicos
        errors = result['errors']
        self.assertIn('El código SKU es obligatorio', errors)
        self.assertIn('El nombre es obligatorio', errors)
        self.assertIn('El costo de adquisición debe ser mayor a 0', errors)
        self.assertIn('El precio de venta debe ser mayor a 0', errors)
    
    def test_validate_producto_data_edge_cases(self):
        """Test para casos límite en validación"""
        # Código SKU muy largo
        result = self.producto.validate_producto_data(
            'A' * 51,  # Más de 50 caracteres
            'Producto',
            Decimal('10.00'),
            Decimal('15.00')
        )
        self.assertFalse(result['valid'])
        self.assertIn('El código SKU no puede tener más de 50 caracteres', result['errors'])
        
        # Nombre muy largo
        result = self.producto.validate_producto_data(
            'PROD-001',
            'A' * 256,  # Más de 255 caracteres
            Decimal('10.00'),
            Decimal('15.00')
        )
        self.assertFalse(result['valid'])
        self.assertIn('El nombre no puede tener más de 255 caracteres', result['errors'])
    
    @patch('models.producto.Producto.execute_query')
    def test_crear_producto_success(self, mock_execute):
        """Test para crear producto exitosamente"""
        mock_execute.return_value = {'success': True, 'lastrowid': 1}
        
        result = self.producto.crear_producto(
            self.datos_validos['codigo_sku'],
            self.datos_validos['nombre'],
            self.datos_validos['descripcion'],
            self.datos_validos['costo_adquisicion'],
            self.datos_validos['precio_venta']
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['producto_id'], 1)
        mock_execute.assert_called_once()
    
    @patch('models.producto.Producto.execute_query')
    def test_crear_producto_validation_error(self, mock_execute):
        """Test para crear producto con datos inválidos"""
        result = self.producto.crear_producto(
            '',  # SKU vacío
            '',  # Nombre vacío
            'Descripción',
            Decimal('-10.00'),  # Costo negativo
            Decimal('-5.00')    # Precio negativo
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        mock_execute.assert_not_called()
    
    @patch('models.producto.Producto.execute_query')
    def test_obtener_producto_por_id_success(self, mock_execute):
        """Test para obtener producto por ID exitosamente"""
        mock_data = {
            'id': 1,
            'codigo_sku': 'PROD-001',
            'nombre': 'Producto Test',
            'descripcion': 'Descripción test',
            'costo_adquisicion': Decimal('100.00'),
            'precio_venta': Decimal('150.00'),
            'fecha_creacion': '2024-01-01 10:00:00',
            'fecha_actualizacion': '2024-01-01 10:00:00'
        }
        mock_execute.return_value = {'success': True, 'data': [mock_data]}
        
        result = self.producto.obtener_producto_por_id(1)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['id'], 1)
        self.assertEqual(result['data']['codigo_sku'], 'PROD-001')
    
    @patch('models.producto.Producto.execute_query')
    def test_obtener_producto_por_id_not_found(self, mock_execute):
        """Test para obtener producto por ID no encontrado"""
        mock_execute.return_value = {'success': True, 'data': []}
        
        result = self.producto.obtener_producto_por_id(999)
        
        self.assertFalse(result['success'])
        self.assertIn('no encontrado', result['error'])
    
    @patch('models.producto.Producto.execute_query')
    def test_obtener_producto_por_sku_success(self, mock_execute):
        """Test para obtener producto por SKU exitosamente"""
        mock_data = {
            'id': 1,
            'codigo_sku': 'PROD-001',
            'nombre': 'Producto Test'
        }
        mock_execute.return_value = {'success': True, 'data': [mock_data]}
        
        result = self.producto.obtener_producto_por_sku('PROD-001')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['codigo_sku'], 'PROD-001')
    
    @patch('models.producto.Producto.execute_query')
    def test_obtener_todos_productos_success(self, mock_execute):
        """Test para obtener todos los productos"""
        mock_data = [
            {'id': 1, 'codigo_sku': 'PROD-001', 'nombre': 'Producto 1'},
            {'id': 2, 'codigo_sku': 'PROD-002', 'nombre': 'Producto 2'}
        ]
        mock_execute.return_value = {'success': True, 'data': mock_data}
        
        result = self.producto.obtener_todos_productos()
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 2)
    
    @patch('models.producto.Producto.execute_query')
    def test_actualizar_producto_success(self, mock_execute):
        """Test para actualizar producto exitosamente"""
        mock_execute.return_value = {'success': True, 'rowcount': 1}
        
        result = self.producto.actualizar_producto(
            1,
            nombre='Producto Actualizado',
            precio_venta=Decimal('200.00')
        )
        
        self.assertTrue(result['success'])
        mock_execute.assert_called_once()
    
    @patch('models.producto.Producto.execute_query')
    def test_eliminar_producto_success(self, mock_execute):
        """Test para eliminar producto exitosamente"""
        mock_execute.return_value = {'success': True, 'rowcount': 1}
        
        result = self.producto.eliminar_producto(1)
        
        self.assertTrue(result['success'])
        mock_execute.assert_called_once()
    
    def test_calcular_margen_ganancia(self):
        """Test para calcular margen de ganancia"""
        # Margen positivo
        margen = self.producto.calcular_margen_ganancia(
            Decimal('100.00'),
            Decimal('150.00')
        )
        self.assertEqual(margen, Decimal('50.00'))
        
        # Margen negativo
        margen = self.producto.calcular_margen_ganancia(
            Decimal('150.00'),
            Decimal('100.00')
        )
        self.assertEqual(margen, Decimal('-33.33'))
        
        # Costo cero
        margen = self.producto.calcular_margen_ganancia(
            Decimal('0.00'),
            Decimal('100.00')
        )
        self.assertEqual(margen, Decimal('0.00'))
    
    @patch('models.producto.Producto.execute_query')
    def test_buscar_productos_success(self, mock_execute):
        """Test para buscar productos"""
        mock_data = [
            {'id': 1, 'codigo_sku': 'PROD-001', 'nombre': 'Producto Test'}
        ]
        mock_execute.return_value = {'success': True, 'data': mock_data}
        
        result = self.producto.buscar_productos('Test')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)

class TestProductoController(unittest.TestCase):
    """Tests para el controlador ProductoController"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.controller = ProductoController()
        
        # Mock del modelo
        self.controller.producto_model = Mock()
    
    def test_validar_datos_producto_valid(self):
        """Test para validación de datos válidos en el controlador"""
        result = self.controller.validar_datos_producto(
            'PROD-001',
            'Producto Test',
            '100.00',
            '150.00'
        )
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validar_datos_producto_invalid_format(self):
        """Test para validación con formato inválido"""
        result = self.controller.validar_datos_producto(
            'PROD-001',
            'Producto Test',
            'abc',  # Formato inválido
            '150.00'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('El costo de adquisición debe ser un número válido', result['errors'])
    
    def test_crear_producto_success(self):
        """Test para crear producto exitosamente desde el controlador"""
        self.controller.producto_model.crear_producto.return_value = {
            'success': True,
            'producto_id': 1
        }
        
        result = self.controller.crear_producto(
            'PROD-001',
            'Producto Test',
            'Descripción',
            '100.00',
            '150.00'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.controller.producto_model.crear_producto.assert_called_once()
    
    def test_crear_producto_validation_error(self):
        """Test para crear producto con error de validación"""
        result = self.controller.crear_producto(
            '',  # SKU vacío
            'Producto Test',
            'Descripción',
            '100.00',
            '150.00'
        )
        
        self.assertFalse(result['success'])
        self.assertIn('message', result)
        self.controller.producto_model.crear_producto.assert_not_called()
    
    def test_listar_productos_success(self):
        """Test para listar productos exitosamente"""
        mock_productos = [
            {
                'id': 1,
                'codigo_sku': 'PROD-001',
                'nombre': 'Producto 1',
                'costo_adquisicion': Decimal('100.00'),
                'precio_venta': Decimal('150.00')
            }
        ]
        
        self.controller.producto_model.obtener_todos_productos.return_value = {
            'success': True,
            'data': mock_productos
        }
        
        result = self.controller.listar_productos()
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        
        # Verificar formato de datos
        producto = result['data'][0]
        self.assertIn('costo_adquisicion_formatted', producto)
        self.assertIn('precio_venta_formatted', producto)
        self.assertIn('margen_ganancia', producto)
        self.assertIn('margen_ganancia_formatted', producto)
    
    def test_obtener_estadisticas_productos(self):
        """Test para obtener estadísticas de productos"""
        mock_productos = [
            {
                'costo_adquisicion': Decimal('100.00'),
                'precio_venta': Decimal('150.00')
            },
            {
                'costo_adquisicion': Decimal('200.00'),
                'precio_venta': Decimal('250.00')
            }
        ]
        
        self.controller.producto_model.obtener_todos_productos.return_value = {
            'success': True,
            'data': mock_productos
        }
        
        result = self.controller.obtener_estadisticas_productos()
        
        self.assertTrue(result['success'])
        
        stats = result['data']
        self.assertEqual(stats['total_productos'], 2)
        self.assertEqual(stats['valor_total'], Decimal('400.00'))
        self.assertIn('valor_total_formatted', stats)
        self.assertIn('margen_promedio', stats)
        self.assertIn('margen_promedio_formatted', stats)
    
    def test_buscar_productos_success(self):
        """Test para buscar productos exitosamente"""
        mock_productos = [
            {
                'id': 1,
                'codigo_sku': 'PROD-001',
                'nombre': 'Producto Test',
                'costo_adquisicion': Decimal('100.00'),
                'precio_venta': Decimal('150.00')
            }
        ]
        
        self.controller.producto_model.buscar_productos.return_value = {
            'success': True,
            'data': mock_productos
        }
        
        result = self.controller.buscar_productos('Test')
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        self.controller.producto_model.buscar_productos.assert_called_once_with('Test')

class TestProductoIntegration(unittest.TestCase):
    """Tests de integración para el módulo de productos"""
    
    def setUp(self):
        """Configuración inicial para tests de integración"""
        self.controller = ProductoController()
    
    @patch('models.producto.Producto.execute_query')
    def test_flujo_completo_producto(self, mock_execute):
        """Test del flujo completo: crear, obtener, actualizar, eliminar"""
        # Mock para crear producto
        mock_execute.return_value = {'success': True, 'lastrowid': 1}
        
        # Crear producto
        result_crear = self.controller.crear_producto(
            'PROD-TEST',
            'Producto de Integración',
            'Descripción de prueba',
            '100.00',
            '150.00'
        )
        
        self.assertTrue(result_crear['success'])
        
        # Mock para obtener producto
        mock_execute.return_value = {
            'success': True,
            'data': [{
                'id': 1,
                'codigo_sku': 'PROD-TEST',
                'nombre': 'Producto de Integración',
                'descripcion': 'Descripción de prueba',
                'costo_adquisicion': Decimal('100.00'),
                'precio_venta': Decimal('150.00'),
                'fecha_creacion': '2024-01-01 10:00:00',
                'fecha_actualizacion': '2024-01-01 10:00:00'
            }]
        }
        
        # Obtener producto
        result_obtener = self.controller.obtener_producto(1)
        self.assertTrue(result_obtener['success'])
        
        # Mock para actualizar producto
        mock_execute.return_value = {'success': True, 'rowcount': 1}
        
        # Actualizar producto
        result_actualizar = self.controller.actualizar_producto(
            1,
            nombre='Producto Actualizado',
            precio_venta='200.00'
        )
        
        self.assertTrue(result_actualizar['success'])
        
        # Mock para eliminar producto
        mock_execute.return_value = {'success': True, 'rowcount': 1}
        
        # Eliminar producto
        result_eliminar = self.controller.eliminar_producto(1)
        self.assertTrue(result_eliminar['success'])

if __name__ == '__main__':
    # Configurar logging para tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar tests
    unittest.main(verbosity=2)