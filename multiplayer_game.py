import pygame
import sys
import time
import socket
from map import Map
from player import Player
from object import Object
from bomba import Bomba
from network import GameNetwork, MessageType

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
        self.player_vel = self.TILE_SIZE
        
        # Red
        self.is_host = is_host
        self.player_id = 1 if is_host else 2
        self.host_ip = host_ip
        self.network = GameNetwork(is_host=is_host, host_ip=host_ip)
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
        
        # Objetos (compartidos)
        self.mapa.crear_obstaculos("level2")
        
        # Controladores
        self.move_delay = 100
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        self.bomba_presionada = False
        self.last_network_update = 0
        self.network_update_interval = 0.033
        
        # Estado del juego
        self.game_running = True
        self.waiting_for_connection = True
        self.connection_start_time = time.time()
        
        # Inicializar red
        self.initialize_network()
    
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
        """Inicializa la conexión de red"""
        try:
            if self.network.initialize():
                self.network_initialized = True
                print("✅ Red inicializada correctamente")
                
                # Si somos host, mostrar nuestra IP
                if self.is_host:
                    local_ip = self.get_local_ip()
                    print(f"📡 Host escuchando en {local_ip}:5555")
                    print("🔄 Esperando que un jugador se conecte...")
                else:
                    print(f"🔗 Intentando conectar a {self.network.host_ip}:5555")
                
                return True
            else:
                print("❌ Error al inicializar la red")
                self.game_running = False
                return False
        except Exception as e:
            print(f"❌ Excepción al inicializar red: {e}")
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
                
                # Testing (solo local)
                if event.key == pygame.K_k:
                    self.local_player.take_damage(1)
                    print(f"Vida local: {self.local_player.life}")
                
                if event.key == pygame.K_h:
                    self.local_player.heal(1)
                    print(f"Vida local: {self.local_player.life}")
                    
                # Debug: mostrar estadísticas de red
                if event.key == pygame.K_F3:
                    print("=== DEBUG RED ===")
                    print(f"Conectado: {self.network.is_connected()}")
                    print(f"Connection Established: {self.network.connection_established}")
                    print(f"Mensajes enviados: {self.network.stats['messages_sent']}")
                    print(f"Mensajes recibidos: {self.network.stats['messages_received']}")
                    print(f"Errores: {self.network.stats['connection_errors']}")
                    print(f"Peer Address: {self.network.peer_address}")
                    
                # Salir durante espera
                if event.key == pygame.K_ESCAPE:
                    if self.waiting_for_connection:
                        print("⏹️ Conexión cancelada por usuario")
                        self.game_running = False
                        return False
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
        
        return True
    
    def place_bomb(self):
        """Coloca una bomba en la posición actual"""
        if not self.network.is_connected():
            print("⚠️ No conectado - no se puede colocar bomba")
            return
        
        grid_x, grid_y = self.ajustar_a_grid(self.local_player.x, self.local_player.y)
        
        # Verificar si ya hay bomba en esa posición
        bomba_existente = False
        for bomba in self.local_bombs + self.remote_bombs:
            if bomba.x == grid_x and bomba.y == grid_y and not bomba.explotada:
                bomba_existente = True
                break
        
        if not bomba_existente:
            # Crear la bomba localmente
            nueva_bomba = Bomba(grid_x, grid_y, self.player_size)
            self.local_bombs.append(nueva_bomba)
            
            # Enviar a red
            bomb_data = {
                'x': grid_x,
                'y': grid_y,
                'player_id': self.player_id,
                'time': nueva_bomba.tiempo_creacion
            }
            
            if self.network.send_bomb_placed(bomb_data):
                print(f"💣 Bomba colocada en ({grid_x}, {grid_y})")
            else:
                print("⚠️ Error enviando bomba a la red")
            
            self.bomba_presionada = True
    
    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula"""
        grid_size = self.player_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y
    
    def update(self, tiempo_actual):
        """Actualiza el estado del juego"""
        # 1. Procesar mensajes de red
        self.process_network_messages()
        
        # 2. Actualizar movimiento local
        self.last_move_time += self.clock.get_time()
        if self.last_move_time >= self.move_delay:
            self.local_player.actualizar_movimiento(self.LARGURA, self.ALTURA)
            self.last_move_time = 0
        
        # 3. Actualizar animación local
        self.local_player.actualizar_animacion(tiempo_actual, pygame.key.get_pressed())
        
        # 4. Actualizar bombas (LOCALES Y REMOTAS)
        self.update_bombs()
        
        # 5. Enviar estado del jugador
        current_time = time.time()
        if current_time - self.last_network_update >= self.network_update_interval:
            self.send_player_state()
            self.last_network_update = current_time
        
        # 6. Verificar fin del juego
        if not self.local_player.is_alive():
            self.game_running = False
            print("💀 ¡Has perdido!")
            # Enviar mensaje de game over
            if self.network.is_connected():
                game_over_msg = {
                    'type': MessageType.GAME_OVER.value,
                    'player_id': self.player_id,
                    'timestamp': time.time()
                }
                self.network._send_message(game_over_msg, self.network.peer_address)
    
    def update_bombs(self):
        """Actualiza todas las bombas (LOCALES Y REMOTAS)"""
        # Actualizar bombas locales
        bombas_a_remover_local = []
        for bomba in self.local_bombs:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                # Procesar destrucción de objetos por bomba local
                self.process_explosion_destruction(bomba, is_local=True)
            
            # Verificar daño al jugador local
            if bomba.explotada and bomba.explosion_activa() and not bomba.causou_dano:
                self.check_player_damage(bomba, self.local_player)
            
            # Limpiar bombas ya terminadas
            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover_local.append(bomba)
        
        for bomba in bombas_a_remover_local:
            self.local_bombs.remove(bomba)
        
        # Actualizar bombas remotas
        bombas_a_remover_remote = []
        for bomba in self.remote_bombs:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                # Procesar destrucción de objetos por bomba remota
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
                        print(f"💥 {'[LOCAL]' if is_local else '[REMOTO]'} Objeto destruido en ({obj.rect.x}, {obj.rect.y})")
                        break
        
        # Sincronizar objetos destruidos (solo si es bomba local)
        if is_local:
            for x, y in destroyed_objects:
                object_data = {'x': x, 'y': y}
                if self.network.send_object_destroyed(object_data):
                    print(f"📤 [SYNC] Enviando destrucción de objeto en ({x}, {y})")
    
    def check_player_damage(self, bomba, player):
        """Verifica si una bomba daña al jugador"""
        player_rect = pygame.Rect(player.x, player.y, self.player_size, self.player_size)
        
        for rect in bomba.explosion_tiles:
            if player_rect.colliderect(rect):
                player.take_damage(1)
                bomba.causou_dano = True
                print(f"🔥 Jugador golpeado! Vida: {player.life}")
                break
    
    def send_player_state(self):
        """Envía el estado del jugador local a la red"""
        if self.network.is_connected():
            player_data = {
                'x': self.local_player.x,
                'y': self.local_player.y,
                'direction': self.local_player.direccion_actual,
                'frame': self.local_player.frame_actual,
                'life': self.local_player.life,
                'moving': self.local_player.esta_moviendose,
                'timestamp': time.time()
            }
            self.network.send_player_state(player_data)
    
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
                        bomba = Bomba(data['x'], data['y'], self.player_size)
                        bomba.tiempo_creacion = data.get('time', time.time())
                        self.remote_bombs.append(bomba)
                        print(f"💣 Bomba remota recibida en ({data['x']}, {data['y']})")
            
            elif msg_type == MessageType.OBJECT_DESTROYED.value:
                # Sincronizar objeto destruido
                x, y = data['x'], data['y']
                self.sync_object_destruction(x, y)
            
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
                print(f"💥 [SYNC] Objeto destruido remotamente en ({x}, {y})")
                break
    
    def draw_waiting_screen(self):
        """Dibuja pantalla de espera de conexión"""
        self.JANELA.fill((0, 0, 30))
        
        font_large = pygame.font.Font(None, 60)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        
        if self.is_host:
            title = font_large.render("Esperando jugador...", True, (255, 255, 255))
            local_ip = self.get_local_ip()
            ip_text = font_medium.render(f"Tu IP: {local_ip} - Puerto: 5555", True, (200, 200, 255))
            ip_rect = ip_text.get_rect(center=(self.LARGURA//2, self.ALTURA//2))
            self.JANELA.blit(ip_text, ip_rect)
        else:
            title = font_large.render("Conectando al host...", True, (255, 255, 255))
            host_text = font_medium.render(f"Host: {self.host_ip} - Puerto: 5555", True, (200, 200, 255))
            host_rect = host_text.get_rect(center=(self.LARGURA//2, self.ALTURA//2))
            self.JANELA.blit(host_text, host_rect)
        
        title_rect = title.get_rect(center=(self.LARGURA//2, self.ALTURA//2 - 100))
        self.JANELA.blit(title, title_rect)
        
        # Estado de conexión
        if self.network.connection_established:
            status_text = "🟢 Conectado - Iniciando juego..."
            color = (0, 255, 0)
        elif self.network.connected:
            status_text = "🟡 Conectando..."
            color = (255, 255, 0)
        else:
            status_text = "🔴 No conectado"
            color = (255, 0, 0)
        
        status = font_medium.render(status_text, True, color)
        status_rect = status.get_rect(center=(self.LARGURA//2, self.ALTURA//2 + 50))
        self.JANELA.blit(status, status_rect)
        
        # Tiempo de espera
        wait_time = int(time.time() - self.connection_start_time)
        time_text = font_small.render(f"Tiempo de espera: {wait_time}s", True, (200, 200, 200))
        time_rect = time_text.get_rect(center=(self.LARGURA//2, self.ALTURA//2 + 100))
        self.JANELA.blit(time_text, time_rect)
        
        # Instrucciones
        instructions = font_small.render("Presiona ESC para cancelar | F3 para debug", True, (150, 150, 200))
        instr_rect = instructions.get_rect(center=(self.LARGURA//2, self.ALTURA - 50))
        self.JANELA.blit(instructions, instr_rect)
        
        pygame.display.update()
    
    def render(self):
        """Renderiza todos los elementos del juego"""
        # 1. Dibujar mapa
        self.mapa.dibujar(self.JANELA)
        
        # 2. Dibujar objetos no destruidos
        for obj in Object.objects:
            if not obj.destruido:
                obj.draw(self.JANELA)
        
        # 3. Dibujar bombas remotas
        for bomba in self.remote_bombs:
            bomba.dibujar(self.JANELA)
        
        # 4. Dibujar bombas locales
        for bomba in self.local_bombs:
            bomba.dibujar(self.JANELA)
        
        # 5. Dibujar jugador remoto
        self.remote_player.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 6. Dibujar jugador local (encima)
        self.local_player.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 7. Dibujar HUD
        self.draw_hud()
        
        # 8. Dibujar estado de conexión
        self.draw_connection_status()
        
        pygame.display.update()
    
    def draw_hud(self):
        """Dibuja la interfaz de usuario"""
        font = pygame.font.Font(None, 36)
        
        # Vida del jugador local
        local_life = font.render(f"Tus Vidas: {self.local_player.life}", True, (255, 255, 255))
        self.JANELA.blit(local_life, (20, self.ALTURA - 60))
        
        # Vida del jugador remoto
        remote_life = font.render(f"Enemigo: {self.remote_player.life}", True, (255, 255, 255))
        remote_rect = remote_life.get_rect(right=self.LARGURA - 20, bottom=self.ALTURA - 60)
        self.JANELA.blit(remote_life, remote_rect)
        
        # Indicador de jugador
        player_text = font.render(f"Jugador {'1 (Host)' if self.is_host else '2 (Cliente)'}", True, (255, 255, 0))
        self.JANELA.blit(player_text, (20, 20))
    
    def draw_connection_status(self):
        """Dibuja el estado de la conexión"""
        font = pygame.font.Font(None, 28)
        
        if self.network.is_connected():
            status = font.render("🟢 Conectado", True, (0, 255, 0))
            time_since = time.time() - self.network.last_heartbeat_received
            ping = font.render(f"Ping: ~{int(time_since * 500)}ms", True, (200, 200, 200))
            ping_rect = ping.get_rect(right=self.LARGURA - 20, top=50)
            self.JANELA.blit(ping, ping_rect)
        else:
            status = font.render("🔴 Desconectado", True, (255, 0, 0))
        
        status_rect = status.get_rect(right=self.LARGURA - 20, top=20)
        self.JANELA.blit(status, status_rect)
    
    def run(self):
        """Bucle principal del juego"""
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
                    pygame.time.delay(500)
                    continue
                
                # Verificar timeout (30 segundos máximo)
                if time.time() - self.connection_start_time > 30:
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
            self.clock.tick(60)
        
        # Pantalla de fin de juego
        if self.network_initialized:
            self.network.disconnect()
        
        self.show_game_over()
    
    def show_game_over(self):
        """Muestra pantalla de fin de juego"""
        font_large = pygame.font.Font(None, 100)
        font_small = pygame.font.Font(None, 36)
        
        # Determinar resultado
        if self.waiting_for_connection:
            result_text = "CONEXIÓN FALLIDA"
            color = (255, 100, 0)
        elif not self.local_player.is_alive():
            result_text = "¡PERDISTE!"
            color = (255, 0, 0)
        else:
            result_text = "¡GANASTE!"
            color = (0, 255, 0)
        
        text = font_large.render(result_text, True, color)
        instruction = font_small.render("Presiona cualquier tecla para salir", True, (255, 255, 255))
        
        text_rect = text.get_rect(center=(self.LARGURA//2, self.ALTURA//2 - 50))
        instr_rect = instruction.get_rect(center=(self.LARGURA//2, self.ALTURA//2 + 50))
        
        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(text, text_rect)
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