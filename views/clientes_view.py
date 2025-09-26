"""
Vista para el módulo de Clientes
Interfaz gráfica usando PyQt5 para gestionar clientes
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QMessageBox, 
                             QDialog, QFormLayout, QDialogButtonBox, 
                             QHeaderView, QAbstractItemView, QGroupBox,
                             QSpacerItem, QSizePolicy, QFrame, QComboBox,
                             QDateEdit, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from controllers.cliente_controller import ClienteController
import logging

logger = logging.getLogger(__name__)

class ClienteDialog(QDialog):
    """
    Dialog para crear/editar clientes
    """
    
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente
        self.is_edit_mode = cliente is not None
        self.controller = ClienteController()
        
        self.setWindowTitle("Editar Cliente" if self.is_edit_mode else "Nuevo Cliente")
        self.setModal(True)
        self.setFixedSize(600, 500)
        
        self.setup_ui()
        self.setup_connections()
        
        if self.is_edit_mode:
            self.load_cliente_data()
    
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Tipo de identificación
        self.tipo_identificacion_combo = QComboBox()
        self.tipo_identificacion_combo.addItems([
            "Cédula de Ciudadanía",
            "Cédula de Extranjería", 
            "NIT",
            "Pasaporte",
            "Tarjeta de Identidad"
        ])
        form_layout.addRow("Tipo de Identificación*:", self.tipo_identificacion_combo)
        
        # Número de identificación
        self.identificacion_edit = QLineEdit()
        self.identificacion_edit.setMaxLength(20)
        self.identificacion_edit.setPlaceholderText("Ej: 12345678")
        form_layout.addRow("Número de Identificación*:", self.identificacion_edit)
        
        # Nombre
        self.nombre_edit = QLineEdit()
        self.nombre_edit.setMaxLength(100)
        self.nombre_edit.setPlaceholderText("Nombre completo del cliente")
        form_layout.addRow("Nombre*:", self.nombre_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setMaxLength(100)
        self.email_edit.setPlaceholderText("cliente@ejemplo.com")
        form_layout.addRow("Email:", self.email_edit)
        
        # Teléfono
        self.telefono_edit = QLineEdit()
        self.telefono_edit.setMaxLength(20)
        self.telefono_edit.setPlaceholderText("Ej: +57 300 123 4567")
        form_layout.addRow("Teléfono:", self.telefono_edit)
        
        # Dirección
        self.direccion_edit = QTextEdit()
        self.direccion_edit.setMaximumHeight(80)
        self.direccion_edit.setPlaceholderText("Dirección completa del cliente")
        form_layout.addRow("Dirección:", self.direccion_edit)
        
        # Ciudad
        self.ciudad_edit = QLineEdit()
        self.ciudad_edit.setMaxLength(50)
        self.ciudad_edit.setPlaceholderText("Ciudad de residencia")
        form_layout.addRow("Ciudad:", self.ciudad_edit)
        
        # Fecha de nacimiento
        self.fecha_nacimiento_edit = QDateEdit()
        self.fecha_nacimiento_edit.setDate(QDate.currentDate().addYears(-30))
        self.fecha_nacimiento_edit.setCalendarPopup(True)
        self.fecha_nacimiento_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Fecha de Nacimiento:", self.fecha_nacimiento_edit)
        
        layout.addLayout(form_layout)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Guardar")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        layout.addWidget(button_box)
        
        # Conectar botones
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Validación en tiempo real
        self.identificacion_edit.textChanged.connect(self.validar_identificacion)
        self.email_edit.textChanged.connect(self.validar_email)
    
    def validar_identificacion(self):
        """Validar número de identificación"""
        texto = self.identificacion_edit.text()
        if texto and not texto.replace('-', '').replace(' ', '').isdigit():
            self.identificacion_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.identificacion_edit.setStyleSheet("")
    
    def validar_email(self):
        """Validar formato de email"""
        email = self.email_edit.text()
        if email and '@' not in email:
            self.email_edit.setStyleSheet("border: 1px solid red;")
        else:
            self.email_edit.setStyleSheet("")
    
    def load_cliente_data(self):
        """Cargar datos del cliente para edición"""
        if self.cliente:
            self.tipo_identificacion_combo.setCurrentText(self.cliente.get('tipo_identificacion', ''))
            self.identificacion_edit.setText(self.cliente.get('numero_identificacion', ''))
            self.nombre_edit.setText(self.cliente.get('nombre', ''))
            self.email_edit.setText(self.cliente.get('email', ''))
            self.telefono_edit.setText(self.cliente.get('telefono', ''))
            self.direccion_edit.setPlainText(self.cliente.get('direccion', ''))
            self.ciudad_edit.setText(self.cliente.get('ciudad', ''))
            
            if self.cliente.get('fecha_nacimiento'):
                fecha = QDate.fromString(self.cliente['fecha_nacimiento'], "yyyy-MM-dd")
                self.fecha_nacimiento_edit.setDate(fecha)
    
    def get_cliente_data(self):
        """Obtener datos del formulario"""
        return {
            'tipo_identificacion': self.tipo_identificacion_combo.currentText(),
            'numero_identificacion': self.identificacion_edit.text().strip(),
            'nombre': self.nombre_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'telefono': self.telefono_edit.text().strip(),
            'direccion': self.direccion_edit.toPlainText().strip(),
            'ciudad': self.ciudad_edit.text().strip(),
            'fecha_nacimiento': self.fecha_nacimiento_edit.date().toString("yyyy-MM-dd")
        }
    
    def accept(self):
        """Validar y aceptar el diálogo"""
        data = self.get_cliente_data()
        
        # Validaciones básicas
        if not data['numero_identificacion']:
            QMessageBox.warning(self, "Error", "El número de identificación es obligatorio")
            return
        
        if not data['nombre']:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        
        super().accept()


class HistorialComprasDialog(QDialog):
    """
    Dialog para mostrar el historial de compras de un cliente
    """
    
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente
        self.controller = ClienteController()
        
        self.setWindowTitle(f"Historial de Compras - {cliente['nombre']}")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.cargar_historial()
    
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Información del cliente
        info_group = QGroupBox("Información del Cliente")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Nombre:"), 0, 0)
        info_layout.addWidget(QLabel(self.cliente['nombre']), 0, 1)
        info_layout.addWidget(QLabel("Identificación:"), 0, 2)
        info_layout.addWidget(QLabel(self.cliente['numero_identificacion']), 0, 3)
        
        layout.addWidget(info_group)
        
        # Tabla de historial
        self.historial_table = QTableWidget()
        self.historial_table.setColumnCount(5)
        self.historial_table.setHorizontalHeaderLabels([
            "Fecha", "Factura", "Total", "Estado", "Productos"
        ])
        
        # Configurar tabla
        header = self.historial_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.historial_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.historial_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.historial_table)
        
        # Estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QGridLayout(stats_group)
        
        self.total_compras_label = QLabel("0")
        self.total_gastado_label = QLabel("$0.00")
        self.promedio_compra_label = QLabel("$0.00")
        
        stats_layout.addWidget(QLabel("Total de Compras:"), 0, 0)
        stats_layout.addWidget(self.total_compras_label, 0, 1)
        stats_layout.addWidget(QLabel("Total Gastado:"), 0, 2)
        stats_layout.addWidget(self.total_gastado_label, 0, 3)
        stats_layout.addWidget(QLabel("Promedio por Compra:"), 0, 4)
        stats_layout.addWidget(self.promedio_compra_label, 0, 5)
        
        layout.addWidget(stats_group)
        
        # Botón cerrar
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText("Cerrar")
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def cargar_historial(self):
        """Cargar historial de compras del cliente"""
        resultado = self.controller.obtener_historial_compras(self.cliente['id'])
        
        if resultado['success']:
            historial = resultado['data']['historial']
            estadisticas = resultado['data']['estadisticas']
            
            # Actualizar tabla
            self.historial_table.setRowCount(len(historial))
            
            for row, compra in enumerate(historial):
                self.historial_table.setItem(row, 0, QTableWidgetItem(compra['fecha']))
                self.historial_table.setItem(row, 1, QTableWidgetItem(compra['numero_factura']))
                
                total_item = QTableWidgetItem(compra['total_formatted'])
                total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.historial_table.setItem(row, 2, total_item)
                
                self.historial_table.setItem(row, 3, QTableWidgetItem(compra['estado']))
                self.historial_table.setItem(row, 4, QTableWidgetItem(str(compra['cantidad_productos'])))
            
            # Actualizar estadísticas
            self.total_compras_label.setText(str(estadisticas['total_compras']))
            self.total_gastado_label.setText(estadisticas['total_gastado_formatted'])
            self.promedio_compra_label.setText(estadisticas['promedio_compra_formatted'])
        else:
            QMessageBox.warning(self, "Error", resultado['message'])


class ClientesView(QWidget):
    """
    Vista principal para gestión de clientes
    """
    
    # Señales
    cliente_seleccionado = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = ClienteController()
        self.clientes_data = []
        self.cliente_seleccionado_actual = None
        
        # Timer para búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.realizar_busqueda)
        
        self.setup_ui()
        self.setup_connections()
        self.cargar_clientes()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Gestión de Clientes")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        # Botones de acción
        self.btn_nuevo = QPushButton("Nuevo Cliente")
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setEnabled(False)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ec7063;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.btn_historial = QPushButton("Ver Historial")
        self.btn_historial.setEnabled(False)
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #af7ac5;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f4d03f;
            }
        """)
        
        toolbar_layout.addWidget(self.btn_nuevo)
        toolbar_layout.addWidget(self.btn_editar)
        toolbar_layout.addWidget(self.btn_eliminar)
        toolbar_layout.addWidget(self.btn_historial)
        toolbar_layout.addWidget(self.btn_actualizar)
        
        # Espaciador
        toolbar_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Búsqueda
        search_label = QLabel("Buscar:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre, identificación o email...")
        self.search_edit.setMaximumWidth(300)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_edit)
        
        layout.addLayout(toolbar_layout)
        
        # Tabla de clientes
        self.setup_table()
        layout.addWidget(self.clientes_table)
        
        # Panel de estadísticas
        self.setup_stats_panel()
        layout.addWidget(self.stats_group)
    
    def setup_table(self):
        """Configurar la tabla de clientes"""
        self.clientes_table = QTableWidget()
        self.clientes_table.setColumnCount(8)
        self.clientes_table.setHorizontalHeaderLabels([
            "ID", "Tipo ID", "Identificación", "Nombre", 
            "Email", "Teléfono", "Ciudad", "Fecha Registro"
        ])
        
        # Ocultar columna ID
        self.clientes_table.setColumnHidden(0, True)
        
        # Configurar encabezados
        header = self.clientes_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        # Configurar comportamiento
        self.clientes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.clientes_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.clientes_table.setAlternatingRowColors(True)
        self.clientes_table.setSortingEnabled(True)
        
        # Estilos
        self.clientes_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
    
    def setup_stats_panel(self):
        """Configurar panel de estadísticas"""
        self.stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout(self.stats_group)
        
        # Total de clientes
        self.total_clientes_label = QLabel("0")
        self.total_clientes_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_clientes_label.setStyleSheet("color: #2c3e50;")
        
        # Clientes activos (con compras)
        self.clientes_activos_label = QLabel("0")
        self.clientes_activos_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.clientes_activos_label.setStyleSheet("color: #27ae60;")
        
        # Nuevos este mes
        self.nuevos_mes_label = QLabel("0")
        self.nuevos_mes_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.nuevos_mes_label.setStyleSheet("color: #3498db;")
        
        stats_layout.addWidget(QLabel("Total de Clientes:"))
        stats_layout.addWidget(self.total_clientes_label)
        stats_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        stats_layout.addWidget(QLabel("Clientes Activos:"))
        stats_layout.addWidget(self.clientes_activos_label)
        stats_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        stats_layout.addWidget(QLabel("Nuevos este Mes:"))
        stats_layout.addWidget(self.nuevos_mes_label)
        
        stats_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones
        self.btn_nuevo.clicked.connect(self.nuevo_cliente)
        self.btn_editar.clicked.connect(self.editar_cliente)
        self.btn_eliminar.clicked.connect(self.eliminar_cliente)
        self.btn_historial.clicked.connect(self.ver_historial)
        self.btn_actualizar.clicked.connect(self.cargar_clientes)
        
        # Tabla
        self.clientes_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.clientes_table.itemDoubleClicked.connect(self.editar_cliente)
        
        # Búsqueda con delay
        self.search_edit.textChanged.connect(self.on_search_text_changed)
    
    def on_search_text_changed(self):
        """Manejar cambio en el texto de búsqueda"""
        self.search_timer.stop()
        self.search_timer.start(500)  # Delay de 500ms
    
    def realizar_busqueda(self):
        """Realizar búsqueda de clientes"""
        termino = self.search_edit.text().strip()
        
        if termino:
            resultado = self.controller.buscar_clientes(termino)
            if resultado['success']:
                self.clientes_data = resultado['data']
                self.actualizar_tabla()
                self.actualizar_estadisticas()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Warning)
        else:
            self.cargar_clientes()
    
    def cargar_clientes(self):
        """Cargar todos los clientes"""
        resultado = self.controller.listar_clientes()
        
        if resultado['success']:
            self.clientes_data = resultado['data']
            self.actualizar_tabla()
            self.actualizar_estadisticas()
        else:
            self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def actualizar_tabla(self):
        """Actualizar la tabla con los datos de clientes"""
        self.clientes_table.setRowCount(len(self.clientes_data))
        
        for row, cliente in enumerate(self.clientes_data):
            # ID (oculto)
            self.clientes_table.setItem(row, 0, QTableWidgetItem(str(cliente['id'])))
            
            # Tipo de identificación
            self.clientes_table.setItem(row, 1, QTableWidgetItem(cliente['tipo_identificacion']))
            
            # Número de identificación
            self.clientes_table.setItem(row, 2, QTableWidgetItem(cliente['numero_identificacion']))
            
            # Nombre
            self.clientes_table.setItem(row, 3, QTableWidgetItem(cliente['nombre']))
            
            # Email
            email = cliente.get('email', '') or 'No especificado'
            self.clientes_table.setItem(row, 4, QTableWidgetItem(email))
            
            # Teléfono
            telefono = cliente.get('telefono', '') or 'No especificado'
            self.clientes_table.setItem(row, 5, QTableWidgetItem(telefono))
            
            # Ciudad
            ciudad = cliente.get('ciudad', '') or 'No especificada'
            self.clientes_table.setItem(row, 6, QTableWidgetItem(ciudad))
            
            # Fecha de registro
            fecha_registro = cliente.get('fecha_registro', '')
            if fecha_registro:
                # Formatear fecha
                from datetime import datetime
                try:
                    fecha_obj = datetime.strptime(fecha_registro, "%Y-%m-%d %H:%M:%S")
                    fecha_formateada = fecha_obj.strftime("%d/%m/%Y")
                except:
                    fecha_formateada = fecha_registro
            else:
                fecha_formateada = 'No disponible'
            
            self.clientes_table.setItem(row, 7, QTableWidgetItem(fecha_formateada))
    
    def actualizar_estadisticas(self):
        """Actualizar panel de estadísticas"""
        resultado = self.controller.obtener_estadisticas_generales()
        
        if resultado['success']:
            stats = resultado['data']
            self.total_clientes_label.setText(str(stats['total_clientes']))
            self.clientes_activos_label.setText(str(stats['clientes_activos']))
            self.nuevos_mes_label.setText(str(stats['nuevos_este_mes']))
        else:
            # Estadísticas básicas basadas en datos actuales
            total = len(self.clientes_data)
            self.total_clientes_label.setText(str(total))
            self.clientes_activos_label.setText("N/A")
            self.nuevos_mes_label.setText("N/A")
    
    def on_selection_changed(self):
        """Manejar cambio de selección en la tabla"""
        selected_rows = self.clientes_table.selectionModel().selectedRows()
        
        if selected_rows:
            row = selected_rows[0].row()
            cliente_id = int(self.clientes_table.item(row, 0).text())
            
            # Buscar cliente en los datos
            self.cliente_seleccionado_actual = None
            for cliente in self.clientes_data:
                if cliente['id'] == cliente_id:
                    self.cliente_seleccionado_actual = cliente
                    break
            
            # Habilitar botones
            self.btn_editar.setEnabled(True)
            self.btn_eliminar.setEnabled(True)
            self.btn_historial.setEnabled(True)
            
            # Emitir señal
            if self.cliente_seleccionado_actual:
                self.cliente_seleccionado.emit(self.cliente_seleccionado_actual)
        else:
            self.cliente_seleccionado_actual = None
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            self.btn_historial.setEnabled(False)
    
    def nuevo_cliente(self):
        """Crear nuevo cliente"""
        dialog = ClienteDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_cliente_data()
            
            resultado = self.controller.crear_cliente(
                data['tipo_identificacion'],
                data['numero_identificacion'],
                data['nombre'],
                data['email'],
                data['telefono'],
                data['direccion'],
                data['ciudad'],
                data['fecha_nacimiento']
            )
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_clientes()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def editar_cliente(self):
        """Editar cliente seleccionado"""
        if not self.cliente_seleccionado_actual:
            return
        
        dialog = ClienteDialog(self, self.cliente_seleccionado_actual)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_cliente_data()
            
            resultado = self.controller.actualizar_cliente(
                self.cliente_seleccionado_actual['id'],
                nombre=data['nombre'],
                email=data['email'],
                telefono=data['telefono'],
                direccion=data['direccion'],
                ciudad=data['ciudad'],
                fecha_nacimiento=data['fecha_nacimiento']
            )
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_clientes()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def eliminar_cliente(self):
        """Eliminar cliente seleccionado"""
        if not self.cliente_seleccionado_actual:
            return
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el cliente '{self.cliente_seleccionado_actual['nombre']}'?\n\n"
            f"Esta acción no se puede deshacer y eliminará también todo su historial de compras.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            resultado = self.controller.eliminar_cliente(self.cliente_seleccionado_actual['id'])
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_clientes()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def ver_historial(self):
        """Ver historial de compras del cliente seleccionado"""
        if not self.cliente_seleccionado_actual:
            return
        
        dialog = HistorialComprasDialog(self, self.cliente_seleccionado_actual)
        dialog.exec_()
    
    def mostrar_mensaje(self, titulo, mensaje, tipo=QMessageBox.Information):
        """Mostrar mensaje al usuario"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(tipo)
        msg_box.exec_()
    
    def obtener_cliente_seleccionado(self):
        """Obtener el cliente actualmente seleccionado"""
        return self.cliente_seleccionado_actual
    
    def seleccionar_cliente_por_id(self, cliente_id):
        """Seleccionar un cliente por su ID"""
        for row in range(self.clientes_table.rowCount()):
            if int(self.clientes_table.item(row, 0).text()) == cliente_id:
                self.clientes_table.selectRow(row)
                break