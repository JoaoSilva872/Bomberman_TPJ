import pygame
import sys
import time
from map import Map
from player import Player
from object import Object

class Game:
    def __init__(self):
        # Configurações da janela
        self.LARGURA = 1280
        self.ALTURA = 720
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Protótipo Bomber")
        
        # Configurações do tabuleiro
        self.TILE_SIZE = 20
        self.COR_CLARA = (240, 240, 240)
        self.COR_ESCURA = (30, 30, 30)
        
        # Configurações do jogador
        self.PLAYER_TILES = 3
        self.player_size = self.TILE_SIZE * self.PLAYER_TILES
        self.player_vel = self.TILE_SIZE
        
        # Colors
        self.border_cor = (80, 60, 60)
        self.object_cor = (0, 120, 0)
        self.destructible_cor = (120, 80, 40)  # Color para bloques destructibles
        
        # Inicializar componentes
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        self.jugador = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel)
        self.jugador.life_max = 3
        self.jugador.life = 3
        self.bombas = []
        
        # Sistema de puntos y tiempo
        self.score = 0
        self.game_time = 180  # 3 minutos en segundos
        self.start_time = time.time()
        
        # Crear obstáculos
        self.crear_obstaculos()
        
        # Controladores de tiempo
        self.move_delay = 100
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        
        # Control de teclas
        self.bomba_presionada = False

    def crear_obstaculos(self):
        """Crea los obstáculos del juego"""
        # Bordes del mapa
        Object(0, 0, 1280, 60, cor=self.border_cor)
        Object(0, 660, 1280, 60, cor=self.border_cor)
        Object(0, 0, 60, 720, cor=self.border_cor)
        Object(1220, 0, 60, 720, cor=self.border_cor)
        
        # Obstáculos fijos (no destructibles)
        Object(120, 120, self.player_size, cor=self.object_cor)
        Object(480, 120, self.player_size, cor=self.object_cor)
        Object(840, 120, self.player_size, cor=self.object_cor)
        Object(1080, 120, self.player_size, cor=self.object_cor)
        
        Object(240, 240, self.player_size, cor=self.object_cor)
        Object(600, 240, self.player_size, cor=self.object_cor)
        Object(960, 240, self.player_size, cor=self.object_cor)
        
        Object(120, 360, self.player_size, cor=self.object_cor)
        Object(480, 360, self.player_size, cor=self.object_cor)
        Object(840, 360, self.player_size, cor=self.object_cor)
        Object(1080, 360, self.player_size, cor=self.object_cor)
        
        Object(240, 480, self.player_size, cor=self.object_cor)
        Object(600, 480, self.player_size, cor=self.object_cor)
        Object(960, 480, self.player_size, cor=self.object_cor)
        
        Object(120, 600, self.player_size, cor=self.object_cor)
        Object(480, 600, self.player_size, cor=self.object_cor)
        Object(840, 600, self.player_size, cor=self.object_cor)
        Object(1080, 600, self.player_size, cor=self.object_cor)
        
        # Obstáculos destructibles
        self.destructible_objects = []
        self.crear_obstaculos_destructibles()

    def crear_obstaculos_destructibles(self):
        """Crea obstáculos que pueden ser destruidos por bombas"""
        # Patrón de obstáculos destructibles
        positions = [
            (240, 120), (360, 120), (720, 120), 
            (120, 240), (360, 240), (720, 240), (1080, 240),
            (240, 360), (720, 360), (960, 360),
            (120, 480), (360, 480), (480, 480), (840, 480), (1080, 480),
            (240, 600), (600, 600), (720, 600), (960, 600)
        ]
        
        for pos in positions:
            x, y = pos
            obj = Object(x, y, self.player_size, cor=self.destructible_cor)
            obj.destructible = True  # Marcar como destructible
            self.destructible_objects.append(obj)

    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula de 3x3"""
        grid_size = self.player_size  # 60 píxeles (3 tiles × 20 píxeles)
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
                    # Verifica se já existe uma bomba ativa (não explodida)
                    bomba_activa = any(not b.explotada for b in self.bombas)
                    
                    if not bomba_activa:
                        from bomba import Bomba
                        # Ajustar posición a la cuadrícula de 3x3
                        grid_x, grid_y = self.ajustar_a_grid(self.jugador.x, self.jugador.y)
                        nueva_bomba = Bomba(grid_x, grid_y, self.player_size)
                        self.bombas.append(nueva_bomba)
                        self.bomba_presionada = True
                        print(f"Bomba colocada em ({grid_x}, {grid_y})")
                    else:
                        print("Já há uma bomba ativa — espere ela explodir!")
                        
                #Testing Life system ========================================================
                # Tecla K → jogador leva 1 de dano
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                # Tecla H → jogador recupera toda a vida
                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
        
        return True
    
    def draw_ui(self):
        """Dibuja la interfaz de usuario en los bordes del mapa"""
        font = pygame.font.Font(None, 36)
        
        # Fondo semitransparente para los textos
        s = pygame.Surface((self.LARGURA, 40), pygame.SRCALPHA)
        s.fill((0, 0, 0, 128))  # Negro semitransparente
        self.JANELA.blit(s, (0, 0))
        
        # Vidas en el borde superior izquierdo
        lives_text = font.render(f"Vidas: {self.jugador.life}", True, (255, 255, 255))
        self.JANELA.blit(lives_text, (20, 10))
        
        # Puntos en el borde superior derecho
        score_text = font.render(f"Puntos: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect()
        score_rect.right = self.LARGURA - 20
        score_rect.top = 10
        self.JANELA.blit(score_text, score_rect)
        
        # Tiempo en el centro del borde superior
        time_left = max(0, self.game_time - (time.time() - self.start_time))
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        time_text = font.render(f"Tiempo: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        time_rect = time_text.get_rect()
        time_rect.centerx = self.LARGURA // 2
        time_rect.top = 10
        self.JANELA.blit(time_text, time_rect)

    def update(self, tiempo_actual):
        """Actualiza el estado del juego"""
        # Actualizar movimiento del jugador
        self.last_move_time += self.clock.get_time()
        if self.last_move_time >= self.move_delay:
            self.jugador.actualizar_movimiento(self.LARGURA, self.ALTURA)
            self.last_move_time = 0
        
        # Actualizar animación del jugador
        keys = pygame.key.get_pressed()
        self.jugador.actualizar_animacion(tiempo_actual, keys)
        
        # Actualizar bombas
        self.actualizar_bombas()
        
        # Verificar si se acabó el tiempo
        if time.time() - self.start_time >= self.game_time:
            self.game_over("¡Tiempo agotado!")
        
        # ⚠️ Se o jogador morrer → chama Game Over
        if not self.jugador.is_alive():
            self.game_over("¡Game Over!")

    def actualizar_bombas(self):
        """Actualiza el estado de las bombas"""
        bombas_a_remover = []

        for bomba in self.bombas:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
                bomba.causou_dano = False
                
                # Verificar destrucción de obstáculos
                self.verificar_destruccion_obstaculos(bomba)

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

        for bomba in bombas_a_remover:
            self.bombas.remove(bomba)

    def verificar_destruccion_obstaculos(self, bomba):
        """Verifica si la explosión destruye obstáculos"""
        for obj in self.destructible_objects[:]:  # Usamos copia para poder remover
            for rect in bomba.explosion_tiles:
                if obj.rect.colliderect(rect):
                    # Destruir obstáculo y dar puntos
                    Object.objects.remove(obj)
                    self.destructible_objects.remove(obj)
                    self.score += 50  # 50 puntos por cada obstáculo destruido
                    print(f"💥 Obstáculo destruido! +50 puntos. Total: {self.score}")
                    break

    def render(self):
        """Renderiza todos los elementos del juego"""
        # Dibujar mapa
        self.mapa.dibujar(self.JANELA)
        
        # Dibujar obstáculos
        for obj in Object.objects:
            obj.draw(self.JANELA)
        
        # Dibujar bombas
        for bomba in self.bombas:
            bomba.dibujar(self.JANELA)
        
        # Dibujar jugador
        self.jugador.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # Dibujar UI en los bordes
        self.draw_ui()
        
        # Actualizar pantalla
        pygame.display.update()
        
    def game_over(self, mensaje):
        """Muestra la pantalla de fin de juego"""
        fonte = pygame.font.Font(None, 72)
        texto = fonte.render(mensaje, True, (255, 0, 0))
        texto_rect = texto.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 - 50))
        
        score_font = pygame.font.Font(None, 48)
        score_text = score_font.render(f"Puntuación final: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 + 50))

        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(texto, texto_rect)
        self.JANELA.blit(score_text, score_rect)
        pygame.display.update()

        print(f"💀 {mensaje} - Puntuación: {self.score}")

        # Espera 3 segundos antes de fechar
        pygame.time.wait(3000)
        pygame.quit()
        sys.exit()

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
            running = self.handle_events()
            self.update(tiempo_actual)
            self.render()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()