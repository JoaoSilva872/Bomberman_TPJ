import pygame

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