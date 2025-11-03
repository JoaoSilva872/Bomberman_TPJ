import pygame
import time

class Bomba:
    def __init__(self, x, y, tamaño_jogador, duracion=3, tile_size=20):
        self.x = x
        self.y = y
        self.tamaño_jogador = tamaño_jogador  # Ex: 3 tiles
        self.tile_size = tile_size
        self.duracion = duracion
        self.tiempo_creacion = time.time()
        self.explotada = False
        self.color = (0, 0, 0)
        self.explosion_tiles = []
        self.explosion_dur = 0.5  # segundos que a explosão fica visível
        self.tiempo_explosion = None

    def dibujar(self, superficie):
        """Desenha a bomba ou a área da explosão"""
        if not self.explotada:
            centro_x = self.x + self.tamaño_jogador // 2
            centro_y = self.y + self.tamaño_jogador // 2
            radio = self.tamaño_jogador // 2 - 2
            pygame.draw.circle(superficie, self.color, (centro_x, centro_y), radio)
            pygame.draw.rect(superficie, (255, 0, 0),
                            (centro_x - 3, centro_y - self.tamaño_jogador // 2, 6, 8))
        else:
            for rect in self.explosion_tiles:
                pygame.draw.rect(superficie, (255, 0, 0), rect)

    def debe_explotar(self):
        """Verifica se deve explodir"""
        return time.time() - self.tiempo_creacion >= self.duracion and not self.explotada

    def explotar(self):
        """Cria a área da explosão"""
        self.explotada = True
        self.tiempo_explosion = time.time()

        p = self.tamaño_jogador  # tamanho total do jogador (ex: 3 tiles)
        self.explosion_tiles = [
            pygame.Rect(self.x, self.y, p, p),               # centro
            pygame.Rect(self.x + p, self.y, p, p),           # direita
            pygame.Rect(self.x - p, self.y, p, p),           # esquerda
            pygame.Rect(self.x, self.y - p, p, p),           # cima
            pygame.Rect(self.x, self.y + p, p, p),           # baixo
        ]
        print("💥 Boom! Bomba explodiu!")

    def explosion_activa(self):
        """Retorna True enquanto a explosão estiver visível"""
        if not self.explotada:
            return False
        return time.time() - self.tiempo_explosion < self.explosion_dur