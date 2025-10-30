import pygame
import sys
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
        
        # Inicializar componentes
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        self.jugador = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel)
        self.jugador.life_max = 3
        self.jugador.life = 3
        self.bombas = []
        
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
        Object(0, 0, 1280, 60, cor=self.border_cor)
        Object(0, 660, 1280, 60, cor=self.border_cor)
        Object(0, 0, 60, 720, cor=self.border_cor)
        Object(1220, 0, 60, 720, cor=self.border_cor)
        Object(120, 120, self.player_size, cor=self.object_cor)
        Object(480, 120, self.player_size, cor=self.object_cor)

    def handle_events(self):
        """Maneja los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b and not self.bomba_presionada:
                    from bomba import Bomba
                    nueva_bomba = Bomba(self.jugador.x, self.jugador.y, self.player_size)
                    self.bombas.append(nueva_bomba)
                    self.bomba_presionada = True
                    print(f"Bomba colocada en ({self.jugador.x}, {self.jugador.y})")
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_b:
                    self.bomba_presionada = False
                    
            
            #Testing ========================================================
            
            if event.type == pygame.KEYDOWN:
                # Tecla K → jogador leva 1 de dano
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                # Tecla H → jogador recupera toda a vida
                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
        
        return True

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

    def actualizar_bombas(self):
        """Actualiza el estado de las bombas"""
        bombas_a_remover = []
        for bomba in self.bombas:
            if bomba.debe_explotar():
                bomba.explotar()
                bombas_a_remover.append(bomba)
        
        for bomba in bombas_a_remover:
            self.bombas.remove(bomba)

    def render(self):
        """Renderiza todos los elementos del juego"""
        # Dibujar mapa
        self.mapa.dibujar(self.JANELA)
        
        # Dibujar obstáculos
        for obj in Object.objects:  # Cambiado de Object.objetos a Object.objects
            obj.draw(self.JANELA)
        
        # Dibujar bombas
        for bomba in self.bombas:
            bomba.dibujar(self.JANELA)
        
        # Dibujar jugador
        self.jugador.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # Actualizar pantalla
        pygame.display.update()
        

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