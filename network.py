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
    
    def __init__(self, is_host=False, host_ip='127.0.0.1', port=5555):
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
        self.heartbeat_interval = 1.0  # Aumentado para LAN
        self.heartbeat_timeout = 5.0   # Aumentado para LAN
        
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
        
        # Hilos
        self.listen_thread = None
        self.receive_thread = None
        self.heartbeat_thread = None
        
    def initialize(self):
        """Inicializa la conexión de red - MEJORADO PARA LAN"""
        try:
            # Crear socket UDP
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Configuraciones importantes para LAN
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.settimeout(0.5)  # Timeout más largo
            
            if self.is_host:
                # Host: bind a todas las interfaces
                self.socket.bind(('0.0.0.0', self.port))
                print(f"🎮 Host iniciado en puerto {self.port}")
                print(f"📡 Escuchando en todas las interfaces...")
                
                # Obtener y mostrar IP local
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                    print(f"📍 Tu IP local es: {local_ip}")
                except:
                    print("⚠️ No se pudo obtener la IP local")
                
                # Hilo para escuchar conexiones
                self.listen_thread = threading.Thread(target=self._listen_for_connections)
                self.listen_thread.daemon = True
                self.listen_thread.start()
            else:
                # Cliente: intentar varias conexiones
                self.peer_address = (self.host_ip, self.port)
                print(f"🔗 Intentando conectar a {self.host_ip}:{self.port}...")
                
                # Enviar solicitud de conexión con más intentos
                self._send_connection_request()
                
            # Hilo para recibir mensajes
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            # Hilo para heartbeat
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self.heartbeat_thread.daemon = True
            self.heartbeat_thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando red: {e}")
            print(f"💡 Asegúrate de que el puerto {self.port} esté libre")
            return False
    
    def _send_connection_request(self):
        """Envía solicitud de conexión con más intentos y mejor logging"""
        max_attempts = 5  # Más intentos
        print(f"🔗 Enviando solicitud de conexión ({max_attempts} intentos)...")
        
        for attempt in range(max_attempts):
            try:
                connection_msg = {
                    'type': MessageType.CONNECTION_REQUEST.value,
                    'player_id': id(self),
                    'timestamp': time.time(),
                    'attempt': attempt,
                    'version': '1.0'
                }
                
                print(f"📤 Intento {attempt + 1}/{max_attempts} a {self.peer_address}...")
                
                if self._send_message(connection_msg, self.peer_address):
                    print(f"  ✅ Mensaje enviado")
                else:
                    print(f"  ❌ Error enviando mensaje")
                
                # Esperar respuesta
                time.sleep(1.0)  # Más tiempo entre intentos
                
                # Si ya estamos conectados, salir
                if self.connection_established:
                    print(f"✅ ¡Conexión establecida después de {attempt + 1} intentos!")
                    return
                    
            except Exception as e:
                print(f"⚠️ Error en intento {attempt + 1}: {e}")
        
        print(f"❌ No se pudo conectar después de {max_attempts} intentos")
    
    def _listen_for_connections(self):
        """Escucha solicitudes de conexión - MEJORADO"""
        print("👂 Escuchando conexiones entrantes...")
        
        try:
            while self.running and not self.connection_established:
                try:
                    data, addr = self.socket.recvfrom(4096)
                    print(f"📨 Datos recibidos de {addr}")
                    
                    try:
                        message = pickle.loads(data)
                        print(f"  📝 Tipo de mensaje: {message.get('type')}")
                    except Exception as e:
                        print(f"  ❌ Error deserializando: {e}")
                        continue
                        
                    if message['type'] == MessageType.CONNECTION_REQUEST.value:
                        print(f"🤝 Solicitud de conexión de {addr}")
                        print(f"  📊 Versión: {message.get('version', 'desconocida')}")
                        print(f"  🆔 ID: {message.get('player_id', 'desconocido')}")
                        
                        self.peer_address = addr
                        
                        # Enviar aceptación
                        response = {
                            'type': MessageType.CONNECTION_ACCEPTED.value,
                            'player_id': 2,
                            'timestamp': time.time(),
                            'message': "Conexión aceptada",
                            'version': '1.0'
                        }
                        
                        if self._send_message(response, addr):
                            print(f"📤 Enviada aceptación a {addr}")
                        else:
                            print(f"❌ Error enviando aceptación")
                        
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
                        print(f"✅ Cliente {addr} conectado exitosamente!")
                        break  # Solo aceptar una conexión
                        
                except socket.timeout:
                    continue
                except ConnectionResetError:
                    print("⚠️ Conexión reseteada")
                    continue
                except Exception as e:
                    print(f"⚠️ Error en listen_for_connections: {e}")
                    continue
        except Exception as e:
            if self.running:
                print(f"❌ Error crítico en listen_for_connections: {e}")
    
    def _receive_messages(self):
        """Recibe mensajes de red - MEJORADO"""
        buffer_size = 8192
        
        print("📡 Iniciando recepción de mensajes...")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(buffer_size)
                self.stats['messages_received'] += 1
                
                try:
                    message = pickle.loads(data)
                except (pickle.UnpicklingError, EOFError) as e:
                    print(f"❌ Error deserializando mensaje de {addr}: {e}")
                    continue
                
                # Debug: mostrar mensajes recibidos
                if self.stats['messages_received'] % 20 == 0:  # Cada 20 mensajes
                    print(f"📊 Mensajes recibidos: {self.stats['messages_received']}")
                
                # Actualizar último heartbeat para CUALQUIER mensaje recibido del peer
                if self.peer_address and addr == self.peer_address:
                    self.last_heartbeat_received = time.time()
                    if not self.connected:
                        self.connected = True
                
                # Procesar tipos específicos
                msg_type = message.get('type')
                
                if msg_type == MessageType.CONNECTION_ACCEPTED.value:
                    if not self.connection_established:
                        self.peer_address = addr
                        self.connected = True
                        self.connection_established = True
                        print(f"✅ ¡Conexión aceptada por el host {addr}!")
                        print(f"  📝 Mensaje: {message.get('message', 'Sin mensaje')}")
                        
                        # Responder confirmación
                        confirm_msg = {
                            'type': MessageType.CONNECTION_CHECK.value,
                            'timestamp': time.time(),
                            'status': 'connected'
                        }
                        self._send_message(confirm_msg, addr)
                
                elif msg_type == MessageType.CONNECTION_CHECK.value:
                    # Si recibimos un check, responder con otro check
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
                    err_no = e.errno if hasattr(e, 'errno') else None
                    if err_no not in [10054, 10053]:  # Errores de conexión cerrada
                        self.stats['connection_errors'] += 1
                        print(f"⚠️ Socket error: {e}")
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error en receive_messages: {e}")
                continue
    
    def _send_message(self, message, address):
        """Envía un mensaje con mejor manejo de errores"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                serialized = pickle.dumps(message)
                
                # Si el mensaje es muy grande, usar prefijo de longitud
                if len(serialized) > 1024:
                    length_prefix = struct.pack('!I', len(serialized))
                    self.socket.sendto(length_prefix + serialized, address)
                else:
                    self.socket.sendto(serialized, address)
                
                self.stats['messages_sent'] += 1
                return True
                
            except socket.error as e:
                if attempt < max_attempts - 1:
                    print(f"⚠️ Error enviando mensaje (intento {attempt + 1}): {e}")
                    time.sleep(0.1)
                    continue
                else:
                    print(f"❌ Error enviando mensaje después de {max_attempts} intentos: {e}")
                    return False
            except Exception as e:
                print(f"❌ Error inesperado enviando mensaje: {e}")
                return False
    
    def send_player_state(self, player_data):
        """Envía el estado del jugador local"""
        if self.peer_address:
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
        if self.peer_address:
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
        if self.peer_address:
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
        if self.peer_address:
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
        if self.peer_address:
            message = {
                'type': MessageType.POWERUP_COLLECTED.value,
                'data': powerup_data,
                'timestamp': time.time(),
                'sequence': self.stats['messages_sent']
            }
            return self._send_message(message, self.peer_address)
        return False
    
    def _heartbeat_loop(self):
        """Envía heartbeats periódicos - MEJORADO"""
        last_heartbeat_sent = 0
        
        print("❤️ Iniciando sistema de heartbeat...")
        
        while self.running:
            current_time = time.time()
            
            # Mostrar estadísticas cada 15 segundos
            if current_time - self.stats['last_debug_time'] > 15:
                print(f"📊 Estadísticas de red:")
                print(f"  📤 Enviados: {self.stats['messages_sent']}")
                print(f"  📥 Recibidos: {self.stats['messages_received']}")
                print(f"  ⚠️ Errores: {self.stats['connection_errors']}")
                print(f"  🔗 Conectado: {self.connected}")
                print(f"  🤝 Establecido: {self.connection_established}")
                if self.peer_address:
                    print(f"  👤 Peer: {self.peer_address}")
                self.stats['last_debug_time'] = current_time
            
            # Solo enviar heartbeats si estamos conectados y tenemos peer
            if self.connected and self.peer_address:
                # Enviar heartbeat cada intervalo
                if current_time - last_heartbeat_sent >= self.heartbeat_interval:
                    heartbeat_msg = {
                        'type': MessageType.HEARTBEAT.value,
                        'timestamp': current_time,
                        'stats': self.stats,
                        'status': 'alive'
                    }
                    if self._send_message(heartbeat_msg, self.peer_address):
                        last_heartbeat_sent = current_time
                    else:
                        print("⚠️ Error enviando heartbeat")
            
            # Verificar conexión
            if self.connected:
                time_since_last = current_time - self.last_heartbeat_received
                
                if time_since_last > self.heartbeat_timeout:
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
                        self.connection_established = False
            
            time.sleep(0.5)  # Más eficiente
    
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
        
        # Para LAN, ser más tolerante
        time_since_last = time.time() - self.last_heartbeat_received
        is_alive = time_since_last < self.heartbeat_timeout * 3  # Más tolerancia
        
        return is_alive and self.peer_address is not None
    
    def disconnect(self):
        """Cierra la conexión limpiamente"""
        print("🔌 Cerrando conexión...")
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
            
            time.sleep(0.5)  # Dar tiempo para enviar último mensaje
            
            try:
                self.socket.close()
                print("✅ Socket cerrado")
            except:
                print("⚠️ Error cerrando socket")
        
        print("🔌 Conexión cerrada")
    
    def get_debug_info(self):
        """Obtiene información de debug"""
        return {
            'connected': self.connected,
            'established': self.connection_established,
            'peer': self.peer_address,
            'stats': self.stats.copy(),
            'last_heartbeat': time.time() - self.last_heartbeat_received
        }