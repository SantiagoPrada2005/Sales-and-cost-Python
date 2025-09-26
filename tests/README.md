# Pruebas de Verificación - Módulo de Clientes

Este directorio contiene las pruebas exhaustivas para el módulo de clientes del sistema de ventas y costos. Las pruebas están diseñadas para verificar que todas las funcionalidades operen según los requisitos especificados, cubriendo casos de uso típicos, escenarios límite y validando tanto el comportamiento esperado como el manejo de errores.

## Estructura de Pruebas

### 📁 Archivos de Prueba

| Archivo | Descripción | Cobertura |
|---------|-------------|-----------|
| `test_cliente.py` | Pruebas unitarias del modelo Cliente | Validaciones, CRUD, manejo de errores |
| `test_cliente_controller.py` | Pruebas del controlador de clientes | Lógica de negocio, formateo de datos |
| `test_cliente_validator.py` | Pruebas del validador de clientes | Validaciones específicas por tipo |
| `test_clientes_view.py` | Pruebas de la interfaz de usuario | Interacciones, señales, UI |
| `test_integration_cliente.py` | Pruebas de integración | Flujos completos entre componentes |
| `test_edge_cases_cliente.py` | Pruebas de casos límite | Escenarios extremos y manejo de errores |
| `test_runner.py` | Script ejecutor de pruebas | Punto de entrada único |

### 🎯 Categorías de Pruebas

#### 1. **Pruebas Unitarias**
- **Modelo (`test_cliente.py`)**
  - Validación de datos de entrada
  - Operaciones CRUD (Crear, Leer, Actualizar, Eliminar)
  - Manejo de errores de base de datos
  - Verificación de duplicados

- **Controlador (`test_cliente_controller.py`)**
  - Lógica de negocio
  - Formateo de datos para la vista
  - Limpieza y normalización de datos
  - Estadísticas y reportes

- **Validador (`test_cliente_validator.py`)**
  - Validaciones por tipo de identificación
  - Formatos de email, teléfono, fechas
  - Validaciones de longitud y caracteres
  - Manejo de campos opcionales

- **Vista (`test_clientes_view.py`)**
  - Inicialización de componentes UI
  - Interacciones de usuario
  - Señales y slots de PyQt5
  - Manejo de estados de botones

#### 2. **Pruebas de Integración**
- **Flujos Completos (`test_integration_cliente.py`)**
  - Creación completa de cliente (Validador → Modelo → Controlador)
  - Búsqueda y listado integrado
  - Actualización con validaciones
  - Eliminación con verificaciones
  - Integración Vista-Controlador

#### 3. **Pruebas de Casos Límite**
- **Escenarios Extremos (`test_edge_cases_cliente.py`)**
  - Datos con longitud máxima
  - Caracteres especiales y Unicode
  - Formatos internacionales
  - Intentos de SQL injection
  - Errores de concurrencia
  - Manejo de memoria y timeouts

## 🚀 Ejecución de Pruebas

### Ejecutar Todas las Pruebas
```bash
python tests/test_runner.py
```

### Ejecutar por Categoría
```bash
# Solo pruebas del modelo
python tests/test_runner.py modelo

# Solo pruebas del controlador
python tests/test_runner.py controlador

# Solo pruebas de validación
python tests/test_runner.py validador

# Solo pruebas de vista
python tests/test_runner.py vista

# Solo pruebas de integración
python tests/test_runner.py integracion

# Solo casos límite
python tests/test_runner.py casos_limite
```

### Opciones de Verbosidad
```bash
# Salida detallada
python tests/test_runner.py -v

# Salida mínima
python tests/test_runner.py -q

# Ayuda
python tests/test_runner.py --help
```

### Ejecutar Pruebas Individuales
```bash
# Ejecutar un archivo específico
python -m unittest tests.test_cliente

# Ejecutar una clase específica
python -m unittest tests.test_cliente.TestCliente

# Ejecutar un método específico
python -m unittest tests.test_cliente.TestCliente.test_crear_cliente_exitoso
```

## 📊 Cobertura de Pruebas

### Funcionalidades Cubiertas

#### ✅ **Gestión de Clientes**
- [x] Creación de clientes con validaciones completas
- [x] Actualización de datos existentes
- [x] Eliminación con verificación de dependencias
- [x] Búsqueda por múltiples criterios
- [x] Listado con paginación y filtros

