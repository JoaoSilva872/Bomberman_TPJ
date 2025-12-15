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
    """Sistema de red para el juego Bomberman usando UDP"""
    
    def __init__(self, is_host=False, host_ip='0.0.0.0', port=4040):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        self.socket = None
        self.connected = False
        self.connection_established = False
        self.peer_address = None
        self.running = True
        
        # Buffer para mensajes recibidos
        self.received_messages = []
        self.message_lock = threading.Lock()
        
        # Para heartbeat - con mejor tolerancia
        self.last_heartbeat_received = time.time()
        self.heartbeat_interval = 0.5
        self.heartbeat_timeout = 3.0
        
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
            'last_debug_time': time.time()
        }
        
    def initialize(self):
        """Inicializa la conexión de red"""
        try:
            # Crear socket UDP con timeout
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(0.1)
            
            if self.is_host:
                # Host: bind al puerto
                self.socket.bind(('0.0.0.0', self.port))
                print(f"🎮 Host iniciado en puerto {self.port}")
                
                # Hilo para escuchar conexiones
                listen_thread = threading.Thread(target=self._listen_for_connections)
                listen_thread.daemon = True
                listen_thread.start()
            else:
                # Cliente: conectar al host
                self.peer_address = (self.host_ip, self.port)
                
                # Enviar solicitud de conexión con reintentos
                self._send_connection_request()
                
                print(f"🔗 Conectando a {self.host_ip}:{self.port}...")
                
            # Hilo para recibir mensajes
            receive_thread = threading.Thread(target=self._receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            # Hilo para heartbeat
            heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            heartbeat_thread.daemon = True
            heartbeat_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando red: {e}")
            return False
    
    def _send_connection_request(self):
        """Envía solicitud de conexión con reintentos"""
        for attempt in range(3):
            try:
                connection_msg = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'player_id': id(self),
                    'timestamp': time.time(),
                    'attempt': attempt
                }
                self._send_message(connection_msg, self.peer_address)
                print(f"📤 Intento {attempt + 1}/3 de conexión...")
                
                # Pequeña pausa entre intentos
                time.sleep(0.3)
                
            except Exception as e:
                print(f"⚠️ Error en intento {attempt + 1}: {e}")
    
    def _listen_for_connections(self):
        """Escucha solicitudes de conexión (solo host) - SOLO UNA CONEXIÓN"""
        try:
            while self.running and not self.connection_established:
                try:
                    data, addr = self.socket.recvfrom(4096)
                    
                    try:
                        message = pickle.loads(data)
                    except:
                        continue
                        
                    if message['type'] == MessageType.CONNECTION_REQUEST.value:
                        print(f"📨 Solicitud de conexión de {addr}")
                        self.peer_address = addr
                        
                        # Enviar aceptación
                        response = {
                            'type': MessageType.CONNECTION_ACCEPTED.value,
                            'player_id': 2,
                            'timestamp': time.time(),
                            'message': "Conexión aceptada"
                        }
                        self._send_message(response, addr)
                        
                        # También enviar un heartbeat inmediato
                        heartbeat_msg = {
                            'type': MessageType.HEARTBEAT.value,
                            'timestamp': time.time(),
                            'welcome': True
                        }
                        self._send_message(heartbeat_msg, addr)
                        
                        self.connected = True
                        self.connection_established = True
                        self.last_heartbeat_received = time.time()
                        print(f"✅ Cliente conectado: {addr}")
                        print(f"📤 Enviado heartbeat de bienvenida a {addr}")
                        break  # Solo aceptar una conexión
                        
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    continue
                except Exception as e:
                    # Ignorar errores de conexión cerrada
                    if "10054" not in str(e):
                        print(f"⚠️ Error en listen_for_connections: {e}")
                    continue
        except Exception as e:
            if self.running:
                print(f"❌ Error crítico en listen_for_connections: {e}")
    
    def _receive_messages(self):
        """Recibe mensajes de red con mejor manejo de errores"""
        buffer_size = 8192
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(buffer_size)
                self.stats['messages_received'] += 1
                
                try:
                    message = pickle.loads(data)
                except (pickle.UnpicklingError, EOFError):
                    continue
                
                # Actualizar último heartbeat para CUALQUIER mensaje recibido del peer
                if self.peer_address and addr == self.peer_address:
                    self.last_heartbeat_received = time.time()
                
                # Procesar tipos específicos
                msg_type = message.get('type')
                
                if msg_type == MessageType.CONNECTION_ACCEPTED.value:
                    if not self.connection_established:
                        self.peer_address = addr
                        self.connected = True
                        self.connection_established = True
                        print("✅ Conexión aceptada por el host")
                        # Responder confirmación
                        confirm_msg = {
                            'type': MessageType.CONNECTION_CHECK.value,
                            'timestamp': time.time(),
                            'status': 'ok'
                        }
                        self._send_message(confirm_msg, addr)
                
                elif msg_type == MessageType.CONNECTION_CHECK.value:
                    # Si recibimos un check, responder con otro check
                    if self.is_host:
                        check_response = {
                            'type': MessageType.CONNECTION_CHECK.value,
                            'timestamp': time.time(),
                            'status': 'ok'
                        }
                        self._send_message(check_response, addr)
                
                # Agregar mensaje al buffer
                with self.message_lock:
                    self.received_messages.append((message, addr))
                    
            except socket.timeout:
                continue
            except ConnectionResetError:
                if self.running and self.connected:
                    print("⚠️ Conexión reseteada por el peer")
                    self.connected = False
                continue
            except socket.error as e:
                if self.running:
                    # Ignorar errores de conexión cerrada (10054 en Windows)
                    err_no = e.errno if hasattr(e, 'errno') else None
                    if err_no != 10054:
                        self.stats['connection_errors'] += 1
                continue
            except Exception as e:
                if self.running:
                    continue
    
    def _send_message(self, message, address):
        """Envía un mensaje a una dirección específica con reintentos"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                serialized = pickle.dumps(message)
                if len(serialized) > 1024:
                    length_prefix = struct.pack('!I', len(serialized))
                    self.socket.sendto(length_prefix + serialized, address)
                else:
                    self.socket.sendto(serialized, address)
                
                self.stats['messages_sent'] += 1
                return True
                
            except (socket.error, ConnectionResetError):
                if attempt < max_attempts - 1:
                    time.sleep(0.05)
                    continue
                else:
                    return False
            except Exception:
                return False
    
    def send_player_state(self, player_data):
        """Envía el estado del jugador local"""
        if self.connected and self.peer_address:
            message = {
                'type': MessageType.PLAYER_STATE.value,
                'player_id': 1 if self.is_host else 2,
                'data': player_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def send_bomb_placed(self, bomb_data):
        """Envía información de bomba colocada"""
        if self.connected and self.peer_address:
            message = {
                'type': MessageType.BOMB_PLACED.value,
                'data': bomb_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def send_object_destroyed(self, object_data):
        """Envía información de objeto destruido"""
        if self.connected and self.peer_address:
            message = {
                'type': MessageType.OBJECT_DESTROYED.value,
                'data': object_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def send_powerup_spawned(self, powerup_data):
        """Envía información de power-up aparecido"""
        if self.connected and self.peer_address:
            message = {
                'type': MessageType.POWERUP_SPAWNED.value,
                'data': powerup_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def send_powerup_collected(self, powerup_data):
        """Envía información de power-up recogido"""
        if self.connected and self.peer_address:
            message = {
                'type': MessageType.POWERUP_COLLECTED.value,
                'data': powerup_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def _heartbeat_loop(self):
        """Envía heartbeats periódicos"""
        last_heartbeat_sent = 0
        
        while self.running:
            current_time = time.time()
            
            # Mostrar estadísticas cada 10 segundos
            if current_time - self.stats['last_debug_time'] > 10 and self.connected:
                print(f"📊 Red: Enviados={self.stats['messages_sent']}, "
                      f"Recibidos={self.stats['messages_received']}, "
                      f"Errores={self.stats['connection_errors']}")
                self.stats['last_debug_time'] = current_time
            
            # Solo enviar heartbeats si estamos conectados
            if self.connected and self.peer_address:
                # Enviar heartbeat cada intervalo
                if current_time - last_heartbeat_sent >= self.heartbeat_interval:
                    heartbeat_msg = {
                        'type': MessageType.HEARTBEAT.value,
                        'timestamp': current_time,
                        'stats': self.stats
                    }
                    if self._send_message(heartbeat_msg, self.peer_address):
                        last_heartbeat_sent = current_time
            
            # Verificar conexión
            time_since_last = current_time - self.last_heartbeat_received
            
            if self.connected and time_since_last > self.heartbeat_timeout:
                print(f"⚠️ Posible pérdida de conexión ({time_since_last:.1f}s sin mensajes)")
                
                # Intentar verificar conexión
                check_msg = {
                    'type': MessageType.CONNECTION_CHECK.value,
                    'timestamp': current_time,
                    'check': 'alive?'
                }
                self._send_message(check_msg, self.peer_address)
                
                if time_since_last > self.heartbeat_timeout * 2:
                    print("❌ Conexión perdida definitivamente")
                    self.connected = False
            
            time.sleep(0.1)
    
    def get_messages(self):
        """Obtiene todos los mensajes recibidos"""
        with self.message_lock:
            messages = self.received_messages.copy()
            self.received_messages.clear()
            return messages
    
    def is_connected(self):
        """Verifica si hay conexión activa"""
        if not self.connected or not self.connection_established:
            return False
        
        time_since_last = time.time() - self.last_heartbeat_received
        is_alive = time_since_last < self.heartbeat_timeout * 1.5
        
        return is_alive
    
    def disconnect(self):
        """Cierra la conexión limpiamente"""
        self.running = False
        if self.socket:
            try:
                if self.connected and self.peer_address:
                    disconnect_msg = {
                        'type': MessageType.GAME_OVER.value,
                        'timestamp': time.time(),
                        'reason': 'disconnect'
                    }
                    self._send_message(disconnect_msg, self.peer_address)
            except:
                pass
            
            time.sleep(0.1)
            try:
                self.socket.close()
            except:
                pass
        
        print("🔌 Conexión cerrada")