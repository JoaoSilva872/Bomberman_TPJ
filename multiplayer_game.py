import pygame
import sys
import time
import socket
from map import Map
from player import Player
from object import Object
from bomba import Bomba
from network import GameNetwork, MessageType
from powerup import PowerUpSystem, PowerUpType

class MultiplayerGame:
    def __init__(self, is_host=False, host_ip='127.0.0.1'):
        # Configuración de ventana
        self.LARGURA = 1260
        self.ALTURA = 720
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption(f"Bomberman - {'Host' if is_host else 'Cliente'}")
        
        # Configuración del tablero
        self.TILE_SIZE = 20
        self.COR_CLARA = (0, 140, 0)
        self.COR_ESCURA = (0, 120, 0)
        
        # Configuración de jugadores
        self.PLAYER_TILES = 3
        self.player_size = self.TILE_SIZE * self.PLAYER_TILES
        self.player_vel = self.TILE_SIZE * 1.5
        
        # Red - MEJORADO: Con configuración optimizada
        self.is_host = is_host
        self.player_id = 1 if is_host else 2
        self.host_ip = host_ip
        
        # Intentar puertos alternativos si 4040 falla
        port = self._get_available_port(4040)
        self.network = GameNetwork(is_host=is_host, host_ip=host_ip, port=port)
        self.network_initialized = False
        
        # Mapa
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        
        # Jugadores
        self.local_player = self.create_player(is_local=True)
        self.remote_player = self.create_player(is_local=False)
        
        # Posiciones iniciales
        self.set_initial_positions()
        
        # Bombas
        self.local_bombs = []
        self.remote_bombs = []
        
        # Sistema de power-ups
        self.powerup_system = PowerUpSystem(probabilidad_spawn=0.35)
        
        # Objetos (compartidos)
        self.mapa.crear_obstaculos("level2")
        
        # Controladores - MEJORADO: Timing optimizado
        self.move_delay = 100  # ms entre movimientos
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        self.bomba_presionada = False
        self.tecla_r_presionada = False
        
        # Control de red - MEJORADO: Envíos optimizados
        self.last_network_update = 0
        self.network_update_interval = 0.033  # ~30 FPS para red
        self.last_player_state_sent = 0
        self.player_state_min_interval = 0.1   # 10 FPS máximo para estado del jugador
        
        # Para throttling inteligente
        self.last_player_position = (0, 0)
        self.position_change_threshold = 5  # Píxeles mínimo para considerar movimiento
        
        # Estado del juego
        self.game_running = True
        self.waiting_for_connection = True
        self.connection_start_time = time.time()
        self.connection_timeout = 60  # 60 segundos máximo
        
        # Estadísticas
        self.network_stats = {
            'player_states_sent': 0,
            'bombs_sent': 0,
            'objects_synced': 0,
            'powerups_synced': 0,
            'last_stats_display': time.time()
        }
        
        # Inicializar red
        self.initialize_network()
    
    def _get_available_port(self, preferred_port):
        """Obtiene un puerto disponible, intentando alternativas si es necesario"""
        ports_to_try = [preferred_port, 5050, 6060, 7070, 8080]
        
        for port in ports_to_try:
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(1)
                test_socket.bind(('127.0.0.1', port))
                test_socket.close()
                if port != preferred_port:
                    print(f"⚠️ Puerto {preferred_port} ocupado, usando {port}")
                return port
            except:
                continue
        
        print(f"⚠️ No se encontraron puertos libres, usando {preferred_port}")
        return preferred_port
    
    def get_local_ip(self):
        """Obtiene la IP local de la máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def initialize_network(self):
        """Inicializa la conexión de red con reintentos"""
        max_retries = 2
        
        for retry in range(max_retries):
            try:
                print(f"🔄 Intento {retry + 1}/{max_retries} de inicializar red...")
                
                if self.network.initialize():
                    self.network_initialized = True
                    print("✅ Red inicializada correctamente")
                    
                    # Si somos host, mostrar nuestra IP
                    if self.is_host:
                        local_ip = self.get_local_ip()
                        print(f"📡 Host escuchando en {local_ip}:{self.network.port}")
                        print("🔄 Esperando que un jugador se conecte...")
                    else:
                        print(f"🔗 Intentando conectar a {self.network.host_ip}:{self.network.port}")
                    
                    return True
                else:
                    print(f"❌ Error al inicializar la red (intento {retry + 1})")
                    
            except Exception as e:
                print(f"❌ Excepción al inicializar red: {e}")
            
            # Esperar antes de reintentar
            if retry < max_retries - 1:
                print("🔄 Reintentando en 2 segundos...")
                time.sleep(2)
        
        print("❌ No se pudo inicializar la red después de varios intentos")
        self.game_running = False
        return False
    
    def set_initial_positions(self):
        """Establece posiciones iniciales de los jugadores"""
        if self.is_host:
            self.local_player.x = 60
            self.local_player.y = 60
            self.remote_player.x = self.LARGURA - 120
            self.remote_player.y = 60
        else:
            self.local_player.x = self.LARGURA - 120
            self.local_player.y = 60
            self.remote_player.x = 60
            self.remote_player.y = 60
    
    def create_player(self, is_local=True):
        """Crea un jugador local o remoto"""
        player = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel)
        player.id = 1 if (is_local and self.is_host) or (not is_local and not self.is_host) else 2
        
        if not is_local:
            # Crear copia de sprites con tinte azul para jugador remoto
            remote_sprites = {}
            for direction in self.local_player.sprites:
                remote_sprites[direction] = []
                for sprite in self.local_player.sprites[direction]:
                    sprite_copy = sprite.copy()
                    # Añadir overlay azul
                    blue_overlay = pygame.Surface(sprite_copy.get_size())
                    blue_overlay.fill((100, 100, 255))
                    blue_overlay.set_alpha(100)
                    sprite_copy.blit(blue_overlay, (0, 0))
                    remote_sprites[direction].append(sprite_copy)
            
            player.sprites = remote_sprites
        
        return player
    
    def handle_events(self):
        """Maneja los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.bomba_presionada:
                    self.place_bomb()
                
                # Control remoto - detonar bombas
                if event.key == pygame.K_r and not self.tecla_r_presionada:
                    if self.local_player.tiene_control_remoto:
                        self.detonar_bombas_remotamente()
                        self.tecla_r_presionada = True
                
                # Testing (solo local)
                if event.key == pygame.K_k:
                    self.local_player.take_damage(1)
                    print(f"Vida local: {self.local_player.life}")
                
                if event.key == pygame.K_h:
                    self.local_player.heal(1)
                    print(f"Vida local: {self.local_player.life}")
                    
                # Debug: mostrar estadísticas de red
                if event.key == pygame.K_F3:
                    self._show_network_debug()
                    
                # Debug: mostrar info de power-ups
                if event.key == pygame.K_p:
                    self._show_powerup_info()
                
                # Debug: mostrar estadísticas del juego
                if event.key == pygame.K_F4:
                    self._show_game_stats()
                
                # Salir durante espera
                if event.key == pygame.K_ESCAPE:
                    if self.waiting_for_connection:
                        print("⏹️ Conexión cancelada por usuario")
                        self.game_running = False
                        return False
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
                if event.key == pygame.K_r:
                    self.tecla_r_presionada = False
        
        return True
    
    def _show_network_debug(self):
        """Muestra información de debug de red"""
        print("=== DEBUG RED ===")
        print(f"Conectado: {self.network.is_connected()}")
        print(f"Connection Established: {self.network.connection_established}")
        print(f"Player ID: {self.player_id}")
        print(f"Host: {self.is_host}")
        print(f"Dirección peer: {self.network.peer_address}")
        print(f"Mensajes enviados: {self.network.stats['messages_sent']}")
        print(f"Mensajes recibidos: {self.network.stats['messages_received']}")
        print(f"Errores: {self.network.stats['connection_errors']}")
        print(f"Tiempo sin heartbeat: {time.time() - self.network.last_heartbeat_received:.1f}s")
        
        # Estadísticas propias
        print(f"Player states enviados: {self.network_stats['player_states_sent']}")
        print(f"Bombas enviadas: {self.network_stats['bombs_sent']}")
        print(f"Objetos sincronizados: {self.network_stats['objects_synced']}")
        print(f"Power-ups sincronizados: {self.network_stats['powerups_synced']}")
    
    def _show_powerup_info(self):
        """Muestra información de power-ups"""
        print("=== POWER-UPS INFO ===")
        print(f"Jugador Local (ID: {self.local_player.id}):")
        print(f"  Max bombas: {self.local_player.max_bombas}")
        print(f"  Bombas colocadas: {self.local_player.bombas_colocadas_actual}/{self.local_player.max_bombas}")
        print(f"  Rango explosión: {self.local_player.rango_explosion}")
        print(f"  Velocidad boost: {self.local_player.velocidad_boost:.1f}")
        print(f"  Escudo activo: {self.local_player.tiene_escudo}")
        print(f"  Control remoto: {self.local_player.tiene_control_remoto}")
        print(f"Jugador Remoto (ID: {self.remote_player.id}):")
        print(f"  Max bombas: {self.remote_player.max_bombas}")
        print(f"  Rango explosión: {self.remote_player.rango_explosion}")
        print(f"  Velocidad boost: {self.remote_player.velocidad_boost:.1f}")
        print(f"  Escudo activo: {self.remote_player.tiene_escudo}")
        print(f"  Control remoto: {self.remote_player.tiene_control_remoto}")
    
    def _show_game_stats(self):
        """Muestra estadísticas del juego"""
        print("=== ESTADÍSTICAS DEL JUEGO ===")
        print(f"Bombas locales activas: {len(self.local_bombs)}")
        print(f"Bombas remotas activas: {len(self.remote_bombs)}")
        print(f"Power-ups en pantalla: {len(self.powerup_system.powerups)}")
        print(f"Objetos destruidos: {len([obj for obj in Object.objects if obj.destruido])}/{len(Object.objects)}")
        print(f"FPS: {int(self.clock.get_fps())}")
        print(f"Tiempo jugado: {(pygame.time.get_ticks() - self.tiempo_inicio) / 1000:.1f}s")
    
    def place_bomb(self):
        """Coloca una bomba en la posición actual"""
        if not self.network.is_connected():
            print("⚠️ No conectado - no se puede colocar bomba")
            return
        
        # Verificar si el jugador ya tiene una bomba activa
        if not self.local_player.puede_colocar_bomba():
            print("⚠️ Ya tienes una bomba activa - espera a que explote")
            return
        
        grid_x, grid_y = self.ajustar_a_grid(self.local_player.x, self.local_player.y)
        
        # Verificar si ya hay bomba en esa posición (de cualquier jugador)
        bomba_existente = False
        for bomba in self.local_bombs + self.remote_bombs:
            if bomba.x == grid_x and bomba.y == grid_y and not bomba.explotada:
                bomba_existente = True
                break
        
        if not bomba_existente:
            # Crear la bomba localmente
            nueva_bomba = Bomba(grid_x, grid_y, self.player_size, 
                              jugador_id=self.player_id,
                              rango_explosion=self.local_player.rango_explosion)
            nueva_bomba.es_remota = False
            self.local_bombs.append(nueva_bomba)
            
            # Marcar que el jugador colocó una bomba con referencia
            self.local_player.colocar_bomba(nueva_bomba)
            
            # Enviar a red
            bomb_data = {
                'x': grid_x,
                'y': grid_y,
                'player_id': self.player_id,
                'time': nueva_bomba.tiempo_creacion,
                'rango_explosion': nueva_bomba.rango_explosion
            }
            
            if self.network.send_bomb_placed(bomb_data):
                print(f"💣 Bomba colocada en ({grid_x}, {grid_y}) - Rango: {nueva_bomba.rango_explosion}")
                self.network_stats['bombs_sent'] += 1
            else:
                print("⚠️ Error enviando bomba a la red")
            
            self.bomba_presionada = True
    
    def detonar_bombas_remotamente(self):
        """Detona todas las bombas del jugador remotamente"""
        print("🎮 Activando control remoto...")
        bombas_detonadas = 0
        
        for bomba in self.local_bombs:
            if not bomba.explotada:
                bomba.explotar(Object.objects)
                bombas_detonadas += 1
        
        if bombas_detonadas > 0:
            print(f"💥 ¡{bombas_detonadas} bombas detonadas remotamente!")
        else:
            print("⚠️ No hay bombas para detonar")
    
    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula"""
        grid_size = self.player_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y
    
    def update(self, tiempo_actual):
        """Actualiza el estado del juego - OPTIMIZADO"""
        # 1. Procesar mensajes de red (SIEMPRE primero)
        self.process_network_messages()
        
        # 2. Actualizar movimiento local CON COLISIÓN DE BOMBAS
        self.last_move_time += self.clock.get_time()
        if self.last_move_time >= self.move_delay:
            todas_bombas = self.local_bombs + self.remote_bombs
            self.local_player.actualizar_movimiento(self.LARGURA, self.ALTURA, todas_bombas)
            self.last_move_time = 0
        
        # 3. ACTUALIZAR COLISIÓN DE BOMBAS LOCALES
        for bomba in self.local_bombs:
            if not bomba.explotada:
                bomba.actualizar_colision(self.local_player.x, self.local_player.y, 
                                         self.player_id, self.player_size)
        
        # 4. Verificar colisiones con power-ups
        jugador_rect = pygame.Rect(self.local_player.x, self.local_player.y, 
                                 self.player_size, self.player_size)
        powerups_recogidos = self.powerup_system.verificar_colisiones(jugador_rect, self.local_player)
        
        # Aplicar power-ups recogidos y sincronizar
        for tipo_powerup in powerups_recogidos:
            self.local_player.aplicar_powerup(tipo_powerup)
            # Enviar a red
            powerup_data = {
                'x': int(jugador_rect.x),
                'y': int(jugador_rect.y),
                'type': tipo_powerup.value,
                'player_id': self.player_id
            }
            if self.network.send_powerup_collected(powerup_data):
                self.network_stats['powerups_synced'] += 1
        
        # 5. Actualizar animación local
        self.local_player.actualizar_animacion(tiempo_actual, pygame.key.get_pressed())
        
        # 6. Actualizar bombas
        self.update_bombs()
        
        # 7. Enviar estado del jugador (CON THROTTLING INTELIGENTE)
        current_time = time.time()
        if current_time - self.last_player_state_sent >= self.player_state_min_interval:
            # Verificar si realmente hay cambios significativos
            current_pos = (self.local_player.x, self.local_player.y)
            dx = abs(current_pos[0] - self.last_player_position[0])
            dy = abs(current_pos[1] - self.last_player_position[1])
            
            # Enviar si se movió significativamente o si cambió estado importante
            keys = pygame.key.get_pressed()
            is_moving = any([
                keys[pygame.K_w], keys[pygame.K_UP],
                keys[pygame.K_s], keys[pygame.K_DOWN],
                keys[pygame.K_a], keys[pygame.K_LEFT],
                keys[pygame.K_d], keys[pygame.K_RIGHT]
            ])
            
            if is_moving or dx > self.position_change_threshold or dy > self.position_change_threshold:
                self.send_player_state()
                self.last_player_position = current_pos
                self.last_player_state_sent = current_time
        
        # 8. Verificar fin del juego
        if not self.local_player.is_alive():
            self.game_running = False
            print("💀 ¡Has perdido!")
            if self.network.is_connected():
                game_over_msg = {
                    'type': MessageType.GAME_OVER.value,
                    'player_id': self.player_id,
                    'timestamp': time.time()
                }
                # Enviar mensaje de fin de juego
                self.network._send_tcp_message(game_over_msg)
        
        # 9. Mostrar estadísticas periódicamente (cada 30 segundos)
        if current_time - self.network_stats['last_stats_display'] > 30:
            print(f"📊 [Stats] Player States: {self.network_stats['player_states_sent']}, "
                  f"Bombs: {self.network_stats['bombs_sent']}, "
                  f"Syncs: {self.network_stats['objects_synced']}+{self.network_stats['powerups_synced']}")
            self.network_stats['last_stats_display'] = current_time
    
    def update_bombs(self):
        """Actualiza todas las bombas (LOCALES Y REMOTAS)"""
        # Actualizar bombas locales
        bombas_a_remover_local = []
        for bomba in self.local_bombs:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                self.process_explosion_destruction(bomba, is_local=True)
            
            # Verificar daño al jugador local
            if bomba.explotada and bomba.explosion_activa() and not bomba.causou_dano:
                self.check_player_damage(bomba, self.local_player)
            
            # Limpiar bombas ya terminadas
            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover_local.append(bomba)
                # Liberar al jugador para colocar otra bomba
                self.local_player.bomba_destruida()
        
        for bomba in bombas_a_remover_local:
            self.local_bombs.remove(bomba)
        
        # Actualizar bombas remotas
        bombas_a_remover_remote = []
        for bomba in self.remote_bombs:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                self.process_explosion_destruction(bomba, is_local=False)
            
            # Verificar daño al jugador local (por bombas remotas)
            if bomba.explotada and bomba.explosion_activa() and not bomba.causou_dano:
                self.check_player_damage(bomba, self.local_player)
            
            # Limpiar bombas ya terminadas
            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover_remote.append(bomba)
        
        for bomba in bombas_a_remover_remote:
            self.remote_bombs.remove(bomba)
    
    def process_explosion_destruction(self, bomba, is_local):
        """Procesa la destrucción de objetos por una explosión"""
        destroyed_objects = []
        
        for obj in Object.objects:
            if obj.destrutivel and not obj.destruido:
                for rect in bomba.explosion_tiles:
                    if obj.rect.colliderect(rect):
                        obj.destruido = True
                        destroyed_objects.append((obj.rect.x, obj.rect.y))
                        
                        # Intentar spawnear power-up (solo si es bomba local)
                        if is_local:
                            powerup = self.powerup_system.intentar_spawn(
                                obj.rect.x, obj.rect.y, 
                                self.player_size
                            )
                            
                            # Si se spawnear un power-up, sincronizar
                            if powerup:
                                powerup_data = {
                                    'x': int(obj.rect.x),
                                    'y': int(obj.rect.y),
                                    'type': powerup.tipo.value
                                }
                                if self.network.send_powerup_spawned(powerup_data):
                                    self.network_stats['powerups_synced'] += 1
                        break
        
        # Sincronizar objetos destruidos (solo si es bomba local)
        if is_local:
            for x, y in destroyed_objects:
                object_data = {'x': int(x), 'y': int(y)}
                if self.network.send_object_destroyed(object_data):
                    self.network_stats['objects_synced'] += 1
    
    def check_player_damage(self, bomba, player):
        """Verifica si una bomba daña al jugador"""
        player_rect = pygame.Rect(player.x, player.y, self.player_size, self.player_size)
        
        for rect in bomba.explosion_tiles:
            if player_rect.colliderect(rect):
                if player.take_damage(1):
                    print(f"🔥 Jugador {player.id} golpeado! Vida: {player.life}")
                bomba.causou_dano = True
                break
    
    def send_player_state(self):
        """Envía el estado del jugador local a la red - OPTIMIZADO"""
        if self.network.is_connected():
            player_data = {
                'x': int(self.local_player.x),
                'y': int(self.local_player.y),
                'direction': self.local_player.direccion_actual,
                'frame': self.local_player.frame_actual,
                'life': self.local_player.life,
                'moving': self.local_player.esta_moviendose,
                'powerup_state': self.local_player.get_estado_powerups(),
                'timestamp': time.time()
            }
            
            if self.network.send_player_state(player_data):
                self.network_stats['player_states_sent'] += 1
                return True
        return False
    
    def process_network_messages(self):
        """Procesa los mensajes recibidos de la red"""
        messages = self.network.get_messages()
        
        for message, addr in messages:
            msg_type = message['type']
            data = message.get('data')
            
            if msg_type == MessageType.PLAYER_STATE.value:
                # Actualizar jugador remoto
                self.remote_player.x = data['x']
                self.remote_player.y = data['y']
                self.remote_player.direccion_actual = data['direction']
                self.remote_player.frame_actual = data['frame']
                self.remote_player.life = data['life']
                self.remote_player.esta_moviendose = data['moving']
                
                # Actualizar power-ups del jugador remoto
                if 'powerup_state' in data:
                    self.remote_player.set_estado_powerups(data['powerup_state'])
            
            elif msg_type == MessageType.BOMB_PLACED.value:
                # Solo procesar si no es nuestra bomba
                if data.get('player_id') != self.player_id:
                    # Verificar si ya existe
                    bomba_existente = False
                    for bomba in self.remote_bombs:
                        if bomba.x == data['x'] and bomba.y == data['y']:
                            bomba_existente = True
                            break
                    
                    if not bomba_existente:
                        rango = data.get('rango_explosion', 1)
                        bomba = Bomba(data['x'], data['y'], self.player_size, 
                                     jugador_id=data['player_id'],
                                     rango_explosion=rango)
                        bomba.tiempo_creacion = data.get('time', time.time())
                        bomba.es_remota = True
                        bomba.es_solida_para_otros = True
                        self.remote_bombs.append(bomba)
            
            elif msg_type == MessageType.OBJECT_DESTROYED.value:
                # Sincronizar objeto destruido
                x, y = data['x'], data['y']
                self.sync_object_destruction(x, y)
            
            elif msg_type == MessageType.POWERUP_SPAWNED.value:
                # Spawnear power-up remoto
                try:
                    tipo_powerup = PowerUpType(data['type'])
                    powerup = self.powerup_system.spawn_powerup(
                        data['x'], data['y'], 
                        tipo_powerup, 
                        self.player_size
                    )
                except:
                    pass
            
            elif msg_type == MessageType.POWERUP_COLLECTED.value:
                # Remover power-up recogido por el otro jugador
                powerup = self.powerup_system.get_powerup_at(data['x'], data['y'])
                if powerup:
                    powerup.recoger()
            
            elif msg_type == MessageType.GAME_OVER.value:
                print("⚠️ El otro jugador se desconectó")
                self.game_running = False
                self.network.connected = False
                self.network.connection_established = False
    
    def sync_object_destruction(self, x, y):
        """Sincroniza la destrucción de un objeto"""
        for obj in Object.objects:
            if obj.rect.x == x and obj.rect.y == y and not obj.destruido:
                obj.destruido = True
                break
    
    def draw_waiting_screen(self):
        """Dibuja pantalla de espera de conexión mejorada"""
        # Fondo con gradiente
        for y in range(self.ALTURA):
            color_value = int(20 + (y / self.ALTURA) * 30)
            pygame.draw.line(self.JANELA, (0, 0, color_value), (0, y), (self.LARGURA, y))
        
        # Panel central
        panel_width = 600
        panel_height = 400
        panel_x = self.LARGURA // 2 - panel_width // 2
        panel_y = self.ALTURA // 2 - panel_height // 2
        
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 0, 40, 220))
        pygame.draw.rect(panel, (0, 150, 255), (0, 0, panel_width, panel_height), 5)
        self.JANELA.blit(panel, (panel_x, panel_y))
        
        font_large = pygame.font.Font(None, 60)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        
        # Título
        title = font_large.render("⚡ ESPERANDO CONEXIÓN ⚡", True, (255, 215, 0))
        title_rect = title.get_rect(center=(self.LARGURA//2, panel_y + 60))
        self.JANELA.blit(title, title_rect)
        
        # Información de conexión
        if self.is_host:
            local_ip = self.get_local_ip()
            ip_text = font_medium.render(f"🌐 TU IP: {local_ip}", True, (100, 200, 255))
            ip_rect = ip_text.get_rect(center=(self.LARGURA//2, panel_y + 120))
            self.JANELA.blit(ip_text, ip_rect)
            
            port_text = font_medium.render(f"🔌 PUERTO: {self.network.port}", True, (100, 200, 255))
            port_rect = port_text.get_rect(center=(self.LARGURA//2, panel_y + 160))
            self.JANELA.blit(port_text, port_rect)
            
            instruction = font_small.render("Comparte estos datos con el otro jugador", True, (180, 180, 255))
            instr_rect = instruction.get_rect(center=(self.LARGURA//2, panel_y + 200))
            self.JANELA.blit(instruction, instr_rect)
        else:
            host_text = font_medium.render(f"🔗 CONECTANDO A: {self.host_ip}", True, (100, 200, 255))
            host_rect = host_text.get_rect(center=(self.LARGURA//2, panel_y + 120))
            self.JANELA.blit(host_text, host_rect)
            
            port_text = font_medium.render(f"🔌 PUERTO: {self.network.port}", True, (100, 200, 255))
            port_rect = port_text.get_rect(center=(self.LARGURA//2, panel_y + 160))
            self.JANELA.blit(port_text, port_rect)
        
        # Estado de conexión
        status_panel = pygame.Surface((400, 50), pygame.SRCALPHA)
        status_panel.fill((0, 0, 0, 150))
        
        if self.network.connection_established:
            status_color = (0, 255, 0)
            status_text = "🟢 CONECTADO - INICIANDO JUEGO..."
        elif self.network.connected:
            status_color = (255, 255, 0)
            status_text = "🟡 CONECTANDO..."
        else:
            status_color = (255, 50, 50)
            status_text = "🔴 SIN CONEXIÓN"
        
        pygame.draw.rect(status_panel, status_color, (0, 0, 400, 50), 3)
        self.JANELA.blit(status_panel, (self.LARGURA//2 - 200, panel_y + 220))
        
        status = font_medium.render(status_text, True, status_color)
        status_rect = status.get_rect(center=(self.LARGURA//2, panel_y + 245))
        self.JANELA.blit(status, status_rect)
        
        # Barra de progreso animada
        wait_time = int(time.time() - self.connection_start_time)
        progress = min(wait_time / self.connection_timeout, 1.0)
        
        progress_bg = pygame.Rect(self.LARGURA//2 - 200, panel_y + 290, 400, 25)
        pygame.draw.rect(self.JANELA, (50, 50, 80), progress_bg)
        pygame.draw.rect(self.JANELA, (100, 100, 255), progress_bg, 3)
        
        # Barra de carga animada
        bar_width = int(380 * progress)
        bar_color = (0, 180, 255) if progress < 0.7 else (255, 100, 0)
        pygame.draw.rect(self.JANELA, bar_color, 
                        (self.LARGURA//2 - 190, panel_y + 295, bar_width, 15))
        
        # Efecto de brillo en la barra
        if bar_width > 10:
            shine = pygame.Surface((bar_width, 5), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 100))
            self.JANELA.blit(shine, (self.LARGURA//2 - 190, panel_y + 295))
        
        # Porcentaje
        percent_text = font_small.render(f"{int(progress * 100)}%", True, (255, 255, 255))
        percent_rect = percent_text.get_rect(center=(self.LARGURA//2, panel_y + 307))
        self.JANELA.blit(percent_text, percent_rect)
        
        # Tiempo
        time_text = font_small.render(f"Tiempo: {wait_time}s / {self.connection_timeout}s", 
                                    True, (200, 200, 200))
        time_rect = time_text.get_rect(center=(self.LARGURA//2, panel_y + 330))
        self.JANELA.blit(time_text, time_rect)
        
        # Instrucciones
        keys_text = font_small.render("Presiona ESC para cancelar  |  F3 para información de red", 
                                    True, (150, 150, 200))
        keys_rect = keys_text.get_rect(center=(self.LARGURA//2, self.ALTURA - 30))
        self.JANELA.blit(keys_text, keys_rect)
        
        # Animación de conexión (puntos que parpadean)
        dot_time = int(time.time() * 3) % 4
        dots = "   "
        if dot_time > 0:
            dots = "." + "   "[:dot_time-1]
        
        connecting_text = font_small.render(f"Conectando{dots}", True, (255, 255, 200))
        connecting_rect = connecting_text.get_rect(center=(self.LARGURA//2, panel_y + 270))
        self.JANELA.blit(connecting_text, connecting_rect)
        
        pygame.display.update()
    
    def render(self):
        """Renderiza todos los elementos del juego"""
        # 1. Dibujar mapa
        self.mapa.dibujar(self.JANELA)
        
        # 2. Dibujar objetos no destruidos
        for obj in Object.objects:
            if not obj.destruido:
                obj.draw(self.JANELA)
        
        # 3. Dibujar power-ups
        self.powerup_system.dibujar_todos(self.JANELA)
        
        # 4. Dibujar bombas remotas
        for bomba in self.remote_bombs:
            bomba.dibujar(self.JANELA)
        
        # 5. Dibujar bombas locales
        for bomba in self.local_bombs:
            bomba.dibujar(self.JANELA)
        
        # 6. Dibujar jugador remoto
        self.remote_player.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 7. Dibujar jugador local (encima)
        self.local_player.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 8. Dibujar HUD
        self.draw_hud()
        
        # 9. Dibujar estado de conexión
        self.draw_connection_status()
        
        pygame.display.update()
    
    def draw_hud(self):
        """Dibuja la interfaz de usuario mejorada"""
        # Fondo general del HUD
        hud_bg = pygame.Surface((self.LARGURA, 150), pygame.SRCALPHA)
        hud_bg.fill((20, 20, 40, 200))
        self.JANELA.blit(hud_bg, (0, 0))
        
        font = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        font_large = pygame.font.Font(None, 42)
        
        # Título del modo
        mode_text = font_large.render("⚔️ MODO MULTIJUGADOR ⚔️", True, (255, 215, 0))
        mode_rect = mode_text.get_rect(center=(self.LARGURA//2, 30))
        self.JANELA.blit(mode_text, mode_rect)
        
        # Panel jugador local (izquierda)
        local_panel = pygame.Surface((300, 90), pygame.SRCALPHA)
        local_panel.fill((0, 40, 80, 180))
        pygame.draw.rect(local_panel, (0, 150, 255), (0, 0, 300, 90), 3)
        self.JANELA.blit(local_panel, (20, 70))
        
        # Vida local
        local_life = font.render(f"❤️ TÚ: {self.local_player.life} vidas", True, (100, 200, 255))
        self.JANELA.blit(local_life, (35, 80))
        
        # Stats locales
        local_stats = font_small.render(
            f"💣 {self.local_player.bombas_colocadas_actual}/{self.local_player.max_bombas} " +
            f"🔥 {self.local_player.rango_explosion}",
            True, (200, 220, 255)
        )
        self.JANELA.blit(local_stats, (35, 115))
        
        # Panel jugador remoto (derecha)
        remote_panel = pygame.Surface((300, 90), pygame.SRCALPHA)
        remote_panel.fill((80, 0, 40, 180))
        pygame.draw.rect(remote_panel, (255, 50, 100), (0, 0, 300, 90), 3)
        self.JANELA.blit(remote_panel, (self.LARGURA - 320, 70))
        
        # Vida remota
        remote_life = font.render(f"💀 RIVAL: {self.remote_player.life} vidas", True, (255, 150, 150))
        remote_rect = remote_life.get_rect(right=self.LARGURA - 35, top=80)
        self.JANELA.blit(remote_life, remote_rect)
        
        # Stats remotos
        remote_stats = font_small.render(
            f"💣 ?/{self.remote_player.max_bombas} " +
            f"🔥 {self.remote_player.rango_explosion}",
            True, (255, 200, 200)
        )
        remote_stats_rect = remote_stats.get_rect(right=self.LARGURA - 35, top=115)
        self.JANELA.blit(remote_stats, remote_stats_rect)
        
        # Power-ups especiales (centro inferior)
        y_special = 80
        if self.local_player.tiene_escudo:
            escudo_panel = pygame.Surface((180, 30), pygame.SRCALPHA)
            escudo_panel.fill((0, 80, 160, 180))
            self.JANELA.blit(escudo_panel, (self.LARGURA//2 - 200, y_special))
            
            escudo_text = font_small.render("🛡️ ESCUDO ACTIVO", True, (150, 220, 255))
            escudo_rect = escudo_text.get_rect(center=(self.LARGURA//2 - 110, y_special + 15))
            self.JANELA.blit(escudo_text, escudo_rect)
            y_special += 35
        
        if self.local_player.tiene_control_remoto:
            control_panel = pygame.Surface((180, 30), pygame.SRCALPHA)
            control_panel.fill((80, 0, 120, 180))
            self.JANELA.blit(control_panel, (self.LARGURA//2 + 20, y_special - 35))
            
            control_text = font_small.render("🎮 CTRL REMOTO (R)", True, (220, 150, 255))
            control_rect = control_text.get_rect(center=(self.LARGURA//2 + 110, y_special - 20))
            self.JANELA.blit(control_text, control_rect)
        
        # Indicador de bomba activa
        if self.local_player.bomba_colocada:
            bomba_panel = pygame.Surface((200, 35), pygame.SRCALPHA)
            bomba_panel.fill((255, 80, 0, 180))
            self.JANELA.blit(bomba_panel, (self.LARGURA//2 - 100, 120))
            
            bomba_text = font.render("💣 ¡BOMBA ACTIVA!", True, (255, 255, 200))
            bomba_rect = bomba_text.get_rect(center=(self.LARGURA//2, 137))
            self.JANELA.blit(bomba_text, bomba_rect)
    
    def draw_connection_status(self):
        """Dibuja el estado de la conexión mejorado"""
        # Panel de estado de conexión (esquina superior derecha)
        status_panel = pygame.Surface((220, 70), pygame.SRCALPHA)
        status_panel.fill((0, 0, 0, 180))
        pygame.draw.rect(status_panel, (100, 100, 200), (0, 0, 220, 70), 2)
        
        self.JANELA.blit(status_panel, (self.LARGURA - 230, 10))
        
        font = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 22)
        
        if self.network.is_connected():
            # Estado de conexión
            status_icon = "🟢" if self.network.is_connected() else "🔴"
            status_color = (0, 255, 0) if self.network.is_connected() else (255, 0, 0)
            
            status = font.render(f"{status_icon} CONECTADO", True, status_color)
            status_rect = status.get_rect(right=self.LARGURA - 20, top=20)
            self.JANELA.blit(status, status_rect)
            
            # Ping
            time_since = time.time() - self.network.last_heartbeat_received
            ping_ms = int(time_since * 500)
            
            # Color del ping según calidad
            if ping_ms < 100:
                ping_color = (0, 255, 0)
            elif ping_ms < 200:
                ping_color = (255, 255, 0)
            elif ping_ms < 400:
                ping_color = (255, 150, 0)
            else:
                ping_color = (255, 0, 0)
            
            ping = font_small.render(f"📶 Ping: ~{ping_ms}ms", True, ping_color)
            ping_rect = ping.get_rect(right=self.LARGURA - 20, top=45)
            self.JANELA.blit(ping, ping_rect)
            
            # Estadísticas rápidas
            stats_text = f"↑{self.network_stats['player_states_sent']} ↓{self.network.stats['messages_received']}"
            stats = font_small.render(stats_text, True, (200, 200, 200))
            stats_rect = stats.get_rect(right=self.LARGURA - 20, top=65)
            self.JANELA.blit(stats, stats_rect)
        else:
            status = font.render("🔴 DESCONECTADO", True, (255, 0, 0))
            status_rect = status.get_rect(right=self.LARGURA - 20, top=20)
            self.JANELA.blit(status, status_rect)
            
            recon_text = font_small.render("Reconectando...", True, (255, 150, 0))
            recon_rect = recon_text.get_rect(right=self.LARGURA - 20, top=45)
            self.JANELA.blit(recon_text, recon_rect)
    
    def run(self):
        """Bucle principal del juego - MEJORADO"""
        # Bucle principal
        while self.game_running:
            tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
            
            # Manejar eventos
            if not self.handle_events():
                break
            
            # Si estamos esperando conexión
            if self.waiting_for_connection:
                # Procesar mensajes de red incluso mientras esperamos
                self.process_network_messages()
                
                # Verificar si ya estamos conectados
                if self.network.is_connected() and self.network.connection_established:
                    self.waiting_for_connection = False
                    print("✅ ¡Conexión establecida! Comenzando juego...")
                    # Pequeña pausa para sincronizar
                    pygame.time.delay(1000)
                    continue
                
                # Verificar timeout
                if time.time() - self.connection_start_time > self.connection_timeout:
                    print("❌ Tiempo de espera agotado para conexión")
                    self.game_running = False
                    break
                
                # Dibujar pantalla de espera
                self.draw_waiting_screen()
                self.clock.tick(30)
                continue
            
            # Juego normal - ya conectados
            self.update(tiempo_actual)
            self.render()
            self.clock.tick(60)  # 60 FPS máximo
        
        # Pantalla de fin de juego
        if self.network_initialized:
            self.network.disconnect()
        
        self.show_game_over()
    
    def show_game_over(self):
        """Muestra pantalla de fin de juego - MEJORADA"""
        font_large = pygame.font.Font(None, 100)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        
        # Determinar resultado
        if self.waiting_for_connection:
            result_text = "CONEXIÓN FALLIDA"
            result_color = (255, 100, 0)
            detail_text = "No se pudo establecer conexión"
        elif not self.local_player.is_alive():
            result_text = "¡PERDISTE!"
            result_color = (255, 0, 0)
            detail_text = f"Vidas restantes: 0"
        elif not self.remote_player.is_alive():
            result_text = "¡GANASTE!"
            result_color = (0, 255, 0)
            detail_text = f"Vidas enemigo: 0"
        else:
            result_text = "JUEGO TERMINADO"
            result_color = (255, 255, 0)
            detail_text = "Conexión perdida"
        
        # Resultado principal
        result = font_large.render(result_text, True, result_color)
        result_rect = result.get_rect(center=(self.LARGURA//2, self.ALTURA//2 - 100))
        
        # Detalle
        detail = font_medium.render(detail_text, True, (255, 255, 255))
        detail_rect = detail.get_rect(center=(self.LARGURA//2, self.ALTURA//2))
        
        # Estadísticas
        stats_texts = [
            f"Tiempo jugado: {(pygame.time.get_ticks() - self.tiempo_inicio) / 1000:.1f}s",
            f"Mensajes enviados: {self.network_stats['player_states_sent']}",
            f"Bombas colocadas: {self.network_stats['bombs_sent']}",
            f"Objetos destruidos: {self.network_stats['objects_synced']}"
        ]
        
        # Instrucción
        instruction = font_small.render("Presiona cualquier tecla para salir", True, (200, 200, 200))
        instr_rect = instruction.get_rect(center=(self.LARGURA//2, self.ALTURA - 50))
        
        # Dibujar todo
        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(result, result_rect)
        self.JANELA.blit(detail, detail_rect)
        
        # Dibujar estadísticas
        y_offset = self.ALTURA//2 + 50
        for stat_text in stats_texts:
            stat = font_small.render(stat_text, True, (180, 180, 180))
            stat_rect = stat.get_rect(center=(self.LARGURA//2, y_offset))
            self.JANELA.blit(stat, stat_rect)
            y_offset += 30
        
        self.JANELA.blit(instruction, instr_rect)
        pygame.display.update()
        
        # Esperar entrada del usuario
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            
            self.clock.tick(30)