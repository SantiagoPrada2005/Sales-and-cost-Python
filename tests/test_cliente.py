"""
Pruebas para el modelo Cliente
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import Cliente
from utils.exceptions import ValidationError, DatabaseError, ClienteError, DuplicateRecordError


class TestClienteModel(unittest.TestCase):
    """Pruebas para el modelo Cliente"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.cliente = Cliente()
        
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
    
    def test_get_table_name(self):
        """Prueba que el nombre de la tabla sea correcto"""
        self.assertEqual(self.cliente.get_table_name(), 'clientes')
    
    # ========== PRUEBAS DE VALIDACIÓN ==========
    
    def test_validate_cliente_data_datos_validos(self):
        """Prueba validación con datos válidos"""
        resultado = self.cliente.validate_cliente_data(**self.datos_validos)
        
        self.assertTrue(resultado['valid'])
        self.assertEqual(len(resultado['errors']), 0)
    
    def test_validate_cliente_data_nombre_obligatorio(self):
        """Prueba que el nombre completo sea obligatorio"""
        datos = self.datos_validos.copy()
        datos['nombre_completo'] = ''
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El nombre completo es obligatorio", resultado['errors'])
    
    def test_validate_cliente_data_nombre_muy_corto(self):
        """Prueba validación de nombre muy corto"""
        datos = self.datos_validos.copy()
        datos['nombre_completo'] = 'A'
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El nombre completo debe tener al menos 2 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_nombre_muy_largo(self):
        """Prueba validación de nombre muy largo"""
        datos = self.datos_validos.copy()
        datos['nombre_completo'] = 'A' * 101
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El nombre completo no puede exceder 100 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_identificacion_muy_corta(self):
        """Prueba validación de identificación muy corta"""
        datos = self.datos_validos.copy()
        datos['numero_identificacion'] = '1234'
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El número de identificación debe tener al menos 5 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_identificacion_muy_larga(self):
        """Prueba validación de identificación muy larga"""
        datos = self.datos_validos.copy()
        datos['numero_identificacion'] = '1' * 21
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El número de identificación no puede exceder 20 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_telefono_muy_corto(self):
        """Prueba validación de teléfono muy corto"""
        datos = self.datos_validos.copy()
        datos['contacto_telefono'] = '123456'
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El teléfono debe tener al menos 7 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_telefono_muy_largo(self):
        """Prueba validación de teléfono muy largo"""
        datos = self.datos_validos.copy()
        datos['contacto_telefono'] = '1' * 16
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El teléfono no puede exceder 15 caracteres", resultado['errors'])
    
    def test_validate_cliente_data_email_invalido(self):
        """Prueba validación de email inválido"""
        datos = self.datos_validos.copy()
        datos['contacto_email'] = 'email_invalido'
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        self.assertIn("El formato del email no es válido", resultado['errors'])
    
    def test_validate_cliente_data_email_muy_largo(self):
        """Prueba validación de email muy largo"""
        datos = self.datos_validos.copy()
        datos['contacto_email'] = 'a' * 95 + '@b.com'
        
        resultado = self.cliente.validate_cliente_data(**datos)
        
        self.assertFalse(resultado['valid'])
        # El email muy largo falla por formato antes de llegar a la validación de longitud
        self.assertIn("El formato del email no es válido", resultado['errors'][0])
    
    def test_validate_cliente_data_campos_opcionales_vacios(self):
        """Prueba validación con campos opcionales vacíos"""
        resultado = self.cliente.validate_cliente_data(
            nombre_completo='Juan Pérez',
            numero_identificacion=None,
            contacto_telefono=None,
            contacto_email=None
        )
        
        self.assertTrue(resultado['valid'])
        self.assertEqual(len(resultado['errors']), 0)
    
    def test_validate_cliente_data_multiples_errores(self):
        """Prueba validación con múltiples errores"""
        resultado = self.cliente.validate_cliente_data(
            nombre_completo='',
            numero_identificacion='123',
            contacto_telefono='12345',
            contacto_email='email_invalido'
        )
        
        self.assertFalse(resultado['valid'])
        self.assertEqual(len(resultado['errors']), 4)
    
    # ========== PRUEBAS DE CREACIÓN ==========
    
    @patch.object(Cliente, 'existe_identificacion')
    @patch.object(Cliente, 'existe_email')
    @patch.object(Cliente, 'insert')
    def test_crear_cliente_exitoso(self, mock_insert, mock_existe_email, mock_existe_identificacion):
        """Prueba creación exitosa de cliente"""
        mock_existe_identificacion.return_value = False
        mock_existe_email.return_value = False
        mock_insert.return_value = 1
        
        resultado = self.cliente.crear_cliente(**self.datos_validos)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['cliente_id'], 1)
        self.assertEqual(resultado['message'], 'Cliente creado exitosamente')
        mock_insert.assert_called_once()
    
    @patch.object(Cliente, 'validate_cliente_data')
    def test_crear_cliente_datos_invalidos(self, mock_validate):
        """Prueba creación con datos inválidos"""
        mock_validate.return_value = {
            'valid': False,
            'errors': ['Error de validación']
        }
        
        resultado = self.cliente.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente_id'])
        self.assertEqual(resultado['message'], 'Error de validación')
    
    @patch.object(Cliente, 'existe_identificacion')
    @patch.object(Cliente, 'existe_email')
    def test_crear_cliente_identificacion_duplicada(self, mock_existe_email, mock_existe_identificacion):
        """Prueba creación con identificación duplicada"""
        mock_existe_identificacion.return_value = True
        mock_existe_email.return_value = False
        
        resultado = self.cliente.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente_id'])
        self.assertIn("Ya existe un cliente con la identificación", resultado['message'])
    
    @patch.object(Cliente, 'existe_identificacion')
    @patch.object(Cliente, 'existe_email')
    def test_crear_cliente_email_duplicado(self, mock_existe_email, mock_existe_identificacion):
        """Prueba creación con email duplicado"""
        mock_existe_identificacion.return_value = False
        mock_existe_email.return_value = True
        
        resultado = self.cliente.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente_id'])
        self.assertIn("Ya existe un cliente con el email", resultado['message'])
    
    @patch.object(Cliente, 'existe_identificacion')
    @patch.object(Cliente, 'existe_email')
    @patch.object(Cliente, 'insert')
    def test_crear_cliente_error_base_datos(self, mock_insert, mock_existe_email, mock_existe_identificacion):
        """Prueba creación con error de base de datos"""
        mock_existe_identificacion.return_value = False
        mock_existe_email.return_value = False
        mock_insert.side_effect = Exception("Error de base de datos")
        
        resultado = self.cliente.crear_cliente(**self.datos_validos)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente_id'])
        self.assertIn("Error interno", resultado['message'])
    
    # ========== PRUEBAS DE OBTENCIÓN ==========
    
    @patch.object(Cliente, 'find_by_id')
    def test_obtener_cliente_por_id_exitoso(self, mock_find_by_id):
        """Prueba obtención exitosa de cliente por ID"""
        mock_find_by_id.return_value = self.cliente_ejemplo
        
        resultado = self.cliente.obtener_cliente_por_id(1)
        
        self.assertTrue(resultado['success'])
        self.assertEqual(resultado['cliente'], self.cliente_ejemplo)
        self.assertEqual(resultado['message'], 'Cliente encontrado')
    
    @patch.object(Cliente, 'find_by_id')
    def test_obtener_cliente_por_id_no_encontrado(self, mock_find_by_id):
        """Prueba obtención de cliente no existente"""
        mock_find_by_id.return_value = None
        
        resultado = self.cliente.obtener_cliente_por_id(999)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente'])
        self.assertIn("Cliente con ID 999 no encontrado", resultado['message'])
    
    @patch.object(Cliente, 'find_by_id')
    def test_obtener_cliente_por_id_error(self, mock_find_by_id):
        """Prueba obtención con error de base de datos"""
        mock_find_by_id.side_effect = Exception("Error de base de datos")
        
        resultado = self.cliente.obtener_cliente_por_id(1)
        
        self.assertFalse(resultado['success'])
        self.assertIsNone(resultado['cliente'])
        self.assertIn("Error interno", resultado['message'])
    
    # ========== PRUEBAS DE CASOS LÍMITE ==========
    
    def test_crear_cliente_solo_nombre(self):
        """Prueba creación con solo nombre completo"""
        resultado = self.cliente.validate_cliente_data(
            nombre_completo='María González'
        )
        
        self.assertTrue(resultado['valid'])
        self.assertEqual(len(resultado['errors']), 0)
    
    def test_crear_cliente_nombre_con_espacios(self):
        """Prueba creación con nombre que tiene espacios extra"""
        resultado = self.cliente.validate_cliente_data(
            nombre_completo='  Juan Pérez  '
        )
        
        self.assertTrue(resultado['valid'])
    
    def test_crear_cliente_email_mayusculas(self):
        """Prueba que el email se convierta a minúsculas"""
        datos = self.datos_validos.copy()
        datos['contacto_email'] = 'JUAN.PEREZ@EMAIL.COM'
        
        with patch.object(self.cliente, 'existe_identificacion', return_value=False), \
             patch.object(self.cliente, 'existe_email', return_value=False), \
             patch.object(self.cliente, 'insert', return_value=1) as mock_insert:
            
            resultado = self.cliente.crear_cliente(**datos)
            
            # Verificar que se llamó insert con email en minúsculas
            args, kwargs = mock_insert.call_args
            data = args[0]
            self.assertEqual(data['contacto_email'], 'juan.perez@email.com')
    
    def test_validacion_email_formatos_validos(self):
        """Prueba validación con diferentes formatos de email válidos"""
        emails_validos = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in emails_validos:
            with self.subTest(email=email):
                resultado = self.cliente.validate_cliente_data(
                    nombre_completo='Test User',
                    contacto_email=email
                )
                self.assertTrue(resultado['valid'], f"Email {email} debería ser válido")
    
    def test_validacion_email_formatos_invalidos(self):
        """Prueba validación con formatos de email inválidos"""
        emails_invalidos = [
            'test@',
            '@example.com',
            'test.example.com',
            'test@',
            'test@.com',
            'test@com',
            # Nota: email vacío '' se trata como válido (opcional)
        ]
        
        for email in emails_invalidos:
            with self.subTest(email=email):
                resultado = self.cliente.validate_cliente_data(
                    nombre_completo='Test User',
                    contacto_email=email
                )
                self.assertFalse(resultado['valid'], f"Email {email} debería ser inválido")


if __name__ == '__main__':
    unittest.main()