"""
Diálogo para crear y editar facturas
Interfaz gráfica usando PyQt5 para gestionar facturas
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QMessageBox, 
                             QFormLayout, QDialogButtonBox, QHeaderView, 
                             QAbstractItemView, QGroupBox, QComboBox,
                             QSpinBox, QDoubleSpinBox, QFrame, QSplitter,
                             QCompleter, QStringListModel, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QValidator, QDoubleValidator, QIntValidator
from controllers.factura_controller import FacturaController
import logging

logger = logging.getLogger(__name__)

class ProductoSearchLineEdit(QLineEdit):
    """LineEdit personalizado para búsqueda de productos"""
    
    producto_seleccionado = pyqtSignal(dict)
    
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.productos_disponibles = []
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.buscar_productos)
        
        self.setPlaceholderText("Buscar producto por código SKU o nombre...")
        self.textChanged.connect(self.on_text_changed)
        
        # Cargar productos disponibles
        self.cargar_productos()
    
    def cargar_productos(self):
        """Cargar lista de productos disponibles"""
        try:
            resultado = self.controller.obtener_productos_disponibles()
            if resultado['success']:
                self.productos_disponibles = resultado['data']
                
                # Configurar autocompletado
                nombres_productos = [p['display_text'] for p in self.productos_disponibles]
                completer = QCompleter(nombres_productos)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                self.setCompleter(completer)
                
        except Exception as e:
            logger.error(f"Error al cargar productos: {str(e)}")
    
    def on_text_changed(self):
        """Manejar cambio de texto"""
        self.search_timer.stop()
        if len(self.text()) >= 2:
            self.search_timer.start(300)
    
    def buscar_productos(self):
        """Buscar productos por término"""
        termino = self.text().strip()
        if not termino:
            return
        
        # Buscar en productos disponibles
        for producto in self.productos_disponibles:
            if (termino.lower() in producto['codigo_sku'].lower() or 
                termino.lower() in producto['nombre'].lower()):
                self.producto_seleccionado.emit(producto)
                break

class FacturaDialog(QDialog):
    """
    Diálogo para crear/editar facturas
    """
    
    def __init__(self, parent=None, factura=None):
        super().__init__(parent)
        self.factura = factura
        self.is_edit_mode = factura is not None
        self.controller = FacturaController()
        self.clientes_data = []
        self.detalles_factura = []
        self.factura_id = None
        
        self.setWindowTitle("Editar Factura" if self.is_edit_mode else "Nueva Factura")
        self.setModal(True)
        self.resize(900, 700)
        
        self.setup_ui()
        self.setup_connections()
        self.cargar_datos_iniciales()
        
        if self.is_edit_mode:
            self.cargar_factura_data()
    
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Editar Factura" if self.is_edit_mode else "Nueva Factura")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Panel principal con splitter
        main_splitter = QSplitter(Qt.Vertical)
        
        # Panel superior - Información de la factura
        info_panel = self.create_info_panel()
        main_splitter.addWidget(info_panel)
        
        # Panel inferior - Detalles de productos
        detalles_panel = self.create_detalles_panel()
        main_splitter.addWidget(detalles_panel)
        
        # Configurar proporciones
        main_splitter.setSizes([200, 400])
        layout.addWidget(main_splitter)
        
        # Panel de totales
        totales_panel = self.create_totales_panel()
        layout.addWidget(totales_panel)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Botones
        self.create_buttons_panel(layout)
    
    def create_info_panel(self):
        """Crear panel de información de la factura"""
        panel = QGroupBox("Información de la Factura")
        layout = QFormLayout(panel)
        
        # Número de factura (solo lectura en modo edición)
        self.numero_factura_edit = QLineEdit()
        if self.is_edit_mode:
            self.numero_factura_edit.setReadOnly(True)
            self.numero_factura_edit.setStyleSheet("background-color: #F8F9FA;")
        else:
            self.numero_factura_edit.setPlaceholderText("Se generará automáticamente")
            self.numero_factura_edit.setReadOnly(True)
            self.numero_factura_edit.setStyleSheet("background-color: #F8F9FA;")
        layout.addRow("Número de Factura:", self.numero_factura_edit)
        
        # Cliente
        self.cliente_combo = QComboBox()
        self.cliente_combo.setMinimumWidth(300)
        layout.addRow("Cliente*:", self.cliente_combo)
        
        # Observaciones
        self.observaciones_edit = QTextEdit()
        self.observaciones_edit.setMaximumHeight(60)
        self.observaciones_edit.setPlaceholderText("Observaciones adicionales (opcional)")
        layout.addRow("Observaciones:", self.observaciones_edit)
        
        return panel
    
    def create_detalles_panel(self):
        """Crear panel de detalles de productos"""
        panel = QGroupBox("Productos de la Factura")
        layout = QVBoxLayout(panel)
        
        # Panel de búsqueda y agregar producto
        search_panel = self.create_search_panel()
        layout.addWidget(search_panel)
        
        # Tabla de productos
        self.productos_table = QTableWidget()
        self.setup_productos_table()
        layout.addWidget(self.productos_table)
        
        # Botones de acciones en productos
        buttons_layout = QHBoxLayout()
        
        self.editar_producto_btn = QPushButton("Editar Cantidad/Precio")
        self.editar_producto_btn.setEnabled(False)
        buttons_layout.addWidget(self.editar_producto_btn)
        
        self.eliminar_producto_btn = QPushButton("Eliminar Producto")
        self.eliminar_producto_btn.setEnabled(False)
        self.eliminar_producto_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:disabled {
                background-color: #6C757D;
            }
        """)
        buttons_layout.addWidget(self.eliminar_producto_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return panel
    
    def create_search_panel(self):
        """Crear panel de búsqueda de productos"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(panel)
        
        # Búsqueda de producto
        layout.addWidget(QLabel("Buscar Producto:"))
        
        self.producto_search = ProductoSearchLineEdit(self.controller)
        self.producto_search.setMinimumWidth(300)
        layout.addWidget(self.producto_search)
        
        # Cantidad
        layout.addWidget(QLabel("Cantidad:"))
        self.cantidad_spin = QSpinBox()
        self.cantidad_spin.setMinimum(1)
        self.cantidad_spin.setMaximum(9999)
        self.cantidad_spin.setValue(1)
        layout.addWidget(self.cantidad_spin)
        
        # Precio unitario
        layout.addWidget(QLabel("Precio:"))
        self.precio_edit = QLineEdit()
        self.precio_edit.setPlaceholderText("0.00")
        validator = QDoubleValidator(0.00, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.precio_edit.setValidator(validator)
        layout.addWidget(self.precio_edit)
        
        # Botón agregar
        self.agregar_producto_btn = QPushButton("Agregar")
        self.agregar_producto_btn.setStyleSheet("""
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
        layout.addWidget(self.agregar_producto_btn)
        
        return panel
    
    def setup_productos_table(self):
        """Configurar tabla de productos"""
        self.productos_table.setColumnCount(6)
        headers = ["Código", "Producto", "Cantidad", "Precio Unit.", "Subtotal", "ID"]
        self.productos_table.setHorizontalHeaderLabels(headers)
        
        # Configurar propiedades
        self.productos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.productos_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.productos_table.setAlternatingRowColors(True)
        
        # Configurar ancho de columnas
        header = self.productos_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Subtotal
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # ID (oculta)
        self.productos_table.setColumnWidth(5, 0)
        self.productos_table.setColumnHidden(5, True)
        
        # Estilo
        self.productos_table.setStyleSheet("""
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
    
    def create_totales_panel(self):
        """Crear panel de totales"""
        panel = QGroupBox("Totales")
        layout = QFormLayout(panel)
        
        # Subtotal
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addRow("Subtotal:", self.subtotal_label)
        
        # Impuestos (19% IVA)
        self.impuestos_label = QLabel("$0.00")
        self.impuestos_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addRow("Impuestos (19%):", self.impuestos_label)
        
        # Total
        self.total_label = QLabel("$0.00")
        self.total_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.total_label.setStyleSheet("color: #28A745;")
        layout.addRow("TOTAL:", self.total_label)
        
        return panel
    
    def create_buttons_panel(self, parent_layout):
        """Crear panel de botones"""
        button_box = QDialogButtonBox()
        
        # Botón guardar
        self.save_btn = QPushButton("Guardar Factura")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056B3;
            }
        """)
        button_box.addButton(self.save_btn, QDialogButtonBox.AcceptRole)
        
        # Botón cancelar
        cancel_btn = QPushButton("Cancelar")
        button_box.addButton(cancel_btn, QDialogButtonBox.RejectRole)
        
        parent_layout.addWidget(button_box)
        
        # Conectar botones
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Búsqueda de productos
        self.producto_search.producto_seleccionado.connect(self.on_producto_encontrado)
        self.agregar_producto_btn.clicked.connect(self.agregar_producto)
        
        # Tabla de productos
        self.productos_table.itemSelectionChanged.connect(self.on_producto_selected)
        self.productos_table.itemDoubleClicked.connect(self.editar_producto_seleccionado)
        
        # Botones de productos
        self.editar_producto_btn.clicked.connect(self.editar_producto_seleccionado)
        self.eliminar_producto_btn.clicked.connect(self.eliminar_producto_seleccionado)
    
    def cargar_datos_iniciales(self):
        """Cargar datos iniciales (clientes)"""
        try:
            # Cargar clientes
            resultado = self.controller.obtener_clientes_activos()
            if resultado['success']:
                self.clientes_data = resultado['data']
                
                # Llenar combo de clientes
                self.cliente_combo.clear()
                self.cliente_combo.addItem("Seleccionar cliente...", None)
                
                for cliente in self.clientes_data:
                    self.cliente_combo.addItem(cliente['display_text'], cliente['id'])
            else:
                self.mostrar_mensaje(f"Error al cargar clientes: {resultado['message']}", "error")
                
        except Exception as e:
            logger.error(f"Error al cargar datos iniciales: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def cargar_factura_data(self):
        """Cargar datos de la factura en modo edición"""
        if not self.is_edit_mode or not self.factura:
            return
        
        try:
            # Cargar detalles completos de la factura
            resultado = self.controller.obtener_factura(self.factura['id'])
            
            if resultado['success']:
                factura_data = resultado['data']
                self.factura_id = factura_data['id']
                
                # Llenar campos
                self.numero_factura_edit.setText(factura_data['numero_factura'])
                
                # Seleccionar cliente
                cliente_id = factura_data['cliente_id']
                for i in range(self.cliente_combo.count()):
                    if self.cliente_combo.itemData(i) == cliente_id:
                        self.cliente_combo.setCurrentIndex(i)
                        break
                
                # Observaciones
                self.observaciones_edit.setPlainText(factura_data.get('observaciones', ''))
                
                # Cargar detalles de productos
                self.detalles_factura = factura_data.get('detalles', [])
                self.actualizar_tabla_productos()
                self.calcular_totales()
                
                # Deshabilitar edición si la factura no está en borrador
                if factura_data.get('estado') != 'borrador':
                    self.deshabilitar_edicion()
            else:
                self.mostrar_mensaje(f"Error al cargar factura: {resultado['message']}", "error")
                self.reject()
                
        except Exception as e:
            logger.error(f"Error al cargar factura: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
            self.reject()
    
    def deshabilitar_edicion(self):
        """Deshabilitar edición para facturas confirmadas/anuladas"""
        self.cliente_combo.setEnabled(False)
        self.observaciones_edit.setReadOnly(True)
        self.producto_search.setEnabled(False)
        self.cantidad_spin.setEnabled(False)
        self.precio_edit.setEnabled(False)
        self.agregar_producto_btn.setEnabled(False)
        self.editar_producto_btn.setEnabled(False)
        self.eliminar_producto_btn.setEnabled(False)
        self.save_btn.setText("Cerrar")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
    
    def on_producto_encontrado(self, producto):
        """Manejar producto encontrado en búsqueda"""
        self.precio_edit.setText(str(producto['precio_venta']))
        self.cantidad_spin.setFocus()
    
    def agregar_producto(self):
        """Agregar producto a la factura"""
        try:
            # Validar datos
            termino_busqueda = self.producto_search.text().strip()
            if not termino_busqueda:
                self.mostrar_mensaje("Debe buscar y seleccionar un producto", "warning")
                return
            
            cantidad = self.cantidad_spin.value()
            precio_text = self.precio_edit.text().strip()
            
            if not precio_text:
                self.mostrar_mensaje("Debe especificar un precio", "warning")
                return
            
            try:
                precio_unitario = float(precio_text)
            except ValueError:
                self.mostrar_mensaje("El precio debe ser un número válido", "warning")
                return
            
            if precio_unitario < 0:
                self.mostrar_mensaje("El precio no puede ser negativo", "warning")
                return
            
            # Buscar producto
            resultado_busqueda = self.controller.buscar_productos(termino_busqueda)
            if not resultado_busqueda['success'] or not resultado_busqueda['data']:
                self.mostrar_mensaje("Producto no encontrado o sin stock disponible", "warning")
                return
            
            producto = resultado_busqueda['data'][0]  # Tomar el primer resultado
            
            # Verificar si ya existe en la factura
            for detalle in self.detalles_factura:
                if detalle.get('producto_id') == producto['id']:
                    self.mostrar_mensaje("El producto ya está en la factura. Use 'Editar' para modificar cantidad o precio.", "warning")
                    return
            
            # Verificar stock disponible
            if producto['stock_actual'] < cantidad:
                self.mostrar_mensaje(f"Stock insuficiente. Disponible: {producto['stock_actual']}", "warning")
                return
            
            # Si estamos en modo edición, agregar a la base de datos
            if self.is_edit_mode and self.factura_id:
                resultado = self.controller.agregar_producto_a_factura(
                    self.factura_id, producto['id'], cantidad, precio_unitario
                )
                
                if not resultado['success']:
                    self.mostrar_mensaje(resultado['message'], "error")
                    return
            
            # Agregar a la lista local
            subtotal = cantidad * precio_unitario
            detalle = {
                'id': len(self.detalles_factura) + 1,  # ID temporal para nuevas facturas
                'producto_id': producto['id'],
                'producto_codigo': producto['codigo_sku'],
                'producto_nombre': producto['nombre'],
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'precio_unitario_raw': precio_unitario,
                'subtotal': f"${subtotal:,.2f}",
                'subtotal_raw': subtotal
            }
            
            self.detalles_factura.append(detalle)
            
            # Actualizar tabla y totales
            self.actualizar_tabla_productos()
            self.calcular_totales()
            
            # Limpiar campos
            self.producto_search.clear()
            self.precio_edit.clear()
            self.cantidad_spin.setValue(1)
            self.producto_search.setFocus()
            
        except Exception as e:
            logger.error(f"Error al agregar producto: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def actualizar_tabla_productos(self):
        """Actualizar tabla de productos"""
        self.productos_table.setRowCount(len(self.detalles_factura))
        
        for row, detalle in enumerate(self.detalles_factura):
            # Código
            self.productos_table.setItem(row, 0, QTableWidgetItem(detalle['producto_codigo']))
            
            # Producto
            self.productos_table.setItem(row, 1, QTableWidgetItem(detalle['producto_nombre']))
            
            # Cantidad
            cantidad_item = QTableWidgetItem(str(detalle['cantidad']))
            cantidad_item.setTextAlignment(Qt.AlignCenter)
            self.productos_table.setItem(row, 2, cantidad_item)
            
            # Precio unitario
            precio_formatted = f"${detalle['precio_unitario_raw']:,.2f}"
            precio_item = QTableWidgetItem(precio_formatted)
            precio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 3, precio_item)
            
            # Subtotal
            subtotal_item = QTableWidgetItem(detalle['subtotal'])
            subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 4, subtotal_item)
            
            # ID (oculto)
            self.productos_table.setItem(row, 5, QTableWidgetItem(str(detalle['id'])))
    
    def calcular_totales(self):
        """Calcular y mostrar totales"""
        subtotal = sum(detalle['subtotal_raw'] for detalle in self.detalles_factura)
        impuestos = subtotal * 0.19  # 19% IVA
        total = subtotal + impuestos
        
        self.subtotal_label.setText(f"${subtotal:,.2f}")
        self.impuestos_label.setText(f"${impuestos:,.2f}")
        self.total_label.setText(f"${total:,.2f}")
    
    def on_producto_selected(self):
        """Manejar selección de producto en la tabla"""
        current_row = self.productos_table.currentRow()
        hay_seleccion = current_row >= 0
        
        self.editar_producto_btn.setEnabled(hay_seleccion)
        self.eliminar_producto_btn.setEnabled(hay_seleccion)
    
    def editar_producto_seleccionado(self):
        """Editar producto seleccionado"""
        current_row = self.productos_table.currentRow()
        if current_row < 0 or current_row >= len(self.detalles_factura):
            return
        
        detalle = self.detalles_factura[current_row]
        
        # Diálogo para editar cantidad y precio
        dialog = QDialog(self)
        dialog.setWindowTitle("Editar Producto")
        dialog.setModal(True)
        dialog.resize(300, 150)
        
        layout = QFormLayout(dialog)
        
        # Mostrar producto
        layout.addRow("Producto:", QLabel(detalle['producto_nombre']))
        
        # Cantidad
        cantidad_spin = QSpinBox()
        cantidad_spin.setMinimum(1)
        cantidad_spin.setMaximum(9999)
        cantidad_spin.setValue(detalle['cantidad'])
        layout.addRow("Cantidad:", cantidad_spin)
        
        # Precio
        precio_edit = QLineEdit()
        precio_edit.setText(str(detalle['precio_unitario_raw']))
        validator = QDoubleValidator(0.00, 999999.99, 2)
        precio_edit.setValidator(validator)
        layout.addRow("Precio Unitario:", precio_edit)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                nueva_cantidad = cantidad_spin.value()
                nuevo_precio = float(precio_edit.text())
                
                if nuevo_precio < 0:
                    self.mostrar_mensaje("El precio no puede ser negativo", "warning")
                    return
                
                # Si estamos en modo edición, actualizar en la base de datos
                if self.is_edit_mode and self.factura_id:
                    resultado = self.controller.actualizar_detalle_factura(
                        detalle['id'], nueva_cantidad, nuevo_precio
                    )
                    
                    if not resultado['success']:
                        self.mostrar_mensaje(resultado['message'], "error")
                        return
                
                # Actualizar detalle local
                detalle['cantidad'] = nueva_cantidad
                detalle['precio_unitario_raw'] = nuevo_precio
                detalle['subtotal_raw'] = nueva_cantidad * nuevo_precio
                detalle['subtotal'] = f"${detalle['subtotal_raw']:,.2f}"
                
                # Actualizar tabla y totales
                self.actualizar_tabla_productos()
                self.calcular_totales()
                
            except ValueError:
                self.mostrar_mensaje("El precio debe ser un número válido", "warning")
            except Exception as e:
                logger.error(f"Error al editar producto: {str(e)}")
                self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def eliminar_producto_seleccionado(self):
        """Eliminar producto seleccionado"""
        current_row = self.productos_table.currentRow()
        if current_row < 0 or current_row >= len(self.detalles_factura):
            return
        
        detalle = self.detalles_factura[current_row]
        
        reply = QMessageBox.question(
            self,
            "Eliminar Producto",
            f"¿Está seguro de eliminar '{detalle['producto_nombre']}' de la factura?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Si estamos en modo edición, eliminar de la base de datos
                if self.is_edit_mode and self.factura_id:
                    resultado = self.controller.eliminar_detalle_factura(detalle['id'])
                    
                    if not resultado['success']:
                        self.mostrar_mensaje(resultado['message'], "error")
                        return
                
                # Eliminar de la lista local
                self.detalles_factura.pop(current_row)
                
                # Actualizar tabla y totales
                self.actualizar_tabla_productos()
                self.calcular_totales()
                
            except Exception as e:
                logger.error(f"Error al eliminar producto: {str(e)}")
                self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def accept(self):
        """Aceptar y guardar factura"""
        try:
            # Validar datos
            if not self.validar_datos():
                return
            
            # Si es modo edición y la factura no está en borrador, solo cerrar
            if (self.is_edit_mode and self.factura and 
                self.factura.get('estado') != 'borrador'):
                super().accept()
                return
            
            # Obtener datos
            cliente_id = self.cliente_combo.currentData()
            observaciones = self.observaciones_edit.toPlainText().strip()
            
            if self.is_edit_mode:
                # En modo edición, los cambios ya se guardaron en tiempo real
                super().accept()
            else:
                # Crear nueva factura
                resultado = self.controller.crear_factura(cliente_id, observaciones)
                
                if resultado['success']:
                    factura_id = resultado['data']['id']
                    
                    # Agregar productos
                    for detalle in self.detalles_factura:
                        resultado_detalle = self.controller.agregar_producto_a_factura(
                            factura_id,
                            detalle['producto_id'],
                            detalle['cantidad'],
                            detalle['precio_unitario_raw']
                        )
                        
                        if not resultado_detalle['success']:
                            self.mostrar_mensaje(
                                f"Error al agregar {detalle['producto_nombre']}: {resultado_detalle['message']}", 
                                "error"
                            )
                            return
                    
                    super().accept()
                else:
                    self.mostrar_mensaje(resultado['message'], "error")
            
        except Exception as e:
            logger.error(f"Error al guardar factura: {str(e)}")
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
    
    def validar_datos(self):
        """Validar datos de la factura"""
        # Validar cliente
        if not self.cliente_combo.currentData():
            self.mostrar_mensaje("Debe seleccionar un cliente", "warning")
            self.cliente_combo.setFocus()
            return False
        
        # Validar que tenga al menos un producto
        if not self.detalles_factura:
            self.mostrar_mensaje("La factura debe tener al menos un producto", "warning")
            self.producto_search.setFocus()
            return False
        
        # Validar observaciones
        observaciones = self.observaciones_edit.toPlainText().strip()
        if len(observaciones) > 500:
            self.mostrar_mensaje("Las observaciones no pueden exceder 500 caracteres", "warning")
            self.observaciones_edit.setFocus()
            return False
        
        return True
    
    def mostrar_mensaje(self, mensaje, tipo="info"):
        """Mostrar mensaje al usuario"""
        if tipo == "error":
            QMessageBox.critical(self, "Error", mensaje)
        elif tipo == "warning":
            QMessageBox.warning(self, "Advertencia", mensaje)
        elif tipo == "success":
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.information(self, "Información", mensaje)