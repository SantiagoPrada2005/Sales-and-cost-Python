"""
Pruebas para la vista de clientes (ClientesView)
"""
import unittest
import sys
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest
from views.clientes_view import ClientesView, ClienteDialog, HistorialComprasDialog


class TestClientesView(unittest.TestCase):
    """Pruebas para la clase ClientesView"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Mock del controlador
        self.mock_controller = Mock()
        
        # Crear la vista con el controlador mockeado
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            self.view = ClientesView()
        
        # Datos de prueba
        self.clientes_data = [
            {
                'id': 1,
                'tipo_identificacion': 'Cédula de Ciudadanía',
                'numero_identificacion': '12345678',
                'nombre': 'Juan Pérez',
                'email': 'juan@email.com',
                'telefono': '3001234567',
                'ciudad': 'Bogotá'
            },
            {
                'id': 2,
                'tipo_identificacion': 'NIT',
                'numero_identificacion': '900123456',
                'nombre': 'María García',
                'email': 'maria@email.com',
                'telefono': '3009876543',
                'ciudad': 'Medellín'
            }
        ]
        
        self.estadisticas_data = {
            'total_clientes': 2,
            'clientes_activos': 1,
            'nuevos_este_mes': 1
        }
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if hasattr(self, 'view'):
            self.view.close()
    
    # ========== Pruebas de inicialización ==========
    
    def test_inicializacion_vista(self):
        """Prueba que la vista se inicialice correctamente"""
        self.assertIsNotNone(self.view)
        self.assertIsNotNone(self.view.controller)
        self.assertIsNotNone(self.view.clientes_table)
        self.assertIsNotNone(self.view.search_edit)
        self.assertIsNotNone(self.view.search_timer)
        self.assertEqual(self.view.clientes_data, [])
        self.assertIsNone(self.view.cliente_seleccionado_actual)
    
    def test_configuracion_tabla(self):
        """Prueba que la tabla se configure correctamente"""
        table = self.view.clientes_table
        
        # Verificar número de columnas
        self.assertEqual(table.columnCount(), 7)
        
        # Verificar headers
        headers_esperados = ["ID", "Tipo ID", "Número ID", "Nombre", "Email", "Teléfono", "Ciudad"]
        for i, header in enumerate(headers_esperados):
            self.assertEqual(table.horizontalHeaderItem(i).text(), header)
        
        # Verificar que la columna ID esté oculta
        self.assertTrue(table.isColumnHidden(0))
    
    def test_configuracion_botones_iniciales(self):
        """Prueba que los botones se configuren correctamente al inicio"""
        # Botones que deben estar habilitados
        self.assertTrue(self.view.btn_nuevo.isEnabled())
        self.assertTrue(self.view.btn_actualizar.isEnabled())
        
        # Botones que deben estar deshabilitados (sin selección)
        self.assertFalse(self.view.btn_editar.isEnabled())
        self.assertFalse(self.view.btn_eliminar.isEnabled())
        self.assertFalse(self.view.btn_historial.isEnabled())
    
    # ========== Pruebas de carga de datos ==========
    
    def test_cargar_clientes_exitoso(self):
        """Prueba carga exitosa de clientes"""
        # Configurar mock
        self.mock_controller.listar_clientes.return_value = {
            'success': True,
            'data': self.clientes_data
        }
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'success': True,
            'data': self.estadisticas_data
        }
        
        # Ejecutar
        self.view.cargar_clientes()
        
        # Verificar
        self.mock_controller.listar_clientes.assert_called_once()
        self.assertEqual(self.view.clientes_data, self.clientes_data)
        self.assertEqual(self.view.clientes_table.rowCount(), 2)
    
    def test_cargar_clientes_error(self):
        """Prueba manejo de error al cargar clientes"""
        # Configurar mock
        self.mock_controller.listar_clientes.return_value = {
            'success': False,
            'message': 'Error de conexión'
        }
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.cargar_clientes()
            
            # Verificar que se muestre el mensaje de error
            mock_mensaje.assert_called_once_with(
                "Error", 
                "Error de conexión", 
                QMessageBox.Critical
            )
    
    def test_actualizar_tabla(self):
        """Prueba actualización de la tabla con datos"""
        # Configurar datos
        self.view.clientes_data = self.clientes_data
        
        # Ejecutar
        self.view.actualizar_tabla()
        
        # Verificar filas
        self.assertEqual(self.view.clientes_table.rowCount(), 2)
        
        # Verificar datos de la primera fila
        self.assertEqual(self.view.clientes_table.item(0, 0).text(), "1")  # ID
        self.assertEqual(self.view.clientes_table.item(0, 1).text(), "Cédula de Ciudadanía")
        self.assertEqual(self.view.clientes_table.item(0, 2).text(), "12345678")
        self.assertEqual(self.view.clientes_table.item(0, 3).text(), "Juan Pérez")
        self.assertEqual(self.view.clientes_table.item(0, 4).text(), "juan@email.com")
        self.assertEqual(self.view.clientes_table.item(0, 5).text(), "3001234567")
        self.assertEqual(self.view.clientes_table.item(0, 6).text(), "Bogotá")
    
    def test_actualizar_tabla_campos_vacios(self):
        """Prueba actualización de tabla con campos vacíos"""
        cliente_sin_datos = {
            'id': 1,
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'numero_identificacion': '12345678',
            'nombre': 'Juan Pérez',
            'email': '',
            'telefono': None,
            'ciudad': ''
        }
        
        self.view.clientes_data = [cliente_sin_datos]
        self.view.actualizar_tabla()
        
        # Verificar que los campos vacíos se muestren como "No especificado"
        self.assertEqual(self.view.clientes_table.item(0, 4).text(), "No especificado")  # Email
        self.assertEqual(self.view.clientes_table.item(0, 5).text(), "No especificado")  # Teléfono
        self.assertEqual(self.view.clientes_table.item(0, 6).text(), "No especificada")  # Ciudad
    
    def test_actualizar_estadisticas(self):
        """Prueba actualización de estadísticas"""
        # Configurar mock
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'success': True,
            'data': self.estadisticas_data
        }
        
        # Ejecutar
        self.view.actualizar_estadisticas()
        
        # Verificar
        self.assertEqual(self.view.total_clientes_label.text(), "2")
        self.assertEqual(self.view.clientes_activos_label.text(), "1")
        self.assertEqual(self.view.nuevos_mes_label.text(), "1")
    
    def test_actualizar_estadisticas_error(self):
        """Prueba manejo de error al actualizar estadísticas"""
        # Configurar mock
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'success': False,
            'message': 'Error al obtener estadísticas'
        }
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.actualizar_estadisticas()
            
            # Verificar que se muestre el mensaje de error
            mock_mensaje.assert_called_once_with(
                "Error", 
                "Error al obtener estadísticas", 
                QMessageBox.Warning
            )
    
    # ========== Pruebas de selección ==========
    
    def test_seleccion_cliente(self):
        """Prueba selección de cliente en la tabla"""
        # Configurar datos
        self.view.clientes_data = self.clientes_data
        self.view.actualizar_tabla()
        
        # Simular selección
        self.view.clientes_table.selectRow(0)
        self.view.on_selection_changed()
        
        # Verificar
        self.assertIsNotNone(self.view.cliente_seleccionado_actual)
        self.assertEqual(self.view.cliente_seleccionado_actual['id'], 1)
        self.assertTrue(self.view.btn_editar.isEnabled())
        self.assertTrue(self.view.btn_eliminar.isEnabled())
        self.assertTrue(self.view.btn_historial.isEnabled())
    
    def test_deseleccion_cliente(self):
        """Prueba deselección de cliente"""
        # Primero seleccionar
        self.view.clientes_data = self.clientes_data
        self.view.actualizar_tabla()
        self.view.clientes_table.selectRow(0)
        self.view.on_selection_changed()
        
        # Luego deseleccionar
        self.view.clientes_table.clearSelection()
        self.view.on_selection_changed()
        
        # Verificar
        self.assertIsNone(self.view.cliente_seleccionado_actual)
        self.assertFalse(self.view.btn_editar.isEnabled())
        self.assertFalse(self.view.btn_eliminar.isEnabled())
        self.assertFalse(self.view.btn_historial.isEnabled())
    
    def test_seleccionar_cliente_por_id(self):
        """Prueba selección de cliente por ID"""
        # Configurar datos
        self.view.clientes_data = self.clientes_data
        self.view.actualizar_tabla()
        
        # Seleccionar por ID
        self.view.seleccionar_cliente_por_id(2)
        
        # Verificar que se seleccionó la fila correcta
        selected_rows = self.view.clientes_table.selectionModel().selectedRows()
        self.assertEqual(len(selected_rows), 1)
        self.assertEqual(selected_rows[0].row(), 1)  # Segunda fila (índice 1)
    
    # ========== Pruebas de búsqueda ==========
    
    def test_busqueda_exitosa(self):
        """Prueba búsqueda exitosa de clientes"""
        # Configurar mock
        self.mock_controller.buscar_clientes.return_value = {
            'success': True,
            'data': [self.clientes_data[0]]  # Solo el primer cliente
        }
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'success': True,
            'data': {'total_clientes': 1, 'clientes_activos': 1, 'nuevos_este_mes': 0}
        }
        
        # Configurar término de búsqueda
        self.view.search_edit.setText("Juan")
        
        # Ejecutar búsqueda
        self.view.realizar_busqueda()
        
        # Verificar
        self.mock_controller.buscar_clientes.assert_called_once_with("Juan")
        self.assertEqual(len(self.view.clientes_data), 1)
        self.assertEqual(self.view.clientes_data[0]['nombre'], "Juan Pérez")
    
    def test_busqueda_vacia(self):
        """Prueba búsqueda con término vacío"""
        # Configurar mock para cargar todos los clientes
        self.mock_controller.listar_clientes.return_value = {
            'success': True,
            'data': self.clientes_data
        }
        self.mock_controller.obtener_estadisticas_generales.return_value = {
            'success': True,
            'data': self.estadisticas_data
        }
        
        # Configurar término vacío
        self.view.search_edit.setText("")
        
        # Ejecutar búsqueda
        self.view.realizar_busqueda()
        
        # Verificar que se carguen todos los clientes
        self.mock_controller.listar_clientes.assert_called_once()
        self.mock_controller.buscar_clientes.assert_not_called()
    
    def test_busqueda_error(self):
        """Prueba manejo de error en búsqueda"""
        # Configurar mock
        self.mock_controller.buscar_clientes.return_value = {
            'success': False,
            'message': 'Error en búsqueda'
        }
        
        # Configurar término de búsqueda
        self.view.search_edit.setText("test")
        
        # Mock del mensaje
        with patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            self.view.realizar_busqueda()
            
            # Verificar que se muestre el mensaje de error
            mock_mensaje.assert_called_once_with(
                "Error", 
                "Error en búsqueda", 
                QMessageBox.Warning
            )
    
    def test_delay_busqueda(self):
        """Prueba que la búsqueda tenga delay"""
        # Verificar que el timer esté configurado
        self.assertIsInstance(self.view.search_timer, QTimer)
        self.assertFalse(self.view.search_timer.isActive())
        
        # Simular cambio de texto
        self.view.on_search_text_changed()
        
        # Verificar que el timer se inicie
        self.assertTrue(self.view.search_timer.isActive())
    
    # ========== Pruebas de CRUD ==========
    
    @patch('views.clientes_view.ClienteDialog')
    def test_nuevo_cliente_exitoso(self, mock_dialog_class):
        """Prueba creación exitosa de nuevo cliente"""
        # Configurar mock del diálogo
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = QDialog.Accepted
        mock_dialog.get_cliente_data.return_value = {
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'numero_identificacion': '87654321',
            'nombre': 'Ana López',
            'email': 'ana@email.com',
            'telefono': '3005555555',
            'direccion': 'Calle 456',
            'ciudad': 'Cali',
            'fecha_nacimiento': '1995-05-15'
        }
        mock_dialog_class.return_value = mock_dialog
        
        # Configurar mock del controlador
        self.mock_controller.crear_cliente.return_value = {
            'success': True,
            'message': 'Cliente creado exitosamente'
        }
        
        # Mock de cargar_clientes y mostrar_mensaje
        with patch.object(self.view, 'cargar_clientes') as mock_cargar, \
             patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            
            # Ejecutar
            self.view.nuevo_cliente()
            
            # Verificar
            mock_dialog_class.assert_called_once_with(self.view)
            self.mock_controller.crear_cliente.assert_called_once()
            mock_mensaje.assert_called_once_with(
                "Éxito", 
                "Cliente creado exitosamente", 
                QMessageBox.Information
            )
            mock_cargar.assert_called_once()
    
    @patch('views.clientes_view.ClienteDialog')
    def test_nuevo_cliente_cancelado(self, mock_dialog_class):
        """Prueba cancelación de creación de cliente"""
        # Configurar mock del diálogo
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = QDialog.Rejected
        mock_dialog_class.return_value = mock_dialog
        
        # Ejecutar
        self.view.nuevo_cliente()
        
        # Verificar que no se llame al controlador
        self.mock_controller.crear_cliente.assert_not_called()
    
    @patch('views.clientes_view.ClienteDialog')
    def test_editar_cliente_exitoso(self, mock_dialog_class):
        """Prueba edición exitosa de cliente"""
        # Configurar cliente seleccionado
        self.view.cliente_seleccionado_actual = self.clientes_data[0]
        
        # Configurar mock del diálogo
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = QDialog.Accepted
        mock_dialog.get_cliente_data.return_value = {
            'nombre': 'Juan Pérez Actualizado',
            'email': 'juan.nuevo@email.com',
            'telefono': '3001111111',
            'direccion': 'Nueva dirección',
            'ciudad': 'Bogotá',
            'fecha_nacimiento': '1990-01-01'
        }
        mock_dialog_class.return_value = mock_dialog
        
        # Configurar mock del controlador
        self.mock_controller.actualizar_cliente.return_value = {
            'success': True,
            'message': 'Cliente actualizado exitosamente'
        }
        
        # Mock de cargar_clientes y mostrar_mensaje
        with patch.object(self.view, 'cargar_clientes') as mock_cargar, \
             patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            
            # Ejecutar
            self.view.editar_cliente()
            
            # Verificar
            mock_dialog_class.assert_called_once_with(self.view, self.clientes_data[0])
            self.mock_controller.actualizar_cliente.assert_called_once()
            mock_mensaje.assert_called_once_with(
                "Éxito", 
                "Cliente actualizado exitosamente", 
                QMessageBox.Information
            )
            mock_cargar.assert_called_once()
    
    def test_editar_cliente_sin_seleccion(self):
        """Prueba edición sin cliente seleccionado"""
        # No seleccionar cliente
        self.view.cliente_seleccionado_actual = None
        
        # Ejecutar
        self.view.editar_cliente()
        
        # Verificar que no se llame al controlador
        self.mock_controller.actualizar_cliente.assert_not_called()
    
    @patch('views.clientes_view.QMessageBox')
    def test_eliminar_cliente_confirmado(self, mock_msgbox_class):
        """Prueba eliminación de cliente confirmada"""
        # Configurar cliente seleccionado
        self.view.cliente_seleccionado_actual = self.clientes_data[0]
        
        # Configurar mock del mensaje de confirmación
        mock_msgbox_class.question.return_value = QMessageBox.Yes
        
        # Configurar mock del controlador
        self.mock_controller.eliminar_cliente.return_value = {
            'success': True,
            'message': 'Cliente eliminado exitosamente'
        }
        
        # Mock de cargar_clientes y mostrar_mensaje
        with patch.object(self.view, 'cargar_clientes') as mock_cargar, \
             patch.object(self.view, 'mostrar_mensaje') as mock_mensaje:
            
            # Ejecutar
            self.view.eliminar_cliente()
            
            # Verificar
            self.mock_controller.eliminar_cliente.assert_called_once_with(1)
            mock_mensaje.assert_called_once_with(
                "Éxito", 
                "Cliente eliminado exitosamente", 
                QMessageBox.Information
            )
            mock_cargar.assert_called_once()
    
    @patch('views.clientes_view.QMessageBox')
    def test_eliminar_cliente_cancelado(self, mock_msgbox_class):
        """Prueba eliminación de cliente cancelada"""
        # Configurar cliente seleccionado
        self.view.cliente_seleccionado_actual = self.clientes_data[0]
        
        # Configurar mock del mensaje de confirmación
        mock_msgbox_class.question.return_value = QMessageBox.No
        
        # Ejecutar
        self.view.eliminar_cliente()
        
        # Verificar que no se llame al controlador
        self.mock_controller.eliminar_cliente.assert_not_called()
    
    def test_eliminar_cliente_sin_seleccion(self):
        """Prueba eliminación sin cliente seleccionado"""
        # No seleccionar cliente
        self.view.cliente_seleccionado_actual = None
        
        # Ejecutar
        self.view.eliminar_cliente()
        
        # Verificar que no se llame al controlador
        self.mock_controller.eliminar_cliente.assert_not_called()
    
    # ========== Pruebas de historial ==========
    
    @patch('views.clientes_view.HistorialComprasDialog')
    def test_ver_historial(self, mock_dialog_class):
        """Prueba visualización de historial de compras"""
        # Configurar cliente seleccionado
        self.view.cliente_seleccionado_actual = self.clientes_data[0]
        
        # Configurar mock del diálogo
        mock_dialog = Mock()
        mock_dialog_class.return_value = mock_dialog
        
        # Ejecutar
        self.view.ver_historial()
        
        # Verificar
        mock_dialog_class.assert_called_once_with(self.view, self.clientes_data[0])
        mock_dialog.exec_.assert_called_once()
    
    def test_ver_historial_sin_seleccion(self):
        """Prueba visualización de historial sin cliente seleccionado"""
        # No seleccionar cliente
        self.view.cliente_seleccionado_actual = None
        
        # Ejecutar
        self.view.ver_historial()
        
        # No debe hacer nada (no hay forma directa de verificar esto)
        # La prueba pasa si no hay excepciones
    
    # ========== Pruebas de utilidades ==========
    
    def test_mostrar_mensaje(self):
        """Prueba mostrar mensaje al usuario"""
        with patch('views.clientes_view.QMessageBox') as mock_msgbox_class:
            mock_msgbox = Mock()
            mock_msgbox_class.return_value = mock_msgbox
            
            # Ejecutar
            self.view.mostrar_mensaje("Título", "Mensaje", QMessageBox.Information)
            
            # Verificar
            mock_msgbox.setWindowTitle.assert_called_once_with("Título")
            mock_msgbox.setText.assert_called_once_with("Mensaje")
            mock_msgbox.setIcon.assert_called_once_with(QMessageBox.Information)
            mock_msgbox.exec_.assert_called_once()
    
    def test_obtener_cliente_seleccionado(self):
        """Prueba obtener cliente seleccionado"""
        # Sin selección
        self.assertIsNone(self.view.obtener_cliente_seleccionado())
        
        # Con selección
        self.view.cliente_seleccionado_actual = self.clientes_data[0]
        self.assertEqual(self.view.obtener_cliente_seleccionado(), self.clientes_data[0])
    
    # ========== Pruebas de señales ==========
    
    def test_emision_senal_cliente_seleccionado(self):
        """Prueba emisión de señal cuando se selecciona un cliente"""
        # Configurar datos
        self.view.clientes_data = self.clientes_data
        self.view.actualizar_tabla()
        
        # Mock de la señal
        with patch.object(self.view.cliente_seleccionado, 'emit') as mock_emit:
            # Simular selección
            self.view.clientes_table.selectRow(0)
            self.view.on_selection_changed()
            
            # Verificar que se emita la señal
            mock_emit.assert_called_once_with(self.clientes_data[0])


class TestClienteDialog(unittest.TestCase):
    """Pruebas para la clase ClienteDialog"""
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todas las pruebas"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_controller = Mock()
        
        # Datos de prueba
        self.cliente_data = {
            'id': 1,
            'tipo_identificacion': 'Cédula de Ciudadanía',
            'numero_identificacion': '12345678',
            'nombre': 'Juan Pérez',
            'email': 'juan@email.com',
            'telefono': '3001234567',
            'direccion': 'Calle 123',
            'ciudad': 'Bogotá',
            'fecha_nacimiento': '1990-01-01'
        }
    
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if hasattr(self, 'dialog'):
            self.dialog.close()
    
    def test_inicializacion_nuevo_cliente(self):
        """Prueba inicialización para nuevo cliente"""
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            self.dialog = ClienteDialog()
            
            self.assertFalse(self.dialog.is_edit_mode)
            self.assertIsNone(self.dialog.cliente)
            self.assertEqual(self.dialog.windowTitle(), "Nuevo Cliente")
    
    def test_inicializacion_editar_cliente(self):
        """Prueba inicialización para editar cliente"""
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            self.dialog = ClienteDialog(cliente=self.cliente_data)
            
            self.assertTrue(self.dialog.is_edit_mode)
            self.assertEqual(self.dialog.cliente, self.cliente_data)
            self.assertEqual(self.dialog.windowTitle(), "Editar Cliente")
    
    def test_get_cliente_data(self):
        """Prueba obtención de datos del formulario"""
        with patch('views.clientes_view.ClienteController', return_value=self.mock_controller):
            self.dialog = ClienteDialog()
            
            # Configurar datos en el formulario
            self.dialog.tipo_identificacion_combo.setCurrentText("Cédula de Ciudadanía")
            self.dialog.identificacion_edit.setText("12345678")
            self.dialog.nombre_edit.setText("Juan Pérez")
            self.dialog.email_edit.setText("juan@email.com")
            self.dialog.telefono_edit.setText("3001234567")
            self.dialog.direccion_edit.setPlainText("Calle 123")
            self.dialog.ciudad_edit.setText("Bogotá")
            
            # Obtener datos
            data = self.dialog.get_cliente_data()
            
            # Verificar
            self.assertEqual(data['tipo_identificacion'], "Cédula de Ciudadanía")
            self.assertEqual(data['numero_identificacion'], "12345678")
            self.assertEqual(data['nombre'], "Juan Pérez")
            self.assertEqual(data['email'], "juan@email.com")
            self.assertEqual(data['telefono'], "3001234567")
            self.assertEqual(data['direccion'], "Calle 123")
            self.assertEqual(data['ciudad'], "Bogotá")


if __name__ == '__main__':
    unittest.main()