#### ✅ **Validaciones**
- [x] Tipos de identificación (Cédula, NIT, Pasaporte, etc.)
- [x] Formatos de identificación por tipo
- [x] Validación de emails con RFC compliance
- [x] Formatos de teléfono nacionales e internacionales
- [x] Fechas de nacimiento con límites lógicos
- [x] Longitudes de campos y caracteres especiales

#### ✅ **Manejo de Errores**
- [x] Errores de base de datos (conexión, integridad, etc.)
- [x] Datos duplicados (identificación, email)
- [x] Validaciones fallidas con mensajes específicos
- [x] Errores de concurrencia
- [x] Timeouts y problemas de red

#### ✅ **Interfaz de Usuario**
- [x] Inicialización de componentes
- [x] Estados de botones según selección
- [x] Búsqueda con delay automático
- [x] Diálogos de creación y edición
- [x] Confirmaciones de eliminación
- [x] Mensajes de error y éxito

#### ✅ **Casos Límite**
- [x] Datos con longitud máxima
- [x] Caracteres Unicode y especiales
- [x] Intentos de SQL injection
- [x] Base de datos vacía o corrupta
- [x] Memoria insuficiente simulada
- [x] Errores intermitentes de conexión

## 🔧 Configuración de Pruebas

### Dependencias
Las pruebas utilizan las siguientes librerías:
- `unittest` - Framework de pruebas estándar de Python
- `unittest.mock` - Para mocking y simulación
- `PyQt5` - Para pruebas de interfaz (mocked)

### Mocking
Las pruebas utilizan mocking extensivo para:
- **Base de datos**: Simulación de conexiones y operaciones
- **PyQt5**: Mock de componentes UI para evitar dependencias gráficas
- **Archivos**: Mock de operaciones de E/S cuando sea necesario

### Datos de Prueba
Los datos de prueba están diseñados para:
- Cubrir todos los tipos de identificación soportados
- Incluir caracteres especiales y Unicode
- Probar límites de longitud de campos
- Simular errores comunes de usuario

## 📈 Métricas de Calidad

### Objetivos de Cobertura
- **Cobertura de código**: >95%
- **Cobertura de ramas**: >90%
- **Casos de error**: 100% de escenarios identificados
- **Validaciones**: 100% de reglas de negocio

### Criterios de Éxito
- ✅ Todas las pruebas pasan sin errores
- ✅ No hay warnings de deprecación
- ✅ Tiempo de ejecución < 30 segundos
- ✅ Cobertura de casos límite completa

## 🐛 Resolución de Problemas

### Errores Comunes

#### Error de Importación
```
ModuleNotFoundError: No module named 'models'
```
**Solución**: Ejecutar desde el directorio raíz del proyecto

#### Error de PyQt5
```
QApplication: invalid style override passed
```
**Solución**: Las pruebas mockean PyQt5, este error es esperado y manejado

#### Error de Base de Datos
```
sqlite3.OperationalError: no such table: clientes
```
**Solución**: Las pruebas usan mocks, verificar configuración de mocking

### Debugging
Para debugging detallado:
```bash
python -m unittest tests.test_cliente -v
```

Para ver stack traces completos:
```bash
python tests/test_runner.py -v 2>&1 | tee test_output.log
```

## 📝 Mantenimiento

### Agregar Nuevas Pruebas
1. Identificar la funcionalidad a probar
2. Determinar la categoría apropiada
3. Crear el método de prueba siguiendo la convención `test_descripcion_funcionalidad`
4. Agregar mocks necesarios
5. Verificar que la prueba falla antes de implementar la funcionalidad
6. Implementar y verificar que la prueba pasa

### Actualizar Pruebas Existentes
1. Identificar cambios en requisitos
2. Actualizar datos de prueba si es necesario
3. Modificar assertions según nuevos comportamientos
4. Ejecutar suite completa para verificar regresiones

### Mejores Prácticas
- **Nombres descriptivos**: Los nombres de pruebas deben explicar qué se está probando
- **Independencia**: Cada prueba debe ser independiente de las demás
- **Datos aislados**: Usar mocks para evitar dependencias externas
- **Assertions claras**: Usar mensajes descriptivos en assertions
- **Cleanup**: Limpiar recursos después de cada prueba

## 📞 Soporte

Para preguntas sobre las pruebas o reportar problemas:
1. Revisar esta documentación
2. Ejecutar las pruebas con verbosidad alta
3. Verificar logs de error
4. Consultar con el equipo de desarrollo

---

**Última actualización**: Enero 2024  
**Versión de pruebas**: 1.0  
**Compatibilidad**: Python 3.7+, PyQt5 5.15+