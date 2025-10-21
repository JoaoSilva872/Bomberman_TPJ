import pygame

class Objeto:
    def __init__(self, x, y, tamanho, cor=(0, 255, 0)):
        """
        x, y: coordenadas do objeto
        tamanho: largura e altura
        cor: cor do objeto
        """
        self.rect = pygame.Rect(x, y, tamanho, tamanho)
        self.cor = cor

    def draw(self, surface):
        """Desenha o objeto na tela"""
        pygame.draw.rect(surface, self.cor, self.rect)

    def colidir(self, outro_rect):
        """Retorna True se colidir com outro rect"""
        return self.rect.colliderect(outro_rect)
