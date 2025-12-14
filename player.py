import pygame
import os
from object import Object

class Player:
    def __init__(self, ancho_ventana, alto_ventana, tamaño, velocidad):
        self.tamaño = tamaño
        self.velocidad = velocidad
        
        # Posición inicial
        self.x = 60
        self.y = 60
        
        # Vida
        self.life_max = 3
        self.life = 3
        
        # Animación
        self.direccion_actual = 'down'
        self.frame_actual = 0
        self.ultimo_cambio_animacion = 0
        self.velocidad_animacion = 180
        self.esta_moviendose = False
        
        # Cargar sprites
        self.sprites = self.cargar_sprites()
        
# Health System functions ================================================================

    def take_damage(self, number):
        """Reduce Life."""
        self.life -= number
        if self.life < 0:
            self.life = 0
            
    def heal(self, number):
        """Restores life"""
        self.life += number
        if self.life > self.life_max:
            self.life = self.life_max
    
    def is_alive(self):
        """Returns true if the player is alive."""
        return self.life > 0
    
# ==========================================================================================

    def cargar_sprites(self):
        """Carga los sprites del jugador usando tus rutas originales"""
        
        def cargar_sprite(ruta, tamaño):
            try:
                # Intenta cargar la imagen
                if not os.path.exists(ruta):
                    raise FileNotFoundError(f"No existe: {ruta}")
                    
                sprite = pygame.image.load(ruta).convert_alpha()
                return pygame.transform.scale(sprite, tamaño)
            except Exception as e:
                # Si falla, crea un cuadrado de color como 'fallback' para que no crashee
                print(f"⚠️ Aviso: No se encontró la imagen en '{ruta}'. Usando cuadro rojo.")
                surf = pygame.Surface(tamaño)
                surf.fill((255, 50, 50)) # Rojo para indicar error visualmente
                return surf

        sprites = {
            'down': [],
            'up': [],
            'left': [],
            'right': []
        }

        # Nombres de archivos basados en TU estructura original
        # Espera archivos tipo: playerSprites/bomberman_down_1.png
        carpeta = 'playerSprites' 
        
        # Verificamos si la carpeta existe para avisarte
        if not os.path.exists(carpeta):
            print(f"❌ ERROR CRÍTICO: La carpeta '{carpeta}' no existe en el directorio del juego.")

        for direccion in sprites.keys():
            for i in range(1, 4): # 1, 2, 3
                # Construye la ruta: playerSprites/bomberman_down_1.png
                nombre_archivo = f'bomberman_{direccion}_{i}.png'
                ruta_imagen = os.path.join(carpeta, nombre_archivo)
                
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
            # Solo reinicia el frame si cambiamos de dirección drásticamente
            # para evitar parpadeos, o reinicialo si prefieres
            # self.frame_actual = 0 

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

        if self.esta_moviendose:
            if tiempo_actual - self.ultimo_cambio_animacion > self.velocidad_animacion:
                self.frame_actual = (self.frame_actual + 1) % len(self.sprites[self.direccion_actual])
                self.ultimo_cambio_animacion = tiempo_actual
        else:
            # Si se detiene, volver al frame 0 (parado)
            self.frame_actual = 0

    def dibujar(self, superficie, tiempo_actual):
        """Dibuja al jugador en la superficie"""
        # Pasamos las teclas presionadas para actualizar el estado de animación
        self.actualizar_animacion(tiempo_actual, pygame.key.get_pressed())
        
        try:
            sprite_actual = self.sprites[self.direccion_actual][self.frame_actual]
            superficie.blit(sprite_actual, (self.x, self.y))
        except IndexError:
            # Por seguridad, si el frame falla, dibuja el primero
            sprite_actual = self.sprites[self.direccion_actual][0]
            superficie.blit(sprite_actual, (self.x, self.y))