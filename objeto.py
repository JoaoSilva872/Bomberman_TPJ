import pygame

class Objeto:
    objetos = []  # lista de todas as instâncias

    def __init__(self, x, y, largura, altura=None, cor=(0, 255, 0)):
        if altura is None:
            altura = largura  # se não passar altura, será quadrado
        self.rect = pygame.Rect(x, y, largura, altura)
        self.cor = cor
        Objeto.objetos.append(self)

    def draw(self, surface):
        pygame.draw.rect(surface, self.cor, self.rect)

    def colidir(self, outro_rect):
        return self.rect.colliderect(outro_rect)

    @classmethod
    def verificar_colisao_com_player(cls, player_rect):
        for obj in cls.objetos:
            if obj.colidir(player_rect):
                return obj
        return None