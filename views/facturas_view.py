"""
Vista para el módulo de Facturas
Interfaz gráfica usando PyQt5 para gestionar facturas
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QMessageBox, 
                             QDialog, QFormLayout, QDialogButtonBox, 
                             QHeaderView, QAbstractItemView, QGroupBox,
                             QSpacerItem, QSizePolicy, QFrame, QComboBox,
                             QDateEdit, QSpinBox, QDoubleSpinBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap
from controllers.factura_controller import FacturaController
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class FacturasView(QWidget):
    """
    Vista principal para gestionar facturas
    """
    
    # Señales
    factura_seleccionada = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = FacturaController()
        self.current_factura = None
        self.facturas_data = []
        
        # Timer para búsqueda
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.realizar_busqueda)
        
        self.setup_ui()
        self.setup_connections()
        self.cargar_facturas()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Gestión de Facturas")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Panel de controles
        controls_frame = self.create_controls_panel()
        layout.addWidget(controls_frame)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo - Lista de facturas
        left_panel = self.create_facturas_panel()
        main_splitter.addWidget(left_panel)
        
        # Panel derecho - Detalles de factura
        right_panel = self.create_detalles_panel()
        main_splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([600, 400])
        layout.addWidget(main_splitter)
        
        # Panel de estadísticas
        stats_panel = self.create_estadisticas_panel()
        layout.addWidget(stats_panel)
    
    def create_controls_panel(self):
        """Crear panel de controles superiores"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Búsqueda
        search_group = QGroupBox("Búsqueda")
        search_layout = QHBoxLayout(search_group)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por número de factura o cliente...")
        self.search_edit.setMinimumWidth(250)
        search_layout.addWidget(self.search_edit)
        
        # Filtros
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)
        
        # Estado
        filter_layout.addWidget(QLabel("Estado:"))
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["Todos", "Borrador", "Confirmada", "Pagada", "Anulada"])
        filter_layout.addWidget(self.estado_combo)
        
        # Fecha desde
        filter_layout.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setDate(QDate.currentDate().addDays(-30))
        self.fecha_desde.setCalendarPopup(True)
        filter_layout.addWidget(self.fecha_desde)
        
        # Fecha hasta
        filter_layout.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setDate(QDate.currentDate())
        self.fecha_hasta.setCalendarPopup(True)
        filter_layout.addWidget(self.fecha_hasta)
        
        # Botones de acción
        actions_group = QGroupBox("Acciones")
        actions_layout = QHBoxLayout(actions_group)
        
        self.nueva_factura_btn = QPushButton("Nueva Factura")
        self.nueva_factura_btn.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        actions_layout.addWidget(self.nueva_factura_btn)
        
        self.editar_factura_btn = QPushButton("Editar")
        self.editar_factura_btn.setEnabled(False)
        actions_layout.addWidget(self.editar_factura_btn)
        
        self.confirmar_factura_btn = QPushButton("Confirmar")
        self.confirmar_factura_btn.setEnabled(False)
        actions_layout.addWidget(self.confirmar_factura_btn)
        
        self.anular_factura_btn = QPushButton("Anular")
        self.anular_factura_btn.setEnabled(False)
        self.anular_factura_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        actions_layout.addWidget(self.anular_factura_btn)
        
        self.actualizar_btn = QPushButton("Actualizar")
        actions_layout.addWidget(self.actualizar_btn)
        
        # Agregar grupos al layout principal
        layout.addWidget(search_group)
        layout.addWidget(filter_group)
        layout.addWidget(actions_group)
        layout.addStretch()
        
        return frame
    
    def create_facturas_panel(self):
        """Crear panel de lista de facturas"""
        panel = QGroupBox("Lista de Facturas")
        layout = QVBoxLayout(panel)
        
        # Tabla de facturas
        self.facturas_table = QTableWidget()
        self.setup_facturas_table()
        layout.addWidget(self.facturas_table)
        
        return panel
    
    def setup_facturas_table(self):
        """Configurar tabla de facturas"""
        self.facturas_table.setColumnCount(6)
        headers = ["Número", "Cliente", "Fecha", "Total", "Estado", "ID"]
        self.facturas_table.setHorizontalHeaderLabels(headers)
        
        # Configurar propiedades de la tabla
        self.facturas_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.facturas_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.facturas_table.setAlternatingRowColors(True)
        self.facturas_table.setSortingEnabled(True)
        
        # Configurar ancho de columnas
        header = self.facturas_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Número
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Cliente
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Total
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Estado
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # ID (oculta)
        self.facturas_table.setColumnWidth(5, 0)
        self.facturas_table.setColumnHidden(5, True)
        
        # Estilo de la tabla
        self.facturas_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QTableWidget::item:selected {
                background-color: #007BFF;
                color: white;
            }
            QHeaderView::section {
                background-color: #495057;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def create_detalles_panel(self):
        """Crear panel de detalles de factura"""
        panel = QGroupBox("Detalles de Factura")
        layout = QVBoxLayout(panel)
        
        # Tabs para organizar información
        self.detalles_tabs = QTabWidget()
        
        # Tab 1: Información general
        info_tab = QWidget()
        info_layout = QFormLayout(info_tab)
        
        self.numero_factura_label = QLabel("-")
        self.numero_factura_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addRow("Número de Factura:", self.numero_factura_label)
        
        self.cliente_label = QLabel("-")
        info_layout.addRow("Cliente:", self.cliente_label)
        
        self.fecha_label = QLabel("-")
        info_layout.addRow("Fecha:", self.fecha_label)
        
        self.estado_label = QLabel("-")
        info_layout.addRow("Estado:", self.estado_label)
        
        self.subtotal_label = QLabel("-")
        info_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.impuestos_label = QLabel("-")
        info_layout.addRow("Impuestos:", self.impuestos_label)
        
        self.total_label = QLabel("-")
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_label.setStyleSheet("color: #28A745;")
        info_layout.addRow("Total:", self.total_label)
        
        self.observaciones_label = QLabel("-")
        self.observaciones_label.setWordWrap(True)
        info_layout.addRow("Observaciones:", self.observaciones_label)
        
        self.detalles_tabs.addTab(info_tab, "Información General")
        
        # Tab 2: Productos
        productos_tab = QWidget()
        productos_layout = QVBoxLayout(productos_tab)
        
        self.productos_table = QTableWidget()
        self.setup_productos_table()
        productos_layout.addWidget(self.productos_table)
        
        self.detalles_tabs.addTab(productos_tab, "Productos")
        
        layout.addWidget(self.detalles_tabs)
        
        return panel
    
    def setup_productos_table(self):
        """Configurar tabla de productos de la factura"""
        self.productos_table.setColumnCount(5)
        headers = ["Código", "Producto", "Cantidad", "Precio Unit.", "Subtotal"]
        self.productos_table.setHorizontalHeaderLabels(headers)
        
        # Configurar propiedades
        self.productos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.productos_table.setAlternatingRowColors(True)
        
        # Configurar ancho de columnas
        header = self.productos_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Subtotal
        
        # Estilo
        self.productos_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                alternate-background-color: #F8F9FA;
            }
            QHeaderView::section {
                background-color: #6C757D;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
        """)
    
    def create_estadisticas_panel(self):
        """Crear panel de estadísticas"""
        panel = QGroupBox("Estadísticas")
        layout = QHBoxLayout(panel)
        
        # Estadísticas básicas
        self.total_facturas_label = QLabel("Total Facturas: 0")
        self.total_facturas_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.total_facturas_label)
        
        self.facturas_confirmadas_label = QLabel("Confirmadas: 0")
        self.facturas_confirmadas_label.setStyleSheet("color: #28A745;")
        layout.addWidget(self.facturas_confirmadas_label)
        
        self.facturas_borrador_label = QLabel("Borradores: 0")
        self.facturas_borrador_label.setStyleSheet("color: #FFC107;")
        layout.addWidget(self.facturas_borrador_label)
        
        self.facturas_anuladas_label = QLabel("Anuladas: 0")
        self.facturas_anuladas_label.setStyleSheet("color: #DC3545;")
        layout.addWidget(self.facturas_anuladas_label)
        
        layout.addStretch()
        
        self.total_ventas_label = QLabel("Total Ventas: $0.00")
        self.total_ventas_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.total_ventas_label.setStyleSheet("color: #007BFF;")
        layout.addWidget(self.total_ventas_label)
        
        return panel
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Búsqueda
        self.search_edit.textChanged.connect(self.on_search_changed)
        
        # Filtros
        self.estado_combo.currentTextChanged.connect(self.aplicar_filtros)
        self.fecha_desde.dateChanged.connect(self.aplicar_filtros)
        self.fecha_hasta.dateChanged.connect(self.aplicar_filtros)
        
        # Botones
        self.nueva_factura_btn.clicked.connect(self.nueva_factura)
        self.editar_factura_btn.clicked.connect(self.editar_factura)
        self.confirmar_factura_btn.clicked.connect(self.confirmar_factura)
        self.anular_factura_btn.clicked.connect(self.anular_factura)
        self.actualizar_btn.clicked.connect(self.cargar_facturas)
        
        # Tabla
        self.facturas_table.itemSelectionChanged.connect(self.on_factura_selected)
        self.facturas_table.itemDoubleClicked.connect(self.editar_factura)
    
    def cargar_facturas(self):
        """Cargar lista de facturas"""
        try:
            # Obtener filtros
            filtros = self.get_filtros_actuales()
            
            # Cargar facturas
            resultado = self.controller.listar_facturas(filtros)
            
            if resultado['success']:
                self.facturas_data = resultado['data']
                self.actualizar_tabla_facturas()
                self.actualizar_estadisticas()
                
                # Mostrar mensaje si no hay facturas
                if not self.facturas_data:
                    self.mostrar_mensaje("No se encontraron facturas con los filtros aplicados", "info")
            else:
                self.mostrar_mensaje(f"Error al cargar facturas: {resultado['message']}", "error")
                
        except Exception as e:
            logger.error(f"Error inesperado al cargar facturas: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def actualizar_tabla_facturas(self):
        """Actualizar contenido de la tabla de facturas"""
        self.facturas_table.setRowCount(len(self.facturas_data))
        
        for row, factura in enumerate(self.facturas_data):
            # Número de factura
            self.facturas_table.setItem(row, 0, QTableWidgetItem(factura['numero_factura']))
            
            # Cliente
            self.facturas_table.setItem(row, 1, QTableWidgetItem(factura['cliente_nombre']))
            
            # Fecha
            self.facturas_table.setItem(row, 2, QTableWidgetItem(factura['fecha_factura']))
            
            # Total
            total_item = QTableWidgetItem(factura['total_factura'])
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.facturas_table.setItem(row, 3, total_item)
            
            # Estado
            estado_item = QTableWidgetItem(factura['estado_display'])
            estado_item.setTextAlignment(Qt.AlignCenter)
            
            # Colorear según estado
            if factura['estado'] == 'confirmada':
                estado_item.setBackground(QColor('#D4EDDA'))
            elif factura['estado'] == 'borrador':
                estado_item.setBackground(QColor('#FFF3CD'))
            elif factura['estado'] == 'anulada':
                estado_item.setBackground(QColor('#F8D7DA'))
            
            self.facturas_table.setItem(row, 4, estado_item)
            
            # ID (oculto)
            self.facturas_table.setItem(row, 5, QTableWidgetItem(str(factura['id'])))
    
    def on_factura_selected(self):
        """Manejar selección de factura"""
        current_row = self.facturas_table.currentRow()
        
        if current_row >= 0 and current_row < len(self.facturas_data):
            factura = self.facturas_data[current_row]
            self.current_factura = factura
            
            # Cargar detalles completos
            self.cargar_detalles_factura(factura['id'])
            
            # Actualizar estado de botones
            self.actualizar_botones_estado()
            
            # Emitir señal
            self.factura_seleccionada.emit(factura)
        else:
            self.limpiar_detalles()
            self.current_factura = None
            self.actualizar_botones_estado()
    
    def cargar_detalles_factura(self, factura_id):
        """Cargar detalles completos de una factura"""
        try:
            resultado = self.controller.obtener_factura(factura_id)
            
            if resultado['success']:
                factura = resultado['data']
                
                # Actualizar información general
                self.numero_factura_label.setText(factura['numero_factura'])
                self.cliente_label.setText(factura['cliente_nombre'])
                self.fecha_label.setText(factura['fecha_factura'])
                self.estado_label.setText(factura['estado_display'])
                self.subtotal_label.setText(factura['subtotal_factura'])
                self.impuestos_label.setText(factura['impuestos_factura'])
                self.total_label.setText(factura['total_factura'])
                self.observaciones_label.setText(factura.get('observaciones', 'Sin observaciones'))
                
                # Actualizar tabla de productos
                self.actualizar_tabla_productos(factura.get('detalles', []))
            else:
                self.mostrar_mensaje(f"Error al cargar detalles: {resultado['message']}", "error")
                
        except Exception as e:
            logger.error(f"Error al cargar detalles de factura: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def actualizar_tabla_productos(self, detalles):
        """Actualizar tabla de productos de la factura"""
        self.productos_table.setRowCount(len(detalles))
        
        for row, detalle in enumerate(detalles):
            # Código
            self.productos_table.setItem(row, 0, QTableWidgetItem(detalle['producto_codigo']))
            
            # Producto
            self.productos_table.setItem(row, 1, QTableWidgetItem(detalle['producto_nombre']))
            
            # Cantidad
            cantidad_item = QTableWidgetItem(str(detalle['cantidad']))
            cantidad_item.setTextAlignment(Qt.AlignCenter)
            self.productos_table.setItem(row, 2, cantidad_item)
            
            # Precio unitario
            precio_item = QTableWidgetItem(detalle['precio_unitario'])
            precio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 3, precio_item)
            
            # Subtotal
            subtotal_item = QTableWidgetItem(detalle['subtotal'])
            subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 4, subtotal_item)
    
    def limpiar_detalles(self):
        """Limpiar panel de detalles"""
        self.numero_factura_label.setText("-")
        self.cliente_label.setText("-")
        self.fecha_label.setText("-")
        self.estado_label.setText("-")
        self.subtotal_label.setText("-")
        self.impuestos_label.setText("-")
        self.total_label.setText("-")
        self.observaciones_label.setText("-")
        self.productos_table.setRowCount(0)
    
    def actualizar_botones_estado(self):
        """Actualizar estado de los botones según la factura seleccionada"""
        hay_seleccion = self.current_factura is not None
        
        self.editar_factura_btn.setEnabled(hay_seleccion)
        
        if hay_seleccion:
            estado = self.current_factura['estado']
            
            # Confirmar: solo facturas en borrador
            self.confirmar_factura_btn.setEnabled(estado == 'borrador')
            
            # Anular: solo facturas confirmadas
            self.anular_factura_btn.setEnabled(estado == 'confirmada')
        else:
            self.confirmar_factura_btn.setEnabled(False)
            self.anular_factura_btn.setEnabled(False)
    
    def get_filtros_actuales(self):
        """Obtener filtros actuales"""
        filtros = {}
        
        # Estado
        estado = self.estado_combo.currentText()
        if estado != "Todos":
            filtros['estado'] = estado.lower()
        
        # Fechas
        fecha_desde = self.fecha_desde.date().toPyDate()
        fecha_hasta = self.fecha_hasta.date().toPyDate()
        
        filtros['fecha_desde'] = fecha_desde
        filtros['fecha_hasta'] = fecha_hasta
        
        return filtros
    
    def on_search_changed(self):
        """Manejar cambio en el campo de búsqueda"""
        self.search_timer.stop()
        self.search_timer.start(500)  # Esperar 500ms antes de buscar
    
    def realizar_busqueda(self):
        """Realizar búsqueda de facturas"""
        termino = self.search_edit.text().strip()
        
        if not termino:
            self.cargar_facturas()
            return
        
        # Filtrar facturas localmente
        facturas_filtradas = []
        for factura in self.facturas_data:
            if (termino.lower() in factura['numero_factura'].lower() or 
                termino.lower() in factura['cliente_nombre'].lower()):
                facturas_filtradas.append(factura)
        
        # Actualizar tabla con resultados filtrados
        self.facturas_data = facturas_filtradas
        self.actualizar_tabla_facturas()
    
    def aplicar_filtros(self):
        """Aplicar filtros y recargar facturas"""
        self.cargar_facturas()
    
    def actualizar_estadisticas(self):
        """Actualizar panel de estadísticas"""
        try:
            # Obtener filtros actuales
            filtros = self.get_filtros_actuales()
            
            # Obtener estadísticas
            resultado = self.controller.obtener_estadisticas_ventas(
                filtros.get('fecha_desde'),
                filtros.get('fecha_hasta')
            )
            
            if resultado['success']:
                stats = resultado['data']
                
                self.total_facturas_label.setText(f"Total Facturas: {stats['total_facturas']}")
                self.facturas_confirmadas_label.setText(f"Confirmadas: {stats['facturas_confirmadas']}")
                self.facturas_borrador_label.setText(f"Borradores: {stats['facturas_borrador']}")
                self.facturas_anuladas_label.setText(f"Anuladas: {stats['facturas_anuladas']}")
                self.total_ventas_label.setText(f"Total Ventas: {stats['total_ventas']}")
            
        except Exception as e:
            logger.error(f"Error al actualizar estadísticas: {str(e)}")
    
    def nueva_factura(self):
        """Crear nueva factura"""
        from views.factura_dialog import FacturaDialog
        
        dialog = FacturaDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.cargar_facturas()
            self.mostrar_mensaje("Factura creada exitosamente", "success")
    
    def editar_factura(self):
        """Editar factura seleccionada"""
        if not self.current_factura:
            return
        
        from views.factura_dialog import FacturaDialog
        
        dialog = FacturaDialog(self, self.current_factura)
        if dialog.exec_() == QDialog.Accepted:
            self.cargar_facturas()
            self.mostrar_mensaje("Factura actualizada exitosamente", "success")
    
    def confirmar_factura(self):
        """Confirmar factura seleccionada"""
        if not self.current_factura:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar Factura",
            f"¿Está seguro de confirmar la factura {self.current_factura['numero_factura']}?\n\n"
            "Esta acción actualizará el stock de los productos y no se podrá deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            resultado = self.controller.confirmar_factura(self.current_factura['id'])
            
            if resultado['success']:
                self.cargar_facturas()
                self.mostrar_mensaje(resultado['message'], "success")
            else:
                self.mostrar_mensaje(resultado['message'], "error")
    
    def anular_factura(self):
        """Anular factura seleccionada"""
        if not self.current_factura:
            return
        
        # Solicitar motivo de anulación
        from PyQt5.QtWidgets import QInputDialog
        
        motivo, ok = QInputDialog.getText(
            self,
            "Anular Factura",
            f"Motivo de anulación para la factura {self.current_factura['numero_factura']}:",
            text="Anulación solicitada por el cliente"
        )
        
        if ok:
            reply = QMessageBox.question(
                self,
                "Confirmar Anulación",
                f"¿Está seguro de anular la factura {self.current_factura['numero_factura']}?\n\n"
                "Esta acción devolverá el stock de los productos y no se podrá deshacer.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                resultado = self.controller.anular_factura(self.current_factura['id'], motivo)
                
                if resultado['success']:
                    self.cargar_facturas()
                    self.mostrar_mensaje(resultado['message'], "success")
                else:
                    self.mostrar_mensaje(resultado['message'], "error")
    
    def mostrar_mensaje(self, mensaje, tipo="info"):
        """Mostrar mensaje al usuario"""
        if tipo == "error":
            QMessageBox.critical(self, "Error", mensaje)
        elif tipo == "success":
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.information(self, "Información", mensaje)
    
    def refresh_view(self):
        """Refrescar la vista"""
        self.cargar_facturas()