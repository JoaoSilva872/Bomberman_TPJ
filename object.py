import pygame
import os

class Object:
    objects = []

    def __init__(self, x, y, largura, altura=None, imagem_path=None, destrutivel=False):
        if altura is None:
            altura = largura
        self.rect = pygame.Rect(x, y, largura, altura)
        self.destrutivel = destrutivel
        self.destruido = False
        self.imagem = None
        self.imagem_original = None
        
        # Carrega a imagem se for fornecida
        if imagem_path and os.path.exists(imagem_path):
            self.carregar_imagem(imagem_path, largura, altura)
        else:
            # Fallback para cor sólida se a imagem não existir
            self.cor = (0, 120, 0) if not destrutivel else (120, 60, 0)
            print(f"Aviso: Imagem {imagem_path} não encontrada. Usando cor sólida.")
        
        Object.objects.append(self)

    def carregar_imagem(self, imagem_path, largura, altura):
        """Carrega e redimensiona a imagem para o tamanho do objeto"""
        try:
            self.imagem_original = pygame.image.load(imagem_path).convert_alpha()
            self.imagem = pygame.transform.scale(self.imagem_original, (largura, altura))
            self.cor = None  # Indica que estamos usando imagem
        except pygame.error as e:
            print(f"Erro ao carregar imagem {imagem_path}: {e}")
            self.cor = (0, 120, 0) if not self.destrutivel else (120, 60, 0)

    def draw(self, surface):
        """Desenha o objeto apenas se não foi destruído"""
        if not self.destruido:
            if self.imagem:
                surface.blit(self.imagem, self.rect)
            else:
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