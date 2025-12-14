import pygame
import os
import time
from object import Object

class Player:
    def __init__(self, ancho_ventana, alto_ventana, tamaño, velocidad, id=0):
        self.tamaño = tamaño
        self.velocidad = velocidad
        self.id = id  # ID único del jugador (0 para un jugador, 1/2 para multijugador)
        
        # Posición inicial
        self.x = 60
        self.y = 60
        
        # Vida
        self.life_max = 3
        self.life = 3
        
        # Control de bombas
        self.bomba_colocada = False
        self.ultima_bomba_tiempo = 0
        self.bomba_actual = None
        
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
    
    # Métodos para control de bombas ========================================================
    
    def puede_colocar_bomba(self):
        """Verifica si el jugador puede colocar una bomba"""
        return not self.bomba_colocada
    
    def colocar_bomba(self, bomba=None):
        """Marca que el jugador ha colocado una bomba"""
        self.bomba_colocada = True
        self.ultima_bomba_tiempo = time.time()
        self.bomba_actual = bomba
    
    def bomba_destruida(self):
        """Marca que la bomba del jugador ha sido destruida"""
        self.bomba_colocada = False
        self.bomba_actual = None
    
    # =========================================================================================

    def cargar_sprites(self):
        """Carga los sprites del jugador usando tus rutas originales"""
        
        def cargar_sprite(ruta, tamaño):
            try:
                if not os.path.exists(ruta):
                    raise FileNotFoundError(f"No existe: {ruta}")
                    
                sprite = pygame.image.load(ruta).convert_alpha()
                return pygame.transform.scale(sprite, tamaño)
            except Exception as e:
                print(f"⚠️ Aviso: No se encontró la imagen en '{ruta}'. Usando cuadro rojo.")
                surf = pygame.Surface(tamaño)
                surf.fill((255, 50, 50))
                return surf

        sprites = {
            'down': [],
            'up': [],
            'left': [],
            'right': []
        }

        carpeta = 'playerSprites' 
        
        if not os.path.exists(carpeta):
            print(f"❌ ERROR CRÍTICO: La carpeta '{carpeta}' no existe en el directorio del juego.")

        for direccion in sprites.keys():
            for i in range(1, 4):
                nombre_archivo = f'bomberman_{direccion}_{i}.png'
                ruta_imagen = os.path.join(carpeta, nombre_archivo)
                
                sprite = cargar_sprite(ruta_imagen, (self.tamaño, self.tamaño))
                sprites[direccion].append(sprite)
        
        return sprites

    def actualizar_movimiento(self, ancho_ventana, alto_ventana, bombas=None):
        """Actualiza la posición del jugador con colisión de bombas"""
        if bombas is None:
            bombas = []
            
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

        # Verificar colisión con objetos
        futuro_rect = pygame.Rect(futuro_x, futuro_y, self.tamaño, self.tamaño)
        colision_objeto = Object.verificar_colisao_com_player(futuro_rect)
        
        # Verificar colisión con bombas no explotadas (usando el nuevo sistema)
        colision_bomba = False
        for bomba in bombas:
            if not bomba.explotada:
                # Usar el nuevo sistema de colisiones dinámicas
                if bomba.es_colision_solida(self.id):
                    if futuro_rect.colliderect(bomba.rect):
                        colision_bomba = True
                        break
            # ¡CORRECCIÓN IMPORTANTE! Permitir movimiento si la bomba está explotando
            elif bomba.explotada:
                # Durante la explosión, NO hay colisión (el jugador puede pasar)
                continue

        # Mover si no hay colisión
        if not colision_objeto and not colision_bomba:
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
            self.frame_actual = 0

    def dibujar(self, superficie, tiempo_actual):
        """Dibuja al jugador en la superficie"""
        self.actualizar_animacion(tiempo_actual, pygame.key.get_pressed())
        
        try:
            sprite_actual = self.sprites[self.direccion_actual][self.frame_actual]
            superficie.blit(sprite_actual, (self.x, self.y))
        except IndexError:
            sprite_actual = self.sprites[self.direccion_actual][0]
            superficie.blit(sprite_actual, (self.x, self.y))