import socket
import threading
import pickle
import time
import struct
from enum import Enum

class MessageType(Enum):
    """Tipos de mensajes para el protocol del juego"""
    CONNECTION_REQUEST = 1
    CONNECTION_ACCEPTED = 2
    PLAYER_STATE = 3
    BOMB_PLACED = 4
    BOMB_EXPLODED = 5
    OBJECT_DESTROYED = 6
    PLAYER_HIT = 7
    GAME_OVER = 8
    HEARTBEAT = 9
    POWERUP_SPAWNED = 10
    POWERUP_COLLECTED = 11
    PLAYER_POWERUP_STATE = 12
    CONNECTION_CHECK = 13

class GameNetwork:
    """Sistema de red TCP para el juego Bomberman - VERSIÓN MEJORADA Y ROBUSTA"""
    
    def __init__(self, is_host=False, host_ip='127.0.0.1', port=4040):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        
        # Sockets TCP
        self.server_socket = None
        self.client_socket = None
        self.connection_socket = None
        
        self.connected = False
        self.connection_established = False
        self.peer_address = None
        self.running = True
        
        # Locks para sincronización
        self.connection_lock = threading.Lock()
        self.message_lock = threading.Lock()
        
        # Buffer para mensajes recibidos
        self.received_messages = []
        
        # Heartbeat
        self.last_heartbeat_received = time.time()
        self.heartbeat_interval = 2.0
        self.heartbeat_timeout = 15.0
        
        # Estado del juego compartido
        self.game_state = {
            'players': {},
            'bombs': [],
            'objects': [],
            'powerups': [],
            'time': 0
        }
        
        # Estadísticas para debug
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_errors': 0,
            'last_debug_time': time.time(),
            'last_heartbeat_sent': 0
        }
        
        # Variables de control de threads
        self.accept_thread = None
        self.connect_thread = None
        self.receive_thread = None
        self.heartbeat_thread = None
        
        # Flag para controlar si ya se ha conectado alguien
        self.connection_attempted = False
        
    def initialize(self):
        """Inicializa la conexión TCP"""
        try:
            # Resetear estados
            self.connection_attempted = False
            
            with self.connection_lock:
                self.connected = False
                self.connection_established = False
                self.peer_address = None
            
            if self.is_host:
                # HOST: Crear socket servidor TCP
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.settimeout(0.5)
                
                # Bind a todas las interfaces
                self.server_socket.bind(('0.0.0.0', self.port))
                self.server_socket.listen(1)
                
                print(f"🎮 Host TCP iniciado en puerto {self.port}")
                print("🔄 Esperando conexión de cliente...")
                
                # Mostrar IP local
                local_ip = self._get_local_ip()
                print(f"📡 IP para compartir: {local_ip}")
                
                # Thread para aceptar conexiones
                self.accept_thread = threading.Thread(target=self._accept_connection_loop, daemon=True)
                self.accept_thread.start()
                
            else:
                # CLIENTE: Configurar dirección del host
                self.peer_address = (self.host_ip, self.port)
                print(f"🔗 Intentando conectar a {self.host_ip}:{self.port}")
                
                # Thread para conectar
                self.connect_thread = threading.Thread(target=self._connect_to_host_loop, daemon=True)
                self.connect_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando red TCP: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _accept_connection_loop(self):
        """Loop para aceptar conexiones - HOST"""
        max_wait_time = 30  # 30 segundos máximo
        start_time = time.time()
        
        try:
            while self.running and not self.connection_established and time.time() - start_time < max_wait_time:
                try:
                    print(f"👂 Host esperando en puerto {self.port}...")
                    
                    # Aceptar conexión con timeout
                    self.server_socket.settimeout(1.0)
                    self.connection_socket, client_addr = self.server_socket.accept()
                    
                    print(f"✅ ¡Cliente conectado desde {client_addr}!")
                    
                    # Configurar socket
                    self.client_socket = self.connection_socket
                    self.client_socket.settimeout(0.1)
                    
                    with self.connection_lock:
                        self.peer_address = client_addr
                        self.connected = True
                    
                    # Iniciar threads de red
                    self._start_network_threads()
                    
                    # Pequeña pausa para estabilizar
                    time.sleep(0.2)
                    
                    # Enviar mensaje de bienvenida
                    welcome_msg = {
                        'type': MessageType.CONNECTION_ACCEPTED.value,
                        'message': '¡Bienvenido!',
                        'timestamp': time.time(),
                        'player_id': 2,
                        'data': {
                            'status': 'connected',
                            'player_id': 2
                        }
                    }
                    
                    if self._send_tcp_message(welcome_msg):
                        print("📤 Mensaje de bienvenida enviado")
                        
                        # Marcar como establecido
                        with self.connection_lock:
                            self.connection_established = True
                        
                        print("✅ Conexión TCP completamente establecida")
                        break  # Salir del loop
                    else:
                        print("❌ Error enviando bienvenida")
                        self.client_socket.close()
                        self.client_socket = None
                        
                except socket.timeout:
                    continue  # Timeout normal, continuar esperando
                except Exception as e:
                    print(f"⚠️ Error en accept: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error en accept_connection_loop: {e}")
        
        print(f"🔚 Host terminó de esperar conexiones")
    
    def _connect_to_host_loop(self):
        """Loop para conectar al host - CLIENTE"""
        max_attempts = 5
        attempt = 0
        
        while self.running and attempt < max_attempts:
            try:
                print(f"🔄 Intento {attempt + 1}/{max_attempts}")
                
                # Crear socket
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(3)  # 3 segundos para conectar
                
                print(f"🔗 Conectando a {self.host_ip}:{self.port}...")
                self.client_socket.connect((self.host_ip, self.port))
                self.client_socket.settimeout(0.1)
                
                print("✅ Socket TCP conectado")
                
                with self.connection_lock:
                    self.connected = True
                
                # Iniciar threads de red
                self._start_network_threads()
                
                # Pequeña pausa
                time.sleep(0.2)
                
                # Enviar solicitud de conexión
                request = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'timestamp': time.time(),
                    'player_id': 2,
                    'data': {
                        'action': 'connect_request'
                    }
                }
                
                if self._send_tcp_message(request):
                    print("📤 Solicitud de conexión enviada")
                    
                    # Esperar confirmación
                    print("⏳ Esperando confirmación del host...")
                    confirmation_received = False
                    
                    for _ in range(50):  # Esperar hasta 5 segundos (50 * 0.1)
                        messages = self.get_messages()
                        for msg, _ in messages:
                            if msg.get('type') == MessageType.CONNECTION_ACCEPTED.value:
                                print("✅ Confirmación recibida del host")
                                confirmation_received = True
                                
                                with self.connection_lock:
                                    self.connection_established = True
                                
                                print("✅ Conexión TCP completamente establecida")
                                break
                        
                        if confirmation_received:
                            break
                            
                        time.sleep(0.1)
                    
                    if confirmation_received:
                        break  # Conexión exitosa, salir del loop
                    else:
                        print("❌ No se recibió confirmación del host")
                        
                else:
                    print("❌ Error enviando solicitud")
                
            except ConnectionRefusedError:
                print(f"❌ Conexión rechazada")
            except socket.timeout:
                print(f"⏱️ Timeout de conexión")
            except Exception as e:
                print(f"⚠️ Error en conexión: {e}")
            
            # Limpiar para reintentar
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
            
            with self.connection_lock:
                self.connected = False
                self.connection_established = False
            
            attempt += 1
            if attempt < max_attempts:
                print(f"🔄 Reintentando en 2 segundos...")
                time.sleep(2)
        
        if not self.connection_established:
            print("❌ No se pudo establecer conexión TCP")
    
    def _start_network_threads(self):
        """Inicia los threads de red"""
        # Thread de recepción
        self.receive_thread = threading.Thread(target=self._receive_messages_loop, daemon=True)
        self.receive_thread.start()
        
        # Thread de heartbeat
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        print("📡 Threads de red iniciados")
    
    def _receive_messages_loop(self):
        """Loop principal para recibir mensajes"""
        print("🎯 Thread de recepción iniciado")
        
        buffer = b""
        
        try:
            while self.running:
                # Verificar si estamos conectados
                with self.connection_lock:
                    if not self.connected or not self.client_socket:
                        time.sleep(0.1)
                        continue
                
                try:
                    # Recibir datos
                    data = self.client_socket.recv(4096)
                    
                    if not data:
                        print("📭 Conexión cerrada por el peer")
                        with self.connection_lock:
                            self.connected = False
                            self.connection_established = False
                        break
                    
                    buffer += data
                    
                    with self.connection_lock:
                        self.last_heartbeat_received = time.time()
                    
                    self.stats['messages_received'] += 1
                    
                    # Procesar mensajes completos
                    while len(buffer) >= 4:
                        try:
                            # Obtener longitud
                            msg_length = struct.unpack('!I', buffer[:4])[0]
                            
                            # Verificar si tenemos mensaje completo
                            if len(buffer) < 4 + msg_length:
                                break
                            
                            # Extraer mensaje
                            msg_data = buffer[4:4 + msg_length]
                            buffer = buffer[4 + msg_length:]
                            
                            # Deserializar
                            message = pickle.loads(msg_data)
                            msg_type = message.get('type')
                            
                            # Procesar
                            self._process_received_message(message)
                            
                        except struct.error:
                            print("⚠️ Error en formato de mensaje")
                            buffer = b""
                            break
                        except Exception as e:
                            print(f"⚠️ Error procesando mensaje: {e}")
                            buffer = b""
                            break
                            
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    print("⚠️ Conexión reseteada por el peer")
                    with self.connection_lock:
                        self.connected = False
                        self.connection_established = False
                    break
                except Exception as e:
                    if "10054" in str(e):
                        print("⚠️ Conexión cerrada por el host remoto")
                    else:
                        print(f"⚠️ Error en recepción: {e}")
                    
                    with self.connection_lock:
                        self.connected = False
                        self.connection_established = False
                    break
        
        except Exception as e:
            print(f"💥 ERROR en receive_messages_loop: {e}")
        
        print("🔌 Thread de recepción terminado")
    
    def _process_received_message(self, message):
        """Procesa un mensaje recibido"""
        msg_type = message.get('type')
        
        # Actualizar heartbeat
        with self.connection_lock:
            self.last_heartbeat_received = time.time()
        
        # Procesar según tipo
        if msg_type == MessageType.CONNECTION_ACCEPTED.value:
            print("✅ Conexión aceptada por el host")
            
        elif msg_type == MessageType.CONNECTION_REQUEST.value and self.is_host:
            print("📨 Solicitud de conexión recibida")
            
        elif msg_type == MessageType.HEARTBEAT.value:
            pass  # Solo actualiza timestamp
            
        elif msg_type == MessageType.CONNECTION_CHECK.value:
            if self.is_host:
                response = {
                    'type': MessageType.CONNECTION_CHECK.value,
                    'timestamp': time.time(),
                    'status': 'ok'
                }
                self._send_tcp_message(response)
        
        # Agregar al buffer
        with self.message_lock:
            self.received_messages.append((message, None))
    
    def _send_tcp_message(self, message):
        """Envía un mensaje TCP"""
        try:
            with self.connection_lock:
                if not self.connected or not self.client_socket:
                    print("⚠️ No hay conexión para enviar")
                    return False
            
            # Serializar
            serialized = pickle.dumps(message)
            length = len(serialized)
            
            # Enviar longitud + mensaje
            header = struct.pack('!I', length)
            self.client_socket.sendall(header + serialized)
            
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            
            with self.connection_lock:
                self.connected = False
                self.connection_established = False
            
            return False
    
    def send_player_state(self, player_data):
        """Envía estado del jugador"""
        if self.is_connected():
            message = {
                'type': MessageType.PLAYER_STATE.value,
                'player_id': 1 if self.is_host else 2,
                'data': player_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_bomb_placed(self, bomb_data):
        """Envía bomba colocada"""
        if self.is_connected():
            message = {
                'type': MessageType.BOMB_PLACED.value,
                'data': bomb_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_object_destroyed(self, object_data):
        """Envía objeto destruido"""
        if self.is_connected():
            message = {
                'type': MessageType.OBJECT_DESTROYED.value,
                'data': object_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_spawned(self, powerup_data):
        """Envía power-up aparecido"""
        if self.is_connected():
            message = {
                'type': MessageType.POWERUP_SPAWNED.value,
                'data': powerup_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_collected(self, powerup_data):
        """Envía power-up recogido"""
        if self.is_connected():
            message = {
                'type': MessageType.POWERUP_COLLECTED.value,
                'data': powerup_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def _heartbeat_loop(self):
        """Loop de heartbeat"""
        print("❤️ Thread de heartbeat iniciado")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Estadísticas
                if current_time - self.stats['last_debug_time'] > 10:
                    print(f"📊 Stats: Enviados={self.stats['messages_sent']}, Recibidos={self.stats['messages_received']}")
                    self.stats['last_debug_time'] = current_time
                
                # Enviar heartbeat si estamos conectados
                if self.is_connected():
                    if current_time - self.stats['last_heartbeat_sent'] >= self.heartbeat_interval:
                        heartbeat = {
                            'type': MessageType.HEARTBEAT.value,
                            'timestamp': current_time
                        }
                        
                        if self._send_tcp_message(heartbeat):
                            self.stats['last_heartbeat_sent'] = current_time
                
                # Verificar timeout
                with self.connection_lock:
                    time_since = current_time - self.last_heartbeat_received
                    if self.connected and time_since > self.heartbeat_timeout:
                        print(f"⚠️ Sin mensajes por {time_since:.1f}s")
                        self.connected = False
                        self.connection_established = False
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️ Error en heartbeat: {e}")
                time.sleep(1)
        
        print("💔 Thread de heartbeat terminado")
    
    def get_messages(self):
        """Obtiene mensajes recibidos"""
        with self.message_lock:
            messages = self.received_messages.copy()
            self.received_messages.clear()
            return messages
    
    def is_connected(self):
        """Verifica conexión"""
        with self.connection_lock:
            if not self.connected or not self.connection_established:
                return False
            
            time_since = time.time() - self.last_heartbeat_received
            return time_since < self.heartbeat_timeout
    
    def disconnect(self):
        """Cierra conexión"""
        self.running = False
        
        # Cerrar sockets
        sockets = [self.client_socket, self.server_socket, self.connection_socket]
        for sock in sockets:
            if sock:
                try:
                    sock.close()
                except:
                    pass
        
        # Esperar a que threads terminen
        threads = [self.accept_thread, self.connect_thread, self.receive_thread, self.heartbeat_thread]
        for thread in threads:
            if thread and thread.is_alive():
                thread.join(timeout=1.0)
        
        # Resetear estados
        with self.connection_lock:
            self.connected = False
            self.connection_established = False
        
        print("🔌 Conexión cerrada")
    
    def _get_local_ip(self):
        """Obtiene IP local"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    # Métodos de compatibilidad
    def _send_connection_request(self):
        pass
    
    def _listen_for_connections(self):
        pass
    
    def _receive_messages(self):
        pass
    
    def _send_message(self, message, address):
        pass