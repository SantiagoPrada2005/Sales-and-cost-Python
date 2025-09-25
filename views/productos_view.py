"""
Vista para el módulo de Productos
Interfaz gráfica usando PyQt5 para gestionar productos
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLineEdit, QTextEdit, QLabel, QMessageBox, 
                             QDialog, QFormLayout, QDialogButtonBox, 
                             QHeaderView, QAbstractItemView, QGroupBox,
                             QSpacerItem, QSizePolicy, QFrame, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from controllers.producto_controller import ProductoController
import logging

logger = logging.getLogger(__name__)

class ProductoDialog(QDialog):
    """
    Dialog para crear/editar productos
    """
    
    def __init__(self, parent=None, producto=None):
        super().__init__(parent)
        self.producto = producto
        self.is_edit_mode = producto is not None
        self.controller = ProductoController()
        
        self.setWindowTitle("Editar Producto" if self.is_edit_mode else "Nuevo Producto")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        self.setup_ui()
        self.setup_connections()
        
        if self.is_edit_mode:
            self.load_producto_data()
    
    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Código SKU
        self.sku_edit = QLineEdit()
        self.sku_edit.setMaxLength(50)
        self.sku_edit.setPlaceholderText("Ej: PROD-001")
        form_layout.addRow("Código SKU*:", self.sku_edit)
        
        # Nombre
        self.nombre_edit = QLineEdit()
        self.nombre_edit.setMaxLength(255)
        self.nombre_edit.setPlaceholderText("Nombre del producto")
        form_layout.addRow("Nombre*:", self.nombre_edit)
        
        # Descripción
        self.descripcion_edit = QTextEdit()
        self.descripcion_edit.setMaximumHeight(80)
        self.descripcion_edit.setPlaceholderText("Descripción del producto (opcional)")
        form_layout.addRow("Descripción:", self.descripcion_edit)
        
        # Costo de adquisición
        self.costo_edit = QLineEdit()
        self.costo_edit.setPlaceholderText("0.00")
        form_layout.addRow("Costo de Adquisición*:", self.costo_edit)
        
        # Precio de venta
        self.precio_edit = QLineEdit()
        self.precio_edit.setPlaceholderText("0.00")
        form_layout.addRow("Precio de Venta*:", self.precio_edit)
        
        # Margen de ganancia (solo lectura)
        self.margen_label = QLabel("0.00%")
        self.margen_label.setStyleSheet("color: #2E8B57; font-weight: bold;")
        form_layout.addRow("Margen de Ganancia:", self.margen_label)
        
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
        # Calcular margen automáticamente
        self.costo_edit.textChanged.connect(self.calcular_margen)
        self.precio_edit.textChanged.connect(self.calcular_margen)
        
        # Convertir SKU a mayúsculas
        self.sku_edit.textChanged.connect(lambda text: self.sku_edit.setText(text.upper()))
    
    def calcular_margen(self):
        """Calcular y mostrar el margen de ganancia"""
        try:
            costo_text = self.costo_edit.text().strip()
            precio_text = self.precio_edit.text().strip()
            
            if costo_text and precio_text:
                costo = float(costo_text)
                precio = float(precio_text)
                
                if costo > 0:
                    margen = ((precio - costo) / costo) * 100
                    self.margen_label.setText(f"{margen:.2f}%")
                    
                    # Cambiar color según el margen
                    if margen < 0:
                        self.margen_label.setStyleSheet("color: #DC143C; font-weight: bold;")
                    elif margen < 20:
                        self.margen_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
                    else:
                        self.margen_label.setStyleSheet("color: #2E8B57; font-weight: bold;")
                else:
                    self.margen_label.setText("0.00%")
                    self.margen_label.setStyleSheet("color: #666; font-weight: bold;")
            else:
                self.margen_label.setText("0.00%")
                self.margen_label.setStyleSheet("color: #666; font-weight: bold;")
                
        except ValueError:
            self.margen_label.setText("0.00%")
            self.margen_label.setStyleSheet("color: #666; font-weight: bold;")
    
    def load_producto_data(self):
        """Cargar datos del producto en modo edición"""
        if self.producto:
            self.sku_edit.setText(self.producto.get('codigo_sku', ''))
            self.nombre_edit.setText(self.producto.get('nombre', ''))
            self.descripcion_edit.setPlainText(self.producto.get('descripcion', ''))
            self.costo_edit.setText(str(self.producto.get('costo_adquisicion', '')))
            self.precio_edit.setText(str(self.producto.get('precio_venta', '')))
            
            # Deshabilitar edición del SKU en modo edición
            self.sku_edit.setEnabled(False)
    
    def get_producto_data(self):
        """Obtener datos del formulario"""
        return {
            'codigo_sku': self.sku_edit.text().strip(),
            'nombre': self.nombre_edit.text().strip(),
            'descripcion': self.descripcion_edit.toPlainText().strip(),
            'costo_adquisicion': self.costo_edit.text().strip(),
            'precio_venta': self.precio_edit.text().strip()
        }
    
    def accept(self):
        """Validar y aceptar el diálogo"""
        data = self.get_producto_data()
        
        # Validar datos
        validation = self.controller.validar_datos_producto(
            data['codigo_sku'],
            data['nombre'],
            data['costo_adquisicion'],
            data['precio_venta']
        )
        
        if not validation['valid']:
            QMessageBox.warning(self, "Error de Validación", 
                              "\n".join(validation['errors']))
            return
        
        super().accept()

class ProductosView(QWidget):
    """
    Vista principal para gestionar productos
    """
    
    # Señales
    producto_seleccionado = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.controller = ProductoController()
        self.productos_data = []
        self.producto_seleccionado_actual = None
        
        self.setup_ui()
        self.setup_connections()
        self.cargar_productos()
        
        # Timer para búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.realizar_busqueda)
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Gestión de Productos")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Panel de controles
        controls_group = QGroupBox("Controles")
        controls_layout = QHBoxLayout(controls_group)
        
        # Búsqueda
        search_label = QLabel("Buscar:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Buscar por nombre o código SKU...")
        self.search_edit.setMinimumWidth(250)
        
        # Botones de acción
        self.btn_nuevo = QPushButton("Nuevo Producto")
        self.btn_nuevo.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 16px; }")
        
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setEnabled(False)
        self.btn_editar.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px; }")
        
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px 16px; }")
        
        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 8px 16px; }")
        
        # Agregar controles al layout
        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_edit)
        controls_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        controls_layout.addWidget(self.btn_nuevo)
        controls_layout.addWidget(self.btn_editar)
        controls_layout.addWidget(self.btn_eliminar)
        controls_layout.addWidget(self.btn_actualizar)
        
        layout.addWidget(controls_group)
        
        # Tabla de productos
        self.setup_table()
        layout.addWidget(self.productos_table)
        
        # Panel de estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_total_label = QLabel("Total Productos: 0")
        self.stats_valor_label = QLabel("Valor Total: $0.00")
        self.stats_margen_label = QLabel("Margen Promedio: 0.00%")
        
        stats_layout.addWidget(self.stats_total_label, 0, 0)
        stats_layout.addWidget(self.stats_valor_label, 0, 1)
        stats_layout.addWidget(self.stats_margen_label, 0, 2)
        
        layout.addWidget(stats_group)
    
    def setup_table(self):
        """Configurar la tabla de productos"""
        self.productos_table = QTableWidget()
        self.productos_table.setColumnCount(7)
        
        headers = ["ID", "Código SKU", "Nombre", "Descripción", 
                  "Costo", "Precio", "Margen %"]
        self.productos_table.setHorizontalHeaderLabels(headers)
        
        # Configurar propiedades de la tabla
        self.productos_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.productos_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.productos_table.setAlternatingRowColors(True)
        self.productos_table.setSortingEnabled(True)
        
        # Ajustar columnas
        header = self.productos_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # SKU
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nombre
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Descripción
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Costo
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Margen
        
        # Ocultar columna ID
        self.productos_table.setColumnHidden(0, True)
        
        # Estilo de la tabla
        self.productos_table.setStyleSheet("""
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
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Botones
        self.btn_nuevo.clicked.connect(self.nuevo_producto)
        self.btn_editar.clicked.connect(self.editar_producto)
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_actualizar.clicked.connect(self.cargar_productos)
        
        # Tabla
        self.productos_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.productos_table.itemDoubleClicked.connect(self.editar_producto)
        
        # Búsqueda con delay
        self.search_edit.textChanged.connect(self.on_search_text_changed)
    
    def on_search_text_changed(self):
        """Manejar cambio en el texto de búsqueda"""
        self.search_timer.stop()
        self.search_timer.start(500)  # Delay de 500ms
    
    def realizar_busqueda(self):
        """Realizar búsqueda de productos"""
        termino = self.search_edit.text().strip()
        
        if termino:
            resultado = self.controller.buscar_productos(termino)
            if resultado['success']:
                self.productos_data = resultado['data']
                self.actualizar_tabla()
                self.actualizar_estadisticas()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Warning)
        else:
            self.cargar_productos()
    
    def cargar_productos(self):
        """Cargar todos los productos"""
        resultado = self.controller.listar_productos()
        
        if resultado['success']:
            self.productos_data = resultado['data']
            self.actualizar_tabla()
            self.actualizar_estadisticas()
        else:
            self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def actualizar_tabla(self):
        """Actualizar la tabla con los datos de productos"""
        self.productos_table.setRowCount(len(self.productos_data))
        
        for row, producto in enumerate(self.productos_data):
            # ID (oculto)
            self.productos_table.setItem(row, 0, QTableWidgetItem(str(producto['id'])))
            
            # Código SKU
            self.productos_table.setItem(row, 1, QTableWidgetItem(producto['codigo_sku']))
            
            # Nombre
            self.productos_table.setItem(row, 2, QTableWidgetItem(producto['nombre']))
            
            # Descripción
            descripcion = producto.get('descripcion', '')[:50] + "..." if len(producto.get('descripcion', '')) > 50 else producto.get('descripcion', '')
            self.productos_table.setItem(row, 3, QTableWidgetItem(descripcion))
            
            # Costo
            costo_item = QTableWidgetItem(producto['costo_adquisicion_formatted'])
            costo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 4, costo_item)
            
            # Precio
            precio_item = QTableWidgetItem(producto['precio_venta_formatted'])
            precio_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.productos_table.setItem(row, 5, precio_item)
            
            # Margen
            margen_item = QTableWidgetItem(producto['margen_ganancia_formatted'])
            margen_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Color del margen según el valor
            margen_valor = producto['margen_ganancia']
            if margen_valor < 0:
                margen_item.setForeground(QColor("#DC143C"))
            elif margen_valor < 20:
                margen_item.setForeground(QColor("#FF8C00"))
            else:
                margen_item.setForeground(QColor("#2E8B57"))
            
            self.productos_table.setItem(row, 6, margen_item)
    
    def actualizar_estadisticas(self):
        """Actualizar panel de estadísticas"""
        if not self.productos_data:
            self.stats_total_label.setText("Total Productos: 0")
            self.stats_valor_label.setText("Valor Total: $0.00")
            self.stats_margen_label.setText("Margen Promedio: 0.00%")
            return
        
        resultado = self.controller.obtener_estadisticas_productos()
        
        if resultado['success']:
            stats = resultado['data']
            self.stats_total_label.setText(f"Total Productos: {stats['total_productos']}")
            self.stats_valor_label.setText(f"Valor Total: {stats['valor_total_formatted']}")
            self.stats_margen_label.setText(f"Margen Promedio: {stats['margen_promedio_formatted']}")
    
    def on_selection_changed(self):
        """Manejar cambio de selección en la tabla"""
        selected_items = self.productos_table.selectedItems()
        
        if selected_items:
            row = selected_items[0].row()
            producto_id = int(self.productos_table.item(row, 0).text())
            
            # Buscar el producto en los datos
            self.producto_seleccionado_actual = None
            for producto in self.productos_data:
                if producto['id'] == producto_id:
                    self.producto_seleccionado_actual = producto
                    break
            
            # Habilitar botones
            self.btn_editar.setEnabled(True)
            self.btn_eliminar.setEnabled(True)
            
            # Emitir señal
            if self.producto_seleccionado_actual:
                self.producto_seleccionado.emit(self.producto_seleccionado_actual)
        else:
            self.producto_seleccionado_actual = None
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
    
    def nuevo_producto(self):
        """Crear nuevo producto"""
        dialog = ProductoDialog(self)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_producto_data()
            
            resultado = self.controller.crear_producto(
                data['codigo_sku'],
                data['nombre'],
                data['descripcion'],
                data['costo_adquisicion'],
                data['precio_venta']
            )
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_productos()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def editar_producto(self):
        """Editar producto seleccionado"""
        if not self.producto_seleccionado_actual:
            return
        
        dialog = ProductoDialog(self, self.producto_seleccionado_actual)
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_producto_data()
            
            resultado = self.controller.actualizar_producto(
                self.producto_seleccionado_actual['id'],
                nombre=data['nombre'],
                descripcion=data['descripcion'],
                costo_adquisicion=data['costo_adquisicion'],
                precio_venta=data['precio_venta']
            )
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_productos()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def eliminar_producto(self):
        """Eliminar producto seleccionado"""
        if not self.producto_seleccionado_actual:
            return
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el producto '{self.producto_seleccionado_actual['nombre']}'?\n\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            resultado = self.controller.eliminar_producto(self.producto_seleccionado_actual['id'])
            
            if resultado['success']:
                self.mostrar_mensaje("Éxito", resultado['message'], QMessageBox.Information)
                self.cargar_productos()
            else:
                self.mostrar_mensaje("Error", resultado['message'], QMessageBox.Critical)
    
    def mostrar_mensaje(self, titulo, mensaje, tipo=QMessageBox.Information):
        """Mostrar mensaje al usuario"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(tipo)
        msg_box.exec_()
    
    def obtener_producto_seleccionado(self):
        """Obtener el producto actualmente seleccionado"""
        return self.producto_seleccionado_actual
    
    def seleccionar_producto_por_id(self, producto_id):
        """Seleccionar un producto por su ID"""
        for row in range(self.productos_table.rowCount()):
            if int(self.productos_table.item(row, 0).text()) == producto_id:
                self.productos_table.selectRow(row)
                break