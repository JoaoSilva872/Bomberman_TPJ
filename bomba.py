import pygame
import time

class Bomba:
    def __init__(self, x, y, tamaño, duracion=3):
        self.x = x
        self.y = y
        self.tamaño = tamaño
        self.duracion = duracion  # segundos hasta explosión
        self.tiempo_creacion = time.time()
        self.explotada = False
        self.color = (0, 0, 0)  # Color negro
    
    def dibujar(self, superficie):
        """Dibuja la bomba en la superficie"""
        # Dibujar bomba como círculo negro
        centro_x = self.x + self.tamaño // 2
        centro_y = self.y + self.tamaño // 2
        radio = self.tamaño // 2 - 2
        pygame.draw.circle(superficie, self.color, (centro_x, centro_y), radio)
        
        # Dibujar mecha (pequeño rectángulo rojo)
        pygame.draw.rect(superficie, (255, 0, 0), 
                        (centro_x - 3, centro_y - self.tamaño // 2, 6, 8))
    
    def debe_explotar(self):
        """Verifica si la bomba debe explotar"""
        return time.time() - self.tiempo_creacion >= self.duracion and not self.explotada
    
    def explotar(self):
        """Ejecuta la explosión de la bomba"""
        self.explotada = True
        print("¡Boom! Bomba explotó")