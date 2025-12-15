import socket
import threading
import pickle
import time
import struct
from enum import Enum

class MessageType(Enum):
    """Tipos de mensajes para el protocol del juego - TCP"""
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
    """Sistema de red TCP para el juego Bomberman - VERSIÓN CORREGIDA"""
    
    def __init__(self, is_host=False, host_ip='127.0.0.1', port=4040):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        
        # Sockets TCP
        self.server_socket = None      # Solo para host
        self.client_socket = None      # Socket principal
        self.connection_socket = None  # Socket aceptado
        
        self.connected = False
        self.connection_established = False
        self.peer_address = None
        self.running = True
        
        # Buffer para mensajes
        self.received_messages = []
        self.message_lock = threading.Lock()
        
        # Heartbeat
        self.last_heartbeat_received = time.time()
        self.heartbeat_interval = 2.0
        self.heartbeat_timeout = 15.0
        
        # Estado del juego
        self.game_state = {
            'players': {},
            'bombs': [],
            'objects': [],
            'powerups': [],
            'time': 0
        }
        
        # Estadísticas
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_errors': 0,
            'last_debug_time': time.time()
        }
        
        # Para debug
        self.debug = True
        
    def initialize(self):
        """Inicializa la conexión TCP"""
        try:
            if self.is_host:
                # HOST: Crear socket servidor
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.settimeout(0.5)
                
                # Bind
                self.server_socket.bind(('0.0.0.0', self.port))
                self.server_socket.listen(1)
                
                print(f"🎮 Host TCP iniciado en puerto {self.port}")
                print("🔄 Esperando conexión...")
                
                # Thread para aceptar
                threading.Thread(target=self._accept_connection, daemon=True).start()
                
            else:
                # CLIENTE: Configurar dirección
                self.peer_address = (self.host_ip, self.port)
                print(f"🔗 Intentando conectar a {self.host_ip}:{self.port}")
                
                # Thread para conectar
                threading.Thread(target=self._connect_to_host, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando red: {e}")
            return False
    
    def _accept_connection(self):
        """Acepta conexiones - HOST"""
        try:
            print(f"👂 Host esperando en puerto {self.port}...")
            
            # Aceptar con timeout
            self.connection_socket, client_addr = self.server_socket.accept()
            print(f"✅ Cliente conectado desde {client_addr}")
            
            # Configurar
            self.client_socket = self.connection_socket
            self.client_socket.settimeout(0.1)
            self.peer_address = client_addr
            
            # Marcar como conectado INMEDIATAMENTE
            self.connected = True
            self.connection_established = True
            
            print("✅ Conexión establecida en el host")
            
            # Iniciar threads
            self._start_network_threads()
            
            # Enviar confirmación INMEDIATAMENTE
            self._send_welcome_message()
            
        except socket.timeout:
            print("⏱️ Timeout esperando conexión")
        except Exception as e:
            print(f"❌ Error aceptando: {e}")
    
    def _send_welcome_message(self):
        """Envía mensaje de bienvenida"""
        try:
            welcome = {
                'type': MessageType.CONNECTION_ACCEPTED.value,
                'message': '¡Bienvenido!',
                'timestamp': time.time(),
                'player_id': 2,
                'data': {'status': 'connected'}
            }
            
            if self._send_tcp_message(welcome):
                print("📤 Mensaje de bienvenida enviado")
            else:
                print("❌ Error enviando bienvenida")
                
        except Exception as e:
            print(f"❌ Error en welcome: {e}")
    
    def _connect_to_host(self):
        """Conecta al host - CLIENTE"""
        max_attempts = 5
        attempt = 0
        
        while self.running and attempt < max_attempts:
            try:
                print(f"🔄 Intento {attempt + 1}/{max_attempts}")
                
                # Crear socket
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(5)
                
                # Conectar
                print(f"🔗 Conectando a {self.host_ip}:{self.port}...")
                self.client_socket.connect((self.host_ip, self.port))
                self.client_socket.settimeout(0.1)
                
                print("✅ Socket conectado")
                
                # Marcar como conectado
                self.connected = True
                self.connection_established = True
                
                print("✅ Conexión establecida en el cliente")
                
                # Iniciar threads
                self._start_network_threads()
                
                # Enviar solicitud
                request = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'timestamp': time.time(),
                    'player_id': 2,
                    'data': {'action': 'connect'}
                }
                
                if self._send_tcp_message(request):
                    print("📤 Solicitud enviada")
                else:
                    print("❌ Error enviando solicitud")
                
                return True
                
            except ConnectionRefusedError:
                print("❌ Conexión rechazada")
            except socket.timeout:
                print("⏱️ Timeout")
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            attempt += 1
            if attempt < max_attempts:
                time.sleep(2)
        
        print("❌ No se pudo conectar")
        return False
    
    def _start_network_threads(self):
        """Inicia threads de red"""
        # Thread de recepción
        threading.Thread(target=self._receive_messages_safe, daemon=True).start()
        
        # Thread de heartbeat
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        
        print("📡 Threads de red iniciados")
    
    def _receive_messages_safe(self):
        """Recibe mensajes de forma segura"""
        print("🎯 Thread de recepción INICIADO")
        
        try:
            self._receive_tcp_messages()
        except Exception as e:
            print(f"💥 ERROR CRÍTICO en thread de recepción: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔌 Thread de recepción TERMINADO")
    
    def _receive_tcp_messages(self):
        """Recibe mensajes TCP - VERSIÓN ROBUSTA"""
        buffer = b""
        print(f"📡 Iniciando recepción (host={self.is_host})")
        
        while self.running and self.connected:
            try:
                # Recibir datos
                data = self.client_socket.recv(4096)
                
                if not data:
                    print("📭 Conexión cerrada (recv=0)")
                    self.connected = False
                    break
                
                if self.debug:
                    print(f"📨 Recibidos {len(data)} bytes")
                
                buffer += data
                self.last_heartbeat_received = time.time()
                
                # Procesar buffer
                while True:
                    # Necesitamos al menos 4 bytes para la longitud
                    if len(buffer) < 4:
                        break
                    
                    try:
                        # Obtener longitud
                        msg_length = struct.unpack('!I', buffer[:4])[0]
                        
                        # Verificar si tenemos el mensaje completo
                        if len(buffer) < 4 + msg_length:
                            break
                        
                        # Extraer mensaje
                        msg_data = buffer[4:4 + msg_length]
                        buffer = buffer[4 + msg_length:]
                        
                        # Deserializar
                        try:
                            message = pickle.loads(msg_data)
                            self.stats['messages_received'] += 1
                            
                            if self.debug:
                                print(f"📦 Mensaje recibido - Tipo: {message.get('type')}")
                            
                            # Procesar
                            self._process_received_message(message)
                            
                        except Exception as e:
                            print(f"⚠️ Error deserializando: {e}")
                            continue
                            
                    except struct.error as e:
                        print(f"⚠️ Error en struct.unpack: {e}")
                        buffer = b""  # Limpiar buffer corrupto
                        break
                    except Exception as e:
                        print(f"⚠️ Error procesando: {e}")
                        break
                
            except socket.timeout:
                continue  # Timeout normal
            except ConnectionResetError:
                print("⚠️ Conexión reseteada")
                self.connected = False
                break
            except OSError as e:
                if e.errno == 10054:
                    print("⚠️ Conexión cerrada por peer")
                    self.connected = False
                    break
                else:
                    print(f"⚠️ OSError: {e}")
                    self.connected = False
                    break
            except Exception as e:
                print(f"⚠️ Error inesperado: {e}")
                self.connected = False
                break
        
        print("🔌 Terminando recepción")
    
    def _process_received_message(self, message):
        """Procesa un mensaje recibido"""
        msg_type = message.get('type')
        
        # Actualizar heartbeat para cualquier mensaje
        self.last_heartbeat_received = time.time()
        
        # Procesar según tipo
        if msg_type == MessageType.CONNECTION_ACCEPTED.value:
            print("✅ Conexión aceptada por el host")
            self.connection_established = True
            
        elif msg_type == MessageType.CONNECTION_REQUEST.value and self.is_host:
            # Cliente solicitando conexión (ya estamos conectados)
            print("📨 Solicitud de conexión recibida")
            
        elif msg_type == MessageType.HEARTBEAT.value:
            pass  # Solo heartbeat
            
        elif msg_type == MessageType.CONNECTION_CHECK.value:
            # Responder a check
            if self.is_host:
                response = {
                    'type': MessageType.CONNECTION_CHECK.value,
                    'timestamp': time.time(),
                    'status': 'ok'
                }
                self._send_tcp_message(response)
        
        # Agregar a buffer
        with self.message_lock:
            self.received_messages.append((message, None))
    
    def _send_tcp_message(self, message):
        """Envía mensaje TCP"""
        if not self.client_socket:
            print("⚠️ No hay socket para enviar")
            return False
        
        try:
            # Serializar
            serialized = pickle.dumps(message)
            length = len(serialized)
            
            # Enviar longitud + mensaje
            header = struct.pack('!I', length)
            self.client_socket.sendall(header + serialized)
            
            self.stats['messages_sent'] += 1
            return True
            
        except BrokenPipeError:
            print("🔌 Conexión rota")
            self.connected = False
            return False
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            self.connected = False
            return False
    
    def send_player_state(self, player_data):
        """Envía estado del jugador"""
        if self.connected:
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
        if self.connected:
            message = {
                'type': MessageType.BOMB_PLACED.value,
                'data': bomb_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_object_destroyed(self, object_data):
        """Envía objeto destruido"""
        if self.connected:
            message = {
                'type': MessageType.OBJECT_DESTROYED.value,
                'data': object_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_spawned(self, powerup_data):
        """Envía power-up aparecido"""
        if self.connected:
            message = {
                'type': MessageType.POWERUP_SPAWNED.value,
                'data': powerup_data,
                'timestamp': time.time()
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_collected(self, powerup_data):
        """Envía power-up recogido"""
        if self.connected:
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
            if self.connected:
                current_time = time.time()
                
                # Enviar heartbeat periódicamente
                if current_time - self.stats.get('last_heartbeat_sent', 0) >= self.heartbeat_interval:
                    heartbeat = {
                        'type': MessageType.HEARTBEAT.value,
                        'timestamp': current_time
                    }
                    
                    if self._send_tcp_message(heartbeat):
                        self.stats['last_heartbeat_sent'] = current_time
                
                # Verificar timeout
                time_since = current_time - self.last_heartbeat_received
                if time_since > self.heartbeat_timeout:
                    print(f"⚠️ Sin heartbeat por {time_since:.1f}s")
                    self.connected = False
            
            # Estadísticas
            if current_time - self.stats['last_debug_time'] > 10:
                print(f"📊 Stats: Enviados={self.stats['messages_sent']}, Recibidos={self.stats['messages_received']}")
                self.stats['last_debug_time'] = current_time
            
            time.sleep(0.5)
    
    def get_messages(self):
        """Obtiene mensajes recibidos"""
        with self.message_lock:
            messages = self.received_messages.copy()
            self.received_messages.clear()
            return messages
    
    def is_connected(self):
        """Verifica conexión"""
        return self.connected and self.connection_established
    
    def disconnect(self):
        """Desconectar"""
        self.running = False
        self.connected = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("🔌 Desconectado")