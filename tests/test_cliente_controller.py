"""
Pruebas para el controlador de Cliente
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controllers.cliente_controller import ClienteController
from utils.exceptions import ValidationError, DatabaseError, RecordNotFoundError, ClienteError


class TestClienteController(unittest.TestCase):
    """Pruebas para el controlador de Cliente"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.controller = ClienteController()
        
        # Datos de prueba válidos
        self.datos_validos = {
            'nombre_completo': 'Juan Pérez García',
            'numero_identificacion': '12345678',
            'contacto_telefono': '3001234567',
            'contacto_email': 'juan.perez@email.com'
        }
        
        # Cliente de ejemplo para pruebas
        self.cliente_ejemplo = {
            'id': 1,
            'nombre_completo': 'Juan Pérez García',
            'numero_identificacion': '12345678',
            'contacto_telefono': '3001234567',
            'contacto_email': 'juan.perez@email.com',
            'fecha_creacion': datetime.now(),
            'fecha_actualizacion': datetime.now()
        }
        
        # Resultado exitoso del modelo
        self.resultado_modelo_exitoso = {
            'success': True,
            'cliente_id': 1,
            'message': 'Cliente creado exitosamente'
        }
    
    # ========== PRUEBAS DE CREACIÓN ==========
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    @patch.object(ClienteController, 'cliente_model')
    def test_crear_cliente_exitoso(self, mock_model, mock_validar):
        """Prueba creación exitosa de cliente"""
        mock_validar.return_value = {'valid': True, 'errors': []}
        mock_model.crear_cliente.return_value = self.resultado_modelo_exitoso
        
        resultado = self.controller.crear_cliente(**self.datos_validos)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['cliente_id'], 1)
        self.assertIn('Cliente creado exitosamente', resultado['message'])
        mock_model.crear_cliente.assert_called_once()
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    def test_crear_cliente_datos_invalidos(self, mock_validar):
        """Prueba creación con datos inválidos"""
        mock_validar.return_value = {
            'valid': False,
            'errors': ['Nombre muy corto', 'Email inválido']
        }
        
        resultado = self.controller.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error de validación', resultado['message'])
        self.assertIn('Nombre muy corto', resultado['message'])
        self.assertIn('Email inválido', resultado['message'])
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    @patch.object(ClienteController, 'cliente_model')
    def test_crear_cliente_error_modelo(self, mock_model, mock_validar):
        """Prueba creación con error en el modelo"""
        mock_validar.return_value = {'valid': True, 'errors': []}
        mock_model.crear_cliente.return_value = {
            'success': False,
            'message': 'Error de base de datos'
        }
        
        resultado = self.controller.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'Error de base de datos')
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    @patch.object(ClienteController, 'cliente_model')
    def test_crear_cliente_excepcion_inesperada(self, mock_model, mock_validar):
        """Prueba creación con excepción inesperada"""
        mock_validar.return_value = {'valid': True, 'errors': []}
        mock_model.crear_cliente.side_effect = Exception("Error inesperado")
        
        resultado = self.controller.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    def test_crear_cliente_limpieza_datos(self):
        """Prueba que los datos se limpien correctamente"""
        datos_con_espacios = {
            'nombre_completo': '  Juan Pérez  ',
            'numero_identificacion': '  12345678  ',
            'contacto_telefono': '  3001234567  ',
            'contacto_email': '  JUAN.PEREZ@EMAIL.COM  '
        }
        
        with patch('controllers.cliente_controller.ClienteController.validar_datos_cliente') as mock_validar, \
             patch.object(self.controller, 'cliente_model') as mock_model:
            
            mock_validar.return_value = {'valid': True, 'errors': []}
            mock_model.crear_cliente.return_value = self.resultado_modelo_exitoso
            
            resultado = self.controller.crear_cliente(**datos_con_espacios)
            
            # Verificar que se llamó con datos limpios
            args, kwargs = mock_model.crear_cliente.call_args
            self.assertEqual(kwargs['nombre_completo'], 'Juan Pérez')
            self.assertEqual(kwargs['numero_identificacion'], '12345678')
            self.assertEqual(kwargs['contacto_telefono'], '3001234567')
            self.assertEqual(kwargs['contacto_email'], 'juan.perez@email.com')
    
    # ========== PRUEBAS DE OBTENCIÓN ==========
    
    @patch.object(ClienteController, 'cliente_model')
    @patch('controllers.cliente_controller.ClienteController._formatear_cliente_para_vista')
    def test_obtener_cliente_exitoso(self, mock_formatear, mock_model):
        """Prueba obtención exitosa de cliente"""
        mock_model.obtener_cliente_por_id.return_value = {
            'success': True,
            'cliente': self.cliente_ejemplo
        }
        mock_formatear.return_value = self.cliente_ejemplo
        
        resultado = self.controller.obtener_cliente(1)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['data'], self.cliente_ejemplo)
        mock_formatear.assert_called_once_with(self.cliente_ejemplo)
    
    @patch.object(ClienteController, 'cliente_model')
    def test_obtener_cliente_no_encontrado(self, mock_model):
        """Prueba obtención de cliente no existente"""
        mock_model.obtener_cliente_por_id.return_value = {
            'success': False,
            'message': 'Cliente no encontrado'
        }
        
        resultado = self.controller.obtener_cliente(999)
        
        self.assertFalse(resultado['success'])
        self.assertEqual(resultado['message'], 'Cliente no encontrado')
    
    @patch.object(ClienteController, 'cliente_model')
    def test_obtener_cliente_error(self, mock_model):
        """Prueba obtención con error"""
        mock_model.obtener_cliente_por_id.side_effect = Exception("Error de base de datos")
        
        resultado = self.controller.obtener_cliente(1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    # ========== PRUEBAS DE LISTADO ==========
    
    @patch.object(ClienteController, 'cliente_model')
    @patch('controllers.cliente_controller.ClienteController._formatear_cliente_para_vista')
    def test_listar_clientes_exitoso(self, mock_formatear, mock_model):
        """Prueba listado exitoso de clientes"""
        clientes_mock = [self.cliente_ejemplo, self.cliente_ejemplo.copy()]
        mock_model.obtener_todos_clientes.return_value = {
            'success': True,
            'data': clientes_mock,
            'total': 2
        }
        mock_formatear.side_effect = lambda x: x
        
        resultado = self.controller.listar_clientes()
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 2)
        self.assertEqual(resultado['total'], 2)
    
    @patch.object(ClienteController, 'cliente_model')
    def test_listar_clientes_con_filtro(self, mock_model):
        """Prueba listado con filtro de nombre"""
        mock_model.obtener_todos_clientes.return_value = {
            'success': True,
            'data': [self.cliente_ejemplo],
            'total': 1
        }
        
        resultado = self.controller.listar_clientes(filtro_nombre='Juan')
        
        mock_model.obtener_todos_clientes.assert_called_with(
            filtro_nombre='Juan',
            order_by='nombre_completo'
        )
        self.assertTrue(resultado['success'])
    
    @patch.object(ClienteController, 'cliente_model')
    def test_listar_clientes_error(self, mock_model):
        """Prueba listado con error"""
        mock_model.obtener_todos_clientes.side_effect = Exception("Error de base de datos")
        
        resultado = self.controller.listar_clientes()
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error inesperado', resultado['message'])
    
    # ========== PRUEBAS DE ACTUALIZACIÓN ==========
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    @patch.object(ClienteController, 'cliente_model')
    def test_actualizar_cliente_exitoso(self, mock_model, mock_validar):
        """Prueba actualización exitosa de cliente"""
        mock_validar.return_value = {'valid': True, 'errors': []}
        mock_model.actualizar_cliente.return_value = {
            'success': True,
            'message': 'Cliente actualizado'
        }
        
        datos_actualizacion = {'nombre_completo': 'Juan Pérez Actualizado'}
        resultado = self.controller.actualizar_cliente(1, **datos_actualizacion)
        
        self.assertTrue(resultado['success'])
        mock_model.actualizar_cliente.assert_called_once()
    
    @patch('controllers.cliente_controller.ClienteController.validar_datos_cliente')
    def test_actualizar_cliente_datos_invalidos(self, mock_validar):
        """Prueba actualización con datos inválidos"""
        mock_validar.return_value = {
            'valid': False,
            'errors': ['Nombre inválido']
        }
        
        resultado = self.controller.actualizar_cliente(1, nombre_completo='')
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error de validación', resultado['message'])
    
    # ========== PRUEBAS DE ELIMINACIÓN ==========
    
    @patch.object(ClienteController, 'cliente_model')
    def test_eliminar_cliente_exitoso(self, mock_model):
        """Prueba eliminación exitosa de cliente"""
        mock_model.eliminar_cliente.return_value = {
            'success': True,
            'message': 'Cliente eliminado'
        }
        
        resultado = self.controller.eliminar_cliente(1)
        
        self.assertTrue(resultado['success'])
        mock_model.eliminar_cliente.assert_called_once_with(1)
    
    @patch.object(ClienteController, 'cliente_model')
    def test_eliminar_cliente_con_facturas(self, mock_model):
        """Prueba eliminación de cliente con facturas"""
        mock_model.eliminar_cliente.return_value = {
            'success': False,
            'message': 'No se puede eliminar cliente con facturas'
        }
        
        resultado = self.controller.eliminar_cliente(1)
        
        self.assertFalse(resultado['success'])
        self.assertIn('facturas', resultado['message'])
    
    # ========== PRUEBAS DE BÚSQUEDA ==========
    
    @patch.object(ClienteController, 'cliente_model')
    @patch('controllers.cliente_controller.ClienteController._formatear_cliente_para_vista')
    def test_buscar_clientes_exitoso(self, mock_formatear, mock_model):
        """Prueba búsqueda exitosa de clientes"""
        mock_model.buscar_clientes.return_value = {
            'success': True,
            'data': [self.cliente_ejemplo],
            'total': 1
        }
        mock_formatear.side_effect = lambda x: x
        
        resultado = self.controller.buscar_clientes('Juan')
        
        self.assertTrue(resultado['success'])
        self.assertEqual(len(resultado['data']), 1)
        mock_model.buscar_clientes.assert_called_once_with('Juan')
    
    @patch.object(ClienteController, 'cliente_model')
    def test_buscar_clientes_termino_vacio(self, mock_model):
        """Prueba búsqueda con término vacío"""
        resultado = self.controller.buscar_clientes('')
        
        self.assertFalse(resultado['success'])
        self.assertIn('término de búsqueda', resultado['message'])
        mock_model.buscar_clientes.assert_not_called()
    
    # ========== PRUEBAS DE ESTADÍSTICAS ==========
    
    @patch.object(ClienteController, 'cliente_model')
    def test_obtener_estadisticas_generales_exitoso(self, mock_model):
        """Prueba obtención exitosa de estadísticas generales"""
        mock_model.listar_clientes.return_value = {
            'success': True,
            'data': [self.cliente_ejemplo, self.cliente_ejemplo.copy()],
            'total': 2
        }
        
        resultado = self.controller.obtener_estadisticas_generales()
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['data']['total_clientes'], 2)
        self.assertEqual(resultado['data']['clientes_activos'], 2)
    
    @patch.object(ClienteController, 'cliente_model')
    def test_obtener_estadisticas_cliente_exitoso(self, mock_model):
        """Prueba obtención exitosa de estadísticas de cliente"""
        mock_model.obtener_estadisticas_cliente.return_value = {
            'success': True,
            'data': {
                'total_compras': 5,
                'monto_total': 1000.0,
                'ultima_compra': datetime.now()
            }
        }
        
        resultado = self.controller.obtener_estadisticas_cliente(1)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['data']['total_compras'], 5)
    
    # ========== PRUEBAS DE VALIDACIÓN ==========
    
    def test_validar_datos_cliente_datos_validos(self):
        """Prueba validación con datos válidos"""
        resultado = self.controller.validar_datos_cliente(**self.datos_validos)
        
        self.assertTrue(resultado['valid'])
        self.assertEqual(len(resultado['errors']), 0)
    
    def test_validar_datos_cliente_nombre_vacio(self):
        """Prueba validación con nombre vacío"""
        datos = self.datos_validos.copy()
        datos['nombre_completo'] = ''
        
        resultado = self.controller.validar_datos_cliente(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertTrue(len(resultado['errors']) > 0)
    
    # ========== PRUEBAS DE FORMATEO ==========
    
    def test_formatear_cliente_para_vista(self):
        """Prueba formateo de cliente para vista"""
        cliente_formateado = self.controller._formatear_cliente_para_vista(self.cliente_ejemplo)
        
        # Verificar que contiene los campos esperados por la vista
        campos_esperados = [
            'id', 'nombre_completo', 'numero_identificacion',
            'contacto_telefono', 'contacto_email', 'fecha_creacion',
            'fecha_actualizacion', 'tipo_identificacion', 'nombre',
            'email', 'telefono', 'ciudad'
        ]
        
        for campo in campos_esperados:
            self.assertIn(campo, cliente_formateado)
    
    def test_formatear_cliente_campos_vacios(self):
        """Prueba formateo con campos vacíos"""
        cliente_vacio = {
            'id': 1,
            'nombre_completo': 'Test',
            'numero_identificacion': None,
            'contacto_telefono': None,
            'contacto_email': None,
            'fecha_creacion': datetime.now(),
            'fecha_actualizacion': datetime.now()
        }
        
        cliente_formateado = self.controller._formatear_cliente_para_vista(cliente_vacio)
        
        self.assertEqual(cliente_formateado['numero_identificacion'], '')
        self.assertEqual(cliente_formateado['contacto_telefono'], '')
        self.assertEqual(cliente_formateado['contacto_email'], '')
    
    # ========== PRUEBAS DE CASOS LÍMITE ==========
    
    def test_obtener_cliente_id_invalido(self):
        """Prueba obtención con ID inválido"""
        resultado = self.controller.obtener_cliente(-1)
        
        self.assertFalse(resultado['success'])
    
    def test_actualizar_cliente_sin_cambios(self):
        """Prueba actualización sin cambios"""
        with patch.object(self.controller, 'cliente_model') as mock_model:
            mock_model.actualizar_cliente.return_value = {
                'success': True,
                'message': 'Cliente actualizado'
            }
            
            resultado = self.controller.actualizar_cliente(1)
            
            self.assertTrue(resultado['success'])
    
    def test_buscar_clientes_termino_muy_corto(self):
        """Prueba búsqueda con término muy corto"""
        resultado = self.controller.buscar_clientes('a')
        
        self.assertFalse(resultado['success'])
        self.assertIn('al menos 2 caracteres', resultado['message'])


if __name__ == '__main__':
    unittest.main()