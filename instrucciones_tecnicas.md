# Instrucciones Técnicas Detalladas - Sistema de Ventas y Costos

## Tabla de Contenidos
1. [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
2. [Módulo de Gestión de Productos](#módulo-de-gestión-de-productos)
3. [Módulo de Gestión de Clientes](#módulo-de-gestión-de-clientes)
4. [Módulo de Facturación y Ventas](#módulo-de-facturación-y-ventas)
5. [Módulo de Cuentas Pendientes](#módulo-de-cuentas-pendientes)
6. [Configuración de Base de Datos](#configuración-de-base-de-datos)
7. [Pruebas y Validación](#pruebas-y-validación)

---

## Módulo de Facturación y Ventas

### Funcionalidades Principales
- **Crear Factura**: Generación de nuevas facturas con productos y clientes
- **Gestión de Detalles**: Agregar/quitar productos de la factura
- **Cálculos Automáticos**: Subtotales, impuestos y totales
- **Estados de Factura**: Borrador, confirmada, pagada, anulada
- **Impresión/Exportación**: Generar PDF de facturas
- **Búsqueda y Filtros**: Por cliente, fecha, estado, número

### Implementación del Modelo

#### models/factura.py
```python
from config.database import DatabaseConnection
from utils.validators import FacturaValidator
from utils.exceptions import FacturaError
from datetime import datetime
from decimal import Decimal

class Factura:
    def __init__(self):
        self.db = DatabaseConnection()
        self.validator = FacturaValidator()
    
    def crear(self, cliente_id, observaciones=None):
        """
        Crear una nueva factura en estado borrador
        
        Args:
            cliente_id (int): ID del cliente
            observaciones (str): Observaciones opcionales
            
        Returns:
            int: ID de la factura creada
        """
        # Validar que el cliente existe
        if not self.cliente_existe(cliente_id):
            raise FacturaError("El cliente especificado no existe")
        
        # Generar número de factura
        numero_factura = self.generar_numero_factura()
        
        query = """
        INSERT INTO facturas (numero_factura, cliente_id, fecha_factura, 
                            subtotal_factura, impuestos_factura, total_factura, 
                            estado, observaciones)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        fecha_actual = datetime.now()
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (
                    numero_factura, cliente_id, fecha_actual,
                    Decimal('0.00'), Decimal('0.00'), Decimal('0.00'),
                    'borrador', observaciones
                ))
                conn.commit()
                return cursor.lastrowid
    
    def agregar_detalle(self, factura_id, producto_id, cantidad, precio_unitario=None):
        """
        Agregar un producto a la factura
        
        Args:
            factura_id (int): ID de la factura
            producto_id (int): ID del producto
            cantidad (int): Cantidad del producto
            precio_unitario (Decimal): Precio unitario (opcional, toma del producto si no se especifica)
        """
        # Validar que la factura existe y está en borrador
        factura = self.obtener_por_id(factura_id)
        if not factura:
            raise FacturaError("La factura no existe")
        
        if factura['estado'] != 'borrador':
            raise FacturaError("Solo se pueden modificar facturas en estado borrador")
        
        # Obtener información del producto
        producto = self.obtener_producto(producto_id)
        if not producto:
            raise FacturaError("El producto especificado no existe")
        
        # Usar precio del producto si no se especifica
        if precio_unitario is None:
            precio_unitario = producto['precio_venta']
        
        # Validar cantidad y precio
        self.validator.validar_detalle_factura(cantidad, precio_unitario)
        
        # Verificar stock disponible
        if producto['stock_actual'] < cantidad:
            raise FacturaError(f"Stock insuficiente. Disponible: {producto['stock_actual']}")
        
        # Verificar si el producto ya está en la factura
        detalle_existente = self.obtener_detalle_producto(factura_id, producto_id)
        
        if detalle_existente:
            # Actualizar cantidad existente
            nueva_cantidad = detalle_existente['cantidad'] + cantidad
            self.actualizar_detalle(detalle_existente['id'], nueva_cantidad, precio_unitario)
        else:
            # Crear nuevo detalle
            query = """
            INSERT INTO factura_detalles (factura_id, producto_id, cantidad, 
                                        precio_unitario, subtotal)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            subtotal = Decimal(str(cantidad)) * Decimal(str(precio_unitario))
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (factura_id, producto_id, cantidad, 
                                         precio_unitario, subtotal))
                    conn.commit()
        
        # Recalcular totales de la factura
        self.recalcular_totales(factura_id)
    
    def actualizar_detalle(self, detalle_id, cantidad, precio_unitario):
        """Actualizar un detalle de factura existente"""
        self.validator.validar_detalle_factura(cantidad, precio_unitario)
        
        subtotal = Decimal(str(cantidad)) * Decimal(str(precio_unitario))
        
        query = """
        UPDATE factura_detalles 
        SET cantidad = %s, precio_unitario = %s, subtotal = %s
        WHERE id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cantidad, precio_unitario, subtotal, detalle_id))
                conn.commit()
    
    def eliminar_detalle(self, detalle_id):
        """
        Eliminar un detalle de factura
        
        Args:
            detalle_id (int): ID del detalle a eliminar
        """
        # Obtener información del detalle para validaciones
        detalle = self.obtener_detalle_por_id(detalle_id)
        if not detalle:
            raise FacturaError("El detalle de factura no existe")
        
        # Validar que la factura esté en borrador
        factura = self.obtener_por_id(detalle['factura_id'])
        if factura['estado'] != 'borrador':
            raise FacturaError("Solo se pueden modificar facturas en estado borrador")
        
        query = "DELETE FROM factura_detalles WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (detalle_id,))
                conn.commit()
        
        # Recalcular totales
        self.recalcular_totales(detalle['factura_id'])
    
    def recalcular_totales(self, factura_id):
        """
        Recalcular los totales de una factura basado en sus detalles
        
        Args:
            factura_id (int): ID de la factura
        """
        # Obtener suma de subtotales
        query = """
        SELECT COALESCE(SUM(subtotal), 0) as subtotal_total
        FROM factura_detalles
        WHERE factura_id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (factura_id,))
                result = cursor.fetchone()
                subtotal = result['subtotal_total']
        
        # Calcular impuestos (19% IVA por defecto)
        tasa_impuesto = Decimal('0.19')
        impuestos = subtotal * tasa_impuesto
        total = subtotal + impuestos
        
        # Actualizar factura
        update_query = """
        UPDATE facturas 
        SET subtotal_factura = %s, impuestos_factura = %s, total_factura = %s
        WHERE id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(update_query, (subtotal, impuestos, total, factura_id))
                conn.commit()
    
    def confirmar_factura(self, factura_id):
        """
        Confirmar una factura (cambiar de borrador a confirmada)
        
        Args:
            factura_id (int): ID de la factura
        """
        factura = self.obtener_por_id(factura_id)
        if not factura:
            raise FacturaError("La factura no existe")
        
        if factura['estado'] != 'borrador':
            raise FacturaError("Solo se pueden confirmar facturas en estado borrador")
        
        # Validar que tenga al menos un detalle
        detalles = self.obtener_detalles(factura_id)
        if not detalles:
            raise FacturaError("La factura debe tener al menos un producto")
        
        # Validar stock para todos los productos
        for detalle in detalles:
            producto = self.obtener_producto(detalle['producto_id'])
            if producto['stock_actual'] < detalle['cantidad']:
                raise FacturaError(f"Stock insuficiente para {producto['nombre']}")
        
        # Actualizar stock de productos
        for detalle in detalles:
            self.actualizar_stock_producto(detalle['producto_id'], -detalle['cantidad'])
        
        # Cambiar estado de la factura
        query = "UPDATE facturas SET estado = 'confirmada' WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (factura_id,))
                conn.commit()
    
    def anular_factura(self, factura_id, motivo=None):
        """
        Anular una factura
        
        Args:
            factura_id (int): ID de la factura
            motivo (str): Motivo de anulación
        """
        factura = self.obtener_por_id(factura_id)
        if not factura:
            raise FacturaError("La factura no existe")
        
        if factura['estado'] == 'anulada':
            raise FacturaError("La factura ya está anulada")
        
        # Si la factura estaba confirmada, devolver stock
        if factura['estado'] == 'confirmada':
            detalles = self.obtener_detalles(factura_id)
            for detalle in detalles:
                self.actualizar_stock_producto(detalle['producto_id'], detalle['cantidad'])
        
        # Actualizar estado
        query = """
        UPDATE facturas 
        SET estado = 'anulada', observaciones = CONCAT(COALESCE(observaciones, ''), %s)
        WHERE id = %s
        """
        
        motivo_texto = f"\n[ANULADA] {motivo}" if motivo else "\n[ANULADA]"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (motivo_texto, factura_id))
                conn.commit()
    
    def obtener_por_id(self, factura_id):
        """Obtener factura por ID"""
        query = """
        SELECT f.*, c.nombre_completo as cliente_nombre
        FROM facturas f
        JOIN clientes c ON f.cliente_id = c.id
        WHERE f.id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (factura_id,))
                return cursor.fetchone()
    
    def obtener_todas(self, filtros=None):
        """
        Obtener lista de facturas con filtros opcionales
        
        Args:
            filtros (dict): Filtros opcionales (cliente_id, estado, fecha_desde, fecha_hasta)
        """
        base_query = """
        SELECT f.*, c.nombre_completo as cliente_nombre
        FROM facturas f
        JOIN clientes c ON f.cliente_id = c.id
        WHERE 1=1
        """
        
        params = []
        
        if filtros:
            if filtros.get('cliente_id'):
                base_query += " AND f.cliente_id = %s"
                params.append(filtros['cliente_id'])
            
            if filtros.get('estado'):
                base_query += " AND f.estado = %s"
                params.append(filtros['estado'])
            
            if filtros.get('fecha_desde'):
                base_query += " AND f.fecha_factura >= %s"
                params.append(filtros['fecha_desde'])
            
            if filtros.get('fecha_hasta'):
                base_query += " AND f.fecha_factura <= %s"
                params.append(filtros['fecha_hasta'])
            
            if filtros.get('numero_factura'):
                base_query += " AND f.numero_factura LIKE %s"
                params.append(f"%{filtros['numero_factura']}%")
        
        base_query += " ORDER BY f.fecha_factura DESC, f.id DESC"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                return cursor.fetchall()
    
    def obtener_detalles(self, factura_id):
        """Obtener detalles de una factura"""
        query = """
        SELECT fd.*, p.nombre as producto_nombre, p.codigo as producto_codigo
        FROM factura_detalles fd
        JOIN productos p ON fd.producto_id = p.id
        WHERE fd.factura_id = %s
        ORDER BY fd.id
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (factura_id,))
                return cursor.fetchall()
    
    def obtener_detalle_por_id(self, detalle_id):
        """Obtener un detalle específico por ID"""
        query = "SELECT * FROM factura_detalles WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (detalle_id,))
                return cursor.fetchone()
    
    def obtener_detalle_producto(self, factura_id, producto_id):
        """Obtener detalle de un producto específico en una factura"""
        query = """
        SELECT * FROM factura_detalles 
        WHERE factura_id = %s AND producto_id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (factura_id, producto_id))
                return cursor.fetchone()
    
    def generar_numero_factura(self):
        """Generar número de factura único"""
        query = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_factura, 2) AS UNSIGNED)), 0) + 1 as siguiente
        FROM facturas 
        WHERE numero_factura REGEXP '^F[0-9]+$'
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return f"F{result['siguiente']:06d}"
    
    def cliente_existe(self, cliente_id):
        """Verificar si un cliente existe"""
        query = "SELECT COUNT(*) as count FROM clientes WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id,))
                result = cursor.fetchone()
                return result['count'] > 0
    
    def obtener_producto(self, producto_id):
        """Obtener información de un producto"""
        query = "SELECT * FROM productos WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (producto_id,))
                return cursor.fetchone()
    
    def actualizar_stock_producto(self, producto_id, cambio_cantidad):
        """
        Actualizar stock de un producto
        
        Args:
            producto_id (int): ID del producto
            cambio_cantidad (int): Cantidad a sumar/restar (negativo para restar)
        """
        query = """
        UPDATE productos 
        SET stock_actual = stock_actual + %s
        WHERE id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cambio_cantidad, producto_id))
                conn.commit()
    
    def obtener_estadisticas_ventas(self, fecha_desde=None, fecha_hasta=None):
        """
        Obtener estadísticas de ventas
        
        Args:
            fecha_desde (date): Fecha de inicio
            fecha_hasta (date): Fecha de fin
            
        Returns:
            dict: Estadísticas de ventas
        """
        base_query = """
        SELECT 
            COUNT(*) as total_facturas,
            COALESCE(SUM(total_factura), 0) as total_ventas,
            COALESCE(AVG(total_factura), 0) as promedio_venta,
            COUNT(CASE WHEN estado = 'confirmada' THEN 1 END) as facturas_confirmadas,
            COUNT(CASE WHEN estado = 'borrador' THEN 1 END) as facturas_borrador,
            COUNT(CASE WHEN estado = 'anulada' THEN 1 END) as facturas_anuladas
        FROM facturas
        WHERE 1=1
        """
        
        params = []
        
        if fecha_desde:
            base_query += " AND fecha_factura >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            base_query += " AND fecha_factura <= %s"
            params.append(fecha_hasta)
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                return cursor.fetchone()
```

### Implementación del Controlador

#### controllers/factura_controller.py
```python
from models.factura import Factura
from utils.exceptions import FacturaError
from PyQt5.QtCore import QObject, pyqtSignal

class FacturaController(QObject):
    # Señales para comunicación con la vista
    factura_creada = pyqtSignal(dict)
    factura_actualizada = pyqtSignal(dict)
    detalle_agregado = pyqtSignal(dict)
    detalle_eliminado = pyqtSignal(int)
    factura_confirmada = pyqtSignal(int)
    factura_anulada = pyqtSignal(int)
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.modelo = Factura()
    
    def crear_factura(self, cliente_id, observaciones=None):
        """Crear nueva factura"""
        try:
            factura_id = self.modelo.crear(cliente_id, observaciones)
            factura_creada = self.modelo.obtener_por_id(factura_id)
            self.factura_creada.emit(factura_creada)
            return factura_id
            
        except FacturaError as e:
            self.error_ocurrido.emit(str(e))
            return None
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
            return None
    
    def obtener_facturas(self, filtros=None):
        """Obtener lista de facturas"""
        try:
            return self.modelo.obtener_todas(filtros)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener facturas: {str(e)}")
            return []
    
    def obtener_factura(self, factura_id):
        """Obtener factura específica"""
        try:
            return self.modelo.obtener_por_id(factura_id)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener factura: {str(e)}")
            return None
    
    def obtener_detalles_factura(self, factura_id):
        """Obtener detalles de una factura"""
        try:
            return self.modelo.obtener_detalles(factura_id)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener detalles: {str(e)}")
            return []
    
    def agregar_producto(self, factura_id, producto_id, cantidad, precio_unitario=None):
        """Agregar producto a factura"""
        try:
            self.modelo.agregar_detalle(factura_id, producto_id, cantidad, precio_unitario)
            
            # Obtener el detalle agregado para emitir señal
            detalle = self.modelo.obtener_detalle_producto(factura_id, producto_id)
            self.detalle_agregado.emit(detalle)
            
            # Emitir señal de factura actualizada
            factura_actualizada = self.modelo.obtener_por_id(factura_id)
            self.factura_actualizada.emit(factura_actualizada)
            
        except FacturaError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def eliminar_detalle(self, detalle_id):
        """Eliminar detalle de factura"""
        try:
            # Obtener información del detalle antes de eliminarlo
            detalle = self.modelo.obtener_detalle_por_id(detalle_id)
            if not detalle:
                self.error_ocurrido.emit("El detalle no existe")
                return
            
            factura_id = detalle['factura_id']
            
            self.modelo.eliminar_detalle(detalle_id)
            self.detalle_eliminado.emit(detalle_id)
            
            # Emitir señal de factura actualizada
            factura_actualizada = self.modelo.obtener_por_id(factura_id)
            self.factura_actualizada.emit(factura_actualizada)
            
        except FacturaError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def confirmar_factura(self, factura_id):
        """Confirmar factura"""
        try:
            self.modelo.confirmar_factura(factura_id)
            self.factura_confirmada.emit(factura_id)
            
            # Emitir señal de factura actualizada
            factura_actualizada = self.modelo.obtener_por_id(factura_id)
            self.factura_actualizada.emit(factura_actualizada)
            
        except FacturaError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def anular_factura(self, factura_id, motivo=None):
        """Anular factura"""
        try:
            self.modelo.anular_factura(factura_id, motivo)
            self.factura_anulada.emit(factura_id)
            
            # Emitir señal de factura actualizada
            factura_actualizada = self.modelo.obtener_por_id(factura_id)
            self.factura_actualizada.emit(factura_actualizada)
            
        except FacturaError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def obtener_estadisticas_ventas(self, fecha_desde=None, fecha_hasta=None):
        """Obtener estadísticas de ventas"""
        try:
            return self.modelo.obtener_estadisticas_ventas(fecha_desde, fecha_hasta)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener estadísticas: {str(e)}")
            return None
```

### Implementación de la Vista Principal

#### views/facturas_view.py
```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                            QComboBox, QDateEdit, QMessageBox, QHeaderView,
                            QAbstractItemView, QSplitter, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSlot, QDate
from controllers.factura_controller import FacturaController
from views.factura_dialog import FacturaDialog

class FacturasView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = FacturaController()
        self.setup_ui()
        self.conectar_senales()
        self.cargar_facturas()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Filtros
        filtros_group = QGroupBox("Filtros de Búsqueda")
        filtros_layout = QFormLayout()
        
        self.combo_estado = QComboBox()
        self.combo_estado.addItems(['Todos', 'Borrador', 'Confirmada', 'Anulada'])
        
        self.txt_numero = QLineEdit()
        self.txt_numero.setPlaceholderText("Número de factura...")
        
        self.date_desde = QDateEdit()
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_desde.setCalendarPopup(True)
        
        self.date_hasta = QDateEdit()
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setCalendarPopup(True)
        
        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_limpiar_filtros = QPushButton("Limpiar")
        
        filtros_layout.addRow("Estado:", self.combo_estado)
        filtros_layout.addRow("Número:", self.txt_numero)
        filtros_layout.addRow("Desde:", self.date_desde)
        filtros_layout.addRow("Hasta:", self.date_hasta)
        
        botones_filtros = QHBoxLayout()
        botones_filtros.addWidget(self.btn_filtrar)
        botones_filtros.addWidget(self.btn_limpiar_filtros)
        botones_filtros.addStretch()
        
        filtros_layout.addRow("", botones_filtros)
        filtros_group.setLayout(filtros_layout)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        self.btn_nueva = QPushButton("Nueva Factura")
        self.btn_ver = QPushButton("Ver/Editar")
        self.btn_confirmar = QPushButton("Confirmar")
        self.btn_anular = QPushButton("Anular")
        self.btn_imprimir = QPushButton("Imprimir")
        self.btn_actualizar = QPushButton("Actualizar")
        
        toolbar_layout.addWidget(self.btn_nueva)
        toolbar_layout.addWidget(self.btn_ver)
        toolbar_layout.addWidget(self.btn_confirmar)
        toolbar_layout.addWidget(self.btn_anular)
        toolbar_layout.addWidget(self.btn_imprimir)
        toolbar_layout.addWidget(self.btn_actualizar)
        toolbar_layout.addStretch()
        
        # Tabla de facturas
        self.tabla_facturas = QTableWidget()
        self.configurar_tabla()
        
        # Layout principal
        layout.addWidget(filtros_group)
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.tabla_facturas)
        
        self.setLayout(layout)
        
        # Estado inicial de botones
        self.btn_ver.setEnabled(False)
        self.btn_confirmar.setEnabled(False)
        self.btn_anular.setEnabled(False)
        self.btn_imprimir.setEnabled(False)
    
    def configurar_tabla(self):
        """Configurar tabla de facturas"""
        columnas = ['ID', 'Número', 'Cliente', 'Fecha', 'Subtotal', 
                   'Impuestos', 'Total', 'Estado']
        self.tabla_facturas.setColumnCount(len(columnas))
        self.tabla_facturas.setHorizontalHeaderLabels(columnas)
        
        # Configurar comportamiento
        self.tabla_facturas.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_facturas.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_facturas.setAlternatingRowColors(True)
        
        # Ajustar columnas
        header = self.tabla_facturas.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Número
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Cliente
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Subtotal
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Impuestos
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Total
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Estado
        
        # Ocultar columna ID
        self.tabla_facturas.setColumnHidden(0, True)
    
    def conectar_senales(self):
        """Conectar señales y slots"""
        # Botones
        self.btn_nueva.clicked.connect(self.nueva_factura)
        self.btn_ver.clicked.connect(self.ver_factura)
        self.btn_confirmar.clicked.connect(self.confirmar_factura)
        self.btn_anular.clicked.connect(self.anular_factura)
        self.btn_imprimir.clicked.connect(self.imprimir_factura)
        self.btn_actualizar.clicked.connect(self.cargar_facturas)
        
        # Filtros
        self.btn_filtrar.clicked.connect(self.aplicar_filtros)
        self.btn_limpiar_filtros.clicked.connect(self.limpiar_filtros)
        
        # Tabla
        self.tabla_facturas.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla_facturas.itemDoubleClicked.connect(self.ver_factura)
        
        # Señales del controlador
        self.controller.factura_creada.connect(self.on_factura_creada)
        self.controller.factura_actualizada.connect(self.on_factura_actualizada)
        self.controller.factura_confirmada.connect(self.on_factura_confirmada)
        self.controller.factura_anulada.connect(self.on_factura_anulada)
        self.controller.error_ocurrido.connect(self.mostrar_error)
    
    def cargar_facturas(self):
        """Cargar facturas en la tabla"""
        filtros = self.obtener_filtros()
        facturas = self.controller.obtener_facturas(filtros)
        
        self.tabla_facturas.setRowCount(len(facturas))
        
        for row, factura in enumerate(facturas):
            items = [
                str(factura['id']),
                factura['numero_factura'],
                factura['cliente_nombre'],
                factura['fecha_factura'].strftime('%Y-%m-%d'),
                f"${factura['subtotal_factura']:.2f}",
                f"${factura['impuestos_factura']:.2f}",
                f"${factura['total_factura']:.2f}",
                factura['estado'].replace('_', ' ').title()
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                
                # Colorear según estado
                if factura['estado'] == 'borrador':
                    table_item.setBackground(Qt.yellow)
                elif factura['estado'] == 'confirmada':
                    table_item.setBackground(Qt.green)
                elif factura['estado'] == 'anulada':
                    table_item.setBackground(Qt.red)
                
                self.tabla_facturas.setItem(row, col, table_item)
    
    def obtener_filtros(self):
        """Obtener filtros actuales"""
        filtros = {}
        
        if self.combo_estado.currentText() != 'Todos':
            filtros['estado'] = self.combo_estado.currentText().lower()
        
        if self.txt_numero.text().strip():
            filtros['numero_factura'] = self.txt_numero.text().strip()
        
        filtros['fecha_desde'] = self.date_desde.date().toPyDate()
        filtros['fecha_hasta'] = self.date_hasta.date().toPyDate()
        
        return filtros
    
    def seleccion_cambiada(self):
        """Manejar cambio de selección"""
        tiene_seleccion = len(self.tabla_facturas.selectedItems()) > 0
        self.btn_ver.setEnabled(tiene_seleccion)
        self.btn_imprimir.setEnabled(tiene_seleccion)
        
        if tiene_seleccion:
            factura_id = self.obtener_factura_seleccionada()
            factura = self.controller.obtener_factura(factura_id)
            
            if factura:
                # Habilitar botones según estado
                self.btn_confirmar.setEnabled(factura['estado'] == 'borrador')
                self.btn_anular.setEnabled(factura['estado'] in ['borrador', 'confirmada'])
            else:
                self.btn_confirmar.setEnabled(False)
                self.btn_anular.setEnabled(False)
        else:
            self.btn_confirmar.setEnabled(False)
            self.btn_anular.setEnabled(False)
    
    def obtener_factura_seleccionada(self):
        """Obtener ID de factura seleccionada"""
        fila_actual = self.tabla_facturas.currentRow()
        if fila_actual >= 0:
            return int(self.tabla_facturas.item(fila_actual, 0).text())
        return None
    
    def nueva_factura(self):
        """Crear nueva factura"""
        dialogo = FacturaDialog(self)
        dialogo.exec_()
    
    def ver_factura(self):
        """Ver/editar factura seleccionada"""
        factura_id = self.obtener_factura_seleccionada()
        if factura_id:
            dialogo = FacturaDialog(self, factura_id)
            dialogo.exec_()
    
    def confirmar_factura(self):
        """Confirmar factura seleccionada"""
        factura_id = self.obtener_factura_seleccionada()
        if factura_id:
            respuesta = QMessageBox.question(
                self,
                "Confirmar Factura",
                "¿Está seguro de que desea confirmar esta factura?\n"
                "Esta acción actualizará el stock de productos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                self.controller.confirmar_factura(factura_id)
    
    def anular_factura(self):
        """Anular factura seleccionada"""
        factura_id = self.obtener_factura_seleccionada()
        if factura_id:
            from PyQt5.QtWidgets import QInputDialog
            
            motivo, ok = QInputDialog.getText(
                self,
                "Anular Factura",
                "Ingrese el motivo de anulación:"
            )
            
            if ok:
                self.controller.anular_factura(factura_id, motivo)
    
    def imprimir_factura(self):
        """Imprimir factura seleccionada"""
        factura_id = self.obtener_factura_seleccionada()
        if factura_id:
            # TODO: Implementar generación de PDF
            QMessageBox.information(self, "Información", "Función de impresión en desarrollo")
    
    def aplicar_filtros(self):
        """Aplicar filtros de búsqueda"""
        self.cargar_facturas()
    
    def limpiar_filtros(self):
        """Limpiar filtros de búsqueda"""
        self.combo_estado.setCurrentIndex(0)
        self.txt_numero.clear()
        self.date_desde.setDate(QDate.currentDate().addDays(-30))
        self.date_hasta.setDate(QDate.currentDate())
        self.cargar_facturas()
    
    @pyqtSlot(dict)
    def on_factura_creada(self, factura):
        """Manejar factura creada"""
        QMessageBox.information(self, "Éxito", "Factura creada correctamente")
        self.cargar_facturas()
    
    @pyqtSlot(dict)
    def on_factura_actualizada(self, factura):
        """Manejar factura actualizada"""
        self.cargar_facturas()
    
    @pyqtSlot(int)
    def on_factura_confirmada(self, factura_id):
        """Manejar factura confirmada"""
        QMessageBox.information(self, "Éxito", "Factura confirmada correctamente")
        self.cargar_facturas()
    
    @pyqtSlot(int)
    def on_factura_anulada(self, factura_id):
        """Manejar factura anulada"""
        QMessageBox.information(self, "Éxito", "Factura anulada correctamente")
        self.cargar_facturas()
    
    @pyqtSlot(str)
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)
```

---

## Configuración del Entorno de Desarrollo

### Requisitos Previos
- Python 3.8 o superior
- MySQL Server 8.0 o superior
- Git para control de versiones

### Instalación del Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
venv\Scripts\activate

# Activar entorno virtual (macOS/Linux)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Estructura de Directorios
```
sales-cost-system/
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── config/
│   ├── __init__.py
│   ├── database.py         # Configuración de conexión a BD
│   └── settings.py         # Configuraciones generales
├── models/
│   ├── __init__.py
│   ├── base_model.py       # Clase base para modelos
│   ├── producto.py         # Modelo de productos
│   ├── cliente.py          # Modelo de clientes
│   ├── factura.py          # Modelo de facturas
│   └── pago.py             # Modelo de pagos
├── views/
│   ├── __init__.py
│   ├── main_window.py      # Ventana principal
│   ├── productos_view.py   # Vista de productos
│   ├── clientes_view.py    # Vista de clientes
│   ├── facturacion_view.py # Vista de facturación
│   └── cuentas_view.py     # Vista de cuentas pendientes
├── controllers/
│   ├── __init__.py
│   ├── producto_controller.py
│   ├── cliente_controller.py
│   ├── factura_controller.py
│   └── pago_controller.py
├── utils/
│   ├── __init__.py
│   ├── validators.py       # Validaciones de datos
│   ├── formatters.py       # Formateo de datos
│   └── exceptions.py       # Excepciones personalizadas
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_controllers.py
    └── test_views.py
```

---

## Módulo de Gestión de Productos

### Funcionalidades Principales
- **Crear Producto**: Registro de nuevos productos con validación
- **Leer Productos**: Listado y búsqueda de productos
- **Actualizar Producto**: Modificación de datos existentes
- **Eliminar Producto**: Eliminación con validación de dependencias

### Implementación del Modelo

#### models/producto.py
```python
from config.database import DatabaseConnection
from utils.validators import ProductoValidator
from utils.exceptions import ProductoError
from decimal import Decimal
from datetime import datetime

class Producto:
    def __init__(self):
        self.db = DatabaseConnection()
        self.validator = ProductoValidator()
    
    def crear(self, codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta):
        """
        Crear un nuevo producto
        
        Args:
            codigo_sku (str): Código único del producto
            nombre (str): Nombre del producto
            descripcion (str): Descripción del producto
            costo_adquisicion (Decimal): Costo de adquisición
            precio_venta (Decimal): Precio de venta
            
        Returns:
            int: ID del producto creado
            
        Raises:
            ProductoError: Si los datos no son válidos
        """
        # Validar datos de entrada
        self.validator.validar_producto(codigo_sku, nombre, costo_adquisicion, precio_venta)
        
        # Verificar que el SKU no exista
        if self.existe_sku(codigo_sku):
            raise ProductoError(f"El código SKU '{codigo_sku}' ya existe")
        
        query = """
        INSERT INTO productos (codigo_sku, nombre, descripcion, costo_adquisicion, precio_venta)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (codigo_sku, nombre, descripcion, 
                                     float(costo_adquisicion), float(precio_venta)))
                conn.commit()
                return cursor.lastrowid
    
    def obtener_todos(self, filtro=None, orden='nombre'):
        """
        Obtener lista de productos con filtros opcionales
        
        Args:
            filtro (str): Filtro de búsqueda por nombre o SKU
            orden (str): Campo de ordenamiento
            
        Returns:
            list: Lista de productos
        """
        base_query = """
        SELECT id, codigo_sku, nombre, descripcion, costo_adquisicion, 
               precio_venta, fecha_creacion, fecha_actualizacion
        FROM productos
        """
        
        params = []
        if filtro:
            base_query += " WHERE nombre LIKE %s OR codigo_sku LIKE %s"
            params.extend([f"%{filtro}%", f"%{filtro}%"])
        
        base_query += f" ORDER BY {orden}"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                return cursor.fetchall()
    
    def obtener_por_id(self, producto_id):
        """Obtener producto por ID"""
        query = "SELECT * FROM productos WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (producto_id,))
                return cursor.fetchone()
    
    def actualizar(self, producto_id, **kwargs):
        """
        Actualizar producto existente
        
        Args:
            producto_id (int): ID del producto
            **kwargs: Campos a actualizar
        """
        campos_permitidos = ['codigo_sku', 'nombre', 'descripcion', 
                           'costo_adquisicion', 'precio_venta']
        
        campos_actualizar = {k: v for k, v in kwargs.items() if k in campos_permitidos}
        
        if not campos_actualizar:
            raise ProductoError("No hay campos válidos para actualizar")
        
        # Validar SKU único si se está actualizando
        if 'codigo_sku' in campos_actualizar:
            if self.existe_sku(campos_actualizar['codigo_sku'], excluir_id=producto_id):
                raise ProductoError(f"El código SKU '{campos_actualizar['codigo_sku']}' ya existe")
        
        set_clause = ", ".join([f"{campo} = %s" for campo in campos_actualizar.keys()])
        query = f"UPDATE productos SET {set_clause} WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, list(campos_actualizar.values()) + [producto_id])
                conn.commit()
                return cursor.rowcount > 0
    
    def eliminar(self, producto_id):
        """
        Eliminar producto con validación de dependencias
        
        Args:
            producto_id (int): ID del producto a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
            
        Raises:
            ProductoError: Si el producto tiene dependencias
        """
        # Verificar si el producto está en facturas
        if self.tiene_facturas(producto_id):
            raise ProductoError("No se puede eliminar el producto porque tiene facturas asociadas")
        
        query = "DELETE FROM productos WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (producto_id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def existe_sku(self, codigo_sku, excluir_id=None):
        """Verificar si existe un SKU"""
        query = "SELECT COUNT(*) as count FROM productos WHERE codigo_sku = %s"
        params = [codigo_sku]
        
        if excluir_id:
            query += " AND id != %s"
            params.append(excluir_id)
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['count'] > 0
    
    def tiene_facturas(self, producto_id):
        """Verificar si el producto tiene facturas asociadas"""
        query = "SELECT COUNT(*) as count FROM factura_detalles WHERE producto_id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (producto_id,))
                result = cursor.fetchone()
                return result['count'] > 0
    
    def calcular_margen_ganancia(self, producto_id):
        """Calcular margen de ganancia del producto"""
        producto = self.obtener_por_id(producto_id)
        if not producto:
            return None
        
        costo = Decimal(str(producto['costo_adquisicion']))
        precio = Decimal(str(producto['precio_venta']))
        
        if costo == 0:
            return None
        
        margen = ((precio - costo) / costo) * 100
        return float(margen)
```

### Implementación del Controlador

#### controllers/producto_controller.py
```python
from models.producto import Producto
from utils.exceptions import ProductoError
from PyQt5.QtCore import QObject, pyqtSignal
from decimal import Decimal, InvalidOperation

class ProductoController(QObject):
    # Señales para comunicación con la vista
    producto_creado = pyqtSignal(dict)
    producto_actualizado = pyqtSignal(dict)
    producto_eliminado = pyqtSignal(int)
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.modelo = Producto()
    
    def crear_producto(self, datos_producto):
        """
        Crear nuevo producto desde la vista
        
        Args:
            datos_producto (dict): Datos del producto
        """
        try:
            # Convertir strings a tipos apropiados
            costo = Decimal(str(datos_producto['costo_adquisicion']))
            precio = Decimal(str(datos_producto['precio_venta']))
            
            producto_id = self.modelo.crear(
                codigo_sku=datos_producto['codigo_sku'],
                nombre=datos_producto['nombre'],
                descripcion=datos_producto.get('descripcion', ''),
                costo_adquisicion=costo,
                precio_venta=precio
            )
            
            # Obtener el producto creado para emitir señal
            producto_creado = self.modelo.obtener_por_id(producto_id)
            self.producto_creado.emit(producto_creado)
            
        except (ProductoError, InvalidOperation, ValueError) as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def obtener_productos(self, filtro=None):
        """Obtener lista de productos"""
        try:
            return self.modelo.obtener_todos(filtro=filtro)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener productos: {str(e)}")
            return []
    
    def actualizar_producto(self, producto_id, datos_producto):
        """Actualizar producto existente"""
        try:
            # Preparar datos para actualización
            datos_actualizacion = {}
            
            for campo, valor in datos_producto.items():
                if campo in ['costo_adquisicion', 'precio_venta']:
                    datos_actualizacion[campo] = Decimal(str(valor))
                else:
                    datos_actualizacion[campo] = valor
            
            if self.modelo.actualizar(producto_id, **datos_actualizacion):
                producto_actualizado = self.modelo.obtener_por_id(producto_id)
                self.producto_actualizado.emit(producto_actualizado)
            else:
                self.error_ocurrido.emit("No se pudo actualizar el producto")
                
        except (ProductoError, InvalidOperation, ValueError) as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def eliminar_producto(self, producto_id):
        """Eliminar producto"""
        try:
            if self.modelo.eliminar(producto_id):
                self.producto_eliminado.emit(producto_id)
            else:
                self.error_ocurrido.emit("No se pudo eliminar el producto")
                
        except ProductoError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def obtener_margen_ganancia(self, producto_id):
        """Obtener margen de ganancia del producto"""
        try:
            return self.modelo.calcular_margen_ganancia(producto_id)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al calcular margen: {str(e)}")
            return None
```

### Implementación de la Vista

#### views/productos_view.py
```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                            QDialog, QFormLayout, QTextEdit, QMessageBox,
                            QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSlot
from controllers.producto_controller import ProductoController
from decimal import Decimal

class ProductosView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = ProductoController()
        self.setup_ui()
        self.conectar_senales()
        self.cargar_productos()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("Nuevo Producto")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_actualizar = QPushButton("Actualizar Lista")
        
        # Campo de búsqueda
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre o SKU...")
        self.btn_buscar = QPushButton("Buscar")
        
        toolbar_layout.addWidget(self.btn_nuevo)
        toolbar_layout.addWidget(self.btn_editar)
        toolbar_layout.addWidget(self.btn_eliminar)
        toolbar_layout.addWidget(self.btn_actualizar)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Buscar:"))
        toolbar_layout.addWidget(self.txt_buscar)
        toolbar_layout.addWidget(self.btn_buscar)
        
        # Tabla de productos
        self.tabla_productos = QTableWidget()
        self.configurar_tabla()
        
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.tabla_productos)
        
        self.setLayout(layout)
        
        # Estado inicial de botones
        self.btn_editar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)
    
    def configurar_tabla(self):
        """Configurar tabla de productos"""
        columnas = ['ID', 'SKU', 'Nombre', 'Descripción', 'Costo', 'Precio', 'Margen %', 'Fecha Creación']
        self.tabla_productos.setColumnCount(len(columnas))
        self.tabla_productos.setHorizontalHeaderLabels(columnas)
        
        # Configurar comportamiento de la tabla
        self.tabla_productos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_productos.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_productos.setAlternatingRowColors(True)
        
        # Ajustar columnas
        header = self.tabla_productos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # SKU
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Nombre
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Descripción
        
        # Ocultar columna ID
        self.tabla_productos.setColumnHidden(0, True)
    
    def conectar_senales(self):
        """Conectar señales y slots"""
        # Botones
        self.btn_nuevo.clicked.connect(self.nuevo_producto)
        self.btn_editar.clicked.connect(self.editar_producto)
        self.btn_eliminar.clicked.connect(self.eliminar_producto)
        self.btn_actualizar.clicked.connect(self.cargar_productos)
        self.btn_buscar.clicked.connect(self.buscar_productos)
        
        # Tabla
        self.tabla_productos.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla_productos.itemDoubleClicked.connect(self.editar_producto)
        
        # Campo de búsqueda
        self.txt_buscar.returnPressed.connect(self.buscar_productos)
        
        # Señales del controlador
        self.controller.producto_creado.connect(self.on_producto_creado)
        self.controller.producto_actualizado.connect(self.on_producto_actualizado)
        self.controller.producto_eliminado.connect(self.on_producto_eliminado)
        self.controller.error_ocurrido.connect(self.mostrar_error)
    
    def cargar_productos(self):
        """Cargar productos en la tabla"""
        filtro = self.txt_buscar.text().strip() if self.txt_buscar.text().strip() else None
        productos = self.controller.obtener_productos(filtro=filtro)
        
        self.tabla_productos.setRowCount(len(productos))
        
        for row, producto in enumerate(productos):
            # Calcular margen de ganancia
            margen = self.controller.obtener_margen_ganancia(producto['id'])
            margen_str = f"{margen:.2f}%" if margen is not None else "N/A"
            
            items = [
                str(producto['id']),
                producto['codigo_sku'],
                producto['nombre'],
                producto['descripcion'] or '',
                f"${producto['costo_adquisicion']:.2f}",
                f"${producto['precio_venta']:.2f}",
                margen_str,
                producto['fecha_creacion'].strftime('%Y-%m-%d') if producto['fecha_creacion'] else ''
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                self.tabla_productos.setItem(row, col, table_item)
    
    def seleccion_cambiada(self):
        """Manejar cambio de selección en la tabla"""
        tiene_seleccion = len(self.tabla_productos.selectedItems()) > 0
        self.btn_editar.setEnabled(tiene_seleccion)
        self.btn_eliminar.setEnabled(tiene_seleccion)
    
    def obtener_producto_seleccionado(self):
        """Obtener ID del producto seleccionado"""
        fila_actual = self.tabla_productos.currentRow()
        if fila_actual >= 0:
            return int(self.tabla_productos.item(fila_actual, 0).text())
        return None
    
    def nuevo_producto(self):
        """Abrir diálogo para nuevo producto"""
        dialogo = ProductoDialog(self)
        if dialogo.exec_() == QDialog.Accepted:
            datos = dialogo.obtener_datos()
            self.controller.crear_producto(datos)
    
    def editar_producto(self):
        """Editar producto seleccionado"""
        producto_id = self.obtener_producto_seleccionado()
        if producto_id:
            # Obtener datos del producto
            productos = self.controller.obtener_productos()
            producto = next((p for p in productos if p['id'] == producto_id), None)
            
            if producto:
                dialogo = ProductoDialog(self, producto)
                if dialogo.exec_() == QDialog.Accepted:
                    datos = dialogo.obtener_datos()
                    self.controller.actualizar_producto(producto_id, datos)
    
    def eliminar_producto(self):
        """Eliminar producto seleccionado"""
        producto_id = self.obtener_producto_seleccionado()
        if producto_id:
            fila = self.tabla_productos.currentRow()
            nombre_producto = self.tabla_productos.item(fila, 2).text()
            
            respuesta = QMessageBox.question(
                self, 
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar el producto '{nombre_producto}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                self.controller.eliminar_producto(producto_id)
    
    def buscar_productos(self):
        """Buscar productos"""
        self.cargar_productos()
    
    @pyqtSlot(dict)
    def on_producto_creado(self, producto):
        """Manejar producto creado"""
        QMessageBox.information(self, "Éxito", "Producto creado correctamente")
        self.cargar_productos()
    
    @pyqtSlot(dict)
    def on_producto_actualizado(self, producto):
        """Manejar producto actualizado"""
        QMessageBox.information(self, "Éxito", "Producto actualizado correctamente")
        self.cargar_productos()
    
    @pyqtSlot(int)
    def on_producto_eliminado(self, producto_id):
        """Manejar producto eliminado"""
        QMessageBox.information(self, "Éxito", "Producto eliminado correctamente")
        self.cargar_productos()
    
    @pyqtSlot(str)
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)


class ProductoDialog(QDialog):
    """Diálogo para crear/editar productos"""
    
    def __init__(self, parent=None, producto=None):
        super().__init__(parent)
        self.producto = producto
        self.setup_ui()
        
        if producto:
            self.cargar_datos()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Nuevo Producto" if not self.producto else "Editar Producto")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Formulario
        form_layout = QFormLayout()
        
        self.txt_sku = QLineEdit()
        self.txt_nombre = QLineEdit()
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setMaximumHeight(80)
        self.txt_costo = QLineEdit()
        self.txt_precio = QLineEdit()
        
        form_layout.addRow("Código SKU:", self.txt_sku)
        form_layout.addRow("Nombre:", self.txt_nombre)
        form_layout.addRow("Descripción:", self.txt_descripcion)
        form_layout.addRow("Costo de Adquisición:", self.txt_costo)
        form_layout.addRow("Precio de Venta:", self.txt_precio)
        
        # Botones
        botones_layout = QHBoxLayout()
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_cancelar = QPushButton("Cancelar")
        
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_aceptar)
        botones_layout.addWidget(self.btn_cancelar)
        
        layout.addLayout(form_layout)
        layout.addLayout(botones_layout)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_aceptar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)
    
    def cargar_datos(self):
        """Cargar datos del producto en el formulario"""
        if self.producto:
            self.txt_sku.setText(self.producto['codigo_sku'])
            self.txt_nombre.setText(self.producto['nombre'])
            self.txt_descripcion.setPlainText(self.producto['descripcion'] or '')
            self.txt_costo.setText(str(self.producto['costo_adquisicion']))
            self.txt_precio.setText(str(self.producto['precio_venta']))
    
    def obtener_datos(self):
        """Obtener datos del formulario"""
        return {
            'codigo_sku': self.txt_sku.text().strip(),
            'nombre': self.txt_nombre.text().strip(),
            'descripcion': self.txt_descripcion.toPlainText().strip(),
            'costo_adquisicion': self.txt_costo.text().strip(),
            'precio_venta': self.txt_precio.text().strip()
        }
    
    def accept(self):
        """Validar y aceptar el diálogo"""
        datos = self.obtener_datos()
        
        # Validaciones básicas
        if not datos['codigo_sku']:
            QMessageBox.warning(self, "Error", "El código SKU es obligatorio")
            return
        
        if not datos['nombre']:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio")
            return
        
        try:
            float(datos['costo_adquisicion'])
            float(datos['precio_venta'])
        except ValueError:
            QMessageBox.warning(self, "Error", "Los valores de costo y precio deben ser números válidos")
            return
        
        super().accept()
```

### Validaciones y Utilidades

#### utils/validators.py
```python
from decimal import Decimal, InvalidOperation
from utils.exceptions import ProductoError
import re

class ProductoValidator:
    """Validador para datos de productos"""
    
    def validar_producto(self, codigo_sku, nombre, costo_adquisicion, precio_venta):
        """
        Validar datos completos del producto
        
        Args:
            codigo_sku (str): Código SKU
            nombre (str): Nombre del producto
            costo_adquisicion (Decimal): Costo de adquisición
            precio_venta (Decimal): Precio de venta
            
        Raises:
            ProductoError: Si algún dato no es válido
        """
        self.validar_sku(codigo_sku)
        self.validar_nombre(nombre)
        self.validar_precio(costo_adquisicion, "costo de adquisición")
        self.validar_precio(precio_venta, "precio de venta")
        
        # Validar que el precio sea mayor al costo
        if precio_venta <= costo_adquisicion:
            raise ProductoError("El precio de venta debe ser mayor al costo de adquisición")
    
    def validar_sku(self, codigo_sku):
        """Validar código SKU"""
        if not codigo_sku or not codigo_sku.strip():
            raise ProductoError("El código SKU es obligatorio")
        
        if len(codigo_sku.strip()) > 50:
            raise ProductoError("El código SKU no puede tener más de 50 caracteres")
        
        # Validar formato alfanumérico con guiones y guiones bajos
        if not re.match(r'^[A-Za-z0-9_-]+$', codigo_sku.strip()):
            raise ProductoError("El código SKU solo puede contener letras, números, guiones y guiones bajos")
    
    def validar_nombre(self, nombre):
        """Validar nombre del producto"""
        if not nombre or not nombre.strip():
            raise ProductoError("El nombre del producto es obligatorio")
        
        if len(nombre.strip()) > 255:
            raise ProductoError("El nombre no puede tener más de 255 caracteres")
    
    def validar_precio(self, precio, campo_nombre):
        """Validar precio/costo"""
        try:
            precio_decimal = Decimal(str(precio))
            if precio_decimal < 0:
                raise ProductoError(f"El {campo_nombre} no puede ser negativo")
            if precio_decimal > Decimal('99999999.99'):
                raise ProductoError(f"El {campo_nombre} es demasiado grande")
        except (InvalidOperation, ValueError):
            raise ProductoError(f"El {campo_nombre} debe ser un número válido")
```

#### utils/exceptions.py
```python
class ProductoError(Exception):
    """Excepción personalizada para errores de productos"""
    pass

class ClienteError(Exception):
    """Excepción personalizada para errores de clientes"""
    pass

class FacturaError(Exception):
    """Excepción personalizada para errores de facturación"""
    pass

class PagoError(Exception):
    """Excepción personalizada para errores de pagos"""
    pass

class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos"""
    pass
```

---

## Pruebas Unitarias para Módulo de Productos

#### tests/test_producto_model.py
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from models.producto import Producto
from utils.exceptions import ProductoError

class TestProductoModel(unittest.TestCase):
    
    def setUp(self):
        """Configurar pruebas"""
        self.producto = Producto()
        self.producto.db = Mock()
    
    def test_crear_producto_exitoso(self):
        """Probar creación exitosa de producto"""
        # Configurar mocks
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.producto.db.get_connection.return_value.__enter__.return_value = mock_connection
        
        # Mock para validaciones
        with patch.object(self.producto, 'existe_sku', return_value=False):
            resultado = self.producto.crear(
                codigo_sku="TEST001",
                nombre="Producto Test",
                descripcion="Descripción test",
                costo_adquisicion=Decimal('10.00'),
                precio_venta=Decimal('15.00')
            )
        
        self.assertEqual(resultado, 1)
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
    
    def test_crear_producto_sku_duplicado(self):
        """Probar error por SKU duplicado"""
        with patch.object(self.producto, 'existe_sku', return_value=True):
            with self.assertRaises(ProductoError) as context:
                self.producto.crear(
                    codigo_sku="TEST001",
                    nombre="Producto Test",
                    descripcion="Descripción test",
                    costo_adquisicion=Decimal('10.00'),
                    precio_venta=Decimal('15.00')
                )
            
            self.assertIn("ya existe", str(context.exception))
    
    def test_obtener_todos_sin_filtro(self):
        """Probar obtención de todos los productos"""
        # Configurar mock
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'nombre': 'Producto 1'},
            {'id': 2, 'nombre': 'Producto 2'}
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        self.producto.db.get_connection.return_value.__enter__.return_value = mock_connection
        
        resultado = self.producto.obtener_todos()
        
        self.assertEqual(len(resultado), 2)
        mock_cursor.execute.assert_called_once()
    
    def test_calcular_margen_ganancia(self):
        """Probar cálculo de margen de ganancia"""
        # Mock del producto
        producto_mock = {
            'costo_adquisicion': Decimal('10.00'),
            'precio_venta': Decimal('15.00')
        }
        
        with patch.object(self.producto, 'obtener_por_id', return_value=producto_mock):
            margen = self.producto.calcular_margen_ganancia(1)
            self.assertEqual(margen, 50.0)  # 50% de margen
    
    def test_eliminar_producto_con_facturas(self):
        """Probar error al eliminar producto con facturas"""
        with patch.object(self.producto, 'tiene_facturas', return_value=True):
            with self.assertRaises(ProductoError) as context:
                self.producto.eliminar(1)
            
            self.assertIn("facturas asociadas", str(context.exception))

if __name__ == '__main__':
    unittest.main()
```

---

## Módulo de Gestión de Clientes

### Funcionalidades Principales
- **Crear Cliente**: Registro de nuevos clientes con validación
- **Leer Clientes**: Listado y búsqueda de clientes
- **Actualizar Cliente**: Modificación de datos existentes
- **Eliminar Cliente**: Eliminación con validación de dependencias
- **Historial de Compras**: Visualización del historial de facturas por cliente

### Implementación del Modelo

#### models/cliente.py
```python
from config.database import DatabaseConnection
from utils.validators import ClienteValidator
from utils.exceptions import ClienteError
from datetime import datetime

class Cliente:
    def __init__(self):
        self.db = DatabaseConnection()
        self.validator = ClienteValidator()
    
    def crear(self, nombre_completo, numero_identificacion=None, 
              contacto_telefono=None, contacto_email=None):
        """
        Crear un nuevo cliente
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Returns:
            int: ID del cliente creado
            
        Raises:
            ClienteError: Si los datos no son válidos
        """
        # Validar datos de entrada
        self.validator.validar_cliente(nombre_completo, numero_identificacion, 
                                     contacto_telefono, contacto_email)
        
        # Verificar que la identificación no exista (si se proporciona)
        if numero_identificacion and self.existe_identificacion(numero_identificacion):
            raise ClienteError(f"Ya existe un cliente con la identificación '{numero_identificacion}'")
        
        query = """
        INSERT INTO clientes (nombre_completo, numero_identificacion, 
                            contacto_telefono, contacto_email)
        VALUES (%s, %s, %s, %s)
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (nombre_completo, numero_identificacion,
                                     contacto_telefono, contacto_email))
                conn.commit()
                return cursor.lastrowid
    
    def obtener_todos(self, filtro=None, orden='nombre_completo'):
        """
        Obtener lista de clientes con filtros opcionales
        
        Args:
            filtro (str): Filtro de búsqueda por nombre o identificación
            orden (str): Campo de ordenamiento
            
        Returns:
            list: Lista de clientes
        """
        base_query = """
        SELECT id, nombre_completo, numero_identificacion, contacto_telefono,
               contacto_email, fecha_creacion, fecha_actualizacion
        FROM clientes
        """
        
        params = []
        if filtro:
            base_query += """ 
            WHERE nombre_completo LIKE %s 
            OR numero_identificacion LIKE %s 
            OR contacto_email LIKE %s
            """
            filtro_param = f"%{filtro}%"
            params.extend([filtro_param, filtro_param, filtro_param])
        
        base_query += f" ORDER BY {orden}"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(base_query, params)
                return cursor.fetchall()
    
    def obtener_por_id(self, cliente_id):
        """Obtener cliente por ID"""
        query = "SELECT * FROM clientes WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id,))
                return cursor.fetchone()
    
    def actualizar(self, cliente_id, **kwargs):
        """
        Actualizar cliente existente
        
        Args:
            cliente_id (int): ID del cliente
            **kwargs: Campos a actualizar
        """
        campos_permitidos = ['nombre_completo', 'numero_identificacion', 
                           'contacto_telefono', 'contacto_email']
        
        campos_actualizar = {k: v for k, v in kwargs.items() if k in campos_permitidos}
        
        if not campos_actualizar:
            raise ClienteError("No hay campos válidos para actualizar")
        
        # Validar identificación única si se está actualizando
        if 'numero_identificacion' in campos_actualizar:
            if (campos_actualizar['numero_identificacion'] and 
                self.existe_identificacion(campos_actualizar['numero_identificacion'], 
                                         excluir_id=cliente_id)):
                raise ClienteError(f"Ya existe un cliente con la identificación '{campos_actualizar['numero_identificacion']}'")
        
        set_clause = ", ".join([f"{campo} = %s" for campo in campos_actualizar.keys()])
        query = f"UPDATE clientes SET {set_clause} WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, list(campos_actualizar.values()) + [cliente_id])
                conn.commit()
                return cursor.rowcount > 0
    
    def eliminar(self, cliente_id):
        """
        Eliminar cliente con validación de dependencias
        
        Args:
            cliente_id (int): ID del cliente a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
            
        Raises:
            ClienteError: Si el cliente tiene dependencias
        """
        # Verificar si el cliente tiene facturas
        if self.tiene_facturas(cliente_id):
            raise ClienteError("No se puede eliminar el cliente porque tiene facturas asociadas")
        
        query = "DELETE FROM clientes WHERE id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def existe_identificacion(self, numero_identificacion, excluir_id=None):
        """Verificar si existe una identificación"""
        query = "SELECT COUNT(*) as count FROM clientes WHERE numero_identificacion = %s"
        params = [numero_identificacion]
        
        if excluir_id:
            query += " AND id != %s"
            params.append(excluir_id)
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['count'] > 0
    
    def tiene_facturas(self, cliente_id):
        """Verificar si el cliente tiene facturas asociadas"""
        query = "SELECT COUNT(*) as count FROM facturas WHERE cliente_id = %s"
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id,))
                result = cursor.fetchone()
                return result['count'] > 0
    
    def obtener_historial_compras(self, cliente_id, limite=None):
        """
        Obtener historial de compras del cliente
        
        Args:
            cliente_id (int): ID del cliente
            limite (int): Límite de registros a obtener
            
        Returns:
            list: Lista de facturas del cliente
        """
        query = """
        SELECT f.id, f.numero_factura, f.fecha_factura, f.total_factura, f.estado,
               COUNT(fd.id) as total_items,
               COALESCE(SUM(p.monto_pago), 0) as total_pagado
        FROM facturas f
        LEFT JOIN factura_detalles fd ON f.id = fd.factura_id
        LEFT JOIN pagos p ON f.id = p.factura_id
        WHERE f.cliente_id = %s
        GROUP BY f.id
        ORDER BY f.fecha_factura DESC
        """
        
        params = [cliente_id]
        if limite:
            query += " LIMIT %s"
            params.append(limite)
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    
    def obtener_estadisticas_cliente(self, cliente_id):
        """
        Obtener estadísticas del cliente
        
        Args:
            cliente_id (int): ID del cliente
            
        Returns:
            dict: Estadísticas del cliente
        """
        query = """
        SELECT 
            COUNT(f.id) as total_facturas,
            COALESCE(SUM(f.total_factura), 0) as total_compras,
            COALESCE(SUM(CASE WHEN f.estado = 'pendiente_pago' THEN f.total_factura ELSE 0 END), 0) as total_pendiente,
            COALESCE(AVG(f.total_factura), 0) as promedio_compra,
            MAX(f.fecha_factura) as ultima_compra
        FROM facturas f
        WHERE f.cliente_id = %s
        """
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (cliente_id,))
                return cursor.fetchone()
```

### Implementación del Controlador

#### controllers/cliente_controller.py
```python
from models.cliente import Cliente
from utils.exceptions import ClienteError
from PyQt5.QtCore import QObject, pyqtSignal

class ClienteController(QObject):
    # Señales para comunicación con la vista
    cliente_creado = pyqtSignal(dict)
    cliente_actualizado = pyqtSignal(dict)
    cliente_eliminado = pyqtSignal(int)
    error_ocurrido = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.modelo = Cliente()
    
    def crear_cliente(self, datos_cliente):
        """
        Crear nuevo cliente desde la vista
        
        Args:
            datos_cliente (dict): Datos del cliente
        """
        try:
            cliente_id = self.modelo.crear(
                nombre_completo=datos_cliente['nombre_completo'],
                numero_identificacion=datos_cliente.get('numero_identificacion'),
                contacto_telefono=datos_cliente.get('contacto_telefono'),
                contacto_email=datos_cliente.get('contacto_email')
            )
            
            # Obtener el cliente creado para emitir señal
            cliente_creado = self.modelo.obtener_por_id(cliente_id)
            self.cliente_creado.emit(cliente_creado)
            
        except ClienteError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def obtener_clientes(self, filtro=None):
        """Obtener lista de clientes"""
        try:
            return self.modelo.obtener_todos(filtro=filtro)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener clientes: {str(e)}")
            return []
    
    def actualizar_cliente(self, cliente_id, datos_cliente):
        """Actualizar cliente existente"""
        try:
            if self.modelo.actualizar(cliente_id, **datos_cliente):
                cliente_actualizado = self.modelo.obtener_por_id(cliente_id)
                self.cliente_actualizado.emit(cliente_actualizado)
            else:
                self.error_ocurrido.emit("No se pudo actualizar el cliente")
                
        except ClienteError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def eliminar_cliente(self, cliente_id):
        """Eliminar cliente"""
        try:
            if self.modelo.eliminar(cliente_id):
                self.cliente_eliminado.emit(cliente_id)
            else:
                self.error_ocurrido.emit("No se pudo eliminar el cliente")
                
        except ClienteError as e:
            self.error_ocurrido.emit(str(e))
        except Exception as e:
            self.error_ocurrido.emit(f"Error inesperado: {str(e)}")
    
    def obtener_historial_compras(self, cliente_id):
        """Obtener historial de compras del cliente"""
        try:
            return self.modelo.obtener_historial_compras(cliente_id)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener historial: {str(e)}")
            return []
    
    def obtener_estadisticas_cliente(self, cliente_id):
        """Obtener estadísticas del cliente"""
        try:
            return self.modelo.obtener_estadisticas_cliente(cliente_id)
        except Exception as e:
            self.error_ocurrido.emit(f"Error al obtener estadísticas: {str(e)}")
            return None
```

### Implementación de la Vista

#### views/clientes_view.py
```python
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
                            QDialog, QFormLayout, QMessageBox, QHeaderView,
                            QAbstractItemView, QTabWidget, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSlot
from controllers.cliente_controller import ClienteController

class ClientesView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = ClienteController()
        self.setup_ui()
        self.conectar_senales()
        self.cargar_clientes()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        self.btn_nuevo = QPushButton("Nuevo Cliente")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_historial = QPushButton("Ver Historial")
        self.btn_actualizar = QPushButton("Actualizar Lista")
        
        # Campo de búsqueda
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, identificación o email...")
        self.btn_buscar = QPushButton("Buscar")
        
        toolbar_layout.addWidget(self.btn_nuevo)
        toolbar_layout.addWidget(self.btn_editar)
        toolbar_layout.addWidget(self.btn_eliminar)
        toolbar_layout.addWidget(self.btn_historial)
        toolbar_layout.addWidget(self.btn_actualizar)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Buscar:"))
        toolbar_layout.addWidget(self.txt_buscar)
        toolbar_layout.addWidget(self.btn_buscar)
        
        # Tabla de clientes
        self.tabla_clientes = QTableWidget()
        self.configurar_tabla()
        
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.tabla_clientes)
        
        self.setLayout(layout)
        
        # Estado inicial de botones
        self.btn_editar.setEnabled(False)
        self.btn_eliminar.setEnabled(False)
        self.btn_historial.setEnabled(False)
    
    def configurar_tabla(self):
        """Configurar tabla de clientes"""
        columnas = ['ID', 'Nombre Completo', 'Identificación', 'Teléfono', 
                   'Email', 'Fecha Registro']
        self.tabla_clientes.setColumnCount(len(columnas))
        self.tabla_clientes.setHorizontalHeaderLabels(columnas)
        
        # Configurar comportamiento de la tabla
        self.tabla_clientes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_clientes.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_clientes.setAlternatingRowColors(True)
        
        # Ajustar columnas
        header = self.tabla_clientes.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Nombre
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Identificación
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Teléfono
        header.setSectionResizeMode(4, QHeaderView.Stretch)           # Email
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Fecha
        
        # Ocultar columna ID
        self.tabla_clientes.setColumnHidden(0, True)
    
    def conectar_senales(self):
        """Conectar señales y slots"""
        # Botones
        self.btn_nuevo.clicked.connect(self.nuevo_cliente)
        self.btn_editar.clicked.connect(self.editar_cliente)
        self.btn_eliminar.clicked.connect(self.eliminar_cliente)
        self.btn_historial.clicked.connect(self.ver_historial)
        self.btn_actualizar.clicked.connect(self.cargar_clientes)
        self.btn_buscar.clicked.connect(self.buscar_clientes)
        
        # Tabla
        self.tabla_clientes.itemSelectionChanged.connect(self.seleccion_cambiada)
        self.tabla_clientes.itemDoubleClicked.connect(self.editar_cliente)
        
        # Campo de búsqueda
        self.txt_buscar.returnPressed.connect(self.buscar_clientes)
        
        # Señales del controlador
        self.controller.cliente_creado.connect(self.on_cliente_creado)
        self.controller.cliente_actualizado.connect(self.on_cliente_actualizado)
        self.controller.cliente_eliminado.connect(self.on_cliente_eliminado)
        self.controller.error_ocurrido.connect(self.mostrar_error)
    
    def cargar_clientes(self):
        """Cargar clientes en la tabla"""
        filtro = self.txt_buscar.text().strip() if self.txt_buscar.text().strip() else None
        clientes = self.controller.obtener_clientes(filtro=filtro)
        
        self.tabla_clientes.setRowCount(len(clientes))
        
        for row, cliente in enumerate(clientes):
            items = [
                str(cliente['id']),
                cliente['nombre_completo'],
                cliente['numero_identificacion'] or '',
                cliente['contacto_telefono'] or '',
                cliente['contacto_email'] or '',
                cliente['fecha_creacion'].strftime('%Y-%m-%d') if cliente['fecha_creacion'] else ''
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                self.tabla_clientes.setItem(row, col, table_item)
    
    def seleccion_cambiada(self):
        """Manejar cambio de selección en la tabla"""
        tiene_seleccion = len(self.tabla_clientes.selectedItems()) > 0
        self.btn_editar.setEnabled(tiene_seleccion)
        self.btn_eliminar.setEnabled(tiene_seleccion)
        self.btn_historial.setEnabled(tiene_seleccion)
    
    def obtener_cliente_seleccionado(self):
        """Obtener ID del cliente seleccionado"""
        fila_actual = self.tabla_clientes.currentRow()
        if fila_actual >= 0:
            return int(self.tabla_clientes.item(fila_actual, 0).text())
        return None
    
    def nuevo_cliente(self):
        """Abrir diálogo para nuevo cliente"""
        dialogo = ClienteDialog(self)
        if dialogo.exec_() == QDialog.Accepted:
            datos = dialogo.obtener_datos()
            self.controller.crear_cliente(datos)
    
    def editar_cliente(self):
        """Editar cliente seleccionado"""
        cliente_id = self.obtener_cliente_seleccionado()
        if cliente_id:
            # Obtener datos del cliente
            clientes = self.controller.obtener_clientes()
            cliente = next((c for c in clientes if c['id'] == cliente_id), None)
            
            if cliente:
                dialogo = ClienteDialog(self, cliente)
                if dialogo.exec_() == QDialog.Accepted:
                    datos = dialogo.obtener_datos()
                    self.controller.actualizar_cliente(cliente_id, datos)
    
    def eliminar_cliente(self):
        """Eliminar cliente seleccionado"""
        cliente_id = self.obtener_cliente_seleccionado()
        if cliente_id:
            fila = self.tabla_clientes.currentRow()
            nombre_cliente = self.tabla_clientes.item(fila, 1).text()
            
            respuesta = QMessageBox.question(
                self, 
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar el cliente '{nombre_cliente}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                self.controller.eliminar_cliente(cliente_id)
    
    def ver_historial(self):
        """Ver historial de compras del cliente"""
        cliente_id = self.obtener_cliente_seleccionado()
        if cliente_id:
            fila = self.tabla_clientes.currentRow()
            nombre_cliente = self.tabla_clientes.item(fila, 1).text()
            
            dialogo = HistorialClienteDialog(self, cliente_id, nombre_cliente, self.controller)
            dialogo.exec_()
    
    def buscar_clientes(self):
        """Buscar clientes"""
        self.cargar_clientes()
    
    @pyqtSlot(dict)
    def on_cliente_creado(self, cliente):
        """Manejar cliente creado"""
        QMessageBox.information(self, "Éxito", "Cliente creado correctamente")
        self.cargar_clientes()
    
    @pyqtSlot(dict)
    def on_cliente_actualizado(self, cliente):
        """Manejar cliente actualizado"""
        QMessageBox.information(self, "Éxito", "Cliente actualizado correctamente")
        self.cargar_clientes()
    
    @pyqtSlot(int)
    def on_cliente_eliminado(self, cliente_id):
        """Manejar cliente eliminado"""
        QMessageBox.information(self, "Éxito", "Cliente eliminado correctamente")
        self.cargar_clientes()
    
    @pyqtSlot(str)
    def mostrar_error(self, mensaje):
        """Mostrar mensaje de error"""
        QMessageBox.critical(self, "Error", mensaje)


class ClienteDialog(QDialog):
    """Diálogo para crear/editar clientes"""
    
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente
        self.setup_ui()
        
        if cliente:
            self.cargar_datos()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Nuevo Cliente" if not self.cliente else "Editar Cliente")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout()
        
        # Formulario
        form_layout = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_identificacion = QLineEdit()
        self.txt_telefono = QLineEdit()
        self.txt_email = QLineEdit()
        
        form_layout.addRow("Nombre Completo*:", self.txt_nombre)
        form_layout.addRow("Número de Identificación:", self.txt_identificacion)
        form_layout.addRow("Teléfono:", self.txt_telefono)
        form_layout.addRow("Email:", self.txt_email)
        
        # Botones
        botones_layout = QHBoxLayout()
        self.btn_aceptar = QPushButton("Aceptar")
        self.btn_cancelar = QPushButton("Cancelar")
        
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_aceptar)
        botones_layout.addWidget(self.btn_cancelar)
        
        layout.addLayout(form_layout)
        layout.addLayout(botones_layout)
        
        self.setLayout(layout)
        
        # Conectar señales
        self.btn_aceptar.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)
    
    def cargar_datos(self):
        """Cargar datos del cliente en el formulario"""
        if self.cliente:
            self.txt_nombre.setText(self.cliente['nombre_completo'])
            self.txt_identificacion.setText(self.cliente['numero_identificacion'] or '')
            self.txt_telefono.setText(self.cliente['contacto_telefono'] or '')
            self.txt_email.setText(self.cliente['contacto_email'] or '')
    
    def obtener_datos(self):
        """Obtener datos del formulario"""
        datos = {
            'nombre_completo': self.txt_nombre.text().strip(),
            'numero_identificacion': self.txt_identificacion.text().strip() or None,
            'contacto_telefono': self.txt_telefono.text().strip() or None,
            'contacto_email': self.txt_email.text().strip() or None
        }
        return datos
    
    def accept(self):
        """Validar y aceptar el diálogo"""
        datos = self.obtener_datos()
        
        # Validaciones básicas
        if not datos['nombre_completo']:
            QMessageBox.warning(self, "Error", "El nombre completo es obligatorio")
            return
        
        # Validar email si se proporciona
        if datos['contacto_email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, datos['contacto_email']):
                QMessageBox.warning(self, "Error", "El formato del email no es válido")
                return
        
        super().accept()


class HistorialClienteDialog(QDialog):
    """Diálogo para mostrar historial de compras del cliente"""
    
    def __init__(self, parent, cliente_id, nombre_cliente, controller):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.nombre_cliente = nombre_cliente
        self.controller = controller
        self.setup_ui()
        self.cargar_datos()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle(f"Historial de Compras - {self.nombre_cliente}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Pestañas
        tabs = QTabWidget()
        
        # Pestaña de estadísticas
        self.tab_estadisticas = QWidget()
        self.setup_tab_estadisticas()
        tabs.addTab(self.tab_estadisticas, "Estadísticas")
        
        # Pestaña de historial
        self.tab_historial = QWidget()
        self.setup_tab_historial()
        tabs.addTab(self.tab_historial, "Historial de Facturas")
        
        layout.addWidget(tabs)
        
        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        
        self.setLayout(layout)
    
    def setup_tab_estadisticas(self):
        """Configurar pestaña de estadísticas"""
        layout = QVBoxLayout()
        
        self.txt_estadisticas = QTextEdit()
        self.txt_estadisticas.setReadOnly(True)
        
        layout.addWidget(self.txt_estadisticas)
        self.tab_estadisticas.setLayout(layout)
    
    def setup_tab_historial(self):
        """Configurar pestaña de historial"""
        layout = QVBoxLayout()
        
        self.tabla_historial = QTableWidget()
        columnas = ['Número Factura', 'Fecha', 'Total', 'Estado', 'Items', 'Pagado']
        self.tabla_historial.setColumnCount(len(columnas))
        self.tabla_historial.setHorizontalHeaderLabels(columnas)
        self.tabla_historial.setAlternatingRowColors(True)
        
        # Ajustar columnas
        header = self.tabla_historial.horizontalHeader()
        for i in range(len(columnas)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla_historial)
        self.tab_historial.setLayout(layout)
    
    def cargar_datos(self):
        """Cargar datos del cliente"""
        # Cargar estadísticas
        estadisticas = self.controller.obtener_estadisticas_cliente(self.cliente_id)
        if estadisticas:
            texto_estadisticas = f"""
ESTADÍSTICAS DEL CLIENTE

Nombre: {self.nombre_cliente}

Total de Facturas: {estadisticas['total_facturas']}
Total de Compras: ${estadisticas['total_compras']:.2f}
Total Pendiente: ${estadisticas['total_pendiente']:.2f}
Promedio por Compra: ${estadisticas['promedio_compra']:.2f}
Última Compra: {estadisticas['ultima_compra'].strftime('%Y-%m-%d') if estadisticas['ultima_compra'] else 'N/A'}
            """
            self.txt_estadisticas.setPlainText(texto_estadisticas.strip())
        
        # Cargar historial
        historial = self.controller.obtener_historial_compras(self.cliente_id)
        self.tabla_historial.setRowCount(len(historial))
        
        for row, factura in enumerate(historial):
            items = [
                factura['numero_factura'],
                factura['fecha_factura'].strftime('%Y-%m-%d'),
                f"${factura['total_factura']:.2f}",
                factura['estado'].replace('_', ' ').title(),
                str(factura['total_items']),
                f"${factura['total_pagado']:.2f}"
            ]
            
            for col, item in enumerate(items):
                table_item = QTableWidgetItem(str(item))
                table_item.setFlags(table_item.flags() & ~Qt.ItemIsEditable)
                self.tabla_historial.setItem(row, col, table_item)
```

### Validaciones para Clientes

#### utils/validators.py (extensión)
```python
# Agregar a la clase existente o crear nueva clase ClienteValidator

class ClienteValidator:
    """Validador para datos de clientes"""
    
    def validar_cliente(self, nombre_completo, numero_identificacion=None, 
                       contacto_telefono=None, contacto_email=None):
        """
        Validar datos completos del cliente
        
        Args:
            nombre_completo (str): Nombre completo del cliente
            numero_identificacion (str): Número de identificación
            contacto_telefono (str): Teléfono de contacto
            contacto_email (str): Email de contacto
            
        Raises:
            ClienteError: Si algún dato no es válido
        """
        self.validar_nombre(nombre_completo)
        
        if numero_identificacion:
            self.validar_identificacion(numero_identificacion)
        
        if contacto_telefono:
            self.validar_telefono(contacto_telefono)
        
        if contacto_email:
            self.validar_email(contacto_email)
    
    def validar_nombre(self, nombre_completo):
        """Validar nombre completo"""
        if not nombre_completo or not nombre_completo.strip():
            raise ClienteError("El nombre completo es obligatorio")
        
        if len(nombre_completo.strip()) > 255:
            raise ClienteError("El nombre no puede tener más de 255 caracteres")
        
        # Validar que contenga al menos dos palabras
        palabras = nombre_completo.strip().split()
        if len(palabras) < 2:
            raise ClienteError("Debe ingresar al menos nombre y apellido")
    
    def validar_identificacion(self, numero_identificacion):
        """Validar número de identificación"""
        if len(numero_identificacion.strip()) > 50:
            raise ClienteError("El número de identificación no puede tener más de 50 caracteres")
        
        # Validar formato alfanumérico
        import re
        if not re.match(r'^[A-Za-z0-9-]+$', numero_identificacion.strip()):
            raise ClienteError("El número de identificación solo puede contener letras, números y guiones")
    
    def validar_telefono(self, contacto_telefono):
        """Validar teléfono de contacto"""
        if len(contacto_telefono.strip()) > 50:
            raise ClienteError("El teléfono no puede tener más de 50 caracteres")
        
        # Validar formato de teléfono básico
        import re
        if not re.match(r'^[\d\s\-\+\(\)]+$', contacto_telefono.strip()):
            raise ClienteError("El formato del teléfono no es válido")
    
    def validar_email(self, contacto_email):
        """Validar email de contacto"""
        if len(contacto_email.strip()) > 255:
            raise ClienteError("El email no puede tener más de 255 caracteres")
        
        # Validar formato de email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, contacto_email.strip()):
            raise ClienteError("El formato del email no es válido")
```

---