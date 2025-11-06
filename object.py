import pygame

class Object:
    objects = []

    def __init__(self, x, y, largura, altura=None, cor=(0, 120, 0), destrutivel=False):
        if altura is None:
            altura = largura
        self.rect = pygame.Rect(x, y, largura, altura)
        self.cor = cor
        self.destrutivel = destrutivel  # Se pode ser destruído por bombas
        self.destruido = False  # Estado atual do objeto
        Object.objects.append(self)

    def draw(self, surface):
        """Desenha o objeto apenas se não foi destruído"""
        if not self.destruido:
            pygame.draw.rect(surface, self.cor, self.rect)

    def colidir(self, outro_rect):
        """Verifica colisão apenas se o objeto não foi destruído"""
        if self.destruido:
            return False
        return self.rect.colliderect(outro_rect)

    @classmethod
    def verificar_colisao_com_player(cls, player_rect):
        """Verifica colisão do player com qualquer objeto não destruído"""
        for obj in cls.objects:
            if obj.colidir(player_rect):
                return obj
        return None

    def verificar_explosao(self, bombas):
        """Verifica se este objeto foi atingido por alguma explosão"""
        if not self.destrutivel or self.destruido:
            return False
            
        for bomba in bombas:
            if bomba.explotada and bomba.explosion_activa():
                for explosion_rect in bomba.explosion_tiles:
                    if self.rect.colliderect(explosion_rect):
                        self.destruido = True
                        print(f"💥 Objeto destrutível em ({self.rect.x}, {self.rect.y}) foi destruído!")
                        return True
        return False

    @classmethod
    def atualizar_objetos_destrutiveis(cls, bombas):
        """Atualiza todos os objetos destrutíveis do jogo"""
        for obj in cls.objects:
            if obj.destrutivel:
                obj.verificar_explosao(bombas)