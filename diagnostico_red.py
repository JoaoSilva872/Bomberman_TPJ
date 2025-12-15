import socket
import sys

def diagnosticar_red():
    print("🔍 DIAGNÓSTICO DE RED")
    print("=" * 50)
    
    # Obtener IP local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_local = s.getsockname()[0]
        s.close()
        print(f"📍 IP Local: {ip_local}")
    except:
        print("❌ No se pudo obtener IP local")
        ip_local = "127.0.0.1"
    
    # Obtener nombre de host
    try:
        hostname = socket.gethostname()
        print(f"🖥️  Nombre de host: {hostname}")
    except:
        print("❌ No se pudo obtener nombre de host")
    
    # Verificar si el puerto está libre
    puerto = 5555
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(('', puerto))
        test_socket.close()
        print(f"✅ Puerto {puerto} está libre")
    except:
        print(f"❌ Puerto {puerto} está en uso")
    
    # Probar conexión a internet
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("8.8.8.8", 53))
        s.close()
        print("🌐 Conexión a Internet: OK")
    except:
        print("🌐 Conexión a Internet: FALLO")
    
    print("\n💡 INSTRUCCIONES PARA MULTIJUGADOR:")
    print("1. Ambos PCs deben estar en la MISMA RED (WiFi/Ethernet)")
    print("2. El HOST debe usar esta IP:", ip_local)
    print("3. El CLIENTE debe escribir esa IP")
    print("4. Desactivar firewalls temporalmente si hay problemas")
    
    input("\nPresiona ENTER para salir...")

if __name__ == "__main__":
    diagnosticar_red()