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
    """Sistema de red TCP para el juego Bomberman - VERSIÓN ESTABLE"""
    
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
        
        # Heartbeat - AJUSTADO PARA MÁS ESTABILIDAD
        self.last_heartbeat_received = time.time()
        self.heartbeat_interval = 3.0  # Más lento para reducir tráfico
        self.heartbeat_timeout = 30.0  # Mucho más tolerante
        
        # Estadísticas
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_errors': 0,
            'last_debug_time': time.time(),
            'last_heartbeat_sent': 0
        }
        
        # Para controlar flood de mensajes
        self.last_player_state_sent = 0
        self.player_state_min_interval = 0.05  # 20 mensajes por segundo máximo
        
    def initialize(self):
        """Inicializa la conexión TCP"""
        try:
            if self.is_host:
                # HOST: Crear socket servidor
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.settimeout(1.0)
                
                # Bind
                self.server_socket.bind(('0.0.0.0', self.port))
                self.server_socket.listen(1)
                
                print(f"🎮 Host TCP en puerto {self.port}")
                
                # Thread para aceptar
                threading.Thread(target=self._host_main, daemon=True).start()
                
            else:
                # CLIENTE
                print(f"🔗 Conectando a {self.host_ip}:{self.port}")
                self.peer_address = (self.host_ip, self.port)
                
                # Thread para conectar
                threading.Thread(target=self._client_main, daemon=True).start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando: {e}")
            return False
    
    def _host_main(self):
        """Función principal del host"""
        print("👂 Host esperando conexión...")
        
        try:
            # Aceptar conexión
            self.connection_socket, client_addr = self.server_socket.accept()
            print(f"✅ Cliente conectado: {client_addr}")
            
            # Configurar
            self.client_socket = self.connection_socket
            self.client_socket.settimeout(0.1)
            self.peer_address = client_addr
            
            with self.connection_lock:
                self.connected = True
                self.connection_established = True
            
            # Iniciar recepción
            threading.Thread(target=self._receive_loop, daemon=True).start()
            
            # Pequeña pausa
            time.sleep(0.3)
            
            # Enviar confirmación
            welcome_msg = {
                'type': MessageType.CONNECTION_ACCEPTED.value,
                'message': '¡Bienvenido!',
                'timestamp': time.time(),
                'player_id': 2,
                'data': {'status': 'connected'}
            }
            
            if self._send_tcp_message(welcome_msg):
                print("📤 Confirmación enviada")
            
            # Iniciar heartbeat
            threading.Thread(target=self._heartbeat_loop, daemon=True).start()
            
            print("✅ Host listo para jugar")
            
        except socket.timeout:
            print("⏱️ Host: Timeout esperando conexión")
        except Exception as e:
            print(f"❌ Host error: {e}")
    
    def _client_main(self):
        """Función principal del cliente"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                print(f"🔄 Intento {attempt + 1}/{max_attempts}")
                
                # Conectar
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(5)
                self.client_socket.connect((self.host_ip, self.port))
                self.client_socket.settimeout(0.1)
                
                print("✅ Conectado al host")
                
                with self.connection_lock:
                    self.connected = True
                
                # Iniciar recepción
                threading.Thread(target=self._receive_loop, daemon=True).start()
                
                # Enviar solicitud
                request = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'timestamp': time.time(),
                    'player_id': 2,
                    'data': {'action': 'connect'}
                }
                
                if not self._send_tcp_message(request):
                    print("❌ Error enviando solicitud")
                
                # Esperar confirmación
                print("⏳ Esperando confirmación...")
                start_time = time.time()
                
                while time.time() - start_time < 10.0:
                    messages = self.get_messages()
                    for msg, _ in messages:
                        if msg.get('type') == MessageType.CONNECTION_ACCEPTED.value:
                            print("✅ Confirmación recibida!")
                            
                            with self.connection_lock:
                                self.connection_established = True
                            
                            # Iniciar heartbeat
                            threading.Thread(target=self._heartbeat_loop, daemon=True).start()
                            
                            print("✅ Cliente listo para jugar")
                            return True
                    
                    time.sleep(0.1)
                
                print("❌ No se recibió confirmación")
                
            except ConnectionRefusedError:
                print("❌ Conexión rechazada")
            except socket.timeout:
                print("⏱️ Timeout de conexión")
            except Exception as e:
                print(f"⚠️ Error: {e}")
            
            # Limpiar y reintentar
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
                print(f"🔄 Reintentando en 3 segundos...")
                time.sleep(3)
        
        print("❌ No se pudo conectar")
        return False
    
    def _receive_loop(self):
        """Loop de recepción - MEJORADO"""
        print("📡 Thread de recepción iniciado")
        
        buffer = b""
        error_count = 0
        max_errors = 10
        
        try:
            while self.running and error_count < max_errors:
                try:
                    # Verificar conexión
                    with self.connection_lock:
                        if not self.connected or not self.client_socket:
                            time.sleep(0.1)
                            continue
                    
                    # Recibir datos
                    data = self.client_socket.recv(4096)
                    
                    if not data:
                        print("📭 Conexión cerrada por el peer")
                        with self.connection_lock:
                            self.connected = False
                        break
                    
                    buffer += data
                    error_count = 0  # Resetear contador de errores
                    
                    with self.connection_lock:
                        self.last_heartbeat_received = time.time()
                    
                    self.stats['messages_received'] += 1
                    
                    # Procesar mensajes completos
                    while len(buffer) >= 4:
                        try:
                            # Longitud del mensaje
                            msg_length = struct.unpack('!I', buffer[:4])[0]
                            
                            # Verificar longitud válida (máximo 1MB)
                            if msg_length > 1048576:
                                print("⚠️ Mensaje demasiado grande, ignorando")
                                buffer = b""
                                break
                            
                            # Verificar si tenemos el mensaje completo
                            if len(buffer) < 4 + msg_length:
                                break
                            
                            # Extraer mensaje
                            msg_data = buffer[4:4 + msg_length]
                            buffer = buffer[4 + msg_length:]
                            
                            # Deserializar
                            message = pickle.loads(msg_data)
                            msg_type = message.get('type')
                            
                            # Procesar
                            self._process_message(message)
                            
                        except struct.error:
                            print("⚠️ Error en formato de mensaje")
                            buffer = b""
                            error_count += 1
                            break
                        except Exception as e:
                            print(f"⚠️ Error procesando mensaje: {e}")
                            buffer = b""
                            error_count += 1
                            break
                            
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    print("⚠️ Conexión reseteada")
                    with self.connection_lock:
                        self.connected = False
                    break
                except OSError as e:
                    if e.errno in [10038, 10054]:
                        print("⚠️ Conexión cerrada por el peer")
                    else:
                        print(f"⚠️ OSError: {e}")
                    with self.connection_lock:
                        self.connected = False
                    break
                except Exception as e:
                    print(f"⚠️ Error en recepción: {e}")
                    error_count += 1
                    time.sleep(0.1)
        
        except Exception as e:
            print(f"💥 ERROR en receive_loop: {e}")
        
        print("🔌 Thread de recepción terminado")
    
    def _process_message(self, message):
        """Procesa un mensaje recibido - SILENCIOSO para mensajes frecuentes"""
        msg_type = message.get('type')
        
        # Actualizar heartbeat
        with self.connection_lock:
            self.last_heartbeat_received = time.time()
        
        # Solo mostrar logs para mensajes importantes
        if msg_type not in [MessageType.PLAYER_STATE.value, MessageType.HEARTBEAT.value]:
            print(f"📨 Mensaje recibido - Tipo: {msg_type}")
        
        # Procesar según tipo
        if msg_type == MessageType.CONNECTION_ACCEPTED.value:
            print("✅ Conexión aceptada por el host")
            with self.connection_lock:
                self.connection_established = True
            
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
        """Envía un mensaje TCP - CON RECONEXIÓN"""
        try:
            with self.connection_lock:
                if not self.connected or not self.client_socket:
                    return False
            
            # Serializar
            serialized = pickle.dumps(message)
            length = len(serialized)
            
            # Verificar tamaño
            if length > 1048576:
                print("⚠️ Mensaje demasiado grande para enviar")
                return False
            
            # Enviar longitud + mensaje
            header = struct.pack('!I', length)
            self.client_socket.sendall(header + serialized)
            
            self.stats['messages_sent'] += 1
            return True
            
        except BrokenPipeError:
            print("🔌 Conexión rota al enviar")
            self._try_reconnect()
            return False
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            self._try_reconnect()
            return False
    
    def _try_reconnect(self):
        """Intenta reconectar si se pierde la conexión"""
        if not self.running:
            return
        
        print("🔄 Intentando reconectar...")
        
        with self.connection_lock:
            self.connected = False
            self.connection_established = False
        
        # Cerrar sockets viejos
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        # Solo cliente intenta reconectar automáticamente
        if not self.is_host:
            print("🔄 Cliente intentando reconectar al host...")
            # Intentar reconectar en un thread separado
            threading.Thread(target=self._client_main, daemon=True).start()
    
    def send_player_state(self, player_data):
        """Envía estado del jugador - CON THROTTLING"""
        current_time = time.time()
        
        # Throttling: no enviar demasiados mensajes seguidos
        if current_time - self.last_player_state_sent < self.player_state_min_interval:
            return True  # Simular éxito pero no enviar realmente
        
        if self.is_connected():
            message = {
                'type': MessageType.PLAYER_STATE.value,
                'player_id': 1 if self.is_host else 2,
                'data': player_data,
                'timestamp': current_time
            }
            
            success = self._send_tcp_message(message)
            if success:
                self.last_player_state_sent = current_time
            return success
        
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
        """Loop de heartbeat - MEJORADO"""
        print("❤️ Thread de heartbeat iniciado")
        
        consecutive_failures = 0
        max_failures = 3
        
        while self.running:
            try:
                current_time = time.time()
                
                # Estadísticas cada 30 segundos (menos frecuente)
                if current_time - self.stats['last_debug_time'] > 30:
                    print(f"📊 Stats: Enviados={self.stats['messages_sent']}, Recibidos={self.stats['messages_received']}")
                    self.stats['last_debug_time'] = current_time
                
                # Enviar heartbeat si estamos conectados
                if self.is_connected():
                    if current_time - self.stats['last_heartbeat_sent'] >= self.heartbeat_interval:
                        heartbeat = {
                            'type': MessageType.HEARTBEAT.value,
                            'timestamp': current_time,
                            'seq': self.stats['messages_sent']
                        }
                        
                        if self._send_tcp_message(heartbeat):
                            self.stats['last_heartbeat_sent'] = current_time
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            print(f"⚠️ Heartbeat fallido ({consecutive_failures}/{max_failures})")
                
                # Verificar timeout (más tolerante)
                with self.connection_lock:
                    time_since = current_time - self.last_heartbeat_received
                    if self.connected and time_since > self.heartbeat_timeout:
                        print(f"⚠️ Sin heartbeat por {time_since:.1f}s")
                        self.connected = False
                        self.connection_established = False
                
                # Si hay muchos fallos consecutivos, intentar reconectar
                if consecutive_failures >= max_failures and not self.is_host:
                    print("🔄 Demasiados fallos, intentando reconectar...")
                    self._try_reconnect()
                    consecutive_failures = 0
                
                time.sleep(1.0)  # Más lento
                
            except Exception as e:
                print(f"⚠️ Error en heartbeat: {e}")
                time.sleep(2)
        
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
        """Cierra conexión limpiamente"""
        self.running = False
        
        # Pequeña pausa antes de cerrar
        time.sleep(0.1)
        
        # Cerrar sockets
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
        
        if self.connection_socket:
            try:
                self.connection_socket.close()
            except:
                pass
        
        print("🔌 Conexión cerrada limpiamente")
    
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