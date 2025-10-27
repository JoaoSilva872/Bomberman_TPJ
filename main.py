import pygame
import sys
from objeto import Objeto  # Importamos a classe Objeto (com lista automática)

# Inicializar pygame
pygame.init()

# Configurações da janela
LARGURA = 1280
ALTURA = 720
JANELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Protótipo Bomber")

# Configurações do tabuleiro
TILE_SIZE = 20
COR_CLARA = (240, 240, 240)
COR_ESCURA = (30, 30, 30)

# Configurações do jogador (3x3 tiles)
PLAYER_TILES = 3
player_size = TILE_SIZE * PLAYER_TILES
player_vel = TILE_SIZE  # mover em passos de 1 tile

# Colors
player_cor = (255, 0, 0)
border_cor = (80, 60, 60)
object_cor = (0, 120, 0)

# Posicionar o jogador centralizado e alinhado ao grid
player_x = ((LARGURA // 2) // TILE_SIZE) * TILE_SIZE
player_y = ((ALTURA // 2) // TILE_SIZE) * TILE_SIZE
player_x -= (player_size // 2) // TILE_SIZE * TILE_SIZE
player_y -= (player_size // 2) // TILE_SIZE * TILE_SIZE

# 🔹 Criar obstáculos (objetos verdes fixos)
# Eles são automaticamente adicionados à lista Objeto.objetos
upperBorder = Objeto(0, 0, 1280, 60, cor=border_cor)
bottomBorder = Objeto(0, 660, 1280, 60, cor=border_cor)
leftBorder = Objeto(0, 0, 60, 720, cor=border_cor)
rightBorder = Objeto(1220, 0, 60, 720, cor=border_cor)
bloco1 = Objeto(120, 120, player_size, cor=object_cor)
bloco2 = Objeto(480, 120, player_size, cor=object_cor)

# Controlador de tempo de movimento
move_delay = 100  # ms entre passos
last_move_time = 0

clock = pygame.time.Clock()

while True:
    dt = clock.tick(60)
    last_move_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Teclas pressionadas
    keys = pygame.key.get_pressed()

    # Movimento contínuo no grid com colisão
    if last_move_time >= move_delay:
        futuro_x = player_x
        futuro_y = player_y

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            futuro_y -= player_vel
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            futuro_y += player_vel
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            futuro_x -= player_vel
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            futuro_x += player_vel

        # Criar rect futuro para colisão
        futuro_rect = pygame.Rect(futuro_x, futuro_y, player_size, player_size)

        # 🔹 Agora verificamos colisão com *qualquer* objeto da classe
        colisao = Objeto.verificar_colisao_com_player(futuro_rect)

        # Só mover se não houver colisão
        if not colisao:
            player_x = futuro_x
            player_y = futuro_y

        last_move_time = 0

        # Limites da janela (para o jogador não sair da tela)
        if player_x < 0:
            player_x = 0
        if player_x + player_size > LARGURA:
            player_x = LARGURA - player_size
        if player_y < 0:
            player_y = 0
        if player_y + player_size > ALTURA:
            player_y = ALTURA - player_size

    # 🔹 Desenhar tabuleiro estilo xadrez
    for linha in range(0, ALTURA, TILE_SIZE):
        for coluna in range(0, LARGURA, TILE_SIZE):
            if (linha // TILE_SIZE + coluna // TILE_SIZE) % 2 == 0:
                cor = COR_CLARA
            else:
                cor = COR_ESCURA
            pygame.draw.rect(JANELA, cor, (coluna, linha, TILE_SIZE, TILE_SIZE))

    # 🔹 Desenhar todos os obstáculos criados automaticamente
    for obj in Objeto.objetos:
        obj.draw(JANELA)

    # 🔹 Desenhar jogador
    pygame.draw.rect(JANELA, player_cor, (player_x, player_y, player_size, player_size))

    pygame.display.update()
