import pygame
import os
import time
from object import Object
from powerup import PowerUpType

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
        
        # POWER-UPS ===========================================================
        self.max_bombas = 1  # Límite inicial de bombas
        self.bombas_colocadas_actual = 0  # Contador actual
        self.rango_explosion = 1  # Rango inicial (1 bloque)
        self.velocidad_base = velocidad
        self.velocidad_boost = 1.0  # Multiplicador de velocidad
        
        # Power-ups temporales
        self.tiene_escudo = False
        self.tiene_invencibilidad = False
        self.tiene_control_remoto = False
        
        # Timers para power-ups temporales (en segundos)
        self.escudo_tiempo = 0
        self.invencibilidad_tiempo = 0
        
        # =====================================================================
        
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
        if self.tiene_escudo:
            print(f"🛡️ Jugador {self.id}: ¡Escudo bloqueó el daño!")
            return False  # No recibió daño
        
        if self.tiene_invencibilidad:
            print(f"⚡ Jugador {self.id}: ¡Invencible!")
            return False  # No recibió daño
            
        self.life -= number
        if self.life < 0:
            self.life = 0
        print(f"💔 Jugador {self.id} recibió daño! Vida: {self.life}/{self.life_max}")
        return True  # Recibió daño
            
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
        return self.bombas_colocadas_actual < self.max_bombas
    
    def colocar_bomba(self, bomba=None):
        """Marca que el jugador ha colocado una bomba"""
        self.bomba_colocada = True
        self.ultima_bomba_tiempo = time.time()
        self.bomba_actual = bomba
        self.bombas_colocadas_actual += 1
    
    def bomba_destruida(self):
        """Marca que la bomba del jugador ha sido destruida"""
        self.bomba_colocada = False
        self.bomba_actual = None
        self.bombas_colocadas_actual = max(0, self.bombas_colocadas_actual - 1)
    
    # POWER-UPS SYSTEM ================================================================
    
    def aplicar_powerup(self, tipo_powerup):
        """Aplica un power-up al jugador"""
        if tipo_powerup == PowerUpType.MORE_BOMBS:
            self.max_bombas += 1
            print(f"🎯 Jugador {self.id}: ¡Puedes colocar {self.max_bombas} bombas!")
            
        elif tipo_powerup == PowerUpType.FIRE_UP:
            self.rango_explosion += 1
            print(f"🔥 Jugador {self.id}: ¡Rango de explosión aumentado a {self.rango_explosion}!")
            
        elif tipo_powerup == PowerUpType.SHIELD:
            self.tiene_escudo = True
            self.escudo_tiempo = time.time() + 10  # 10 segundos
            print(f"🛡️ Jugador {self.id}: ¡Escudo activado por 10 segundos!")
            
        elif tipo_powerup == PowerUpType.REMOTE_CONTROL:
            self.tiene_control_remoto = True
            print(f"🎮 Jugador {self.id}: ¡Control remoto activado!")
    
    def actualizar_powerups(self):
        """Actualiza los power-ups temporales"""
        tiempo_actual = time.time()
        
        # Escudo
        if self.tiene_escudo and tiempo_actual > self.escudo_tiempo:
            self.tiene_escudo = False
            print(f"🛡️ Jugador {self.id}: Escudo desactivado")
        
        # Invencibilidad
        if self.tiene_invencibilidad and tiempo_actual > self.invencibilidad_tiempo:
            self.tiene_invencibilidad = False
            print(f"⚡ Jugador {self.id}: Invencibilidad desactivada")
    
    def get_estado_powerups(self):
        """Obtiene el estado actual de los power-ups para la red"""
        return {
            'max_bombas': self.max_bombas,
            'rango_explosion': self.rango_explosion,
            'velocidad_boost': self.velocidad_boost,
            'tiene_escudo': self.tiene_escudo,
            'tiene_control_remoto': self.tiene_control_remoto,
            'escudo_tiempo': self.escudo_tiempo
        }
    
    def set_estado_powerups(self, estado):
        """Establece el estado de power-ups desde la red"""
        self.max_bombas = estado.get('max_bombas', self.max_bombas)
        self.rango_explosion = estado.get('rango_explosion', self.rango_explosion)
        self.velocidad_boost = estado.get('velocidad_boost', self.velocidad_boost)
        self.tiene_escudo = estado.get('tiene_escudo', False)
        self.tiene_control_remoto = estado.get('tiene_control_remoto', False)
        self.escudo_tiempo = estado.get('escudo_tiempo', 0)
        
        # Actualizar velocidad
        self.velocidad = int(self.velocidad_base * self.velocidad_boost)
    
    # ====================================================================================

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
        
        # Actualizar power-ups temporales
        self.actualizar_powerups()

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
            
            # Si tiene escudo, dibujar un efecto de escudo
            if self.tiene_escudo:
                escudo_surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
                pygame.draw.circle(escudo_surf, (100, 180, 255, 100), 
                                 (self.tamaño//2, self.tamaño//2), self.tamaño//2 - 2)
                superficie.blit(escudo_surf, (self.x, self.y))
            
            # Si tiene invencibilidad, efecto de parpadeo
            if self.tiene_invencibilidad and (tiempo_actual // 200) % 2 == 0:
                inv_surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
                pygame.draw.circle(inv_surf, (255, 255, 100, 150), 
                                 (self.tamaño//2, self.tamaño//2), self.tamaño//2)
                superficie.blit(inv_surf, (self.x, self.y))
            
            superficie.blit(sprite_actual, (self.x, self.y))
            
        except IndexError:
            sprite_actual = self.sprites[self.direccion_actual][0]
            superficie.blit(sprite_actual, (self.x, self.y))