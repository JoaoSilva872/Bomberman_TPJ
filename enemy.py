import pygame
import random
import time
import os

class Enemy:
    def __init__(self, x, y, tamaño, velocidad=2, vida=1):
        self.x = x
        self.y = y
        self.tamaño = tamaño
        self.velocidad = velocidad
        self.vida = vida
        self.vida_max = vida
        self.direccion = random.choice(['up', 'down', 'left', 'right'])
        self.tiempo_ultimo_cambio = time.time()
        self.tiempo_cambio_direccion = random.uniform(1.0, 3.0)  # Cambia dirección cada 1-3 segundos
        
        # Rectángulo para colisiones
        self.rect = pygame.Rect(x, y, tamaño, tamaño)
        
        # Cargar sprite del enemigo
        self.cargar_sprites()
        self.direccion_actual = 'down'
        self.frame_actual = 0
        self.ultimo_cambio_animacion = 0
        self.velocidad_animacion = 200
        
        # Estado
        self.activo = True
        self.invencible = False
        self.tiempo_invencibilidad = 0
    
    def cargar_sprites(self):
        """Carga los sprites del enemigo"""
        self.sprites = {
            'down': [],
            'up': [],
            'left': [],
            'right': []
        }
        
        # Intentar cargar sprites personalizados, sino usar sprites por defecto
        try:
            carpeta = 'enemySprites'
            if os.path.exists(carpeta):
                for direccion in self.sprites.keys():
                    for i in range(1, 4):
                        nombre_archivo = f'enemy_{direccion}_{i}.png'
                        ruta_imagen = os.path.join(carpeta, nombre_archivo)
                        if os.path.exists(ruta_imagen):
                            sprite = pygame.image.load(ruta_imagen).convert_alpha()
                            sprite = pygame.transform.scale(sprite, (self.tamaño, self.tamaño))
                            self.sprites[direccion].append(sprite)
                        else:
                            raise FileNotFoundError
            else:
                raise FileNotFoundError
        except:
            # Crear sprites por defecto (círculos rojos)
            for direccion in self.sprites.keys():
                for i in range(3):
                    surf = pygame.Surface((self.tamaño, self.tamaño), pygame.SRCALPHA)
                    color = (255, 50, 50) if i == 0 else (220, 40, 40) if i == 1 else (200, 30, 30)
                    pygame.draw.circle(surf, color, (self.tamaño//2, self.tamaño//2), self.tamaño//2 - 2)
                    # Ojos
                    pygame.draw.circle(surf, (255, 255, 255), (self.tamaño//3, self.tamaño//3), 4)
                    pygame.draw.circle(surf, (255, 255, 255), (2*self.tamaño//3, self.tamaño//3), 4)
                    pygame.draw.circle(surf, (0, 0, 0), (self.tamaño//3, self.tamaño//3), 2)
                    pygame.draw.circle(surf, (0, 0, 0), (2*self.tamaño//3, self.tamaño//3), 2)
                    self.sprites[direccion].append(surf)
    
    def actualizar(self, objetos, bombas, ancho_ventana, alto_ventana):
        """Actualiza el movimiento y estado del enemigo"""
        if not self.activo:
            return
        
        # Actualizar invencibilidad
        if self.invencible and time.time() > self.tiempo_invencibilidad:
            self.invencible = False
        
        # Cambiar dirección aleatoriamente
        tiempo_actual = time.time()
        if tiempo_actual - self.tiempo_ultimo_cambio > self.tiempo_cambio_direccion:
            self.direccion = random.choice(['up', 'down', 'left', 'right'])
            self.tiempo_ultimo_cambio = tiempo_actual
            self.tiempo_cambio_direccion = random.uniform(1.0, 3.0)
        
        # Calcular movimiento futuro
        futuro_x = self.x
        futuro_y = self.y
        
        if self.direccion == 'up':
            futuro_y -= self.velocidad
            self.direccion_actual = 'up'
        elif self.direccion == 'down':
            futuro_y += self.velocidad
            self.direccion_actual = 'down'
        elif self.direccion == 'left':
            futuro_x -= self.velocidad
            self.direccion_actual = 'left'
        elif self.direccion == 'right':
            futuro_x += self.velocidad
            self.direccion_actual = 'right'
        
        # Verificar colisiones con objetos
        futuro_rect = pygame.Rect(futuro_x, futuro_y, self.tamaño, self.tamaño)
        colision_objeto = False
        
        for obj in objetos:
            if not obj.destruido and futuro_rect.colliderect(obj.rect):
                colision_objeto = True
                # Cambiar dirección al chocar
                self.direccion = random.choice(['up', 'down', 'left', 'right'])
                break
        
        # Verificar colisiones con bombas
        colision_bomba = False
        for bomba in bombas:
            if not bomba.explotada and bomba.es_colision_solida(-1):  # -1 para enemigos
                if futuro_rect.colliderect(bomba.rect):
                    colision_bomba = True
                    self.direccion = random.choice(['up', 'down', 'left', 'right'])
                    break
        
        # Mover si no hay colisión
        if not colision_objeto and not colision_bomba:
            self.x = futuro_x
            self.y = futuro_y
            self.rect.x = self.x
            self.rect.y = self.y
        else:
            # Si hay colisión, cambiar dirección inmediatamente
            self.tiempo_ultimo_cambio = 0
        
        # Mantener dentro de los límites
        self.x = max(0, min(self.x, ancho_ventana - self.tamaño))
        self.y = max(0, min(self.y, alto_ventana - self.tamaño))
        self.rect.x = self.x
        self.rect.y = self.y
    
    def actualizar_animacion(self, tiempo_actual):
        """Actualiza la animación del enemigo"""
        if tiempo_actual - self.ultimo_cambio_animacion > self.velocidad_animacion:
            self.frame_actual = (self.frame_actual + 1) % len(self.sprites[self.direccion_actual])
            self.ultimo_cambio_animacion = tiempo_actual
    
    def dibujar(self, superficie, tiempo_actual):
        """Dibuja el enemigo"""
        if not self.activo:
            return
        
        self.actualizar_animacion(tiempo_actual)
        
        # Efecto de parpadeo si es invencible
        if self.invencible and (tiempo_actual // 100) % 2 == 0:
            return
        
        try:
            sprite = self.sprites[self.direccion_actual][self.frame_actual]
            superficie.blit(sprite, (self.x, self.y))
            
            # Dibujar barra de vida si no está al máximo
            if self.vida < self.vida_max:
                barra_ancho = self.tamaño
                barra_alto = 5
                barra_x = self.x
                barra_y = self.y - barra_alto - 2
                
                # Fondo de la barra
                pygame.draw.rect(superficie, (100, 0, 0), 
                               (barra_x, barra_y, barra_ancho, barra_alto))
                
                # Vida actual
                vida_porcentaje = self.vida / self.vida_max
                pygame.draw.rect(superficie, (0, 255, 0),
                               (barra_x, barra_y, barra_ancho * vida_porcentaje, barra_alto))
        except:
            # Fallback: círculo rojo
            centro_x = self.x + self.tamaño // 2
            centro_y = self.y + self.tamaño // 2
            pygame.draw.circle(superficie, (255, 0, 0), (centro_x, centro_y), self.tamaño // 2)
    
    def recibir_dano(self, cantidad=1):
        """El enemigo recibe daño"""
        if self.invencible or not self.activo:
            return False
        
        self.vida -= cantidad
        self.invencible = True
        self.tiempo_invencibilidad = time.time() + 0.5  # 0.5 segundos de invencibilidad
        
        if self.vida <= 0:
            self.activo = False
            return True  # Enemigo eliminado
        
        return False  # Enemigo herido pero vivo
    
    def colisiona_con(self, rect):
        """Verifica colisión con un rectángulo"""
        if not self.activo:
            return False
        return self.rect.colliderect(rect)