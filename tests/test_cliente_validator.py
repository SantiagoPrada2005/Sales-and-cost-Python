"""
Pruebas para el validador de clientes (ClienteValidator)
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from utils.validators import ClienteValidator
from utils.exceptions import ValidationError


class TestClienteValidator(unittest.TestCase):
    """Pruebas para la clase ClienteValidator"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.validator = ClienteValidator()
    
    # ========== Pruebas para validar_cliente_completo ==========
    
    def test_validar_cliente_completo_datos_validos(self):
        """Prueba validación completa con todos los datos válidos"""
        try:
            self.validator.validar_cliente_completo(
                tipo_identificacion="Cédula de Ciudadanía",
                numero_identificacion="12345678",
                nombre="Juan Pérez",
                email="juan@email.com",
                telefono="3001234567",
                direccion="Calle 123 #45-67",
                ciudad="Bogotá",
                fecha_nacimiento="1990-01-01"
            )
        except ValidationError:
            self.fail("validar_cliente_completo() falló con datos válidos")
    
    def test_validar_cliente_completo_campos_opcionales_vacios(self):
        """Prueba validación completa con campos opcionales vacíos"""
        try:
            self.validator.validar_cliente_completo(
                tipo_identificacion="Cédula de Ciudadanía",
                numero_identificacion="12345678",
                nombre="Juan Pérez",
                email="",
                telefono="",
                direccion="",
                ciudad="",
                fecha_nacimiento=None
            )
        except ValidationError:
            self.fail("validar_cliente_completo() falló con campos opcionales vacíos")
    
    def test_validar_cliente_completo_tipo_identificacion_requerido(self):
        """Prueba que el tipo de identificación sea requerido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_cliente_completo(
                tipo_identificacion="",
                numero_identificacion="12345678",
                nombre="Juan Pérez"
            )
        self.assertIn("Tipo de identificación", str(context.exception))
    
    def test_validar_cliente_completo_numero_identificacion_requerido(self):
        """Prueba que el número de identificación sea requerido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_cliente_completo(
                tipo_identificacion="Cédula de Ciudadanía",
                numero_identificacion="",
                nombre="Juan Pérez"
            )
        self.assertIn("Número de identificación", str(context.exception))
    
    def test_validar_cliente_completo_nombre_requerido(self):
        """Prueba que el nombre sea requerido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_cliente_completo(
                tipo_identificacion="Cédula de Ciudadanía",
                numero_identificacion="12345678",
                nombre=""
            )
        self.assertIn("Nombre", str(context.exception))
    
    # ========== Pruebas para validar_tipo_identificacion ==========
    
    def test_validar_tipo_identificacion_validos(self):
        """Prueba tipos de identificación válidos"""
        tipos_validos = [
            "Cédula de Ciudadanía",
            "Cédula de Extranjería",
            "NIT",
            "Pasaporte",
            "Tarjeta de Identidad"
        ]
        
        for tipo in tipos_validos:
            try:
                self.validator.validar_tipo_identificacion(tipo)
            except ValidationError:
                self.fail(f"validar_tipo_identificacion() falló con tipo válido: {tipo}")
    
    def test_validar_tipo_identificacion_invalido(self):
        """Prueba tipo de identificación inválido"""
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_tipo_identificacion("Tipo Inválido")
        self.assertIn("Tipo de identificación inválido", str(context.exception))
    
    # ========== Pruebas para validar_identificacion_por_tipo ==========
    
    def test_validar_cedula_ciudadania_valida(self):
        """Prueba validación de cédula de ciudadanía válida"""
        numeros_validos = ["123456", "12345678", "1234567890"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_identificacion_por_tipo(numero, "Cédula de Ciudadanía")
            except ValidationError:
                self.fail(f"validar_identificacion_por_tipo() falló con cédula válida: {numero}")
    
    def test_validar_cedula_ciudadania_invalida(self):
        """Prueba validación de cédula de ciudadanía inválida"""
        numeros_invalidos = ["12345", "12345678901", "abc123"]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_identificacion_por_tipo(numero, "Cédula de Ciudadanía")
    
    def test_validar_cedula_extranjeria_valida(self):
        """Prueba validación de cédula de extranjería válida"""
        numeros_validos = ["123456", "123456789012"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_identificacion_por_tipo(numero, "Cédula de Extranjería")
            except ValidationError:
                self.fail(f"validar_identificacion_por_tipo() falló con cédula de extranjería válida: {numero}")
    
    def test_validar_nit_valido(self):
        """Prueba validación de NIT válido"""
        numeros_validos = ["123456789", "123456789012345"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_identificacion_por_tipo(numero, "NIT")
            except ValidationError:
                self.fail(f"validar_identificacion_por_tipo() falló con NIT válido: {numero}")
    
    def test_validar_nit_invalido(self):
        """Prueba validación de NIT inválido"""
        numeros_invalidos = ["12345678", "1234567890123456"]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_identificacion_por_tipo(numero, "NIT")
    
    def test_validar_pasaporte_valido(self):
        """Prueba validación de pasaporte válido"""
        numeros_validos = ["AB1234", "123456789ABC"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_identificacion_por_tipo(numero, "Pasaporte")
            except ValidationError:
                self.fail(f"validar_identificacion_por_tipo() falló con pasaporte válido: {numero}")
    
    def test_validar_pasaporte_invalido(self):
        """Prueba validación de pasaporte inválido"""
        numeros_invalidos = ["AB123", "1234567890123"]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_identificacion_por_tipo(numero, "Pasaporte")
    
    def test_validar_tarjeta_identidad_valida(self):
        """Prueba validación de tarjeta de identidad válida"""
        numeros_validos = ["12345678", "123456789012345"]
        
        for numero in numeros_validos:
            try:
                self.validator.validar_identificacion_por_tipo(numero, "Tarjeta de Identidad")
            except ValidationError:
                self.fail(f"validar_identificacion_por_tipo() falló con tarjeta de identidad válida: {numero}")
    
    def test_validar_tarjeta_identidad_invalida(self):
        """Prueba validación de tarjeta de identidad inválida"""
        numeros_invalidos = ["1234567", "1234567890123456"]
        
        for numero in numeros_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_identificacion_por_tipo(numero, "Tarjeta de Identidad")
    
    # ========== Pruebas para validar_nombre_format ==========
    
    def test_validar_nombre_format_valido(self):
        """Prueba validación de formato de nombre válido"""
        nombres_validos = [
            "Juan Pérez",
            "María José García-López",
            "José O'Connor",
            "Ana María",
            "Carlos Andrés Rodríguez"
        ]
        
        for nombre in nombres_validos:
            try:
                self.validator.validar_nombre_format(nombre)
            except ValidationError:
                self.fail(f"validar_nombre_format() falló con nombre válido: {nombre}")
    
    def test_validar_nombre_format_invalido(self):
        """Prueba validación de formato de nombre inválido"""
        nombres_invalidos = [
            "Juan123",
            "María@email",
            "José#Pérez",
            "Ana$María"
        ]
        
        for nombre in nombres_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_nombre_format(nombre)
    
    # ========== Pruebas para validar_email ==========
    
    def test_validar_email_valido(self):
        """Prueba validación de email válido"""
        emails_validos = [
            "test@example.com",
            "user.name@domain.co",
            "test+tag@example.org"
        ]
        
        for email in emails_validos:
            try:
                self.validator.validar_email(email)
            except ValidationError:
                self.fail(f"validar_email() falló con email válido: {email}")
    
    def test_validar_email_invalido(self):
        """Prueba validación de email inválido"""
        emails_invalidos = [
            "email_invalido",
            "@domain.com",
            "user@",
            "user@domain"
        ]
        
        for email in emails_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_email(email)
    
    def test_validar_email_muy_largo(self):
        """Prueba validación de email muy largo"""
        email_largo = "a" * 95 + "@test.com"  # Más de 100 caracteres
        with self.assertRaises(ValidationError):
            self.validator.validar_email(email_largo)
    
    # ========== Pruebas para validar_telefono ==========
    
    def test_validar_telefono_valido(self):
        """Prueba validación de teléfono válido"""
        telefonos_validos = [
            "3001234567",
            "+57 300 123 4567",
            "(300) 123-4567",
            "300-123-4567"
        ]
        
        for telefono in telefonos_validos:
            try:
                self.validator.validar_telefono(telefono)
            except ValidationError:
                self.fail(f"validar_telefono() falló con teléfono válido: {telefono}")
    
    def test_validar_telefono_invalido(self):
        """Prueba validación de teléfono inválido"""
        telefonos_invalidos = [
            "123456",  # Muy corto
            "abc123def",  # Contiene letras
            "123456789012345678901"  # Muy largo
        ]
        
        for telefono in telefonos_invalidos:
            with self.assertRaises(ValidationError):
                self.validator.validar_telefono(telefono)
    
    # ========== Pruebas para validar_ciudad_format ==========
    
    def test_validar_ciudad_format_valida(self):
        """Prueba validación de formato de ciudad válida"""
        ciudades_validas = [
            "Bogotá",
            "Medellín",
            "Cali",
            "Santa Marta",
            "San José"
        ]
        
        for ciudad in ciudades_validas:
            try:
                self.validator.validar_ciudad_format(ciudad)
            except ValidationError:
                self.fail(f"validar_ciudad_format() falló con ciudad válida: {ciudad}")
    
    def test_validar_ciudad_format_invalida(self):
        """Prueba validación de formato de ciudad inválida"""
        ciudades_invalidas = [
            "Bogotá123",
            "Ciudad@Test",
            "Medellín#1"
        ]
        
        for ciudad in ciudades_invalidas:
            with self.assertRaises(ValidationError):
                self.validator.validar_ciudad_format(ciudad)
    
    # ========== Pruebas para validar_fecha_nacimiento ==========
    
    def test_validar_fecha_nacimiento_valida(self):
        """Prueba validación de fecha de nacimiento válida"""
        fechas_validas = [
            "1990-01-01",
            "2000-12-31",
            datetime(1985, 5, 15)
        ]
        
        for fecha in fechas_validas:
            try:
                self.validator.validar_fecha_nacimiento(fecha)
            except ValidationError:
                self.fail(f"validar_fecha_nacimiento() falló con fecha válida: {fecha}")
    
    def test_validar_fecha_nacimiento_formato_invalido(self):
        """Prueba validación de fecha de nacimiento con formato inválido"""
        fechas_invalidas = [
            "01/01/1990",
            "1990-13-01",
            "fecha_invalida"
        ]
        
        for fecha in fechas_invalidas:
            with self.assertRaises(ValidationError):
                self.validator.validar_fecha_nacimiento(fecha)
    
    def test_validar_fecha_nacimiento_futura(self):
        """Prueba validación de fecha de nacimiento futura"""
        fecha_futura = datetime.now() + timedelta(days=1)
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_fecha_nacimiento(fecha_futura)
        self.assertIn("no puede ser futura", str(context.exception))
    
    def test_validar_fecha_nacimiento_muy_antigua(self):
        """Prueba validación de fecha de nacimiento muy antigua"""
        fecha_antigua = datetime(1900, 1, 1)
        with self.assertRaises(ValidationError) as context:
            self.validator.validar_fecha_nacimiento(fecha_antigua)
        self.assertIn("edad no válida", str(context.exception))
    
    # ========== Pruebas para validar_actualizacion_cliente ==========
    
    def test_validar_actualizacion_cliente_campos_validos(self):
        """Prueba validación de actualización con campos válidos"""
        try:
            self.validator.validar_actualizacion_cliente(
                nombre="Juan Pérez",
                email="juan@email.com",
                telefono="3001234567",
                direccion="Calle 123",
                ciudad="Bogotá",
                fecha_nacimiento="1990-01-01"
            )
        except ValidationError:
            self.fail("validar_actualizacion_cliente() falló con campos válidos")
    
    def test_validar_actualizacion_cliente_campos_vacios(self):
        """Prueba validación de actualización con campos vacíos (deben ser ignorados)"""
        try:
            self.validator.validar_actualizacion_cliente(
                nombre="",
                email="",
                telefono="",
                direccion="",
                ciudad="",
                fecha_nacimiento=""
            )
        except ValidationError:
            self.fail("validar_actualizacion_cliente() falló con campos vacíos")
    
    def test_validar_actualizacion_cliente_nombre_invalido(self):
        """Prueba validación de actualización con nombre inválido"""
        with self.assertRaises(ValidationError):
            self.validator.validar_actualizacion_cliente(nombre="Juan123")
    
    def test_validar_actualizacion_cliente_email_invalido(self):
        """Prueba validación de actualización con email inválido"""
        with self.assertRaises(ValidationError):
            self.validator.validar_actualizacion_cliente(email="email_invalido")
    
    # ========== Pruebas para validar_cliente (método legacy) ==========
    
    def test_validar_cliente_legacy_datos_validos(self):
        """Prueba validación legacy con datos válidos"""
        try:
            self.validator.validar_cliente(
                nombre="Juan Pérez",
                identificacion="12345678",
                email="juan@email.com",
                telefono="3001234567"
            )
        except ValidationError:
            self.fail("validar_cliente() falló con datos válidos")
    
    def test_validar_cliente_legacy_campos_opcionales_none(self):
        """Prueba validación legacy con campos opcionales None"""
        try:
            self.validator.validar_cliente(
                nombre="Juan Pérez",
                identificacion="12345678",
                email=None,
                telefono=None
            )
        except ValidationError:
            self.fail("validar_cliente() falló con campos opcionales None")
    
    def test_validar_cliente_legacy_identificacion_invalida(self):
        """Prueba validación legacy con identificación inválida"""
        with self.assertRaises(ValidationError):
            self.validator.validar_cliente(
                nombre="Juan Pérez",
                identificacion="abc123",
                email="juan@email.com"
            )
    
    # ========== Pruebas de casos límite ==========
    
    def test_identificacion_con_espacios_y_guiones(self):
        """Prueba identificación con espacios y guiones"""
        try:
            self.validator.validar_identificacion_por_tipo("123-456-789", "Cédula de Ciudadanía")
        except ValidationError:
            self.fail("validar_identificacion_por_tipo() falló con espacios y guiones")
    
    def test_nombre_con_caracteres_especiales_validos(self):
        """Prueba nombre con caracteres especiales válidos"""
        nombres_especiales = [
            "José María",
            "Ana-Sofía",
            "O'Connor",
            "María José García-López"
        ]
        
        for nombre in nombres_especiales:
            try:
                self.validator.validar_nombre_format(nombre)
            except ValidationError:
                self.fail(f"validar_nombre_format() falló con nombre especial válido: {nombre}")
    
    def test_telefono_con_formato_internacional(self):
        """Prueba teléfono con formato internacional"""
        try:
            self.validator.validar_telefono("+57 300 123 4567")
        except ValidationError:
            self.fail("validar_telefono() falló con formato internacional")
    
    def test_validacion_multiple_errores(self):
        """Prueba que se capture el primer error cuando hay múltiples errores"""
        with self.assertRaises(ValidationError):
            self.validator.validar_cliente_completo(
                tipo_identificacion="Tipo Inválido",  # Error 1
                numero_identificacion="abc",  # Error 2
                nombre=""  # Error 3
            )


if __name__ == '__main__':
    unittest.main()