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
    """Sistema de red TCP para el juego Bomberman - MANTIENE MISMO NOMBRE"""
    
    def __init__(self, is_host=False, host_ip='127.0.0.1', port=4040):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        
        # Sockets TCP
        self.server_socket = None      # Solo para host (socket servidor)
        self.client_socket = None      # Socket de conexión principal
        self.connection_socket = None  # Socket aceptado (en host)
        
        self.connected = False
        self.connection_established = False
        self.peer_address = None       # Dirección del peer (para compatibilidad)
        self.running = True
        
        # Buffer para mensajes recibidos
        self.received_messages = []
        self.message_lock = threading.Lock()
        
        # Heartbeat - TCP es más tolerante
        self.last_heartbeat_received = time.time()
        self.heartbeat_interval = 1.0    # Menos frecuente que UDP
        self.heartbeat_timeout = 10.0    # Más tolerante en TCP
        
        # Estado del juego compartido (para compatibilidad)
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
            'last_heartbeat_sent': 0
        }
        
        # Threads
        self.receive_thread = None
        self.heartbeat_thread = None
        
    def initialize(self):
        """Inicializa la conexión TCP - MANTIENE MISMA FIRMA"""
        try:
            if self.is_host:
                # HOST: Crear socket servidor TCP
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.settimeout(0.5)  # Timeout para accept
                
                # Bind a todas las interfaces
                self.server_socket.bind(('0.0.0.0', self.port))
                self.server_socket.listen(1)  # Solo 1 conexión (2 jugadores)
                
                print(f"🎮 Host TCP iniciado en puerto {self.port}")
                print("🔄 Esperando que un jugador se conecte...")
                
                # Mostrar IPs disponibles
                local_ip = self._get_local_ip()
                print(f"📡 Conectarse usando: {local_ip}:{self.port}")
                
                # Thread para aceptar conexión
                accept_thread = threading.Thread(target=self._accept_connection, daemon=True)
                accept_thread.start()
                
            else:
                # CLIENTE: Conectar al host
                self.peer_address = (self.host_ip, self.port)
                print(f"🔗 Intentando conectar a {self.host_ip}:{self.port}...")
                
                # Thread para conectar (con reintentos)
                connect_thread = threading.Thread(target=self._connect_to_host, daemon=True)
                connect_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando red TCP: {e}")
            self.game_running = False
            return False
    
    def _accept_connection(self):
        """Acepta conexiones entrantes - SOLO HOST"""
        try:
            print(f"👂 Host esperando conexión en puerto {self.port}...")
            
            # Aceptar conexión (bloqueante con timeout)
            self.connection_socket, client_addr = self.server_socket.accept()
            self.connection_socket.settimeout(0.1)  # Timeout corto para recv
            
            print(f"✅ ¡Cliente conectado desde {client_addr}!")
            
            # Configurar
            self.client_socket = self.connection_socket
            self.peer_address = client_addr
            self.connected = True
            self.connection_established = True
            
            # Iniciar threads de recepción
            self._start_network_threads()
            
            # Enviar confirmación de conexión
            response = {
                'type': MessageType.CONNECTION_ACCEPTED.value,
                'message': '¡Conexión TCP establecida!',
                'timestamp': time.time(),
                'player_id': 2  # Cliente es jugador 2
            }
            self._send_tcp_message(response)
            
            print("📤 Enviada confirmación de conexión al cliente")
            
        except socket.timeout:
            print("⏱️ Timeout esperando conexión")
        except Exception as e:
            if self.running:
                print(f"❌ Error aceptando conexión: {e}")
    
    def _connect_to_host(self):
        """Conecta al host - SOLO CLIENTE"""
        max_attempts = 10
        attempt = 0
        
        while self.running and not self.connection_established and attempt < max_attempts:
            try:
                print(f"🔄 Intento {attempt + 1}/{max_attempts} de conexión...")
                
                # Crear socket TCP
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(5)  # Timeout de conexión
                
                # Conectar al host
                self.client_socket.connect((self.host_ip, self.port))
                self.client_socket.settimeout(0.1)  # Timeout corto para recv
                
                print("✅ Socket TCP conectado, esperando confirmación...")
                
                # Iniciar threads de recepción
                self._start_network_threads()
                
                # Enviar solicitud de conexión
                request = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'timestamp': time.time(),
                    'player_id': 2  # Cliente es jugador 2
                }
                self._send_tcp_message(request)
                
                # Esperar confirmación (con timeout)
                start_time = time.time()
                while time.time() - start_time < 5.0 and not self.connection_established:
                    # Procesar mensajes recibidos
                    messages = self.get_messages()
                    for message, _ in messages:
                        if message.get('type') == MessageType.CONNECTION_ACCEPTED.value:
                            self.connected = True
                            self.connection_established = True
                            print("✅ ¡Conexión TCP establecida con el host!")
                            return True
                    
                    time.sleep(0.1)
                
                # Si no se confirmó en 5 segundos, reintentar
                print("⏱️ Timeout esperando confirmación del host")
                self.client_socket.close()
                self.client_socket = None
                
            except socket.timeout:
                print(f"⏱️ Timeout en intento {attempt + 1}")
            except ConnectionRefusedError:
                print(f"❌ Conexión rechazada - ¿El host está ejecutándose?")
            except Exception as e:
                print(f"⚠️ Error en intento {attempt + 1}: {e}")
            
            attempt += 1
            if attempt < max_attempts:
                time.sleep(2)  # Esperar antes de reintentar
        
        print("❌ No se pudo establecer conexión TCP después de varios intentos")
        return False
    
    def _start_network_threads(self):
        """Inicia los threads de red"""
        # Thread de recepción
        self.receive_thread = threading.Thread(target=self._receive_tcp_messages, daemon=True)
        self.receive_thread.start()
        
        # Thread de heartbeat
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def _receive_tcp_messages(self):
        """Recibe mensajes TCP con formato de longitud"""
        buffer = b""
        
        while self.running and self.connected:
            try:
                # Recibir datos
                data = self.client_socket.recv(4096)
                if not data:
                    print("⚠️ Conexión cerrada por el peer")
                    self.connected = False
                    self.connection_established = False
                    break
                
                buffer += data
                self.stats['messages_received'] += 1
                self.last_heartbeat_received = time.time()
                
                # Procesar todos los mensajes completos en el buffer
                while len(buffer) >= 4:
                    # Los primeros 4 bytes son la longitud del mensaje
                    msg_length = struct.unpack('!I', buffer[:4])[0]
                    
                    # Verificar si tenemos el mensaje completo
                    if len(buffer) >= 4 + msg_length:
                        # Extraer el mensaje
                        msg_data = buffer[4:4 + msg_length]
                        buffer = buffer[4 + msg_length:]  # Quitar mensaje procesado
                        
                        try:
                            message = pickle.loads(msg_data)
                            
                            # Actualizar heartbeat para CUALQUIER mensaje
                            self.last_heartbeat_received = time.time()
                            
                            # Procesar tipos específicos
                            msg_type = message.get('type')
                            
                            if msg_type == MessageType.CONNECTION_ACCEPTED.value:
                                if not self.connection_established:
                                    self.connected = True
                                    self.connection_established = True
                                    print("✅ Conexión aceptada por el host (TCP)")
                            
                            elif msg_type == MessageType.CONNECTION_CHECK.value:
                                # Responder check
                                if self.is_host:
                                    check_response = {
                                        'type': MessageType.CONNECTION_CHECK.value,
                                        'timestamp': time.time(),
                                        'status': 'ok'
                                    }
                                    self._send_tcp_message(check_response)
                            
                            # Agregar mensaje al buffer
                            with self.message_lock:
                                self.received_messages.append((message, None))
                                
                        except Exception as e:
                            print(f"⚠️ Error deserializando mensaje TCP: {e}")
                            continue
                    else:
                        # Mensaje incompleto, esperar más datos
                        break
                        
            except socket.timeout:
                continue  # Timeout normal en recv
            except ConnectionResetError:
                print("⚠️ Conexión TCP reseteada por el peer")
                self.connected = False
                self.connection_established = False
                break
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error en receive_tcp_messages: {e}")
                    self.connected = False
                    self.connection_established = False
                break
        
        print("🔌 Thread de recepción TCP terminado")
    
    def _send_tcp_message(self, message):
        """Envía un mensaje TCP con formato de longitud"""
        if not self.client_socket:
            print("⚠️ No hay socket TCP para enviar")
            return False
        
        try:
            # Serializar mensaje
            serialized = pickle.dumps(message)
            
            # Añadir longitud (4 bytes) al principio
            length = struct.pack('!I', len(serialized))
            full_message = length + serialized
            
            # Enviar todo
            self.client_socket.sendall(full_message)
            self.stats['messages_sent'] += 1
            return True
            
        except BrokenPipeError:
            print("❌ Conexión TCP rota - no se pudo enviar")
            self.connected = False
            return False
        except Exception as e:
            print(f"❌ Error enviando mensaje TCP: {e}")
            self.connected = False
            return False
    
    def send_player_state(self, player_data):
        """Envía el estado del jugador - MANTIENE MISMA FIRMA"""
        if self.connected and self.connection_established:
            message = {
                'type': MessageType.PLAYER_STATE.value,
                'player_id': 1 if self.is_host else 2,
                'data': player_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_tcp_message(message)
        return False
    
    def send_bomb_placed(self, bomb_data):
        """Envía información de bomba colocada - MANTIENE MISMA FIRMA"""
        if self.connected and self.connection_established:
            message = {
                'type': MessageType.BOMB_PLACED.value,
                'data': bomb_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_tcp_message(message)
        return False
    
    def send_object_destroyed(self, object_data):
        """Envía información de objeto destruido - MANTIENE MISMA FIRMA"""
        if self.connected and self.connection_established:
            message = {
                'type': MessageType.OBJECT_DESTROYED.value,
                'data': object_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_spawned(self, powerup_data):
        """Envía información de power-up aparecido - MANTIENE MISMA FIRMA"""
        if self.connected and self.connection_established:
            message = {
                'type': MessageType.POWERUP_SPAWNED.value,
                'data': powerup_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_tcp_message(message)
        return False
    
    def send_powerup_collected(self, powerup_data):
        """Envía información de power-up recogido - MANTIENE MISMA FIRMA"""
        if self.connected and self.connection_established:
            message = {
                'type': MessageType.POWERUP_COLLECTED.value,
                'data': powerup_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_tcp_message(message)
        return False
    
    def _heartbeat_loop(self):
        """Envía heartbeats periódicos - TCP"""
        while self.running:
            current_time = time.time()
            
            # Mostrar estadísticas cada 10 segundos
            if current_time - self.stats.get('last_debug_time', 0) > 10 and self.connected:
                print(f"📊 TCP Stats: Enviados={self.stats['messages_sent']}, "
                      f"Recibidos={self.stats['messages_received']}, "
                      f"Errores={self.stats['connection_errors']}")
                self.stats['last_debug_time'] = current_time
            
            # Enviar heartbeat si estamos conectados
            if self.connected and self.connection_established:
                # Enviar heartbeat cada intervalo
                if current_time - self.stats.get('last_heartbeat_sent', 0) >= self.heartbeat_interval:
                    heartbeat_msg = {
                        'type': MessageType.HEARTBEAT.value,
                        'timestamp': current_time,
                        'stats': self.stats
                    }
                    if self._send_tcp_message(heartbeat_msg):
                        self.stats['last_heartbeat_sent'] = current_time
            
            # Verificar conexión
            time_since_last = current_time - self.last_heartbeat_received
            
            if self.connected and time_since_last > self.heartbeat_timeout:
                print(f"⚠️ Posible pérdida de conexión TCP ({time_since_last:.1f}s sin mensajes)")
                
                # Intentar verificar conexión
                check_msg = {
                    'type': MessageType.CONNECTION_CHECK.value,
                    'timestamp': current_time,
                    'check': 'alive?'
                }
                self._send_tcp_message(check_msg)
                
                if time_since_last > self.heartbeat_timeout * 2:
                    print("❌ Conexión TCP perdida definitivamente")
                    self.connected = False
                    self.connection_established = False
            
            time.sleep(0.5)  # Más lento que UDP
    
    def get_messages(self):
        """Obtiene todos los mensajes recibidos - MANTIENE MISMA FIRMA"""
        with self.message_lock:
            messages = self.received_messages.copy()
            self.received_messages.clear()
            return messages
    
    def is_connected(self):
        """Verifica si hay conexión activa - MANTIENE MISMA FIRMA"""
        if not self.connected or not self.connection_established:
            return False
        
        # Verificar timeout
        time_since_last = time.time() - self.last_heartbeat_received
        is_alive = time_since_last < self.heartbeat_timeout * 1.5
        
        return is_alive
    
    def disconnect(self):
        """Cierra la conexión limpiamente - MANTIENE MISMA FIRMA"""
        self.running = False
        self.connected = False
        self.connection_established = False
        
        # Enviar mensaje de desconexión si hay conexión
        if self.client_socket:
            try:
                disconnect_msg = {
                    'type': MessageType.GAME_OVER.value,
                    'timestamp': time.time(),
                    'reason': 'disconnect'
                }
                self._send_tcp_message(disconnect_msg)
                time.sleep(0.1)  # Dar tiempo a enviar
            except:
                pass
            
            # Cerrar socket
            try:
                self.client_socket.close()
            except:
                pass
        
        # Cerrar socket servidor si existe
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        if self.connection_socket:
            try:
                self.connection_socket.close()
            except:
                pass
        
        print("🔌 Conexión TCP cerrada")
    
    # Métodos auxiliares para compatibilidad
    def _get_local_ip(self):
        """Obtiene la IP local - para mostrar al host"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _send_connection_request(self):
        """Método vacío para compatibilidad - ya no se usa en TCP"""
        pass
    
    def _listen_for_connections(self):
        """Método vacío para compatibilidad - ya no se usa en TCP"""
        pass
    
    def _receive_messages(self):
        """Método vacío para compatibilidad - reemplazado por _receive_tcp_messages"""
        pass
    
    def _send_message(self, message, address):
        """Método vacío para compatibilidad - reemplazado por _send_tcp_message"""
        pass