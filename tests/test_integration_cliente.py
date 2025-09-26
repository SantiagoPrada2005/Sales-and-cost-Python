"""
Pruebas de integración para el módulo de clientes.
Verifica que el modelo, controlador y vista trabajen correctamente en conjunto.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import Cliente
from controllers.cliente_controller import ClienteController
from views.clientes_view import ClientesView, ClienteDialog
from utils.validators import ClienteValidator


class TestIntegracionCliente(unittest.TestCase):
    """Pruebas de integración para el módulo completo de clientes."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        # Mock de la base de datos
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        
        # Datos de prueba
        self.cliente_data = {
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'Juan Pérez',
            'email': 'juan@email.com',
            'telefono': '3001234567',
            'direccion': 'Calle 123',
            'ciudad': 'Bogotá',
            'fecha_nacimiento': '1990-01-01'
        }
    
    @patch('models.cliente.get_db_connection')
    def test_flujo_completo_creacion_cliente(self, mock_get_db):
        """Prueba el flujo completo de creación de un cliente."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchone.return_value = None  # No existe cliente duplicado
        self.mock_cursor.lastrowid = 1
        
        # 1. Validar datos con ClienteValidator
        validator = ClienteValidator()
        errores = validator.validar_cliente_completo(self.cliente_data)
        self.assertEqual(len(errores), 0, "Los datos deben ser válidos")
        
        # 2. Crear cliente usando el modelo
        cliente = Cliente()
        resultado = cliente.crear_cliente(self.cliente_data)
        
        # 3. Verificar que el cliente se creó correctamente
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['cliente_id'], 1)
        
        # 4. Verificar que se llamaron los métodos correctos de la base de datos
        self.mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()
    
    @patch('models.cliente.get_db_connection')
    def test_flujo_completo_con_controlador(self, mock_get_db):
        """Prueba el flujo completo usando el controlador."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchone.return_value = None  # No existe cliente duplicado
        self.mock_cursor.lastrowid = 1
        
        # Crear controlador
        controller = ClienteController()
        
        # Crear cliente a través del controlador
        resultado = controller.crear_cliente(self.cliente_data)
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['cliente_id'], 1)
        
        # Verificar que los datos fueron limpiados correctamente
        self.mock_cursor.execute.assert_called()
        call_args = self.mock_cursor.execute.call_args[0]
        self.assertIn('INSERT INTO clientes', call_args[0])
    
    @patch('models.cliente.get_db_connection')
    def test_busqueda_y_listado_integrado(self, mock_get_db):
        """Prueba la funcionalidad de búsqueda y listado integrada."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Datos de clientes simulados
        clientes_mock = [
            (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 'juan@email.com', 
             '3001234567', 'Calle 123', 'Bogotá', '1990-01-01'),
            (2, 'Cédula de Ciudadanía', '87654321', 'María García', 'maria@email.com',
             '3009876543', 'Carrera 456', 'Medellín', '1985-05-15')
        ]
        self.mock_cursor.fetchall.return_value = clientes_mock
        
        # Crear controlador
        controller = ClienteController()
        
        # Listar todos los clientes
        clientes = controller.listar_clientes()
        
        # Verificar que se obtuvieron los clientes
        self.assertEqual(len(clientes), 2)
        self.assertEqual(clientes[0]['nombre'], 'Juan Pérez')
        self.assertEqual(clientes[1]['nombre'], 'María García')
        
        # Buscar cliente específico
        self.mock_cursor.fetchall.return_value = [clientes_mock[0]]
        resultados = controller.buscar_clientes('Juan')
        
        # Verificar resultado de búsqueda
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]['nombre'], 'Juan Pérez')
    
    @patch('models.cliente.get_db_connection')
    def test_actualizacion_cliente_integrada(self, mock_get_db):
        """Prueba la actualización de cliente de forma integrada."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Cliente existente
        cliente_existente = (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 
                           'juan@email.com', '3001234567', 'Calle 123', 'Bogotá', '1990-01-01')
        self.mock_cursor.fetchone.return_value = cliente_existente
        
        # Datos actualizados
        datos_actualizados = {
            'nombre': 'Juan Carlos Pérez',
            'telefono': '3001111111',
            'direccion': 'Calle 456'
        }
        
        # Crear controlador
        controller = ClienteController()
        
        # 1. Validar datos de actualización
        validator = ClienteValidator()
        errores = validator.validar_actualizacion_cliente(datos_actualizados)
        self.assertEqual(len(errores), 0)
        
        # 2. Actualizar cliente
        resultado = controller.actualizar_cliente(1, datos_actualizados)
        
        # 3. Verificar resultado
        self.assertTrue(resultado['success'])
        self.mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()
    
    @patch('models.cliente.get_db_connection')
    def test_eliminacion_cliente_con_validaciones(self, mock_get_db):
        """Prueba la eliminación de cliente con validaciones."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Cliente sin facturas asociadas
        self.mock_cursor.fetchone.side_effect = [
            (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 'juan@email.com', 
             '3001234567', 'Calle 123', 'Bogotá', '1990-01-01'),  # Cliente existe
            None  # No tiene facturas
        ]
        
        # Crear controlador
        controller = ClienteController()
        
        # Eliminar cliente
        resultado = controller.eliminar_cliente(1)
        
        # Verificar resultado
        self.assertTrue(resultado['success'])
        self.mock_cursor.execute.assert_called()
        self.mock_db.commit.assert_called()
    
    @patch('models.cliente.get_db_connection')
    def test_eliminacion_cliente_con_facturas(self, mock_get_db):
        """Prueba que no se pueda eliminar un cliente con facturas."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Cliente con facturas asociadas
        self.mock_cursor.fetchone.side_effect = [
            (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 'juan@email.com', 
             '3001234567', 'Calle 123', 'Bogotá', '1990-01-01'),  # Cliente existe
            (1,)  # Tiene facturas
        ]
        
        # Crear controlador
        controller = ClienteController()
        
        # Intentar eliminar cliente
        resultado = controller.eliminar_cliente(1)
        
        # Verificar que no se pudo eliminar
        self.assertFalse(resultado['success'])
        self.assertIn('facturas asociadas', resultado['message'])
    
    @patch('models.cliente.get_db_connection')
    def test_estadisticas_generales_integradas(self, mock_get_db):
        """Prueba la obtención de estadísticas generales."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Estadísticas simuladas
        self.mock_cursor.fetchone.side_effect = [
            (100,),  # total_clientes
            (85,),   # clientes_con_identificacion
            (70,),   # clientes_con_telefono
            (60,)    # clientes_con_email
        ]
        
        # Crear controlador
        controller = ClienteController()
        
        # Obtener estadísticas
        estadisticas = controller.obtener_estadisticas_generales()
        
        # Verificar estadísticas
        self.assertEqual(estadisticas['total_clientes'], 100)
        self.assertEqual(estadisticas['clientes_con_identificacion'], 85)
        self.assertEqual(estadisticas['clientes_con_telefono'], 70)
        self.assertEqual(estadisticas['clientes_con_email'], 60)
        self.assertEqual(estadisticas['clientes_activos'], 100)  # Igual al total
        self.assertEqual(estadisticas['nuevos_este_mes'], 0)     # Placeholder
    
    def test_validacion_datos_invalidos_integrada(self):
        """Prueba la validación integrada de datos inválidos."""
        # Datos inválidos
        datos_invalidos = {
            'tipo_identificacion': 'Tipo Inválido',
            'identificacion': '123',  # Muy corta
            'nombre': '',  # Vacío
            'email': 'email_invalido',
            'telefono': '123',  # Muy corto
            'fecha_nacimiento': '2025-01-01'  # Fecha futura
        }
        
        # Validar con ClienteValidator
        validator = ClienteValidator()
        errores = validator.validar_cliente_completo(datos_invalidos)
        
        # Verificar que se detectaron múltiples errores
        self.assertGreater(len(errores), 0)
        
        # Crear controlador
        controller = ClienteController()
        
        # Intentar crear cliente con datos inválidos
        resultado = controller.crear_cliente(datos_invalidos)
        
        # Verificar que falló
        self.assertFalse(resultado['success'])
        self.assertIn('errores', resultado)
    
    @patch('models.cliente.get_db_connection')
    def test_manejo_errores_base_datos(self, mock_get_db):
        """Prueba el manejo de errores de base de datos."""
        # Configurar mock para simular error de base de datos
        mock_get_db.side_effect = Exception("Error de conexión a la base de datos")
        
        # Crear controlador
        controller = ClienteController()
        
        # Intentar crear cliente
        resultado = controller.crear_cliente(self.cliente_data)
        
        # Verificar que se manejó el error
        self.assertFalse(resultado['success'])
        self.assertIn('Error', resultado['message'])
    
    @patch('models.cliente.get_db_connection')
    def test_formateo_datos_para_vista(self, mock_get_db):
        """Prueba el formateo de datos para la vista."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Cliente con algunos campos vacíos
        cliente_mock = (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 
                       None, '3001234567', '', 'Bogotá', '1990-01-01')
        self.mock_cursor.fetchone.return_value = cliente_mock
        
        # Crear controlador
        controller = ClienteController()
        
        # Obtener cliente
        cliente = controller.obtener_cliente(1)
        
        # Verificar formateo
        self.assertTrue(cliente['success'])
        cliente_data = cliente['cliente']
        
        # Verificar que los campos vacíos se manejan correctamente
        self.assertEqual(cliente_data['email'], '')
        self.assertEqual(cliente_data['direccion'], '')
        self.assertEqual(cliente_data['telefono'], '3001234567')
    
    @patch('models.cliente.get_db_connection')
    def test_busqueda_con_filtros_multiples(self, mock_get_db):
        """Prueba la búsqueda con múltiples criterios."""
        # Configurar mock de base de datos
        mock_get_db.return_value = self.mock_db
        
        # Resultados de búsqueda simulados
        resultados_mock = [
            (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez', 'juan@email.com',
             '3001234567', 'Calle 123', 'Bogotá', '1990-01-01')
        ]
        self.mock_cursor.fetchall.return_value = resultados_mock
        
        # Crear controlador
        controller = ClienteController()
        
        # Buscar por diferentes criterios
        resultados = controller.buscar_clientes('Juan')
        
        # Verificar resultados
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]['nombre'], 'Juan Pérez')
        
        # Verificar que se ejecutó la consulta correcta
        self.mock_cursor.execute.assert_called()
        call_args = self.mock_cursor.execute.call_args[0]
        self.assertIn('WHERE', call_args[0])
        self.assertIn('OR', call_args[0])


