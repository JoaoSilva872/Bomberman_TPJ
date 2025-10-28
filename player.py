import pygame
import os
from object import Object

class Player:
    def __init__(self, ancho_ventana, alto_ventana, tamaño, velocidad):
        self.tamaño = tamaño
        self.velocidad = velocidad
        
        # Posición inicial
        self.x = ((ancho_ventana // 2) // (tamaño // 3)) * (tamaño // 3)
        self.y = ((alto_ventana // 2) // (tamaño // 3)) * (tamaño // 3)
        self.x -= (tamaño // 2) // (tamaño // 3) * (tamaño // 3)
        self.y -= (tamaño // 2) // (tamaño // 3) * (tamaño // 3)
        
        # Animación
        self.direccion_actual = 'down'
        self.frame_actual = 0
        self.ultimo_cambio_animacion = 0
        self.velocidad_animacion = 350
        self.esta_moviendose = False
        
        # Cargar sprites
        self.sprites = self.cargar_sprites()

    def cargar_sprites(self):
        """Carga los sprites del jugador"""
        def cargar_sprite(ruta, tamaño):
            try:
                sprite = pygame.image.load(ruta).convert_alpha()
                return pygame.transform.scale(sprite, tamaño)
            except:
                print(f"Error cargando: {ruta}")
                surf = pygame.Surface(tamaño, pygame.SRCALPHA)
                pygame.draw.rect(surf, (255, 0, 0), (0, 0, tamaño[0], tamaño[1]))
                return surf

        sprites = {
            'down': [],
            'up': [],
            'left': [],
            'right': []
        }

        for direccion in sprites.keys():
            for i in range(1,4):
                ruta_imagen = os.path.join('images', f'bomberman_{direccion}_{i}.png')
                sprite = cargar_sprite(ruta_imagen, (self.tamaño, self.tamaño))
                sprites[direccion].append(sprite)
        
        return sprites

    def actualizar_movimiento(self, ancho_ventana, alto_ventana):
        """Actualiza la posición del jugador"""
        keys = pygame.key.get_pressed()
        futuro_x = self.x
        futuro_y = self.y
        nueva_direccion = self.direccion_actual

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            futuro_y -= self.velocidad
            nueva_direccion = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            futuro_y += self.velocidad
            nueva_direccion = "down"
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            futuro_x -= self.velocidad
            nueva_direccion = "left"
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            futuro_x += self.velocidad
            nueva_direccion = "right"

        # Actualizar dirección si cambió
        if nueva_direccion != self.direccion_actual:
            self.direccion_actual = nueva_direccion
            self.frame_actual = 0

        # Verificar colisión
        futuro_rect = pygame.Rect(futuro_x, futuro_y, self.tamaño, self.tamaño)
        colision = Object.verificar_colisao_com_player(futuro_rect)

        # Mover si no hay colisión
        if not colision:
            self.x = futuro_x
            self.y = futuro_y

        # Limites de la ventana
        self.x = max(0, min(self.x, ancho_ventana - self.tamaño))
        self.y = max(0, min(self.y, alto_ventana - self.tamaño))

    def actualizar_animacion(self, tiempo_actual, keys):
        """Actualiza la animación del jugador"""
        self.esta_moviendose = any([
            keys[pygame.K_w], keys[pygame.K_UP],
            keys[pygame.K_s], keys[pygame.K_DOWN],
            keys[pygame.K_a], keys[pygame.K_LEFT],
            keys[pygame.K_d], keys[pygame.K_RIGHT]
        ])

        if self.esta_moviendose and tiempo_actual - self.ultimo_cambio_animacion > self.velocidad_animacion:
            self.frame_actual = (self.frame_actual + 1) % len(self.sprites[self.direccion_actual])
            self.ultimo_cambio_animacion = tiempo_actual
        elif not self.esta_moviendose:
            self.frame_actual = 0

    def dibujar(self, superficie, tiempo_actual):
        """Dibuja al jugador en la superficie"""
        self.actualizar_animacion(tiempo_actual, pygame.key.get_pressed())
        sprite_actual = self.sprites[self.direccion_actual][self.frame_actual]
        superficie.blit(sprite_actual, (self.x, self.y))