import pygame
import sys

class Menu:
    def __init__(self, largura=1280, altura=720):
        self.LARGURA = largura
        self.ALTURA = altura
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Protótipo Bomber - Menu")
        
        # Cores
        self.COR_FUNDO = (30, 30, 60)
        self.COR_TITULO = (255, 255, 0)
        self.COR_TEXTO = (255, 255, 255)
        self.COR_BOTAO = (0, 120, 0)
        self.COR_BOTAO_HOVER = (0, 180, 0)
        
        # Fontes
        self.fonte_titulo = pygame.font.Font(None, 100)
        self.fonte_texto = pygame.font.Font(None, 36)
        
        # Botão
        self.botao_iniciar = pygame.Rect(self.LARGURA // 2 - 100, self.ALTURA // 2 + 50, 200, 50)
        self.botao_sair = pygame.Rect(self.LARGURA // 2 - 100, self.ALTURA // 2 + 120, 200, 50)
        
    def desenhar(self):
        """Desenha o menu na tela"""
        # Fundo
        self.JANELA.fill(self.COR_FUNDO)
        
        # Título
        titulo = self.fonte_titulo.render("Bomberman Game", True, self.COR_TITULO)
        titulo_rect = titulo.get_rect(center=(self.LARGURA // 2, self.ALTURA // 3))
        self.JANELA.blit(titulo, titulo_rect)
        
        # Botão Iniciar
        mouse_pos = pygame.mouse.get_pos()
        cor_botao_iniciar = self.COR_BOTAO_HOVER if self.botao_iniciar.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_iniciar, self.botao_iniciar, border_radius=10)
        texto_iniciar = self.fonte_texto.render("INICIAR JOGO", True, self.COR_TEXTO)
        texto_iniciar_rect = texto_iniciar.get_rect(center=self.botao_iniciar.center)
        self.JANELA.blit(texto_iniciar, texto_iniciar_rect)
        
        # Botão Sair
        cor_botao_sair = self.COR_BOTAO_HOVER if self.botao_sair.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_sair, self.botao_sair, border_radius=10)
        texto_sair = self.fonte_texto.render("SAIR", True, self.COR_TEXTO)
        texto_sair_rect = texto_sair.get_rect(center=self.botao_sair.center)
        self.JANELA.blit(texto_sair, texto_sair_rect)
        
        pygame.display.update()
    
    def executar(self):
        """Executa o loop principal do menu"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Verifica clique no botão Iniciar
                    if self.botao_iniciar.collidepoint(mouse_pos):
                        return True  # Inicia o jogo
                    
                    # Verifica clique no botão Sair
                    if self.botao_sair.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                
                # Também permite iniciar com Enter
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return True
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            self.desenhar()
            pygame.time.Clock().tick(60)
        
        return False