class TestIntegracionVista(unittest.TestCase):
    """Pruebas de integración específicas para la vista."""
    
    def setUp(self):
        """Configuración inicial para pruebas de vista."""
        # Mock del controlador
        self.mock_controller = Mock()
        
        # Datos de prueba
        self.clientes_mock = [
            {
                'id': 1,
                'tipo_identificacion': 'Cédula de Ciudadanía',
                'identificacion': '12345678',
                'nombre': 'Juan Pérez',
                'email': 'juan@email.com',
                'telefono': '3001234567',
                'direccion': 'Calle 123',
                'ciudad': 'Bogotá',
                'fecha_nacimiento': '1990-01-01'
            }
        ]
    
    @patch('PyQt5.QtWidgets.QApplication')
    def test_integracion_vista_controlador_carga_datos(self, mock_app):
        """Prueba la integración entre vista y controlador para cargar datos."""
        # Configurar mock del controlador
        self.mock_controller.listar_clientes.return_value = self.clientes_mock
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'total_clientes': 1,
            'clientes_activos': 1,
            'nuevos_este_mes': 0
        }
        
        # Crear vista con controlador mock
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            vista = ClientesView()
            
            # Simular carga de datos
            vista.cargar_clientes()
            
            # Verificar que se llamaron los métodos del controlador
            self.mock_controller.listar_clientes.assert_called_once()
    
    @patch('PyQt5.QtWidgets.QApplication')
    def test_integracion_vista_controlador_busqueda(self, mock_app):
        """Prueba la integración entre vista y controlador para búsqueda."""
        # Configurar mock del controlador
        self.mock_controller.buscar_clientes.return_value = self.clientes_mock
        
        # Crear vista con controlador mock
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            vista = ClientesView()
            
            # Simular búsqueda
            vista.realizar_busqueda('Juan')
            
            # Verificar que se llamó el método de búsqueda
            self.mock_controller.buscar_clientes.assert_called_once_with('Juan')


if __name__ == '__main__':
    unittest.main()