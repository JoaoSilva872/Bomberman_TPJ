import pygame
import sys
import time
import random
from map import Map
from player import Player
from object import Object
from bomba import Bomba
from powerup import PowerUpSystem, PowerUpType
from enemy import Enemy  # NUEVO
from exit_point import ExitPoint  # NUEVO

class Game:
    def __init__(self):
        # Configurações da janela
        self.LARGURA = 1260
        self.ALTURA = 720
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Protótipo Bomber - Maze 21x11")
        
        # Configurações do tabuleiro
        self.TILE_SIZE = 20
        self.COR_CLARA = (0, 140, 0)
        self.COR_ESCURA = (0, 120, 0)
        
        # Configurações do jogador
        self.PLAYER_TILES = 3
        self.player_size = self.TILE_SIZE * self.PLAYER_TILES
        self.player_vel = self.TILE_SIZE
        
        # Inicializar componentes
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        self.jugador = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel, id=0)
        self.jugador.life_max = 3
        self.jugador.life = 3
        self.bombas = []
        
        # Sistema de power-ups
        self.powerup_system = PowerUpSystem(probabilidad_spawn=0.35)
        
        # Crear obstáculos através do mapa (maze_21x11)
        self.mapa.crear_obstaculos("level2")
        
        # NUEVO: Enemigos
        self.enemigos = []
        self.num_enemigos_inicial = 5  # Número inicial de enemigos
        self.enemigos_eliminados = 0
        self.tiempo_ultimo_spawn = time.time()
        self.intervalo_spawn = 30.0  # Spawn cada 30 segundos
        self.max_enemigos = 10  # Máximo de enemigos en pantalla

        # AHORA SÍ crear enemigos
        self.crear_enemigos()
        
        # NUEVO: Punto de salida
        self.exit_point = None
        self.crear_punto_salida()
        self.nivel_completado = False
        
        # Controladores de tempo
        self.move_delay = 100
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        
        # Control de teclas
        self.bomba_presionada = False
        self.tecla_r_presionada = False  # Para control remoto
        
        # NUEVO: Variables para spawn de enemigos
        self.tiempo_ultimo_spawn = time.time()
        self.intervalo_spawn = 30.0  # Spawn cada 30 segundos
        self.max_enemigos = 10  # Máximo de enemigos en pantalla
    
    def crear_enemigos(self):
        """Crea enemigos en posiciones aleatorias"""
        for _ in range(self.num_enemigos_inicial):
            self.spawn_enemigo_aleatorio()
    
    def spawn_enemigo_aleatorio(self):
        """Crea un enemigo en una posición aleatoria válida"""
        if len(self.enemigos) >= self.max_enemigos:
            return
        
        intentos = 0
        while intentos < 100:
            # Generar posición aleatoria en la cuadrícula
            grid_x = random.randint(0, (self.LARGURA // self.player_size) - 1) * self.player_size
            grid_y = random.randint(0, (self.ALTURA // self.player_size) - 1) * self.player_size
            
            # Verificar que no esté en la posición del jugador
            if abs(grid_x - self.jugador.x) < self.player_size * 2 and abs(grid_y - self.jugador.y) < self.player_size * 2:
                intentos += 1
                continue
            
            # Verificar que no colisione con objetos no destruidos
            enemigo_rect = pygame.Rect(grid_x, grid_y, self.player_size, self.player_size)
            colision = False
            
            for obj in Object.objects:
                if not obj.destruido and enemigo_rect.colliderect(obj.rect):
                    colision = True
                    break
            
            if not colision:
                # Crear enemigo con vida aleatoria (1-3)
                vida = random.randint(1, 3)
                velocidad = random.uniform(1.0, 2.5)
                enemigo = Enemy(grid_x, grid_y, self.player_size, velocidad, vida)
                self.enemigos.append(enemigo)
                print(f"👾 Enemigo apareció en ({grid_x}, {grid_y}) - Vida: {vida}")
                break
            
            intentos += 1
    
    def crear_punto_salida(self):
        """Crea el punto de salida en una posición aleatoria"""
        intentos = 0
        while intentos < 100:
            grid_x = random.randint(0, (self.LARGURA // self.player_size) - 1) * self.player_size
            grid_y = random.randint(0, (self.ALTURA // self.player_size) - 1) * self.player_size
            
            # Verificar que no esté cerca del jugador
            if abs(grid_x - self.jugador.x) < self.player_size * 3 and abs(grid_y - self.jugador.y) < self.player_size * 3:
                intentos += 1
                continue
            
            # Verificar que no colisione con objetos
            exit_rect = pygame.Rect(grid_x, grid_y, self.player_size, self.player_size)
            colision = False
            
            for obj in Object.objects:
                if not obj.destruido and exit_rect.colliderect(obj.rect):
                    colision = True
                    break
            
            if not colision:
                self.exit_point = ExitPoint(grid_x, grid_y, self.player_size)
                print(f"🚪 Punto de salida en ({grid_x}, {grid_y})")
                break
            
            intentos += 1
        
        # Si no se encontró posición, usar una por defecto
        if not self.exit_point:
            self.exit_point = ExitPoint(self.LARGURA - self.player_size * 3, 
                                       self.ALTURA - self.player_size * 3, 
                                       self.player_size)
    
    def handle_events(self):
        """Maneja los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.bomba_presionada:
                    # Verificar si el jugador puede colocar bomba (solo una)
                    if not self.jugador.puede_colocar_bomba():
                        print("⚠️ Ya tienes una bomba activa - espera a que explote")
                        return True
                    
                    # Verificar si ya existe una bomba activa en esa posición
                    grid_x, grid_y = self.ajustar_a_grid(self.jugador.x, self.jugador.y)
                    bomba_en_posicion = False
                    for b in self.bombas:
                        if not b.explotada and b.x == grid_x and b.y == grid_y:
                            bomba_en_posicion = True
                            break
                    
                    if not bomba_en_posicion:
                        # Ajustar posición a la cuadrícula de 3x3
                        nueva_bomba = Bomba(grid_x, grid_y, self.player_size, 
                                          jugador_id=self.jugador.id,
                                          rango_explosion=self.jugador.rango_explosion)
                        self.bombas.append(nueva_bomba)
                        self.jugador.colocar_bomba(nueva_bomba)
                        self.bomba_presionada = True
                        print(f"💣 Bomba colocada en ({grid_x}, {grid_y}) - Rango: {self.jugador.rango_explosion}")
                    else:
                        print("Ya hay una bomba en esta posición")
                
                # Control remoto - detonar bombas
                if event.key == pygame.K_r and not self.tecla_r_presionada:
                    if self.jugador.tiene_control_remoto:
                        self.detonar_bombas_remotamente()
                        self.tecla_r_presionada = True

                # Testing Life system
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
                    
                # Debug: mostrar info
                if event.key == pygame.K_p:
                    print("=== INFO DEL JUEGO ===")
                    print(f"Enemigos vivos: {len([e for e in self.enemigos if e.activo])}")
                    print(f"Enemigos eliminados: {self.enemigos_eliminados}")
                    print(f"Salida activada: {self.exit_point.activado if self.exit_point else False}")
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
                if event.key == pygame.K_r:
                    self.tecla_r_presionada = False
        
        return True
    
    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula"""
        grid_size = self.player_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y
    
    def detonar_bombas_remotamente(self):
        """Detona todas las bombas del jugador remotamente"""
        print("🎮 Activando control remoto...")
        bombas_detonadas = 0
        
        for bomba in self.bombas:
            if not bomba.explotada and bomba.jugador_id == self.jugador.id:
                bomba.explotar(Object.objects)
                bombas_detonadas += 1
        
        if bombas_detonadas > 0:
            print(f"💥 ¡{bombas_detonadas} bombas detonadas remotamente!")
        else:
            print("⚠️ No hay bombas para detonar")
    
    def update(self, tiempo_actual):
        """Actualiza el estado del juego"""
        # Actualizar movimiento del jugador
        self.last_move_time += self.clock.get_time()
        if self.last_move_time >= self.move_delay:
            # Pasar todas las bombas para colisión
            self.jugador.actualizar_movimiento(self.LARGURA, self.ALTURA, self.bombas)
            self.last_move_time = 0
        
        # Actualizar animación del jugador
        keys = pygame.key.get_pressed()
        self.jugador.actualizar_animacion(tiempo_actual, keys)
        
        # Actualizar estado de colisión de las bombas
        for bomba in self.bombas:
            bomba.actualizar_colision(self.jugador.x, self.jugador.y, self.jugador.id, self.player_size)
        
        # Actualizar bombas (explosiones, etc.)
        self.actualizar_bombas()
        
        # Verificar colisiones con power-ups
        jugador_rect = pygame.Rect(self.jugador.x, self.jugador.y, 
                                 self.player_size, self.player_size)
        powerups_recogidos = self.powerup_system.verificar_colisiones(jugador_rect, self.jugador)
        
        # Aplicar power-ups recogidos
        for tipo_powerup in powerups_recogidos:
            self.jugador.aplicar_powerup(tipo_powerup)
        
        # Atualizar objetos destrutíveis
        Object.atualizar_objetos_destrutiveis(self.bombas)
        
        # NUEVO: Actualizar enemigos
        self.actualizar_enemigos(tiempo_actual)
        
        # NUEVO: Verificar colisión con enemigos
        self.verificar_colision_enemigos()
        
        # NUEVO: Verificar si todos los enemigos fueron eliminados
        if self.exit_point and not self.exit_point.activado:
            enemigos_vivos = [e for e in self.enemigos if e.activo]
            if len(enemigos_vivos) == 0:
                self.exit_point.activar()
                print("🎉 ¡Todos los enemigos eliminados! La salida está activada.")
        
        # NUEVO: Verificar si el jugador llega a la salida
        if self.exit_point and self.exit_point.activado:
            if self.exit_point.colisiona_con(jugador_rect):
                print("🏁 ¡Has llegado a la salida! Nivel completado.")
                self.nivel_completado = True
        
        # NUEVO: Spawn periódico de enemigos
        tiempo_actual_seg = time.time()
        if tiempo_actual_seg - self.tiempo_ultimo_spawn > self.intervalo_spawn:
            if len(self.enemigos) < self.max_enemigos:
                self.spawn_enemigo_aleatorio()
                self.tiempo_ultimo_spawn = tiempo_actual_seg
    
    def actualizar_enemigos(self, tiempo_actual):
        """Actualiza todos los enemigos"""
        enemigos_a_remover = []
        
        for enemigo in self.enemigos:
            if enemigo.activo:
                enemigo.actualizar(Object.objects, self.bombas, self.LARGURA, self.ALTURA)
                enemigo.actualizar_animacion(tiempo_actual)
            else:
                enemigos_a_remover.append(enemigo)
        
        # Remover enemigos inactivos
        for enemigo in enemigos_a_remover:
            self.enemigos.remove(enemigo)
    
    def verificar_colision_enemigos(self):
        """Verifica colisiones entre jugador y enemigos"""
        jugador_rect = pygame.Rect(self.jugador.x, self.jugador.y, 
                                 self.player_size, self.player_size)
        
        for enemigo in self.enemigos:
            if enemigo.activo and enemigo.colisiona_con(jugador_rect):
                # El enemigo daña al jugador
                if self.jugador.take_damage(1):
                    print(f"👾 ¡Enemigo golpeó al jugador! Vida: {self.jugador.life}")
                
                # El jugador también daña al enemigo (opcional)
                # enemigo.recibir_dano(1)
                
                break
    
    def actualizar_bombas(self):
        """Actualiza el estado de las bombas"""
        bombas_a_remover = []

        for bomba in self.bombas:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
                bomba.causou_dano = False
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                self.procesar_explosion_destruccion(bomba)
            
            # NUEVO: Verificar daño a enemigos
            if bomba.explotada and bomba.explosion_activa() and not bomba.causou_dano:
                self.verificar_dano_enemigos(bomba)

            if bomba.explosion_activa():
                player_rect = pygame.Rect(self.jugador.x, self.jugador.y,
                                        self.player_size, self.player_size)

                if not getattr(bomba, "causou_dano", False):
                    for rect in bomba.explosion_tiles:
                        if player_rect.colliderect(rect):
                            self.jugador.take_damage(1)
                            bomba.causou_dano = True
                            print(f"🔥 Jogador atingido pela explosão! Vida: {self.jugador.life}")
                            break

            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover.append(bomba)
                # Notificar al jugador que su bomba fue destruida
                self.jugador.bomba_destruida()

        for bomba in bombas_a_remover:
            self.bombas.remove(bomba)
    
    def verificar_dano_enemigos(self, bomba):
        """Verifica si la explosión daña a los enemigos"""
        for enemigo in self.enemigos:
            if enemigo.activo:
                for rect in bomba.explosion_tiles:
                    if enemigo.rect.colliderect(rect):
                        if enemigo.recibir_dano(1):
                            print(f"💥 ¡Enemigo eliminado!")
                            self.enemigos_eliminados += 1
                        bomba.causou_dano = True
                        break
    
    def procesar_explosion_destruccion(self, bomba):
        """Procesa la destrucción de objetos por una explosión"""
        objetos_destruidos = []
        
        for obj in Object.objects:
            if obj.destrutivel and not obj.destruido:
                for rect in bomba.explosion_tiles:
                    if obj.rect.colliderect(rect):
                        obj.destruido = True
                        objetos_destruidos.append(obj)
                        print(f"💥 Objeto destruido en ({obj.rect.x}, {obj.rect.y})")
                        
                        # Intentar spawnear power-up
                        self.powerup_system.intentar_spawn(
                            obj.rect.x, obj.rect.y, 
                            self.player_size
                        )
                        break
        
        return objetos_destruidos
    
    def draw_lives(self):
        """Desenha a vida do jogador na tela"""
        font = pygame.font.Font(None, 36)
        text = font.render(f"Player Lives: {self.jugador.life}x", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 30))
        self.JANELA.blit(text, text_rect)
        
        # Dibujar info de power-ups
        font_small = pygame.font.Font(None, 24)
        
        # Bombas
        bombas_text = font_small.render(f"Bombas: {self.jugador.bombas_colocadas_actual}/{self.jugador.max_bombas}", 
                                        True, (255, 200, 100))
        self.JANELA.blit(bombas_text, (10, 10))
        
        # Rango
        rango_text = font_small.render(f"Rango: {self.jugador.rango_explosion}", 
                                        True, (255, 150, 50))
        self.JANELA.blit(rango_text, (10, 35))
        
        # ELIMINADO: Velocidad boost
        
        # Escudo
        if self.jugador.tiene_escudo:
            escudo_text = font_small.render("ESCUDO", True, (100, 180, 255))
            self.JANELA.blit(escudo_text, (10, 60))
        
        # Control remoto
        if self.jugador.tiene_control_remoto:
            control_text = font_small.render("CTRL REMOTO (R)", True, (180, 50, 230))
            self.JANELA.blit(control_text, (10, 85))
        
        # Info de enemigos y salida
        enemigos_vivos = len([e for e in self.enemigos if e.activo])
        enemigos_text = font_small.render(f"Enemigos: {enemigos_vivos}", True, (255, 100, 100))
        enemigos_rect = enemigos_text.get_rect(right=self.LARGURA - 10, top=10)
        self.JANELA.blit(enemigos_text, enemigos_rect)
        
        if self.exit_point:
            estado_salida = "ACTIVADA" if self.exit_point.activado else "DESACTIVADA"
            color_salida = (0, 255, 0) if self.exit_point.activado else (255, 100, 100)
            salida_text = font_small.render(f"Salida: {estado_salida}", True, color_salida)
            salida_rect = salida_text.get_rect(right=self.LARGURA - 10, top=35)
            self.JANELA.blit(salida_text, salida_rect)
        
        # Instrucciones
        if self.exit_point and not self.exit_point.activado:
            instruccion_text = font_small.render("Elimina todos los enemigos para activar la salida", 
                                                True, (255, 255, 0))
            instruccion_rect = instruccion_text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 80))
            self.JANELA.blit(instruccion_text, instruccion_rect)
        elif self.exit_point and self.exit_point.activado:
            instruccion_text = font_small.render("¡Salida activada! Llega a la puerta para completar el nivel", 
                                                True, (0, 255, 0))
            instruccion_rect = instruccion_text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 80))
            self.JANELA.blit(instruccion_text, instruccion_rect)

    def render(self):
        """Renderiza todos los elementos del juego"""
        # 1. Dibujar mapa (fundo)
        self.mapa.dibujar(self.JANELA)
        
        # 2. Dibujar obstáculos NÃO DESTRUÍDOS
        for obj in Object.objects:
            if not obj.destruido:
                obj.draw(self.JANELA)
        
        # 3. Dibujar power-ups
        self.powerup_system.dibujar_todos(self.JANELA)
        
        # 4. Dibujar bombas e EXPLOSÕES
        for bomba in self.bombas:
            bomba.dibujar(self.JANELA)
        
        # 5. NUEVO: Dibujar enemigos
        tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
        for enemigo in self.enemigos:
            enemigo.dibujar(self.JANELA, tiempo_actual)
        
        # 6. NUEVO: Dibujar punto de salida
        if self.exit_point:
            self.exit_point.dibujar(self.JANELA, tiempo_actual)
        
        # 7. Dibujar jugador (por cima de tudo)
        self.jugador.dibujar(self.JANELA, tiempo_actual)
        
        # 8. Desenhar vidas (UI)
        self.draw_lives()
        
        # 9. Dibujar indicador de bomba activa
        if self.jugador.bomba_colocada:
            font = pygame.font.Font(None, 24)
            text = font.render("¡Bomba activa! (Espera a que explote)", True, (255, 255, 0))
            text_rect = text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 60))
            self.JANELA.blit(text, text_rect)
        
        # Actualizar pantalla
        pygame.display.update()
        
    def game_over(self, victoria=False):
        """Mostra a tela de Game Over e retorna ao menu"""
        fonte_grande = pygame.font.Font(None, 100)
        fonte_pequena = pygame.font.Font(None, 36)
        
        if victoria:
            texto_game_over = fonte_grande.render("¡VICTORIA!", True, (0, 255, 0))
            texto_instrucao = fonte_pequena.render("¡Nivel completado! Presiona cualquier tecla para volver al menú", True, (255, 255, 255))
        else:
            texto_game_over = fonte_grande.render("GAME OVER", True, (255, 0, 0))
            texto_instrucao = fonte_pequena.render("Presiona cualquier tecla para volver al menú", True, (255, 255, 255))
        
        # Estadísticas
        fonte_stats = pygame.font.Font(None, 28)
        stats_texts = [
            f"Enemigos eliminados: {self.enemigos_eliminados}",
            f"Tiempo jugado: {(pygame.time.get_ticks() - self.tiempo_inicio) / 1000:.1f}s",
            f"Bombas colocadas: {len(self.bombas)}"
        ]
        
        texto_game_over_rect = texto_game_over.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 - 100))
        texto_instrucao_rect = texto_instrucao.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 + 50))

        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(texto_game_over, texto_game_over_rect)
        self.JANELA.blit(texto_instrucao, texto_instrucao_rect)
        
        # Dibujar estadísticas
        y_offset = self.ALTURA // 2 - 30
        for stat_text in stats_texts:
            stat = fonte_stats.render(stat_text, True, (180, 180, 180))
            stat_rect = stat.get_rect(center=(self.LARGURA // 2, y_offset))
            self.JANELA.blit(stat, stat_rect)
            y_offset += 30
        
        pygame.display.update()

        print("💀 GAME OVER - Voltando ao menu...")

        # Espera el jugador pressionar qualquer tecla
        esperando = True
        while esperando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    esperando = False
        
        return

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
            running = self.handle_events()
            self.update(tiempo_actual)
            self.render()
            self.clock.tick(60)
            
            # ⚠️ Se o jogador morrer → chama Game Over
            if not self.jugador.is_alive():
                self.game_over(victoria=False)
                return
            
            # ⚠️ Si el nivel está completado → chama Game Over con victoria
            if self.nivel_completado:
                self.game_over(victoria=True)
                return
        
        pygame.quit()
        sys.exit()