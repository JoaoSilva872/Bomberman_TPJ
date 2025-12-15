import socket
import sys

def test_tcp_server():
    """Prueba simple de servidor TCP"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 4040))
    server.listen(1)
    
    print("🎮 Servidor TCP escuchando en puerto 4040")
    print("Para probar desde otro PC usa:")
    print("  python test_tcp_simple.py --client [IP_DE_ESTE_PC]")
    print("\nEsperando conexión...")
    
    try:
        client, addr = server.accept()
        print(f"✅ ¡Cliente conectado desde {addr}!")
        
        # Enviar mensaje
        client.send(b"HOLA_CLIENTE")
        
        # Recibir respuesta
        data = client.recv(1024)
        print(f"📨 Cliente respondió: {data.decode()}")
        
        client.close()
        print("🔌 Conexión cerrada")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        server.close()

def test_tcp_client(server_ip):
    """Prueba simple de cliente TCP"""
    print(f"🔗 Conectando a {server_ip}:4040...")
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client.connect((server_ip, 4040))
        print("✅ ¡Conectado!")
        
        # Recibir mensaje
        data = client.recv(1024)
        print(f"📨 Servidor dice: {data.decode()}")
        
        # Responder
        client.send(b"HOLA_SERVIDOR")
        print("📤 Enviada respuesta")
        
        client.close()
        print("✅ Prueba TCP exitosa")
        
    except ConnectionRefusedError:
        print("❌ Conexión rechazada. Verifica:")
        print("   1. Que el servidor esté ejecutándose")
        print("   2. Que no haya firewall bloqueando")
        print("   3. Que la IP sea correcta")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎮 TEST SIMPLE DE CONEXIÓN TCP")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  Servidor: python test_tcp_simple.py --server")
        print("  Cliente:  python test_tcp_simple.py --client [IP_SERVIDOR]")
        print("\nEjemplo para LAN:")
        print("  En PC 1 (Host): python test_tcp_simple.py --server")
        print("  En PC 2 (Cliente): python test_tcp_simple.py --client 192.168.1.100")
        sys.exit(1)
    
    if sys.argv[1] == "--server":
        test_tcp_server()
    elif sys.argv[1] == "--client":
        if len(sys.argv) < 3:
            print("❌ Necesitas especificar IP del servidor")
            print("Ejemplo: python test_tcp_simple.py --client 192.168.1.100")
            sys.exit(1)
        test_tcp_client(sys.argv[2])
    else:
        print("❌ Opción inválida")