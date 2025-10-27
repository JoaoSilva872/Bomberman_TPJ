import pygame

class Object:
    objects = []  # Cambiado de 'objetos' a 'objects'

    def __init__(self, x, y, largura, altura=None, cor=(0, 255, 0)):
        if altura is None:
            altura = largura
        self.rect = pygame.Rect(x, y, largura, altura)
        self.cor = cor
        Object.objects.append(self)  # Cambiado a Object.objects

    def draw(self, surface):
        pygame.draw.rect(surface, self.cor, self.rect)

    def colidir(self, outro_rect):
        return self.rect.colliderect(outro_rect)

    @classmethod
    def verificar_colisao_com_player(cls, player_rect):
        for obj in cls.objects:  # Cambiado a cls.objects
            if obj.colidir(player_rect):
                return obj
        return None