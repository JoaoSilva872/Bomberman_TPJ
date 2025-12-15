import pygame
import random
import os
from enum import Enum

class PowerUpType(Enum):
    """Tipos de power-ups disponibles"""
    MORE_BOMBS = 1      # Más bombas
    FIRE_UP = 2         # Rango de explosión
    SPEED_UP = 3        # Velocidad
    SHIELD = 4          # Escudo temporal
    REMOTE_CONTROL = 5  # Control remoto

class PowerUp:
    """Clase base para power-ups"""
    
    # Colores para cada tipo de power-up
    COLORS = {
        PowerUpType.MORE_BOMBS: (255, 50, 50),      # Rojo
        PowerUpType.FIRE_UP: (255, 140, 0),         # Naranja
        PowerUpType.SPEED_UP: (50, 255, 50),        # Verde
        PowerUpType.SHIELD: (100, 180, 255),        # Azul claro
        PowerUpType.REMOTE_CONTROL: (180, 50, 230), # Púrpura
    }
    
    # Símbolos/texto para cada power-up
    SYMBOLS = {
        PowerUpType.MORE_BOMBS: "B+",
        PowerUpType.FIRE_UP: "F+",
        PowerUpType.SPEED_UP: "S+",
        PowerUpType.SHIELD: "SHD",
        PowerUpType.REMOTE_CONTROL: "R",
    }
    
    # Nombres para mostrar
    NAMES = {
        PowerUpType.MORE_BOMBS: "Más Bombas",
        PowerUpType.FIRE_UP: "Rango+",
        PowerUpType.SPEED_UP: "Velocidad",
        PowerUpType.SHIELD: "Escudo",
        PowerUpType.REMOTE_CONTROL: "Control Remoto",
    }
    
    def __init__(self, x, y, tipo, tamaño=60):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.tamaño = tamaño
        self.activo = True
        
        # Rectángulo para colisiones
        self.rect = pygame.Rect(x, y, tamaño, tamaño)
        
        # Color y símbolo
        self.color = self.COLORS.get(tipo, (255, 255, 255))
        self.simbolo = self.SYMBOLS.get(tipo, "?")
        self.nombre = self.NAMES.get(tipo, "Power-up")
        
        # Intentar cargar imagen
        self.imagen = None
        self.cargar_imagen()
        
        # Animación
        self.tiempo_creacion = pygame.time.get_ticks()
        self.anim_offset = 0
    
    def cargar_imagen(self):
        """Intenta cargar una imagen para el power-up"""
        try:
            nombre_archivo = f"powerup_{self.tipo.value}.png"
            ruta = os.path.join('Object&Bomb_Sprites', nombre_archivo)
            if os.path.exists(ruta):
                self.imagen = pygame.image.load(ruta)
                self.imagen = pygame.transform.scale(self.imagen, (self.tamaño, self.tamaño))
        except:
            pass  # Usaremos dibujo si no hay imagen
    
    def actualizar_animacion(self):
        """Actualiza la animación del power-up"""
        tiempo_actual = pygame.time.get_ticks()
        self.anim_offset = (tiempo_actual // 100) % 10  # Para animación
    
    def dibujar(self, superficie):
        """Dibuja el power-up en la pantalla"""
        if not self.activo:
            return
        
        self.actualizar_animacion()
        
        if self.imagen:
            superficie.blit(self.imagen, (self.x, self.y))
        else:
            # Dibujar un círculo con efecto de brillo
            centro_x = self.x + self.tamaño // 2
            centro_y = self.y + self.tamaño // 2
            radio = self.tamaño // 2 - 2
            
            # Círculo exterior con brillo
            pygame.draw.circle(superficie, self.color, 
                             (centro_x, centro_y),
                             radio + 1)
            
            # Círculo principal
            pygame.draw.circle(superficie, (255, 255, 255),
                             (centro_x, centro_y),
                             radio - 2)
            
            # Círculo interior con color
            pygame.draw.circle(superficie, self.color,
                             (centro_x, centro_y),
                             radio - 4)
            
            # Dibujar el símbolo
            font = pygame.font.Font(None, 24)
            texto = font.render(self.simbolo, True, (255, 255, 255))
            texto_rect = texto.get_rect(center=(centro_x, centro_y))
            superficie.blit(texto, texto_rect)
            
            # Efecto de brillo animado
            if self.anim_offset < 5:
                pygame.draw.circle(superficie, (255, 255, 200, 100),
                                 (centro_x, centro_y),
                                 radio - 2, 2)
    
    def colisiona_con(self, jugador_rect):
        """Verifica si el jugador colisiona con el power-up"""
        return self.activo and self.rect.colliderect(jugador_rect)
    
    def recoger(self):
        """Marca el power-up como recogido"""
        self.activo = False
    
    def debe_desaparecer(self):
        """Verifica si el power-up debe desaparecer (temporalmente deshabilitado)"""
        return False  # Los power-ups permanecen hasta que se recojan

class PowerUpSystem:
    """Sistema para manejar power-ups en el juego"""
    
    def __init__(self, probabilidad_spawn=0.35):  # 35% de chance
        self.powerups = []
        self.probabilidad_spawn = probabilidad_spawn
        
        # Power-ups disponibles para spawnear con probabilidades
        self.tipos_disponibles = [
            PowerUpType.MORE_BOMBS,    # 35%
            PowerUpType.FIRE_UP,       # 30%
            PowerUpType.SPEED_UP,      # 20%
            PowerUpType.SHIELD,        # 10%
            PowerUpType.REMOTE_CONTROL # 5%
        ]
        
        self.probabilidades = [0.35, 0.30, 0.20, 0.10, 0.05]
    
    def intentar_spawn(self, x, y, tamaño):
        """Intenta spawnear un power-up en una posición"""
        if random.random() < self.probabilidad_spawn:
            # Elegir tipo basado en probabilidades
            tipo = random.choices(self.tipos_disponibles, weights=self.probabilidades, k=1)[0]
            
            # Crear power-up
            powerup = PowerUp(x, y, tipo, tamaño)
            self.powerups.append(powerup)
            print(f"✨ Power-up '{powerup.nombre}' apareció en ({x}, {y})")
            return powerup
        return None
    
    def spawn_powerup(self, x, y, tipo, tamaño):
        """Spawn específico de un power-up (para multijugador)"""
        powerup = PowerUp(x, y, tipo, tamaño)
        self.powerups.append(powerup)
        return powerup
    
    def verificar_colisiones(self, jugador_rect, jugador):
        """Verifica si el jugador recoge algún power-up"""
        powerups_recogidos = []
        
        for powerup in self.powerups[:]:
            if powerup.activo and powerup.colisiona_con(jugador_rect):
                powerup.recoger()
                powerups_recogidos.append(powerup.tipo)
                print(f"🎯 Jugador recogió {powerup.nombre}")
        
        # Limpiar power-ups recogidos
        self.powerups = [p for p in self.powerups if p.activo]
        
        return powerups_recogidos
    
    def dibujar_todos(self, superficie):
        """Dibuja todos los power-ups activos"""
        for powerup in self.powerups:
            powerup.dibujar(superficie)
    
    def limpiar(self):
        """Limpia todos los power-ups"""
        self.powerups.clear()
    
    def get_powerup_at(self, x, y):
        """Obtiene un power-up en una posición específica"""
        for powerup in self.powerups:
            if powerup.x == x and powerup.y == y:
                return powerup
        return None