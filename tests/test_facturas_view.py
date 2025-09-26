"""
Pruebas para la vista de facturas (FacturasView)
Prueban la interfaz de usuario y las interacciones
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QKeySequence

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from views.facturas_view import FacturasView
from controllers.factura_controller import FacturaController


class TestFacturasView(unittest.TestCase):
    """
    Pruebas para la vista de facturas
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración de clase - crear aplicación QT"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Mock del controlador para evitar conexiones reales
        with patch('views.facturas_view.FacturaController') as mock_controller_class:
            self.mock_controller = MagicMock()
            mock_controller_class.return_value = self.mock_controller
            
            # Configurar respuestas por defecto del mock
            self.mock_controller.listar_facturas.return_value = {
                'success': True,
                'data': [],
                'message': 'No hay facturas'
            }
            
            # Crear la vista
            self.view = FacturasView()
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if hasattr(self, 'view'):
            self.view.close()
            self.view.deleteLater()
    
    # ==================== PRUEBAS DE INICIALIZACIÓN ====================
    
    def test_inicializacion_vista(self):
        """Prueba la inicialización correcta de la vista"""
        # Verificar que la vista se creó correctamente
        self.assertIsInstance(self.view, FacturasView)
        self.assertIsNotNone(self.view.controller)
        self.assertIsNone(self.view.current_factura)
        self.assertEqual(self.view.facturas_data, [])
    
    def test_componentes_ui_creados(self):
        """Prueba que todos los componentes de UI se crearon"""
        # Verificar componentes principales
        self.assertTrue(hasattr(self.view, 'search_edit'))
        self.assertTrue(hasattr(self.view, 'estado_combo'))
        self.assertTrue(hasattr(self.view, 'fecha_desde'))
        self.assertTrue(hasattr(self.view, 'fecha_hasta'))
        self.assertTrue(hasattr(self.view, 'facturas_table'))
        self.assertTrue(hasattr(self.view, 'nueva_factura_btn'))
        self.assertTrue(hasattr(self.view, 'editar_factura_btn'))
        self.assertTrue(hasattr(self.view, 'confirmar_factura_btn'))
        self.assertTrue(hasattr(self.view, 'anular_factura_btn'))
        self.assertTrue(hasattr(self.view, 'actualizar_btn'))
    
    def test_timer_busqueda_configurado(self):
        """Prueba que el timer de búsqueda está configurado"""
        self.assertIsInstance(self.view.search_timer, QTimer)
        self.assertTrue(self.view.search_timer.isSingleShot())
    
    # ==================== PRUEBAS DE CARGA DE DATOS ====================
    
    def test_cargar_facturas_exitoso(self):
        """Prueba carga exitosa de facturas"""
        # Configurar datos de prueba
        facturas_test = [
            {
                'id': 1,
                'numero_factura': 'F-001',
                'cliente_nombre': 'Cliente Test',
                'fecha_factura': '2024-01-15',
                'total_factura': '$1,000.00',
                'estado_display': 'Confirmada'
            }
        ]
        
        self.mock_controller.listar_facturas.return_value = {
            'success': True,
            'data': facturas_test,
            'message': 'Facturas cargadas exitosamente'
        }
        
        # Ejecutar carga
        self.view.cargar_facturas()
        
        # Verificar que se cargaron los datos
        self.assertEqual(self.view.facturas_data, facturas_test)
        self.mock_controller.listar_facturas.assert_called()
    
    def test_cargar_facturas_error(self):
        """Prueba manejo de error al cargar facturas"""
        # Configurar error
        self.mock_controller.listar_facturas.return_value = {
            'success': False,
            'data': None,
            'message': 'Error de conexión'
        }
        
        # Mock del mensaje de error
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.cargar_facturas()
            
            # Verificar que se mostró el mensaje de error
            mock_mensaje.assert_called_with('Error al cargar facturas: Error de conexión', 'error')
    
    def test_cargar_facturas_vacia(self):
        """Prueba carga cuando no hay facturas"""
        # Configurar respuesta vacía
        self.mock_controller.listar_facturas.return_value = {
            'success': True,
            'data': [],
            'message': 'No hay facturas'
        }
        
        # Mock del mensaje informativo
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.cargar_facturas()
            
            # Verificar que se mostró el mensaje informativo
            mock_mensaje.assert_called_with('No se encontraron facturas con los filtros aplicados', 'info')
    
    # ==================== PRUEBAS DE BÚSQUEDA Y FILTROS ====================
    
    def test_busqueda_por_texto(self):
        """Prueba búsqueda por texto"""
        # Configurar datos de prueba
        self.view.facturas_data = [
            {'numero_factura': 'F-001', 'cliente_nombre': 'Cliente A'},
            {'numero_factura': 'F-002', 'cliente_nombre': 'Cliente B'},
            {'numero_factura': 'F-003', 'cliente_nombre': 'Cliente A'}
        ]
        
        # Simular búsqueda
        self.view.search_edit.setText('Cliente A')
        
        # Ejecutar búsqueda
        self.view.realizar_busqueda()
        
        # Verificar que se filtraron correctamente
        self.assertEqual(len(self.view.facturas_data), 2)
    
    def test_busqueda_por_numero_factura(self):
        """Prueba búsqueda por número de factura"""
        # Configurar datos de prueba
        self.view.facturas_data = [
            {'numero_factura': 'F-001', 'cliente_nombre': 'Cliente A'},
            {'numero_factura': 'F-002', 'cliente_nombre': 'Cliente B'}
        ]
        
        # Simular búsqueda
        self.view.search_edit.setText('F-001')
        
        # Ejecutar búsqueda
        self.view.realizar_busqueda()
        
        # Verificar resultado
        self.assertEqual(len(self.view.facturas_data), 1)
        self.assertEqual(self.view.facturas_data[0]['numero_factura'], 'F-001')
    
    def test_busqueda_sin_resultados(self):
        """Prueba búsqueda sin resultados"""
        # Configurar datos de prueba
        self.view.facturas_data = [
            {'numero_factura': 'F-001', 'cliente_nombre': 'Cliente A'}
        ]
        
        # Simular búsqueda sin resultados
        self.view.search_edit.setText('NoExiste')
        
        # Ejecutar búsqueda
        self.view.realizar_busqueda()
        
        # Verificar que no hay resultados
        self.assertEqual(len(self.view.facturas_data), 0)
    
    def test_limpiar_busqueda(self):
        """Prueba limpiar búsqueda"""
        # Configurar búsqueda inicial
        self.view.search_edit.setText('test')
        
        # Limpiar búsqueda
        self.view.search_edit.clear()
        
        # Mock para verificar que se recarga
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            self.view.realizar_busqueda()
            mock_cargar.assert_called_once()
    
    def test_timer_busqueda_delay(self):
        """Prueba que el timer de búsqueda tiene delay"""
        # Simular cambio de texto
        with patch.object(self.view.search_timer, 'start') as mock_start:
            with patch.object(self.view.search_timer, 'stop') as mock_stop:
                self.view.on_search_changed()
                
                # Verificar que se paró y reinició el timer
                mock_stop.assert_called_once()
                mock_start.assert_called_once_with(500)
    
    # ==================== PRUEBAS DE SELECCIÓN DE FACTURAS ====================
    
    def test_seleccion_factura(self):
        """Prueba selección de factura en la tabla"""
        # Configurar datos de prueba
        factura_test = {
            'id': 1,
            'numero_factura': 'F-001',
            'cliente_nombre': 'Cliente Test'
        }
        
        self.view.facturas_data = [factura_test]
        self.view.actualizar_tabla_facturas()
        
        # Simular selección
        self.view.facturas_table.selectRow(0)
        
        # Mock para cargar detalles
        with patch.object(self.view, 'cargar_detalles_factura') as mock_cargar_detalles:
            self.view.on_factura_selected()
            
            # Verificar que se cargaron los detalles
            mock_cargar_detalles.assert_called_with(1)
    
    def test_deseleccion_factura(self):
        """Prueba deselección de factura"""
        # Configurar factura seleccionada
        self.view.current_factura = {'id': 1}
        
        # Simular deselección
        self.view.facturas_table.clearSelection()
        self.view.on_factura_selected()
        
        # Verificar que se limpió la selección
        self.assertIsNone(self.view.current_factura)
    
    # ==================== PRUEBAS DE ACCIONES DE BOTONES ====================
    
    @patch('views.facturas_view.FacturaDialog')
    def test_nueva_factura(self, mock_dialog_class):
        """Prueba creación de nueva factura"""
        # Configurar mock del diálogo
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = 1  # QDialog.Accepted
        mock_dialog_class.return_value = mock_dialog
        
        # Mock para recargar facturas
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
                self.view.nueva_factura()
                
                # Verificar que se abrió el diálogo
                mock_dialog_class.assert_called_once_with(self.view)
                mock_dialog.exec_.assert_called_once()
                
                # Verificar que se recargaron las facturas
                mock_cargar.assert_called_once()
                mock_mensaje.assert_called_with('Factura creada exitosamente', 'success')
    
    @patch('views.facturas_view.FacturaDialog')
    def test_editar_factura_sin_seleccion(self, mock_dialog_class):
        """Prueba editar factura sin selección"""
        # No hay factura seleccionada
        self.view.current_factura = None
        
        # Intentar editar
        self.view.editar_factura()
        
        # Verificar que no se abrió el diálogo
        mock_dialog_class.assert_not_called()
    
    @patch('views.facturas_view.FacturaDialog')
    def test_editar_factura_con_seleccion(self, mock_dialog_class):
        """Prueba editar factura con selección"""
        # Configurar factura seleccionada
        factura_test = {'id': 1, 'numero_factura': 'F-001'}
        self.view.current_factura = factura_test
        
        # Configurar mock del diálogo
        mock_dialog = MagicMock()
        mock_dialog.exec_.return_value = 1  # QDialog.Accepted
        mock_dialog_class.return_value = mock_dialog
        
        # Mock para recargar facturas
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
                self.view.editar_factura()
                
                # Verificar que se abrió el diálogo con la factura
                mock_dialog_class.assert_called_once_with(self.view, factura_test)
                
                # Verificar que se recargaron las facturas
                mock_cargar.assert_called_once()
                mock_mensaje.assert_called_with('Factura actualizada exitosamente', 'success')
    
    def test_confirmar_factura_sin_seleccion(self):
        """Prueba confirmar factura sin selección"""
        # No hay factura seleccionada
        self.view.current_factura = None
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.confirmar_factura()
            
            # Verificar que se mostró mensaje de error
            mock_mensaje.assert_called_with('Debe seleccionar una factura', 'error')
    
    def test_confirmar_factura_exitoso(self):
        """Prueba confirmación exitosa de factura"""
        # Configurar factura seleccionada
        self.view.current_factura = {'id': 1, 'numero_factura': 'F-001'}
        
        # Configurar respuesta exitosa del controlador
        self.mock_controller.confirmar_factura.return_value = {
            'success': True,
            'message': 'Factura confirmada exitosamente'
        }
        
        # Mock para recargar y mostrar mensaje
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
                self.view.confirmar_factura()
                
                # Verificar llamadas
                self.mock_controller.confirmar_factura.assert_called_once_with(1)
                mock_cargar.assert_called_once()
                mock_mensaje.assert_called_with('Factura confirmada exitosamente', 'success')
    
    def test_confirmar_factura_error(self):
        """Prueba error al confirmar factura"""
        # Configurar factura seleccionada
        self.view.current_factura = {'id': 1}
        
        # Configurar respuesta de error del controlador
        self.mock_controller.confirmar_factura.return_value = {
            'success': False,
            'message': 'Error al confirmar factura'
        }
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.confirmar_factura()
            
            # Verificar que se mostró el mensaje de error
            mock_mensaje.assert_called_with('Error al confirmar factura', 'error')
    
    # ==================== PRUEBAS DE CARGA DE DETALLES ====================
    
    def test_cargar_detalles_factura_exitoso(self):
        """Prueba carga exitosa de detalles de factura"""
        # Configurar respuesta del controlador
        factura_detallada = {
            'numero_factura': 'F-001',
            'cliente_nombre': 'Cliente Test',
            'fecha_factura': '2024-01-15',
            'estado_display': 'Confirmada',
            'subtotal_factura': '$1,000.00',
            'impuestos_factura': '$190.00',
            'total_factura': '$1,190.00',
            'observaciones': 'Factura de prueba',
            'detalles': []
        }
        
        self.mock_controller.obtener_factura.return_value = {
            'success': True,
            'data': factura_detallada
        }
        
        # Mock para actualizar tabla de productos
        with patch.object(self.view, 'actualizar_tabla_productos') as mock_actualizar:
            self.view.cargar_detalles_factura(1)
            
            # Verificar que se actualizaron los labels
            self.assertEqual(self.view.numero_factura_label.text(), 'F-001')
            self.assertEqual(self.view.cliente_label.text(), 'Cliente Test')
            
            # Verificar que se actualizó la tabla de productos
            mock_actualizar.assert_called_once_with([])
    
    def test_cargar_detalles_factura_error(self):
        """Prueba error al cargar detalles de factura"""
        # Configurar respuesta de error
        self.mock_controller.obtener_factura.return_value = {
            'success': False,
            'message': 'Factura no encontrada'
        }
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.cargar_detalles_factura(999)
            
            # Verificar que se mostró el mensaje de error
            mock_mensaje.assert_called_with('Error al cargar detalles: Factura no encontrada', 'error')
    
    # ==================== PRUEBAS DE MENSAJES ====================
    
    @patch('views.facturas_view.QMessageBox')
    def test_mostrar_mensaje_error(self, mock_messagebox):
        """Prueba mostrar mensaje de error"""
        self.view.mostrar_mensaje('Error de prueba', 'error')
        
        # Verificar que se llamó el método correcto
        mock_messagebox.critical.assert_called_once_with(
            self.view, 'Error', 'Error de prueba'
        )
    
    @patch('views.facturas_view.QMessageBox')
    def test_mostrar_mensaje_exito(self, mock_messagebox):
        """Prueba mostrar mensaje de éxito"""
        self.view.mostrar_mensaje('Operación exitosa', 'success')
        
        # Verificar que se llamó el método correcto
        mock_messagebox.information.assert_called_once_with(
            self.view, 'Éxito', 'Operación exitosa'
        )
    
    @patch('views.facturas_view.QMessageBox')
    def test_mostrar_mensaje_info(self, mock_messagebox):
        """Prueba mostrar mensaje informativo"""
        self.view.mostrar_mensaje('Información de prueba', 'info')
        
        # Verificar que se llamó el método correcto
        mock_messagebox.information.assert_called_once_with(
            self.view, 'Información', 'Información de prueba'
        )
    
    # ==================== PRUEBAS DE ACTUALIZACIÓN DE TABLA ====================
    
    def test_actualizar_tabla_facturas(self):
        """Prueba actualización de tabla de facturas"""
        # Configurar datos de prueba
        facturas_test = [
            {
                'numero_factura': 'F-001',
                'cliente_nombre': 'Cliente A',
                'fecha_factura': '2024-01-15',
                'total_factura': '$1,000.00',
                'estado_display': 'Confirmada'
            },
            {
                'numero_factura': 'F-002',
                'cliente_nombre': 'Cliente B',
                'fecha_factura': '2024-01-16',
                'total_factura': '$500.00',
                'estado_display': 'Borrador'
            }
        ]
        
        self.view.facturas_data = facturas_test
        
        # Actualizar tabla
        self.view.actualizar_tabla_facturas()
        
        # Verificar que la tabla tiene las filas correctas
        self.assertEqual(self.view.facturas_table.rowCount(), 2)
        
        # Verificar contenido de la primera fila
        self.assertEqual(self.view.facturas_table.item(0, 0).text(), 'F-001')
        self.assertEqual(self.view.facturas_table.item(0, 1).text(), 'Cliente A')
    
    def test_actualizar_tabla_facturas_vacia(self):
        """Prueba actualización de tabla con datos vacíos"""
        self.view.facturas_data = []
        
        # Actualizar tabla
        self.view.actualizar_tabla_facturas()
        
        # Verificar que la tabla está vacía
        self.assertEqual(self.view.facturas_table.rowCount(), 0)
    
    # ==================== PRUEBAS DE REFRESH ====================
    
    def test_refresh_view(self):
        """Prueba refrescar vista"""
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            self.view.refresh_view()
            
            # Verificar que se recargaron las facturas
            mock_cargar.assert_called_once()
    
    # ==================== PRUEBAS DE FILTROS ====================
    
    def test_aplicar_filtros(self):
        """Prueba aplicación de filtros"""
        # Configurar filtros
        self.view.estado_combo.setCurrentText('Confirmada')
        
        # Mock para cargar facturas con filtros
        with patch.object(self.view, 'cargar_facturas') as mock_cargar:
            self.view.aplicar_filtros()
            
            # Verificar que se recargaron las facturas
            mock_cargar.assert_called_once()
    
    def test_get_filtros_actuales(self):
        """Prueba obtener filtros actuales"""
        # Configurar algunos filtros
        self.view.estado_combo.setCurrentText('Confirmada')
        
        # Obtener filtros
        filtros = self.view.get_filtros_actuales()
        
        # Verificar estructura de filtros
        self.assertIsInstance(filtros, dict)
        self.assertIn('estado', filtros)


if __name__ == '__main__':
    unittest.main()