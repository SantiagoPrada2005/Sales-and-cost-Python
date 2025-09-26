import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
from models.factura import Factura
from utils.exceptions import ValidationError, DatabaseError

class TestFacturaModel(unittest.TestCase):
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.factura = Factura()
        
    @patch.object(Factura, 'cliente_existe')
    @patch.object(Factura, 'generar_numero_factura')
    def test_crear_factura_exitosa(self, mock_generar_numero, mock_cliente_existe):
        """Prueba creación exitosa de factura"""
        # Configurar mocks
        mock_cliente_existe.return_value = True
        mock_generar_numero.return_value = "FAC-001"
        
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.crear_factura(cliente_id=1, observaciones='Factura de prueba')
            
            self.assertTrue(resultado['success'])
            self.assertEqual(resultado['data']['numero_factura'], "FAC-001")
            self.assertEqual(resultado['data']['cliente_id'], 1)
        
    @patch.object(Factura, 'cliente_existe')
    def test_crear_factura_cliente_inexistente(self, mock_cliente_existe):
        """Prueba creación de factura con cliente inexistente"""
        # Cliente no existe
        mock_cliente_existe.return_value = False
        
        resultado = self.factura.crear_factura(cliente_id=999, observaciones='Factura de prueba')
        
        self.assertFalse(resultado['success'])
        self.assertIn('El cliente especificado no existe', resultado['message'])
        
    @patch('models.factura.FacturaValidator')
    @patch.object(Factura, 'cliente_existe')
    def test_crear_factura_observaciones_muy_largas(self, mock_cliente_existe, mock_validator):
        """Prueba creación de factura con observaciones muy largas"""
        # Configurar mocks
        mock_cliente_existe.return_value = True
        mock_validator_instance = mock_validator.return_value
        mock_validator_instance.validar_observaciones.side_effect = ValidationError("El campo 'Observaciones' no puede exceder 500 caracteres")
        
        resultado = self.factura.crear_factura(cliente_id=1, observaciones='x' * 1001)
        
        self.assertFalse(resultado['success'])
        self.assertIn("El campo 'Observaciones' no puede exceder 500 caracteres", resultado['message'])
        
    @patch.object(Factura, 'recalcular_totales')
    @patch.object(Factura, 'obtener_detalle_producto')
    @patch.object(Factura, 'obtener_producto')
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_agregar_detalle_exitoso(self, mock_obtener_factura, 
                                   mock_obtener_producto, mock_obtener_detalle, mock_recalcular):
        """Prueba agregar detalle exitosamente"""
        # Configurar mocks
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'estado': 'borrador'}
        }
        mock_obtener_producto.return_value = {
            'precio_venta': 100.0,
            'stock_actual': 50
        }
        mock_obtener_detalle.return_value = None  # No existe detalle previo
        mock_recalcular.return_value = None  # recalcular_totales no retorna nada
        
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.agregar_detalle(factura_id=1, producto_id=1, cantidad=2, precio_unitario=100.0)
            
            self.assertTrue(resultado['success'])
        
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_agregar_detalle_factura_confirmada(self, mock_obtener_factura):
        """Prueba agregar detalle a factura confirmada"""
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'estado': 'confirmada'}
        }
        
        resultado = self.factura.agregar_detalle(factura_id=1, producto_id=1, cantidad=2, precio_unitario=100.0)
        
        self.assertFalse(resultado['success'])
        self.assertIn('borrador', resultado['message'])
        
    @patch.object(Factura, 'obtener_producto')
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_agregar_detalle_producto_inexistente(self, mock_obtener_factura, mock_obtener_producto):
        """Prueba agregar detalle con producto inexistente"""
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'estado': 'borrador'}
        }
        mock_obtener_producto.return_value = None  # Producto no existe
        
        resultado = self.factura.agregar_detalle(factura_id=1, producto_id=999, cantidad=2, precio_unitario=100.0)
        
        self.assertFalse(resultado['success'])
        self.assertIn('El producto especificado no existe', resultado['message'])
        
    @patch.object(Factura, 'obtener_producto')
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_agregar_detalle_stock_insuficiente(self, mock_obtener_factura, mock_obtener_producto):
        """Prueba agregar detalle con stock insuficiente"""
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'estado': 'borrador'}
        }
        mock_obtener_producto.return_value = {
            'precio_venta': 100.0,
            'stock_actual': 1  # Stock insuficiente
        }
        
        resultado = self.factura.agregar_detalle(factura_id=1, producto_id=1, cantidad=5, precio_unitario=100.0)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Stock insuficiente', resultado['message'])
        
    @patch.object(Factura, 'recalcular_totales')
    @patch.object(Factura, 'obtener_factura_por_id')
    @patch.object(Factura, 'obtener_detalle_por_id')
    def test_eliminar_detalle_exitoso(self, mock_obtener_detalle, 
                                    mock_obtener_factura, mock_recalcular):
        """Prueba eliminar detalle exitosamente"""
        mock_obtener_detalle.return_value = {'id': 1, 'factura_id': 1}
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'estado': 'borrador'}
        }
        mock_recalcular.return_value = None  # recalcular_totales no retorna nada
        
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.eliminar_detalle(1)
            
            self.assertTrue(resultado['success'])
        
    @patch.object(Factura, 'actualizar_stock_producto')
    @patch.object(Factura, 'obtener_producto')
    @patch.object(Factura, 'obtener_detalles_factura')
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_confirmar_factura_exitosa(self, mock_obtener_factura, 
                                     mock_obtener_detalles, mock_obtener_producto, mock_actualizar_stock):
        """Prueba confirmar factura exitosamente"""
        # Configurar mocks
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'borrador', 'total_factura': 200.0}
        }
        mock_obtener_detalles.return_value = {
            'success': True,
            'data': [{'producto_id': 1, 'cantidad': 2}]
        }
        mock_obtener_producto.return_value = {
            'stock_actual': 50,
            'nombre': 'Producto Test'
        }
        mock_actualizar_stock.return_value = None
        
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.confirmar_factura(1)
            
            self.assertTrue(resultado['success'])
        
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_confirmar_factura_ya_confirmada(self, mock_obtener_factura):
        """Prueba confirmar factura ya confirmada"""
        mock_obtener_factura.return_value = {
            'success': True,
            'data': {'id': 1, 'estado': 'confirmada', 'total_factura': 200.0}
        }
        
        resultado = self.factura.confirmar_factura(1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Solo se pueden confirmar facturas en estado borrador', resultado['message'])
        
    @patch.object(Factura, 'obtener_factura_por_id')
    def test_confirmar_factura_inexistente(self, mock_obtener_factura):
        """Prueba confirmar factura inexistente"""
        mock_obtener_factura.return_value = {
            'success': False,
            'message': 'Factura no encontrada'
        }
        
        resultado = self.factura.confirmar_factura(999)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Factura no encontrada', resultado['message'])
        
    def test_obtener_factura_por_id_exitoso(self):
        """Prueba obtener factura por ID exitosamente"""
        factura_mock = {
            'id': 1,
            'numero_factura': 'FAC-001',
            'cliente_id': 1,
            'fecha_creacion': datetime.now(),
            'estado': 'borrador',
            'total_factura': 200.0
        }
        
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = factura_mock
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.obtener_factura_por_id(1)
            
            self.assertTrue(resultado['success'])
            self.assertEqual(resultado['data']['id'], 1)
            self.assertEqual(resultado['data']['numero_factura'], 'FAC-001')
        
    def test_obtener_factura_inexistente(self):
        """Prueba obtener factura inexistente"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.obtener_factura_por_id(999)
            
            self.assertFalse(resultado['success'])
            self.assertIn('Factura no encontrada', resultado['message'])
        
    def test_cliente_existe_verdadero(self):
        """Prueba cliente_existe retorna True"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 1}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.cliente_existe(1)
            
            self.assertTrue(resultado)
        
    def test_cliente_existe_falso(self):
        """Prueba cliente_existe retorna False"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 0}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            resultado = self.factura.cliente_existe(999)
            
            self.assertFalse(resultado)
        
    def test_generar_numero_factura_primera(self):
        """Prueba generar número de factura cuando es la primera"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'siguiente': 1}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            numero = self.factura.generar_numero_factura()
            
            self.assertEqual(numero, "F000001")
        
    def test_generar_numero_factura_consecutivo(self):
        """Prueba generar número de factura consecutivo"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'siguiente': 6}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            numero = self.factura.generar_numero_factura()
            
            self.assertEqual(numero, "F000006")
        
    def test_recalcular_totales_exitoso(self):
        """Prueba recalcular totales exitosamente"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Usar Decimal en lugar de float para evitar el error de tipos
        mock_cursor.fetchone.return_value = {'subtotal_total': Decimal('250.0')}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # recalcular_totales no retorna nada, solo ejecuta
            self.factura.recalcular_totales(1)
            
            # Verificar que se llamó execute en el cursor
            self.assertTrue(mock_cursor.execute.called)
        
    def test_recalcular_totales_sin_detalles(self):
        """Prueba recalcular totales sin detalles"""
        # Mock de la conexión de base de datos
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # Usar Decimal en lugar de float para evitar el error de tipos
        mock_cursor.fetchone.return_value = {'subtotal_total': Decimal('0.0')}
        
        with patch.object(self.factura.db, 'get_connection') as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            
            # recalcular_totales no retorna nada, solo ejecuta
            self.factura.recalcular_totales(1)
            
            # Verificar que se llamó execute en el cursor
            self.assertTrue(mock_cursor.execute.called)
        
    @patch('models.factura.FacturaValidator')
    def test_actualizar_detalle_cantidad_invalida(self, mock_validator):
        """Prueba actualizar detalle con cantidad inválida"""
        # Configurar validador para que falle
        mock_validator_instance = mock_validator.return_value
        mock_validator_instance.validar_detalle_factura.side_effect = ValidationError("El campo 'Cantidad' debe ser mayor o igual a 1")
        
        resultado = self.factura.actualizar_detalle(detalle_id=1, cantidad=-1, precio_unitario=100.0)
        
        self.assertFalse(resultado['success'])
        self.assertIn("El campo 'Cantidad' debe ser mayor o igual a 1", resultado['message'])

if __name__ == '__main__':
    unittest.main()