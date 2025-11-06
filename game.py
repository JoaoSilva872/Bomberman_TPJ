import pygame
import sys
from map import Map
from player import Player
from object import Object

class Game:
    def __init__(self):
        # Configurações da janela
        self.LARGURA = 1280
        self.ALTURA = 720
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Protótipo Bomber")
        
        # Configurações do tabuleiro
        self.TILE_SIZE = 20
        self.COR_CLARA = (240, 240, 240)
        self.COR_ESCURA = (30, 30, 30)
        
        # Configurações do jogador
        self.PLAYER_TILES = 3
        self.player_size = self.TILE_SIZE * self.PLAYER_TILES
        self.player_vel = self.TILE_SIZE
        
        # Colors
        self.border_cor = (80, 60, 60)
        self.object_cor = (0, 120, 0)
        self.destructible_cor = (139, 69, 19)  # Marrom para objetos destrutíveis
        
        # Inicializar componentes
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        self.jugador = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel)
        self.jugador.life_max = 3
        self.jugador.life = 3
        self.bombas = []
        
        # Crear obstáculos
        self.crear_obstaculos()
        
        # Controladores de tempo
        self.move_delay = 100
        self.last_move_time = 0
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        
        # Control de teclas
        self.bomba_presionada = False

    def crear_obstaculos(self):
        """Crea los obstáculos del juego"""
        # Limpar objetos anteriores (se houver)
        Object.objects.clear()
        
        # Obstáculos indestrutíveis (bordas)
        Object(0, 0, 1280, 60, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        Object(0, 660, 1280, 60, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        Object(0, 0, 60, 720, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        Object(1200, 0, 80, 720, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        
        # Obstáculos indestrutíveis internos
        Object(120, 120, 60, 60, "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
        
        # Obstáculos destrutíveis
        Object(480, 180, 60, 60, "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)

    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula de 3x3"""
        grid_size = self.player_size  # 60 píxeles (3 tiles × 20 píxeles)
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y

    def handle_events(self):
        """Maneja los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not self.bomba_presionada:
                    # Verifica se já existe uma bomba ativa (não explodida)
                    bomba_activa = any(not b.explotada for b in self.bombas)
                    
                    if not bomba_activa:
                        from bomba import Bomba
                        # Ajustar posición a la cuadrícula de 3x3
                        grid_x, grid_y = self.ajustar_a_grid(self.jugador.x, self.jugador.y)
                        nueva_bomba = Bomba(grid_x, grid_y, self.player_size)
                        self.bombas.append(nueva_bomba)
                        self.bomba_presionada = True
                        print(f"Bomba colocada em ({grid_x}, {grid_y})")
                    else:
                        print("Já há uma bomba ativa — espere ela explodir!")

                #Testing Life system ========================================================
                # Tecla K → jogador leva 1 de dano
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                # Tecla H → jogador recupera toda a vida
                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
        
        return True
    
    def draw_lives(self):
        """Desenha a vida do jogador na tela"""
        font = pygame.font.Font(None, 36)
        text = font.render(f"Player Lives: {self.jugador.life}x", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 30))
        self.JANELA.blit(text, text_rect)

    def update(self, tiempo_actual):
        """Actualiza el estado del juego"""
        # Actualizar movimiento del jugador
        self.last_move_time += self.clock.get_time()
        if self.last_move_time >= self.move_delay:
            self.jugador.actualizar_movimiento(self.LARGURA, self.ALTURA)
            self.last_move_time = 0
        
        # Actualizar animación del jugador
        keys = pygame.key.get_pressed()
        self.jugador.actualizar_animacion(tiempo_actual, keys)
        
        # Actualizar bombas
        self.actualizar_bombas()
        
        # Atualizar objetos destrutíveis (NOVO)
        Object.atualizar_objetos_destrutiveis(self.bombas)

    def actualizar_bombas(self):
        """Actualiza el estado de las bombas"""
        bombas_a_remover = []

        for bomba in self.bombas:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
                bomba.causou_dano = False

            if bomba.explosion_activa():
                player_rect = pygame.Rect(self.jugador.x, self.jugador.y,
                                        self.player_size, self.player_size)

                if not getattr(bomba, "causou_dano", False):
                    for rect in bomba.explosion_tiles:
                        if player_rect.colliderect(rect):
                            self.jugador.take_damage(1)
                            bomba.causou_dano = True
                            print(f"🔥 Jogador atingido pela explosão! Vida: {self.jugador.life}")
                            break

            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover.append(bomba)

        for bomba in bombas_a_remover:
            self.bombas.remove(bomba)

    def render(self):
        """Renderiza todos los elementos del juego"""
        # 1. Dibujar mapa (fundo)
        self.mapa.dibujar(self.JANELA)
        
        # 2. Dibujar obstáculos NÃO DESTRUÍDOS
        for obj in Object.objects:
            if not obj.destruido:  # Só desenha se não foi destruído
                obj.draw(self.JANELA)
        
        # 3. Dibujar bombas e EXPLOSÕES (por cima dos objetos destrutíveis)
        for bomba in self.bombas:
            bomba.dibujar(self.JANELA)
        
        # 4. Dibujar jugador (por cima de tudo)
        self.jugador.dibujar(self.JANELA, pygame.time.get_ticks() - self.tiempo_inicio)
        
        # 5. Desenhar vidas (UI)
        self.draw_lives()
        
        # Actualizar pantalla
        pygame.display.update()

        
    def game_over(self):
        """Mostra a tela de Game Over e retorna ao menu"""
        fonte_grande = pygame.font.Font(None, 100)
        fonte_pequena = pygame.font.Font(None, 36)
        
        texto_game_over = fonte_grande.render("GAME OVER", True, (255, 0, 0))
        texto_instrucao = fonte_pequena.render("Pressione qualquer tecla para voltar ao menu", True, (255, 255, 255))
        
        texto_game_over_rect = texto_game_over.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 - 50))
        texto_instrucao_rect = texto_instrucao.get_rect(center=(self.LARGURA // 2, self.ALTURA // 2 + 50))

        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(texto_game_over, texto_game_over_rect)
        self.JANELA.blit(texto_instrucao, texto_instrucao_rect)
        pygame.display.update()

        print("💀 GAME OVER - Voltando ao menu...")

        # Espera o jogador pressionar qualquer tecla
        esperando = True
        while esperando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    esperando = False
        
        return

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
            running = self.handle_events()
            self.update(tiempo_actual)
            self.render()
            self.clock.tick(60)
            
            # ⚠️ Se o jogador morrer → chama Game Over
            if not self.jugador.is_alive():
                self.game_over()
                return
        
        pygame.quit()
        sys.exit()