import pygame
import sys
import os
from objeto import Objeto

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
player_vel = TILE_SIZE

# Colors
border_cor = (80, 60, 60)
object_cor = (0, 120, 0)

# ====== SISTEMA DE SPRITES ======
def cargar_sprite(ruta, tamaño):
    """Carga una imagen y la escala al tamaño correcto"""
    try:
        sprite = pygame.image.load(ruta).convert_alpha()
        return pygame.transform.scale(sprite, tamaño)
    except:
        print(f"Error cargando: {ruta}")
        # Crear sprite temporal si no existe
        surf = pygame.Surface(tamaño, pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 0, 0), (0, 0, tamaño[0], tamaño[1]))
        return surf

# Cargar sprites de Bomberman
sprites_bomberman = {
    'down': [],
    'up': [],
    'left': [],
    'right': []
}

tamaño_sprite = (player_size, player_size)

# Cargar los 3 frames para cada dirección
for direccion in sprites_bomberman.keys():
    for i in range(1, 3):
        ruta_imagen = os.path.join('images', f'bomberman_{direccion}_{i}.png')
        sprite = cargar_sprite(ruta_imagen, tamaño_sprite)
        sprites_bomberman[direccion].append(sprite)

# Variables de animación
direccion_actual = 'down'
frame_actual = 0
ultimo_cambio_animacion = 0
velocidad_animacion = 200  # ms entre frames
esta_moviendose = False  # Nueva variable para controlar movimiento

# ====== FIN SISTEMA DE SPRITES ======

# Posicionar o jogador
player_x = ((LARGURA // 2) // TILE_SIZE) * TILE_SIZE
player_y = ((ALTURA // 2) // TILE_SIZE) * TILE_SIZE
player_x -= (player_size // 2) // TILE_SIZE * TILE_SIZE
player_y -= (player_size // 2) // TILE_SIZE * TILE_SIZE

# 🔹 Criar obstáculos
upperBorder = Objeto(0, 0, 1280, 60, cor=border_cor)
bottomBorder = Objeto(0, 660, 1280, 60, cor=border_cor)
leftBorder = Objeto(0, 0, 60, 720, cor=border_cor)
rightBorder = Objeto(1220, 0, 60, 720, cor=border_cor)
bloco1 = Objeto(120, 120, player_size, cor=object_cor)
bloco2 = Objeto(480, 120, player_size, cor=object_cor)

# Controladores de tiempo
move_delay = 100
last_move_time = 0
clock = pygame.time.Clock()
tiempo_inicio = pygame.time.get_ticks()

while True:
    tiempo_actual = pygame.time.get_ticks() - tiempo_inicio
    dt = clock.tick(60)
    last_move_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Teclas pressionadas
    keys = pygame.key.get_pressed()

    # Verificar si el jugador se está moviendo
    esta_moviendose = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_s] or keys[pygame.K_DOWN] or keys[pygame.K_a] or keys[pygame.K_LEFT] or keys[pygame.K_d] or keys[pygame.K_RIGHT]

    # Movimento contínuo no grid com colisão
    if last_move_time >= move_delay:
        futuro_x = player_x
        futuro_y = player_y
        nueva_direccion = direccion_actual

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            futuro_y -= player_vel
            nueva_direccion = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            futuro_y += player_vel
            nueva_direccion = "down"
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            futuro_x -= player_vel
            nueva_direccion = "left"
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            futuro_x += player_vel
            nueva_direccion = "right"

        # Actualizar dirección si cambió
        if nueva_direccion != direccion_actual:
            direccion_actual = nueva_direccion
            frame_actual = 0  # Reiniciar animación al cambiar dirección
            ultimo_cambio_animacion = tiempo_actual

        # Criar rect futuro para colisão
        futuro_rect = pygame.Rect(futuro_x, futuro_y, player_size, player_size)

        # Verificar colisão
        colisao = Objeto.verificar_colisao_com_player(futuro_rect)

        # Só mover se não houver colisão
        if not colisao:
            player_x = futuro_x
            player_y = futuro_y

        last_move_time = 0

        # Limites da janela
        if player_x < 0:
            player_x = 0
        if player_x + player_size > LARGURA:
            player_x = LARGURA - player_size
        if player_y < 0:
            player_y = 0
        if player_y + player_size > ALTURA:
            player_y = ALTURA - player_size

    # Actualizar animación SOLO cuando se está moviendo
    if esta_moviendose and tiempo_actual - ultimo_cambio_animacion > velocidad_animacion:
        frame_actual = (frame_actual + 1) % len(sprites_bomberman[direccion_actual])
        ultimo_cambio_animacion = tiempo_actual
    elif not esta_moviendose:
        # Cuando no se mueve, mostrar el primer frame (posición de reposo)
        frame_actual = 0

    # 🔹 Desenhar tabuleiro estilo xadrez
    for linha in range(0, ALTURA, TILE_SIZE):
        for coluna in range(0, LARGURA, TILE_SIZE):
            if (linha // TILE_SIZE + coluna // TILE_SIZE) % 2 == 0:
                cor = COR_CLARA
            else:
                cor = COR_ESCURA
            pygame.draw.rect(JANELA, cor, (coluna, linha, TILE_SIZE, TILE_SIZE))

    # 🔹 Desenhar todos os obstáculos
    for obj in Objeto.objetos:
        obj.draw(JANELA)

    # 🔹 DESENHAR JOGADOR COM SPRITE
    sprite_a_dibujar = sprites_bomberman[direccion_actual][frame_actual]
    JANELA.blit(sprite_a_dibujar, (player_x, player_y))

    pygame.display.update()