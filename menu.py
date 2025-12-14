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
        self.COR_BOTAO_MULTI = (0, 100, 200)
        self.COR_BOTAO_MULTI_HOVER = (0, 150, 255)
        
        # Fontes
        self.fonte_titulo = pygame.font.Font(None, 100)
        self.fonte_texto = pygame.font.Font(None, 36)
        
        # Botões
        self.botao_single = pygame.Rect(self.LARGURA // 2 - 100, self.ALTURA // 2, 200, 50)
        self.botao_multi = pygame.Rect(self.LARGURA // 2 - 100, self.ALTURA // 2 + 70, 200, 50)
        self.botao_sair = pygame.Rect(self.LARGURA // 2 - 100, self.ALTURA // 2 + 140, 200, 50)
        
    def desenhar(self):
        """Desenha o menu na tela"""
        # Fundo
        self.JANELA.fill(self.COR_FUNDO)
        
        # Título
        titulo = self.fonte_titulo.render("Bomberman Game", True, self.COR_TITULO)
        titulo_rect = titulo.get_rect(center=(self.LARGURA // 2, self.ALTURA // 3))
        self.JANELA.blit(titulo, titulo_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Botão Singleplayer
        cor_botao_single = self.COR_BOTAO_HOVER if self.botao_single.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_single, self.botao_single, border_radius=10)
        texto_single = self.fonte_texto.render("UN JUGADOR", True, self.COR_TEXTO)
        texto_single_rect = texto_single.get_rect(center=self.botao_single.center)
        self.JANELA.blit(texto_single, texto_single_rect)
        
        # Botão Multijugador
        cor_botao_multi = self.COR_BOTAO_MULTI_HOVER if self.botao_multi.collidepoint(mouse_pos) else self.COR_BOTAO_MULTI
        pygame.draw.rect(self.JANELA, cor_botao_multi, self.botao_multi, border_radius=10)
        texto_multi = self.fonte_texto.render("MULTIJUGADOR", True, self.COR_TEXTO)
        texto_multi_rect = texto_multi.get_rect(center=self.botao_multi.center)
        self.JANELA.blit(texto_multi, texto_multi_rect)
        
        # Botão Sair
        cor_botao_sair = self.COR_BOTAO_HOVER if self.botao_sair.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_sair, self.botao_sair, border_radius=10)
        texto_sair = self.fonte_texto.render("SALIR", True, self.COR_TEXTO)
        texto_sair_rect = texto_sair.get_rect(center=self.botao_sair.center)
        self.JANELA.blit(texto_sair, texto_sair_rect)
        
        # Instrucciones
        instrucciones = [
            "ENTER: Un jugador",
            "M: Multijugador",
            "ESC: Salir"
        ]
        
        fonte_pequena = pygame.font.Font(None, 24)
        for i, instruccion in enumerate(instrucciones):
            texto = fonte_pequena.render(instruccion, True, (200, 200, 200))
            texto_rect = texto.get_rect(center=(self.LARGURA // 2, self.ALTURA - 50 + i * 25))
            self.JANELA.blit(texto, texto_rect)
        
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
                    
                    # Verifica clique no botão Singleplayer
                    if self.botao_single.collidepoint(mouse_pos):
                        return "single"  # Retorna tipo de juego
                    
                    # Verifica clique no botão Multijugador
                    if self.botao_multi.collidepoint(mouse_pos):
                        return "multi"  # Retorna tipo de juego
                    
                    # Verifica clique no botão Sair
                    if self.botao_sair.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                
                # También permite iniciar con teclas
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return "single"
                    if event.key == pygame.K_m:
                        return "multi"
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            self.desenhar()
            pygame.time.Clock().tick(60)
        
        return None