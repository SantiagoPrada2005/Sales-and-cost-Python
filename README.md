# Sistema de Ventas y Costos

Sistema integral para gestión de ventas y control de costos desarrollado en Python con PyQt5 y MySQL.

## Características Principales

- **Gestión de Productos**: Registro, actualización y control de inventario
- **Gestión de Clientes**: Administración de información de clientes
- **Facturación y Ventas**: Creación y gestión de facturas
- **Cuentas Pendientes**: Control de pagos y cartera
- **Interfaz Gráfica**: Interfaz moderna desarrollada con PyQt5
- **Base de Datos**: Almacenamiento seguro en MySQL

## Requisitos del Sistema

- Python 3.8 o superior
- MySQL Server 8.0 o superior
- Sistema operativo: Windows, macOS o Linux

## Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd Sales-and-cost-Python
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos

1. Crear archivo `.env` basado en `.env.example`:
```bash
cp .env.example .env
```

2. Editar el archivo `.env` con tus credenciales de MySQL:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_NAME=sales_cost_system
```

3. Crear la base de datos en MySQL:
```sql
CREATE DATABASE sales_cost_system;
```

### 5. Ejecutar la Aplicación

```bash
python main.py
```

## Estructura del Proyecto

```
sales-cost-system/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── .env.example           # Ejemplo de configuración
├── config/                # Configuraciones
│   ├── database.py        # Conexión a BD
│   └── settings.py        # Configuraciones generales
├── models/                # Modelos de datos
│   └── base_model.py      # Clase base
├── views/                 # Interfaces de usuario
├── controllers/           # Lógica de negocio
├── utils/                 # Utilidades
│   ├── validators.py      # Validaciones
│   ├── formatters.py      # Formateo de datos
│   └── exceptions.py      # Excepciones personalizadas
├── tests/                 # Pruebas unitarias
└── logs/                  # Archivos de log
```

## Estado del Desarrollo

### ✅ Completado
- [x] Estructura del proyecto
- [x] Configuración del entorno
- [x] Conexión a base de datos
- [x] Clases base y utilidades
- [x] Sistema de logging
- [x] Validadores y formateadores

### 🚧 En Desarrollo
- [ ] Modelos de datos (Producto, Cliente, Factura, Pago)
- [ ] Interfaces de usuario (PyQt5)
- [ ] Controladores de lógica de negocio
- [ ] Esquema de base de datos
- [ ] Pruebas unitarias

### 📋 Pendiente
- [ ] Reportes y estadísticas
- [ ] Exportación de datos
- [ ] Configuración avanzada
- [ ] Documentación completa

## Desarrollo

### Ejecutar Pruebas

```bash
pytest tests/
```

### Formatear Código

```bash
black .
```

### Verificar Estilo

```bash
flake8 .
```

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## Documentación Técnica

Para información detallada sobre la implementación, consultar:
- `arquitectura.md` - Arquitectura del sistema
- `instrucciones_tecnicas.md` - Instrucciones técnicas detalladas

Claro, aquí tienes el alcance mínimo necesario para un sistema de costeo de productos de reventa y facturación, enfocado en las funcionalidades que mencionas.

Alcance Mínimo Viable (MVP)
El objetivo es desarrollar una aplicación de escritorio funcional que permita a un usuario gestionar el ciclo básico de ventas de productos de reventa, desde su registro hasta el seguimiento de pagos de clientes.

1. Módulo de Productos
Este módulo se centrará en la gestión de productos que se compran para ser revendidos.

Registro de Productos:
Campos Esenciales: Código (o SKU), Nombre/Descripción, Costo de Adquisición (cuánto te cuesta a ti) y Precio de Venta (a cuánto lo vendes).
Funcionalidad: Permitir crear, editar y eliminar productos. No se incluirá manejo de stock (inventario) en esta versión mínima para simplificar.
2. Módulo de Clientes
La gestión de clientes es fundamental para asociar ventas y deudas.

Registro de Clientes:
Campos Esenciales: Nombre completo, Número de identificación (opcional, ej. DNI, RUC) y un campo para contacto (teléfono o email).
Funcionalidad: Permitir crear, editar y eliminar clientes de la base de datos.
3. Módulo de Facturación y Ventas
Este es el núcleo del sistema, donde se registran las transacciones.

Creación de Facturas Simples:
Encabezado: Debe permitir seleccionar un cliente ya registrado y asignará automáticamente un número de factura y la fecha actual.
Cuerpo de la Factura:
Un buscador simple para encontrar y agregar productos a la factura.
Al agregar un producto, se debe pedir la cantidad. El sistema debe calcular el subtotal por línea (Cantidad x Precio de Venta).
Pie de la Factura:
El sistema debe calcular y mostrar el Total a Pagar de la factura. En esta versión mínima no se manejarán impuestos para simplificar.
Registro de Pagos (Funcionalidad Clave):
Al momento de guardar la factura, el sistema debe preguntar cómo se pagará:
Pago Total: La factura se marca como "Pagada".
Pago Parcial: Se debe habilitar un campo para ingresar el monto del abono. La factura se marcará como "Pendiente de Pago".
Sin Pago (Crédito): Se registra la factura con un pago de cero y se marca como "Pendiente de Pago".
4. Módulo de Cuentas Pendientes de Clientes
Este módulo es crucial para el seguimiento de las deudas.

Consulta de Estado de Cuenta por Cliente:
Funcionalidad: Una pantalla donde se pueda seleccionar un cliente y el sistema muestre:
Un listado de todas sus facturas, indicando el total de cada una, el monto que ha pagado y el saldo pendiente.
Un Saldo Total Adeudado por ese cliente (la suma de los saldos de todas sus facturas pendientes).
Registro de Abonos a Facturas Existentes:
Funcionalidad: En la pantalla de estado de cuenta, debe haber una opción para "Registrar un Abono" a una factura específica que esté pendiente. El sistema debe actualizar el saldo de esa factura y, por ende, el saldo total del cliente.
Tecnologías (Stack Propuesto)
Lenguaje: Python.
Interfaz Gráfica (GUI): PyQt5 (permite crear interfaces de escritorio sencillas y funcionales).
Base de Datos: MySQL (para almacenar de forma persistente los datos de productos, clientes y facturas).

Conector Python-MySQL: mysql-connector-python.
Resumen del Flujo de Usuario Mínimo
Preparación: El usuario registra sus productos (con costo y precio de venta) y a sus clientes.
Venta: El usuario crea una nueva factura, elige un cliente, agrega los productos y las cantidades.

Cobro: Al finalizar la venta, el sistema le pregunta por el pago. El usuario registra si fue total, parcial o a crédito. La factura se guarda.
Seguimiento: Más tarde, el usuario puede ir a la sección de "Cuentas Pendientes", seleccionar un cliente y ver cuánto le debe. Si el cliente realiza un abono, el usuario lo registra en el sistema sobre la factura correspondiente.
