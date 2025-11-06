import pygame
from object import Object

class Map:
    def __init__(self, ancho, alto, tile_size, cor_clara, cor_escura):
        self.ancho = ancho
        self.alto = alto
        self.tile_size = 60
        self.cor_clara = cor_clara
        self.cor_escura = cor_escura
    
    def dibujar(self, superficie):
        """Dibuja el mapa estilo ajedrez"""
        for linha in range(0, self.alto, self.tile_size):
            for coluna in range(0, self.ancho, self.tile_size):
                if (linha // self.tile_size + coluna // self.tile_size) % 2 == 0:
                    cor = self.cor_clara
                else:
                    cor = self.cor_escura
                pygame.draw.rect(superficie, cor, (coluna, linha, self.tile_size, self.tile_size))
    
    def crear_obstaculos(self):
        """Crea los obstáculos del juego"""
        # Limpar objetos anteriores (se houver)
        Object.objects.clear()
        
        # Obstáculos indestrutíveis (bordas)
        Object(0, 0, 1280, 60, destrutivel=False)
        Object(0, 660, 1280, 60, destrutivel=False)
        Object(0, 0, 60, 720, destrutivel=False)
        Object(1200, 0, 60, 720, destrutivel=False)
        
        
        # Obstáculos indestrutíveis internos
        Object(120, 120, 60, 60, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        
        # Obstáculos destrutíveis
        Object(480, 180, 60, 60, "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
        Object(540, 180, 60, 60, "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
        Object(600, 180, 60, 60, "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)