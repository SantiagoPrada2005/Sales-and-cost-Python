"""
Script para ejecutar todas las pruebas del módulo de clientes.
Proporciona un punto de entrada único para ejecutar todas las pruebas de verificación.
"""

import unittest
import sys
import os
from io import StringIO

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar todos los módulos de prueba
from tests.test_cliente import TestClienteModel
from tests.test_cliente_controller import TestClienteController
from tests.test_cliente_validator import TestClienteValidator
from tests.test_clientes_view import TestClientesView, TestClienteDialog
from tests.test_integration_cliente import TestIntegracionCliente, TestIntegracionVista
from tests.test_edge_cases_cliente import TestCasosLimiteCliente, TestManejadorErroresEspecificos


class ColoredTextTestResult(unittest.TextTestResult):
    """Resultado de pruebas con colores para mejor visualización."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.verbosity = verbosity  # Guardar verbosity como atributo de instancia
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write("✓ ")
            self.stream.writeln(f"{test._testMethodName}")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write("✗ ERROR: ")
            self.stream.writeln(f"{test._testMethodName}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write("✗ FAIL: ")
            self.stream.writeln(f"{test._testMethodName}")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write("⚠ SKIP: ")
            self.stream.writeln(f"{test._testMethodName} - {reason}")


def crear_suite_completa():
    """Crea una suite con todas las pruebas del módulo de clientes."""
    suite = unittest.TestSuite()
    
    # Agregar pruebas del modelo
    suite.addTest(unittest.makeSuite(TestClienteModel))
    
    # Agregar pruebas del controlador
    suite.addTest(unittest.makeSuite(TestClienteController))
    
    # Agregar pruebas del validador
    suite.addTest(unittest.makeSuite(TestClienteValidator))
    
    # Agregar pruebas de la vista
    suite.addTest(unittest.makeSuite(TestClientesView))
    suite.addTest(unittest.makeSuite(TestClienteDialog))
    
    # Agregar pruebas de integración
    suite.addTest(unittest.makeSuite(TestIntegracionCliente))
    suite.addTest(unittest.makeSuite(TestIntegracionVista))
    
    # Agregar pruebas de casos límite
    suite.addTest(unittest.makeSuite(TestCasosLimiteCliente))
    suite.addTest(unittest.makeSuite(TestManejadorErroresEspecificos))
    
    return suite


def crear_suite_por_categoria(categoria):
    """Crea una suite para una categoría específica de pruebas."""
    suite = unittest.TestSuite()
    
    if categoria == 'modelo':
        suite.addTest(unittest.makeSuite(TestClienteModel))
    elif categoria == 'controlador':
        suite.addTest(unittest.makeSuite(TestClienteController))
    elif categoria == 'validador':
        suite.addTest(unittest.makeSuite(TestClienteValidator))
    elif categoria == 'vista':
        suite.addTest(unittest.makeSuite(TestClientesView))
        suite.addTest(unittest.makeSuite(TestClienteDialog))
    elif categoria == 'integracion':
        suite.addTest(unittest.makeSuite(TestIntegracionCliente))
        suite.addTest(unittest.makeSuite(TestIntegracionVista))
    elif categoria == 'casos_limite':
        suite.addTest(unittest.makeSuite(TestCasosLimiteCliente))
        suite.addTest(unittest.makeSuite(TestManejadorErroresEspecificos))
    
    return suite


def ejecutar_pruebas(suite, verbosity=2):
    """Ejecuta las pruebas y muestra los resultados."""
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        resultclass=ColoredTextTestResult,
        stream=sys.stdout
    )
    
    print("=" * 70)
    print("EJECUTANDO PRUEBAS DEL MÓDULO DE CLIENTES")
    print("=" * 70)
    
    resultado = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("RESUMEN DE RESULTADOS")
    print("=" * 70)
    
    total_pruebas = resultado.testsRun
    errores = len(resultado.errors)
    fallos = len(resultado.failures)
    omitidas = len(resultado.skipped)
    exitosas = total_pruebas - errores - fallos - omitidas
    
    print(f"Total de pruebas ejecutadas: {total_pruebas}")
    print(f"✓ Exitosas: {exitosas}")
    print(f"✗ Fallos: {fallos}")
    print(f"✗ Errores: {errores}")
    print(f"⚠ Omitidas: {omitidas}")
    
    if errores > 0:
        print(f"\n🔴 ERRORES ({errores}):")
        for test, error in resultado.errors:
            error_msg = error.split('\n')[0]
            print(f"  - {test}: {error_msg}")
    
    if fallos > 0:
        print(f"\n🟡 FALLOS ({fallos}):")
        for test, failure in resultado.failures:
            failure_msg = failure.split('\n')[0]
            print(f"  - {test}: {failure_msg}")
    
    porcentaje_exito = (exitosas / total_pruebas * 100) if total_pruebas > 0 else 0
    print(f"\n📊 Porcentaje de éxito: {porcentaje_exito:.1f}%")
    
    if porcentaje_exito == 100:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    elif porcentaje_exito >= 90:
        print("✅ Excelente cobertura de pruebas")
    elif porcentaje_exito >= 80:
        print("⚠️ Buena cobertura, pero hay áreas de mejora")
    else:
        print("❌ Se requiere atención en las pruebas")
    
    return resultado.wasSuccessful()


def mostrar_ayuda():
    """Muestra la ayuda del script."""
    print("Uso: python test_runner.py [categoria] [opciones]")
    print("\nCategorías disponibles:")
    print("  all          - Ejecutar todas las pruebas (por defecto)")
    print("  modelo       - Solo pruebas del modelo Cliente")
    print("  controlador  - Solo pruebas del ClienteController")
    print("  validador    - Solo pruebas del ClienteValidator")
    print("  vista        - Solo pruebas de las vistas")
    print("  integracion  - Solo pruebas de integración")
    print("  casos_limite - Solo pruebas de casos límite")
    print("\nOpciones:")
    print("  -v, --verbose    - Salida detallada")
    print("  -q, --quiet      - Salida mínima")
    print("  -h, --help       - Mostrar esta ayuda")
    print("\nEjemplos:")
    print("  python test_runner.py")
    print("  python test_runner.py modelo")
    print("  python test_runner.py integracion -v")


def main():
    """Función principal del script."""
    # Parsear argumentos
    args = sys.argv[1:]
    categoria = 'all'
    verbosity = 2
    
    if '-h' in args or '--help' in args:
        mostrar_ayuda()
        return
    
    if '-q' in args or '--quiet' in args:
        verbosity = 0
        args = [arg for arg in args if arg not in ['-q', '--quiet']]
    
    if '-v' in args or '--verbose' in args:
        verbosity = 2
        args = [arg for arg in args if arg not in ['-v', '--verbose']]
    
    if args:
        categoria = args[0]
    
    # Crear suite según la categoría
    if categoria == 'all':
        suite = crear_suite_completa()
    else:
        suite = crear_suite_por_categoria(categoria)
        if suite.countTestCases() == 0:
            print(f"❌ Categoría '{categoria}' no reconocida.")
            print("Usa 'python test_runner.py --help' para ver las opciones disponibles.")
            return
    
    # Ejecutar pruebas
    exito = ejecutar_pruebas(suite, verbosity)
    
    # Salir con código apropiado
    sys.exit(0 if exito else 1)


if __name__ == '__main__':
    main()