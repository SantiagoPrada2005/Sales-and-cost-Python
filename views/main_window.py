"""
Ventana Principal del Sistema de Ventas y Costos
Interfaz principal con pestañas para cada módulo
"""
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QStatusBar, QMenuBar, 
                             QAction, QMessageBox, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from views.productos_view import ProductosView
from views.clientes_view import ClientesView
import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación
    Contiene pestañas para cada módulo del sistema
    """
    
    # Señales
    aplicacion_cerrada = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_connections()
        
        logger.info("Ventana principal inicializada")
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Configuración de la ventana
        self.setWindowTitle("Sistema de Ventas y Costos")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Widget central con pestañas
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Crear pestañas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        
        # Agregar pestañas de módulos
        self.setup_tabs()
        
        main_layout.addWidget(self.tabs)
        
        # Aplicar estilos
        self.apply_styles()
    
    def setup_tabs(self):
        """Configurar las pestañas de los módulos"""
        # Pestaña de Productos
        self.productos_view = ProductosView()
        self.tabs.addTab(self.productos_view, "📦 Productos")
        
        # Pestaña de Clientes
        self.clientes_view = ClientesView()
        self.tabs.addTab(self.clientes_view, "👥 Clientes")
        
        # Pestañas placeholder para futuros módulos
        self.setup_placeholder_tab("🧾 Facturación", "Módulo de facturación y ventas")
        self.setup_placeholder_tab("💰 Cuentas Pendientes", "Módulo de cuentas por cobrar")
        self.setup_placeholder_tab("📊 Reportes", "Módulo de reportes y estadísticas")
        
        # Establecer la pestaña de productos como activa
        self.tabs.setCurrentIndex(0)
    
    def setup_placeholder_tab(self, title, description):
        """Crear una pestaña placeholder para módulos futuros"""
        placeholder_widget = QWidget()
        layout = QVBoxLayout(placeholder_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # Etiqueta principal
        main_label = QLabel(f"{title}")
        main_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        main_label.setFont(font)
        
        # Etiqueta de descripción
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin-top: 10px;")
        
        # Etiqueta de estado
        status_label = QLabel("🚧 En desarrollo")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("color: #ff9800; margin-top: 20px; font-weight: bold;")
        
        layout.addWidget(main_label)
        layout.addWidget(desc_label)
        layout.addWidget(status_label)
        
        self.tabs.addTab(placeholder_widget, title)
    
    def setup_menu(self):
        """Configurar la barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        archivo_menu = menubar.addMenu('&Archivo')
        
        # Acción Salir
        salir_action = QAction('&Salir', self)
        salir_action.setShortcut('Ctrl+Q')
        salir_action.setStatusTip('Salir de la aplicación')
        salir_action.triggered.connect(self.close)
        archivo_menu.addAction(salir_action)
        
        # Menú Ver
        ver_menu = menubar.addMenu('&Ver')
        
        # Acción Actualizar
        actualizar_action = QAction('&Actualizar', self)
        actualizar_action.setShortcut('F5')
        actualizar_action.setStatusTip('Actualizar datos')
        actualizar_action.triggered.connect(self.actualizar_datos)
        ver_menu.addAction(actualizar_action)
        
        # Menú Ayuda
        ayuda_menu = menubar.addMenu('&Ayuda')
        
        # Acción Acerca de
        acerca_action = QAction('&Acerca de', self)
        acerca_action.setStatusTip('Información sobre la aplicación')
        acerca_action.triggered.connect(self.mostrar_acerca_de)
        ayuda_menu.addAction(acerca_action)
    
    def setup_status_bar(self):
        """Configurar la barra de estado"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Mensaje inicial
        self.status_bar.showMessage("Sistema de Ventas y Costos - Listo", 3000)
        
        # Timer para actualizar la hora
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_status_bar)
        self.timer.start(60000)  # Actualizar cada minuto
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Conexión para cambio de pestañas
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Conexiones con la vista de productos
        if hasattr(self.productos_view, 'producto_seleccionado'):
            self.productos_view.producto_seleccionado.connect(self.on_producto_seleccionado)
        
        # Conexiones con la vista de clientes
        if hasattr(self.clientes_view, 'cliente_seleccionado'):
            self.clientes_view.cliente_seleccionado.connect(self.on_cliente_seleccionado)
    
    def apply_styles(self):
        """Aplicar estilos a la ventana"""
        # Estilo para las pestañas
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-bottom: none;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def actualizar_datos(self):
        """Actualizar datos de la pestaña actual"""
        current_index = self.tabs.currentIndex()
        current_widget = self.tabs.widget(current_index)
        
        if current_widget == self.productos_view:
            if hasattr(self.productos_view, 'cargar_productos'):
                self.productos_view.cargar_productos()
                self.status_bar.showMessage("Productos actualizados", 2000)
        elif current_widget == self.clientes_view:
            if hasattr(self.clientes_view, 'cargar_clientes'):
                self.clientes_view.cargar_clientes()
                self.status_bar.showMessage("Clientes actualizados", 2000)
        else:
            self.status_bar.showMessage("Actualización no disponible para esta pestaña", 2000)
    
    def actualizar_status_bar(self):
        """Actualizar la barra de estado con información actual"""
        from datetime import datetime
        hora_actual = datetime.now().strftime("%H:%M")
        
        current_index = self.tabs.currentIndex()
        tab_name = self.tabs.tabText(current_index).replace("📦 ", "").replace("👥 ", "").replace("🧾 ", "").replace("💰 ", "").replace("📊 ", "")
        
        self.status_bar.showMessage(f"Módulo: {tab_name} | {hora_actual}")
    
    def on_tab_changed(self, index):
        """Manejar cambio de pestaña"""
        tab_name = self.tabs.tabText(index)
        logger.info(f"Cambiando a pestaña: {tab_name}")
        self.actualizar_status_bar()
    
    def on_producto_seleccionado(self, producto):
        """Manejar selección de producto"""
        if producto:
            mensaje = f"Producto seleccionado: {producto.get('nombre', 'Sin nombre')}"
            self.status_bar.showMessage(mensaje, 3000)
    
    def on_cliente_seleccionado(self, cliente):
        """Manejar selección de cliente"""
        if cliente:
            mensaje = f"Cliente seleccionado: {cliente.get('nombre', 'Sin nombre')}"
            self.status_bar.showMessage(mensaje, 3000)
    
    def mostrar_acerca_de(self):
        """Mostrar diálogo Acerca de"""
        QMessageBox.about(self, "Acerca de", 
                         """
                         <h3>Sistema de Ventas y Costos</h3>
                         <p><b>Versión:</b> 1.0.0</p>
                         <p><b>Descripción:</b> Sistema integral para gestión de ventas, 
                         inventario y control de costos.</p>
                         <p><b>Tecnologías:</b> Python 3.x, PyQt5, MySQL</p>
                         <p><b>Autor:</b> Equipo de Desarrollo</p>
                         """)
    
    def closeEvent(self, event):
        """Manejar evento de cierre de la ventana"""
        reply = QMessageBox.question(self, 'Confirmar Salida',
                                   '¿Está seguro que desea salir de la aplicación?',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            logger.info("Cerrando aplicación")
            self.aplicacion_cerrada.emit()
            event.accept()
        else:
            event.ignore()