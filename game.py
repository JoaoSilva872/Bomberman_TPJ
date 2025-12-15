import pygame
import sys
import time
from map import Map
from player import Player
from object import Object
from bomba import Bomba
from powerup import PowerUpSystem, PowerUpType

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
        
        # Controladores de tempo
        self.move_delay = 100
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        
        # Control de teclas
        self.bomba_presionada = False
        self.tecla_r_presionada = False  # Para control remoto

    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula de 3x3"""
        grid_size = self.player_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y

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

                # Testing Life system ========================================================
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
                    
                # Debug: mostrar info de power-ups
                if event.key == pygame.K_p:
                    print("=== POWER-UPS INFO ===")
                    print(f"Max bombas: {self.jugador.max_bombas}")
                    print(f"Rango explosión: {self.jugador.rango_explosion}")
                    print(f"Velocidad boost: {self.jugador.velocidad_boost:.1f}")
                    print(f"Escudo activo: {self.jugador.tiene_escudo}")
                    print(f"Control remoto: {self.jugador.tiene_control_remoto}")
                    print(f"Bombas colocadas: {self.jugador.bombas_colocadas_actual}/{self.jugador.max_bombas}")
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
                if event.key == pygame.K_r:
                    self.tecla_r_presionada = False
        
        return True
    
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
        
        # Velocidad
        velocidad_text = font_small.render(f"Vel: x{self.jugador.velocidad_boost:.1f}", 
                                         True, (100, 255, 100))
        self.JANELA.blit(velocidad_text, (10, 60))
        
        # Escudo
        if self.jugador.tiene_escudo:
            escudo_text = font_small.render("ESCUDO", True, (100, 180, 255))
            self.JANELA.blit(escudo_text, (10, 85))
        
        # Control remoto
        if self.jugador.tiene_control_remoto:
            control_text = font_small.render("CTRL REMOTO (R)", True, (180, 50, 230))
            self.JANELA.blit(control_text, (10, 110))

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
        
        # 5. Dibujar jugador (por cima de tudo)
        self.jugador.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 6. Desenhar vidas (UI)
        self.draw_lives()
        
        # 7. Dibujar indicador de bomba activa
        if self.jugador.bomba_colocada:
            font = pygame.font.Font(None, 24)
            text = font.render("¡Bomba activa! (Espera a que explote)", True, (255, 255, 0))
            text_rect = text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 60))
            self.JANELA.blit(text, text_rect)
        
        # Actualizar pantalla
        pygame.display.update()

        
    def game_over(self):
        """Mostra a tela de Game Over e retorna ao menu"""
        fonte_grande = pygame.font.Font(None, 100)
        fonte_pequena = pygame.font.Font(None, 36)
        
        texto_game_over = fonte_grande.render("GAME OVER", True, (255, 0, 0))
        texto_instrucao = fonte_pequena.render("Pressione qualquer tecla para voltar ao menu", True, (255, 255, 255))
        
        texto_game_over_rect = texto_game_over.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 - 50))
        texto_instrucao_rect = texto_instrucao.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 + 50))

        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(texto_game_over, texto_game_over_rect)
        self.JANELA.blit(texto_instrucao, texto_instrucao_rect)
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
                self.game_over()
                return
        
        pygame.quit()
        sys.exit()