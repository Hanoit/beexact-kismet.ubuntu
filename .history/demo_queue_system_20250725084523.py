#!/usr/bin/env python3
"""
Demonstration script for the new file queue processing system
"""
import os
import time
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def demo_queue_system():
    """Demonstrate the new queue processing system"""
    
    print("🚀 DEMOSTRACIÓN DEL SISTEMA DE COLA DE PROCESAMIENTO")
    print("=" * 60)
    
    # Check if we have a real Kismet file to work with
    watch_dir = os.getenv("WATCH_DIRECTORY", "/opt/kismetFiles")
    existing_files = [f for f in os.listdir(watch_dir) if f.endswith('.kismet')]
    
    if not existing_files:
        print("❌ No se encontraron archivos .kismet para demostrar")
        print("   Por favor, copie algunos archivos .kismet a /opt/kismetFiles")
        return
    
    print(f"📁 Directorio de monitoreo: {watch_dir}")
    print(f"📊 Archivos .kismet encontrados: {len(existing_files)}")
    
    # Show existing files
    print("\n📋 Archivos disponibles:")
    for i, filename in enumerate(existing_files[:5], 1):  # Show first 5
        file_path = os.path.join(watch_dir, filename)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"   {i}. {filename} ({size_mb:.1f} MB)")
    
    if len(existing_files) > 5:
        print(f"   ... y {len(existing_files) - 5} archivos más")
    
    print("\n🔄 Cómo funciona el sistema de cola:")
    print("   1. Se detecta un nuevo archivo .kismet")
    print("   2. Se verifica que el archivo esté completamente copiado")
    print("   3. Se agrega a la cola de procesamiento")
    print("   4. Se procesa secuencialmente (uno por uno)")
    print("   5. Se generan reportes de diagnóstico")
    
    print("\n📊 Ventajas del sistema de cola:")
    print("   ✅ Procesamiento secuencial (evita sobrecarga)")
    print("   ✅ Detección de archivos completos")
    print("   ✅ Prevención de duplicados")
    print("   ✅ Manejo robusto de errores")
    print("   ✅ Estadísticas en tiempo real")
    print("   ✅ Reportes de diagnóstico detallados")
    
    print("\n🔧 Configuración actual:")
    print(f"   • Directorio de monitoreo: {os.getenv('WATCH_DIRECTORY', '/opt/kismetFiles')}")
    print(f"   • Directorio de salida: {os.getenv('OUT_DIRECTORY', '/opt/kismetFiles')}")
    print(f"   • Procesar sin ubicación: {os.getenv('PROCESS_WITHOUT_LOCATION', 'No configurado')}")
    print(f"   • Intervalo de verificación: {os.getenv('CHECK_INTERVAL', '300')} segundos")
    
    print("\n📈 Archivos generados por cada procesamiento:")
    print("   • {filename}.csv - Datos exportados")
    print("   • {filename}.log - Log de procesamiento")
    print("   • {filename}_DIAGNOSTIC.log - Reporte de diagnóstico")
    print("   • {filename}_NOT_VENDOR.log - MACs sin fabricante")
    print("   • {filename}_NOT_PROVIDER.log - MACs sin proveedor")
    
    print("\n🎯 Para iniciar el sistema:")
    print("   python3 kismet_export.py")
    
    print("\n👀 Para monitorear en tiempo real:")
    print("   tail -f /opt/kismetFiles/*.log")
    
    print("\n📋 Para ver archivos procesados:")
    print("   ls -la /opt/kismetFiles/*.csv")
    
    print("\n🔍 Para ver reportes de diagnóstico:")
    print("   ls -la /opt/kismetFiles/*_DIAGNOSTIC.log")
    
    print("\n" + "=" * 60)
    print("✅ El sistema está listo para procesar archivos automáticamente!")
    print("   Simplemente copie archivos .kismet al directorio de monitoreo")

if __name__ == '__main__':
    demo_queue_system() 