"""
Pruebas de casos límite y escenarios de error específicos para el módulo de clientes.
Cubre situaciones extremas, límites de datos y manejo de errores complejos.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from datetime import datetime, date
import sqlite3

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cliente import Cliente
from controllers.cliente_controller import ClienteController
from utils.validators import ClienteValidator


class TestCasosLimiteCliente(unittest.TestCase):
    """Pruebas de casos límite para el módulo de clientes."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
    
    def test_nombre_con_longitud_maxima(self):
        """Prueba nombres con longitud máxima permitida."""
        validator = ClienteValidator()
        
        # Nombre de exactamente 100 caracteres
        nombre_maximo = 'A' * 100
        resultado = validator.validar_nombre_format(nombre_maximo)
        self.assertTrue(resultado['valido'])
        
        # Nombre de 101 caracteres (excede el límite)
        nombre_excesivo = 'A' * 101
        resultado = validator.validar_nombre_format(nombre_excesivo)
        self.assertFalse(resultado['valido'])
    
    def test_identificacion_con_caracteres_especiales(self):
        """Prueba identificaciones con caracteres especiales válidos."""
        validator = ClienteValidator()
        
        # Cédula con guiones
        resultado = validator.validar_identificacion_por_tipo('12.345.678-9', 'Cédula de Ciudadanía')
        self.assertTrue(resultado['valido'])
        
        # NIT con guión
        resultado = validator.validar_identificacion_por_tipo('900123456-7', 'NIT')
        self.assertTrue(resultado['valido'])
        
        # Pasaporte con letras y números
        resultado = validator.validar_identificacion_por_tipo('AB123456', 'Pasaporte')
        self.assertTrue(resultado['valido'])
    
    def test_email_con_longitud_maxima(self):
        """Prueba emails con longitud máxima."""
        validator = ClienteValidator()
        
        # Email de exactamente 100 caracteres
        usuario_largo = 'a' * 85  # 85 + '@test.com' = 94 caracteres
        email_largo = f"{usuario_largo}@test.com"
        resultado = validator.validar_email(email_largo)
        self.assertTrue(resultado['valido'])
        
        # Email que excede 100 caracteres
        usuario_muy_largo = 'a' * 95
        email_muy_largo = f"{usuario_muy_largo}@test.com"
        resultado = validator.validar_email(email_muy_largo)
        self.assertFalse(resultado['valido'])
    
    def test_telefono_formatos_internacionales(self):
        """Prueba diferentes formatos de teléfono internacionales."""
        validator = ClienteValidator()
        
        # Formatos válidos
        telefonos_validos = [
            '+57 300 123 4567',
            '+1-555-123-4567',
            '+44 20 7946 0958',
            '(+57) 300 123 4567',
            '300.123.4567'
        ]
        
        for telefono in telefonos_validos:
            resultado = validator.validar_telefono(telefono)
            self.assertTrue(resultado['valido'], f"Teléfono {telefono} debería ser válido")
    
    def test_fecha_nacimiento_limites(self):
        """Prueba fechas de nacimiento en los límites."""
        validator = ClienteValidator()
        
        # Fecha hace exactamente 120 años
        fecha_120_anos = date(date.today().year - 120, 1, 1).strftime('%Y-%m-%d')
        resultado = validator.validar_fecha_nacimiento(fecha_120_anos)
        self.assertTrue(resultado['valido'])
        
        # Fecha hace 121 años (muy antigua)
        fecha_121_anos = date(date.today().year - 121, 1, 1).strftime('%Y-%m-%d')
        resultado = validator.validar_fecha_nacimiento(fecha_121_anos)
        self.assertFalse(resultado['valido'])
        
        # Fecha de ayer (válida)
        fecha_ayer = date(date.today().year, date.today().month, date.today().day - 1).strftime('%Y-%m-%d')
        resultado = validator.validar_fecha_nacimiento(fecha_ayer)
        self.assertTrue(resultado['valido'])
    
    @patch('models.cliente.get_db_connection')
    def test_creacion_cliente_con_datos_unicode(self, mock_get_db):
        """Prueba creación de cliente con caracteres Unicode."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchone.return_value = None
        self.mock_cursor.lastrowid = 1
        
        # Datos con caracteres especiales
        cliente_data = {
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'José María Ñoño',
            'email': 'josé@email.com',
            'telefono': '3001234567',
            'direccion': 'Calle 123 #45-67',
            'ciudad': 'Bogotá D.C.',
            'fecha_nacimiento': '1990-01-01'
        }
        
        cliente = Cliente()
        resultado = cliente.crear_cliente(cliente_data)
        
        self.assertTrue(resultado['success'])
    
    @patch('models.cliente.get_db_connection')
    def test_manejo_multiples_errores_simultaneos(self, mock_get_db):
        """Prueba el manejo de múltiples errores simultáneos."""
        mock_get_db.return_value = self.mock_db
        
        # Simular error de integridad y otro error
        self.mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        
        controller = ClienteController()
        
        # Datos que causarían múltiples errores
        datos_problematicos = {
            'tipo_identificacion': 'Tipo Inválido',
            'identificacion': '123',  # Muy corta
            'nombre': '',  # Vacío
            'email': 'email_invalido',
            'telefono': '123'  # Muy corto
        }
        
        resultado = controller.crear_cliente(datos_problematicos)
        
        self.assertFalse(resultado['success'])
        self.assertIn('errores', resultado)
    
    @patch('models.cliente.get_db_connection')
    def test_busqueda_con_caracteres_especiales(self, mock_get_db):
        """Prueba búsqueda con caracteres especiales y SQL injection."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchall.return_value = []
        
        controller = ClienteController()
        
        # Términos de búsqueda con caracteres especiales
        terminos_especiales = [
            "José María",
            "O'Connor",
            "Jean-Pierre",
            "María José & Asociados",
            "Cliente #1",
            "50% Descuento"
        ]
        
        for termino in terminos_especiales:
            resultado = controller.buscar_clientes(termino)
            self.assertIsInstance(resultado, list)
    
    @patch('models.cliente.get_db_connection')
    def test_busqueda_con_sql_injection_attempt(self, mock_get_db):
        """Prueba que la búsqueda sea segura contra SQL injection."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchall.return_value = []
        
        controller = ClienteController()
        
        # Intentos de SQL injection
        intentos_maliciosos = [
            "'; DROP TABLE clientes; --",
            "' OR '1'='1",
            "'; DELETE FROM clientes WHERE id > 0; --",
            "' UNION SELECT * FROM usuarios --"
        ]
        
        for intento in intentos_maliciosos:
            resultado = controller.buscar_clientes(intento)
            # Debe retornar lista vacía sin causar errores
            self.assertIsInstance(resultado, list)
            self.assertEqual(len(resultado), 0)
    
    @patch('models.cliente.get_db_connection')
    def test_actualizacion_con_datos_parciales_extremos(self, mock_get_db):
        """Prueba actualización con datos parciales en casos extremos."""
        mock_get_db.return_value = self.mock_db
        
        # Cliente existente
        cliente_existente = (1, 'Cédula de Ciudadanía', '12345678', 'Juan Pérez',
                           'juan@email.com', '3001234567', 'Calle 123', 'Bogotá', '1990-01-01')
        self.mock_cursor.fetchone.return_value = cliente_existente
        
        controller = ClienteController()
        
        # Actualización solo con espacios en blanco
        datos_espacios = {
            'nombre': '   ',
            'direccion': '\t\n',
            'ciudad': '    '
        }
        
        resultado = controller.actualizar_cliente(1, datos_espacios)
        self.assertFalse(resultado['success'])
    
    @patch('models.cliente.get_db_connection')
    def test_eliminacion_cliente_inexistente(self, mock_get_db):
        """Prueba eliminación de cliente que no existe."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchone.return_value = None  # Cliente no existe
        
        controller = ClienteController()
        resultado = controller.eliminar_cliente(99999)
        
        self.assertFalse(resultado['success'])
        self.assertIn('no existe', resultado['message'])
    
    @patch('models.cliente.get_db_connection')
    def test_obtencion_estadisticas_con_base_datos_vacia(self, mock_get_db):
        """Prueba obtención de estadísticas con base de datos vacía."""
        mock_get_db.return_value = self.mock_db
        
        # Todas las consultas retornan 0
        self.mock_cursor.fetchone.return_value = (0,)
        
        controller = ClienteController()
        estadisticas = controller.obtener_estadisticas_generales()
        
        self.assertEqual(estadisticas['total_clientes'], 0)
        self.assertEqual(estadisticas['clientes_con_identificacion'], 0)
        self.assertEqual(estadisticas['clientes_con_telefono'], 0)
        self.assertEqual(estadisticas['clientes_con_email'], 0)
    
    @patch('models.cliente.get_db_connection')
    def test_manejo_timeout_base_datos(self, mock_get_db):
        """Prueba manejo de timeout en base de datos."""
        # Simular timeout
        mock_get_db.side_effect = sqlite3.OperationalError("database is locked")
        
        controller = ClienteController()
        resultado = controller.crear_cliente({
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'Juan Pérez'
        })
        
        self.assertFalse(resultado['success'])
        self.assertIn('Error', resultado['message'])
    
    def test_validacion_datos_con_encoding_problematico(self):
        """Prueba validación con datos que pueden causar problemas de encoding."""
        validator = ClienteValidator()
        
        # Datos con diferentes encodings
        datos_encoding = {
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'José María Ñoño Gütiérrez',
            'email': 'josé.maría@email.com',
            'telefono': '3001234567',
            'direccion': 'Calle 123 #45-67 Apto 8°',
            'ciudad': 'Bogotá D.C.',
            'fecha_nacimiento': '1990-01-01'
        }
        
        errores = validator.validar_cliente_completo(datos_encoding)
        # No debe haber errores por caracteres especiales válidos
        self.assertEqual(len(errores), 0)
    
    @patch('models.cliente.get_db_connection')
    def test_concurrencia_creacion_clientes(self, mock_get_db):
        """Prueba manejo de concurrencia en creación de clientes."""
        mock_get_db.return_value = self.mock_db
        
        # Simular que el cliente no existe en la primera verificación
        # pero sí existe cuando se intenta crear (creado por otro proceso)
        self.mock_cursor.fetchone.side_effect = [
            None,  # Primera verificación: no existe
        ]
        self.mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        
        cliente = Cliente()
        resultado = cliente.crear_cliente({
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'Juan Pérez',
            'email': 'juan@email.com'
        })
        
        self.assertFalse(resultado['success'])
        self.assertIn('ya existe', resultado['message'])
    
    @patch('models.cliente.get_db_connection')
    def test_historial_compras_cliente_sin_compras(self, mock_get_db):
        """Prueba obtención de historial de compras para cliente sin compras."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchall.return_value = []  # Sin compras
        
        cliente = Cliente()
        historial = cliente.obtener_historial_compras(1)
        
        self.assertEqual(len(historial), 0)
    
    def test_validacion_identificacion_con_espacios_y_caracteres(self):
        """Prueba validación de identificación con espacios y caracteres especiales."""
        validator = ClienteValidator()
        
        # Identificaciones con espacios que deben ser válidas después de limpiar
        identificaciones_con_espacios = [
            '  12345678  ',
            '12.345.678-9',
            ' 900123456-7 ',
            'AB 123456',
            '  TI-12345678  '
        ]
        
        tipos = [
            'Cédula de Ciudadanía',
            'Cédula de Ciudadanía',
            'NIT',
            'Pasaporte',
            'Tarjeta de Identidad'
        ]
        
        for identificacion, tipo in zip(identificaciones_con_espacios, tipos):
            resultado = validator.validar_identificacion_por_tipo(identificacion, tipo)
            self.assertTrue(resultado['valido'], 
                          f"Identificación '{identificacion}' tipo '{tipo}' debería ser válida")
    
    @patch('models.cliente.get_db_connection')
    def test_busqueda_con_termino_muy_largo(self, mock_get_db):
        """Prueba búsqueda con término extremadamente largo."""
        mock_get_db.return_value = self.mock_db
        self.mock_cursor.fetchall.return_value = []
        
        controller = ClienteController()
        
        # Término de búsqueda muy largo
        termino_largo = 'A' * 1000
        resultado = controller.buscar_clientes(termino_largo)
        
        # Debe manejar el término largo sin errores
        self.assertIsInstance(resultado, list)
    
    def test_validacion_email_casos_extremos(self):
        """Prueba validación de email en casos extremos."""
        validator = ClienteValidator()
        
        # Emails en casos límite
        casos_extremos = [
            ('a@b.co', True),  # Email mínimo válido
            ('@domain.com', False),  # Sin usuario
            ('user@', False),  # Sin dominio
            ('user@domain', False),  # Sin TLD
            ('user..user@domain.com', False),  # Doble punto
            ('user@domain..com', False),  # Doble punto en dominio
            ('user@domain.c', False),  # TLD muy corto
            ('user@domain.toolongextension', False),  # TLD muy largo
        ]
        
        for email, esperado in casos_extremos:
            resultado = validator.validar_email(email)
            self.assertEqual(resultado['valido'], esperado, 
                           f"Email '{email}' debería ser {'válido' if esperado else 'inválido'}")


class TestManejadorErroresEspecificos(unittest.TestCase):
    """Pruebas específicas para manejo de errores complejos."""
    
    @patch('models.cliente.get_db_connection')
    def test_error_conexion_base_datos_intermitente(self, mock_get_db):
        """Prueba manejo de errores intermitentes de conexión."""
        # Simular conexión que falla intermitentemente
        mock_get_db.side_effect = [
            Exception("Connection timeout"),
            Exception("Database locked"),
            Exception("Disk full")
        ]
        
        controller = ClienteController()
        
        # Múltiples intentos que fallan
        for _ in range(3):
            resultado = controller.listar_clientes()
            self.assertEqual(len(resultado), 0)
    
    @patch('models.cliente.get_db_connection')
    def test_corrupcion_datos_base_datos(self, mock_get_db):
        """Prueba manejo de datos corruptos en base de datos."""
        mock_get_db.return_value = self.mock_db
        
        # Simular datos corruptos (tupla incompleta)
        self.mock_cursor.fetchall.return_value = [
            (1, 'Cédula', '12345'),  # Datos incompletos
            (2,),  # Muy pocos campos
            None   # Registro nulo
        ]
        
        controller = ClienteController()
        clientes = controller.listar_clientes()
        
        # Debe manejar datos corruptos sin fallar
        self.assertIsInstance(clientes, list)
    
    def test_memoria_insuficiente_simulada(self):
        """Prueba manejo de situaciones de memoria insuficiente."""
        validator = ClienteValidator()
        
        # Simular datos muy grandes que podrían causar problemas de memoria
        datos_grandes = {
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'identificacion': '12345678',
            'nombre': 'A' * 50,  # Nombre largo pero válido
            'email': 'test@email.com',
            'telefono': '3001234567',
            'direccion': 'B' * 200,  # Dirección muy larga
            'ciudad': 'Bogotá',
            'fecha_nacimiento': '1990-01-01'
        }
        
        # La validación debe completarse sin problemas
        errores = validator.validar_cliente_completo(datos_grandes)
        self.assertIsInstance(errores, list)


if __name__ == '__main__':
    unittest.main()