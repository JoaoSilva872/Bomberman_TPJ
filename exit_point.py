import pygame
import os

class ExitPoint:
    def __init__(self, x, y, tamaño):
        self.x = x
        self.y = y
        self.tamaño = tamaño
        self.rect = pygame.Rect(x, y, tamaño, tamaño)
        self.activado = False
        self.tiempo_activacion = 0
        
        # Cargar sprites
        self.sprites = {
            'inactivo': None,
            'activo': None,
            'animacion': []
        }
        self.cargar_sprites()
        
        # Animación
        self.frame_actual = 0
        self.ultimo_cambio_animacion = 0
        self.velocidad_animacion = 150
    
    def cargar_sprites(self):
        """Carga los sprites de la salida"""
        try:
            # Intentar cargar sprites personalizados
            carpeta = 'Object&Bomb_Sprites'
            
            # Sprite inactivo
            ruta_inactivo = os.path.join(carpeta, 'exit_inactive.png')
            if os.path.exists(ruta_inactivo):
                self.sprites['inactivo'] = pygame.image.load(ruta_inactivo).convert_alpha()
                self.sprites['inactivo'] = pygame.transform.scale(self.sprites['inactivo'], 
                                                                (self.tamaño, self.tamaño))
            
            # Sprite activo
            ruta_activo = os.path.join(carpeta, 'exit_active.png')
            if os.path.exists(ruta_activo):
                self.sprites['activo'] = pygame.image.load(ruta_activo).convert_alpha()
                self.sprites['activo'] = pygame.transform.scale(self.sprites['activo'], 
                                                               (self.tamaño, self.tamaño))
            
            # Sprites de animación
            for i in range(1, 5):
                ruta_anim = os.path.join(carpeta, f'exit_anim_{i}.png')
                if os.path.exists(ruta_anim):
                    sprite = pygame.image.load(ruta_anim).convert_alpha()
                    sprite = pygame.transform.scale(sprite, (self.tamaño, self.tamaño))
                    self.sprites['animacion'].append(sprite)
        except:
            pass
        
        # Crear sprites por defecto si no hay imágenes
        if not self.sprites['inactivo']:
            surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
            pygame.draw.rect(surf, (100, 100, 100), (0, 0, self.tamaño, self.tamaño))
            pygame.draw.rect(surf, (150, 150, 150), (0, 0, self.tamaño, self.tamaño), 3)
            pygame.draw.circle(surf, (200, 200, 0), (self.tamaño//2, self.tamaño//2), self.tamaño//4)
            self.sprites['inactivo'] = surf
        
        if not self.sprites['activo']:
            surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
            pygame.draw.rect(surf, (150, 150, 100), (0, 0, self.tamaño, self.tamaño))
            pygame.draw.rect(surf, (255, 255, 0), (0, 0, self.tamaño, self.tamaño), 3)
            pygame.draw.circle(surf, (255, 255, 0), (self.tamaño//2, self.tamaño//2), self.tamaño//4)
            self.sprites['activo'] = surf
        
        if len(self.sprites['animacion']) == 0:
            for i in range(4):
                surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
                color = (255, 255, 100 + i*20)
                pygame.draw.rect(surf, (150, 150, 100), (0, 0, self.tamaño, self.tamaño))
                pygame.draw.rect(surf, color, (0, 0, self.tamaño, self.tamaño), 3)
                pygame.draw.circle(surf, color, (self.tamaño//2, self.tamaño//2), self.tamaño//4 + i*2)
                self.sprites['animacion'].append(surf)
    
    def activar(self):
        """Activa el punto de salida"""
        self.activado = True
        self.tiempo_activacion = pygame.time.get_ticks()
    
    def desactivar(self):
        """Desactiva el punto de salida"""
        self.activado = False
    
    def actualizar_animacion(self, tiempo_actual):
        """Actualiza la animación de la salida"""
        if self.activado and len(self.sprites['animacion']) > 0:
            if tiempo_actual - self.ultimo_cambio_animacion > self.velocidad_animacion:
                self.frame_actual = (self.frame_actual + 1) % len(self.sprites['animacion'])
                self.ultimo_cambio_animacion = tiempo_actual
    
    def dibujar(self, superficie, tiempo_actual):
        """Dibuja el punto de salida"""
        self.actualizar_animacion(tiempo_actual)
        
        if self.activado:
            if len(self.sprites['animacion']) > 0:
                sprite = self.sprites['animacion'][self.frame_actual]
            else:
                sprite = self.sprites['activo']
        else:
            sprite = self.sprites['inactivo']
        
        superficie.blit(sprite, (self.x, self.y))
        
        # Dibujar efecto de brillo si está activado
        if self.activado:
            brillo = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
            alpha = 100 + (tiempo_actual // 50) % 155
            brillo.fill((255, 255, 200, alpha))
            superficie.blit(brillo, (self.x, self.y), special_flags=pygame.BLEND_ALPHA_SDL2)
    
    def colisiona_con(self, rect):
        """Verifica colisión con un rectángulo"""
        return self.rect.colliderect(rect)
    
    def es_salida_disponible(self):
        """Verifica si la salida está disponible (activada)"""
        return self.activado