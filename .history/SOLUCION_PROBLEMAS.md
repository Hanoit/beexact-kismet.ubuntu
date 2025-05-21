# Solución de Problemas - BeeExact Kismet Ubuntu

## Problemas Identificados y Soluciones

### 1. Problema con la lectura del archivo `.env`

**Problema:** El archivo de configuración se llamaba `_.env` en lugar de `.env`, lo que causaba que las variables de entorno no se cargaran correctamente.

**Solución:** 
- Se copió el archivo `_.env` a `.env` para que python-dotenv pueda encontrarlo
- Se verificó que todas las variables de entorno se cargan correctamente

**Verificación:**
```bash
python3 test_env_reading.py
```

### 2. Problema con la detección de archivos completamente copiados

**Problema:** El sistema original solo verificaba el tamaño del archivo para determinar si había terminado de copiarse, lo cual no es suficiente para archivos grandes o copias lentas.

**Solución implementada:**

#### A. Nuevo módulo de monitoreo de archivos (`utils/file_monitor.py`)

- **FileStabilityMonitor**: Clase que monitorea la estabilidad de archivos
- **wait_for_stability()**: Espera a que el archivo sea estable (tamaño y tiempo de modificación constantes)
- **wait_for_accessibility()**: Verifica que el archivo sea accesible y no esté bloqueado
- **is_file_accessible()**: Verifica si el archivo puede ser abierto para lectura

#### B. Mejoras en WatchingDirectory.py

- Integración del nuevo sistema de monitoreo
- Mejor logging y manejo de errores
- Validación del directorio de vigilancia
- Timeout configurable para evitar esperas infinitas

### 3. Configuración del directorio de vigilancia

**Directorio configurado:** `/opt/kismetFiles`

**Verificación:**
```bash
ls -la /opt/kismetFiles
```

## Cómo funciona el nuevo sistema

### 1. Detección de archivos nuevos
- El sistema usa `watchdog` para detectar cuando se crean nuevos archivos `.kismet`
- Se verifica que el archivo no haya sido procesado previamente

### 2. Verificación de estabilidad
- **Tiempo de estabilidad**: 5 segundos por defecto (configurable)
- **Tiempo máximo de espera**: 5 minutos (configurable)
- **Verificaciones**: Tamaño del archivo y tiempo de modificación

### 3. Verificación de accesibilidad
- Se intenta abrir el archivo para lectura
- Timeout de 30 segundos para accesibilidad
- Previene procesamiento de archivos bloqueados

### 4. Procesamiento
- Una vez que el archivo es estable y accesible, se procesa
- Se exporta a CSV con análisis de dispositivos WiFi
- Se registra en la base de datos como procesado

## Configuración del archivo `.env`

```env
# Directory where Kismet files are saved
WATCH_DIRECTORY="/opt/kismetFiles"

# How often the directory is checked for new files (in seconds)
CHECK_INTERVAL=300

# Number of CPU cores to dedicate for processing
NUM_WORKERS=6

# Flip the coordinates if needed (0 = False, 1 = True)
FLIP_XY=1

# API Key for MacVendor API
API_KEY_MACVENDOR=your_api_key_here

# Directory where the output CSV files will be saved
OUT_DIRECTORY="/opt/kismetFiles"

# Database Directory
DB_DIRECTORY="."

# Show in the console processing progress
BASIC_VERBOSE=0

# Show in the console processing progress with details
ADVANCE_VERBOSE=0
```

## Uso del sistema

### 1. Ejecutar el sistema principal
```bash
python3 kismet_export.py
```

### 2. Probar el sistema de monitoreo
```bash
python3 test_file_monitoring.py
```

### 3. Verificar configuración
```bash
python3 test_env_reading.py
```

## Mejoras implementadas

### 1. Logging mejorado
- Logs detallados de cada paso del proceso
- Información de progreso y errores
- Timestamps en todos los logs

### 2. Manejo de errores robusto
- Timeouts configurables
- Validación de directorios y archivos
- Rollback en caso de errores

### 3. Monitoreo de archivos avanzado
- Verificación de estabilidad por tamaño y tiempo
- Verificación de accesibilidad
- Prevención de procesamiento de archivos incompletos

### 4. Configuración flexible
- Variables de entorno para todos los parámetros
- Timeouts configurables
- Directorios configurables

### 5. Reportes de diagnóstico silenciosos
- Los reportes de diagnóstico se guardan automáticamente en archivos de log
- No se imprimen en la terminal para evitar saturar la consola
- Cada archivo procesado genera su propio archivo de diagnóstico
- Formato: `{filename}_DIAGNOSTIC.log`

## Estructura del proyecto

```
beexact-kismet.ubuntu/
├── .env                          # Archivo de configuración (creado desde _.env)
├── kismet_export.py              # Script principal
├── services/
│   ├── WatchingDirectory.py      # Monitoreo de directorio (mejorado)
│   ├── DirectoryFilesProcessor.py # Procesamiento de archivos
│   └── KismetAnalyzer.py         # Análisis de archivos Kismet
├── utils/
│   └── file_monitor.py           # Nuevo módulo de monitoreo de archivos
├── database/
│   └── SessionKismetDB.py        # Gestión de base de datos
└── test_*.py                     # Scripts de prueba
```

## Recomendaciones

1. **Monitoreo**: Usar `tail -f` en los logs para monitorear el sistema
2. **Backup**: Hacer backup regular de la base de datos `kismet.db`
3. **Espacio en disco**: Monitorear el espacio en `/opt/kismetFiles`
4. **Permisos**: Asegurar que el usuario tenga permisos de escritura en `/opt/kismetFiles`

## Troubleshooting

### El sistema no detecta archivos nuevos
1. Verificar que el directorio `/opt/kismetFiles` existe
2. Verificar permisos de lectura en el directorio
3. Verificar que los archivos tienen extensión `.kismet`

### Los archivos no se procesan
1. Verificar logs para errores específicos
2. Verificar que la base de datos `kismet.db` existe y es accesible
3. Verificar que el archivo `.env` está en el directorio raíz

### Procesamiento lento
1. Ajustar `NUM_WORKERS` en el archivo `.env`
2. Verificar recursos del sistema (CPU, memoria, disco)
3. Considerar reducir `CHECK_INTERVAL` para archivos grandes

### Errores de MacVendor API (404 Not Found)
1. **Es normal** que muchos MACs devuelvan 404 - no todos están en la base de datos
2. El sistema ahora maneja estos errores silenciosamente
3. Se implementó rate limiting para evitar sobrecargar la API
4. Los MACs no encontrados se registran en logs de debug, no como warnings

### Configuración de API
- **API_KEY_MACVENDOR**: Token de la API de MacVendor (opcional)
- **Rate limiting**: 100ms mínimo entre peticiones a la API
- **Cache**: Los resultados se almacenan en la base de datos local 