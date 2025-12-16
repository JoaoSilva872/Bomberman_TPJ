import pygame
import sys
import random
import math

class Particle:
    """Partículas para el fondo animado - versión simplificada"""
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.randint(1, 3)
        self.speed = random.uniform(0.3, 1.0)
        self.color = (random.randint(50, 100), random.randint(100, 200), random.randint(200, 255))
        self.direction = random.uniform(0, 2 * math.pi)
        
    def update(self):
        self.x += math.cos(self.direction) * self.speed
        self.y += math.sin(self.direction) * self.speed
        
        # Rebotar en los bordes
        if self.x < 0 or self.x > 1280:
            self.direction = math.pi - self.direction
        if self.y < 0 or self.y > 720:
            self.direction = -self.direction
            
        # Reaparecer si se sale
        if self.x < -10 or self.x > 1290 or self.y < -10 or self.y > 730:
            self.x = random.randint(0, 1280)
            self.y = random.randint(0, 720)
            
    def draw(self, surface):
        # Versión simplificada sin transparencia
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)

class Button:
    """Botón con efectos visuales mejorados"""
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.clicked = False
        self.hover_progress = 0  # Para animación suave
        
        # Efecto de brillo
        self.glow_alpha = 0
        self.glow_direction = 1
        
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Animación suave de hover
        if self.is_hovered and self.hover_progress < 1.0:
            self.hover_progress = min(1.0, self.hover_progress + 0.15)
        elif not self.is_hovered and self.hover_progress > 0:
            self.hover_progress = max(0.0, self.hover_progress - 0.1)
            
        # Efecto de brillo cuando se hover
        if self.is_hovered:
            self.glow_alpha = min(255, self.glow_alpha + 10)
        else:
            self.glow_alpha = max(0, self.glow_alpha - 5)
            
        return self.is_hovered and was_hovered
    
    def draw(self, surface, font):
        # Color interpolado para animación suave
        current_color = []
        for i in range(3):
            current_color.append(
                int(self.color[i] + (self.hover_color[i] - self.color[i]) * self.hover_progress)
            )
        
        # Dibujar botón con bordes redondeados
        pygame.draw.rect(surface, current_color, self.rect, border_radius=12)
        
        # Borde del botón
        border_color = (min(255, current_color[0] + 50), 
                       min(255, current_color[1] + 50), 
                       min(255, current_color[2] + 50))
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=12)
        
        # Texto con sombra
        text_surf = font.render(self.text, True, self.text_color)
        text_shadow = font.render(self.text, True, (0, 0, 0, 150))
        
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow_rect = text_shadow.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
        
        surface.blit(text_shadow, shadow_rect)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                return True
        return False

class Menu:
    def __init__(self, largura=1280, altura=720):
        self.LARGURA = largura
        self.ALTURA = altura
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Bomberman - Menú Principal")
        
        # Cargar fuente o usar por defecto
        try:
            self.font_large = pygame.font.Font(None, 100)
            self.font_medium = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 36)
        except:
            self.font_large = pygame.font.SysFont('Arial', 100, bold=True)
            self.font_medium = pygame.font.SysFont('Arial', 48, bold=True)
            self.font_small = pygame.font.SysFont('Arial', 36)
        
        # Colores
        self.colors = {
            'background': (10, 20, 40),
            'title_gradient_start': (255, 100, 0),
            'title_gradient_end': (255, 200, 0),
            'button_normal': (30, 60, 120),
            'button_hover': (50, 100, 200),
            'button_multi_normal': (120, 30, 150),
            'button_multi_hover': (180, 50, 220),
            'button_exit_normal': (150, 30, 30),
            'button_exit_hover': (200, 50, 50),
            'text': (255, 255, 255),
            'particles': (100, 150, 255)
        }
        
        # Botones
        button_width = 400
        button_height = 70
        button_x = self.LARGURA // 2 - button_width // 2
        
        self.botones = {
            'single': Button(button_x, 300, button_width, button_height,
                           "UN JUGADOR", 
                           self.colors['button_normal'], 
                           self.colors['button_hover']),
            
            'multi': Button(button_x, 390, button_width, button_height,
                          "MULTIJUGADOR", 
                          self.colors['button_multi_normal'], 
                          self.colors['button_multi_hover']),
            
            'exit': Button(button_x, 480, button_width, button_height,
                         "SALIR", 
                         self.colors['button_exit_normal'], 
                         self.colors['button_exit_hover'])
        }
        
        # Partículas para el fondo
        self.particles = [Particle(self.LARGURA, self.ALTURA) for _ in range(30)]
        
        # Animación del título
        self.title_offset = 0
        self.title_direction = 1
        self.title_speed = 0.05
        
        # Efecto de parpadeo para instrucciones
        self.blink_timer = 0
        self.blink_visible = True
        
        # Logo/Banner (puedes reemplazar con una imagen si tienes)
        self.logo_size = 150
        self.logo_rotation = 0
        
    def draw_background(self):
        """Dibuja el fondo con gradiente"""
        # Gradiente vertical azul
        for y in range(self.ALTURA):
            # Color que va de oscuro a más claro
            r = int(10 + (y / self.ALTURA) * 15)
            g = int(20 + (y / self.ALTURA) * 30)
            b = int(40 + (y / self.ALTURA) * 60)
            pygame.draw.line(self.JANELA, (r, g, b), (0, y), (self.LARGURA, y))
        
        # Patrón de cuadrícula sutil
        grid_color = (20, 40, 80, 50)
        grid_size = 60
        
        for x in range(0, self.LARGURA, grid_size):
            pygame.draw.line(self.JANELA, grid_color, (x, 0), (x, self.ALTURA), 1)
        for y in range(0, self.ALTURA, grid_size):
            pygame.draw.line(self.JANELA, grid_color, (0, y), (self.LARGURA, y), 1)
        
        # Efecto de brillo en el centro
        center_x, center_y = self.LARGURA // 2, self.ALTURA // 2
        for i in range(200, 0, -20):
            alpha = int(30 * (i / 200))
            color = (100, 150, 255, alpha)
            surf = pygame.Surface((i * 2, i * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (i, i), i)
            self.JANELA.blit(surf, (center_x - i, center_y - i))
    
    def draw_title(self):
        """Dibuja el título con efectos"""
        title_text = "BOMBERMAN"
        
        # Efecto de flotación
        self.title_offset += self.title_speed * self.title_direction
        if abs(self.title_offset) > 5:
            self.title_direction *= -1
        
        y_offset = 100 + self.title_offset
        
        # Gradiente de color en el título
        title_width = self.font_large.size(title_text)[0]
        title_x = self.LARGURA // 2 - title_width // 2
        
        for i, letter in enumerate(title_text):
            # Color interpolado
            progress = i / (len(title_text) - 1) if len(title_text) > 1 else 0.5
            r = int(self.colors['title_gradient_start'][0] + 
                   (self.colors['title_gradient_end'][0] - self.colors['title_gradient_start'][0]) * progress)
            g = int(self.colors['title_gradient_start'][1] + 
                   (self.colors['title_gradient_end'][1] - self.colors['title_gradient_start'][1]) * progress)
            b = int(self.colors['title_gradient_start'][2] + 
                   (self.colors['title_gradient_end'][2] - self.colors['title_gradient_start'][2]) * progress)
            
            # Sombra
            shadow = self.font_large.render(letter, True, (0, 0, 0, 150))
            shadow_pos = (title_x + i * self.font_large.size("M")[0] + 3, y_offset + 3)
            self.JANELA.blit(shadow, shadow_pos)
            
            # Texto principal
            letter_surf = self.font_large.render(letter, True, (r, g, b))
            letter_pos = (title_x + i * self.font_large.size("M")[0], y_offset)
            self.JANELA.blit(letter_surf, letter_pos)
            
            # Efecto de brillo en algunas letras
            if i % 2 == 0:
                glow = pygame.Surface((letter_surf.get_width() + 4, letter_surf.get_height() + 4), pygame.SRCALPHA)
                glow.fill((r, g, b, 30))
                self.JANELA.blit(glow, (letter_pos[0] - 2, letter_pos[1] - 2))
        
        # Subtítulo
        subtitle = "CLÁSICO"
        subtitle_surf = self.font_medium.render(subtitle, True, (200, 200, 255))
        subtitle_rect = subtitle_surf.get_rect(center=(self.LARGURA // 2, y_offset + 80))
        
        # Fondo para subtítulo
        subtitle_bg = pygame.Surface((subtitle_rect.width + 40, subtitle_rect.height + 20), pygame.SRCALPHA)
        subtitle_bg.fill((0, 0, 0, 100))
        pygame.draw.rect(subtitle_bg, (255, 255, 255, 50), subtitle_bg.get_rect(), 2)
        
        self.JANELA.blit(subtitle_bg, (subtitle_rect.x - 20, subtitle_rect.y - 10))
        self.JANELA.blit(subtitle_surf, subtitle_rect)
    
    def draw_logo(self):
        """Dibuja un logo animado (bomba giratoria)"""
        center_x, center_y = self.LARGURA // 2, 250
        
        # Base de la bomba
        bomb_color = (50, 50, 50)
        fuse_color = (255, 100, 0)
        
        # Rotación
        self.logo_rotation = (self.logo_rotation + 0.5) % 360
        
        # Crear superficie para la bomba
        bomb_surf = pygame.Surface((self.logo_size, self.logo_size), pygame.SRCALPHA)
        
        # Cuerpo de la bomba
        pygame.draw.circle(bomb_surf, bomb_color, 
                          (self.logo_size // 2, self.logo_size // 2), 
                          self.logo_size // 3)
        
        # Mechón (que gira)
        fuse_length = self.logo_size // 3
        fuse_end_x = self.logo_size // 2 + int(math.cos(math.radians(self.logo_rotation)) * fuse_length)
        fuse_end_y = self.logo_size // 2 + int(math.sin(math.radians(self.logo_rotation)) * fuse_length)
        
        pygame.draw.line(bomb_surf, fuse_color,
                        (self.logo_size // 2, self.logo_size // 2),
                        (fuse_end_x, fuse_end_y), 5)
        
        # Punto en el extremo del mechón
        pygame.draw.circle(bomb_surf, (255, 200, 0), (fuse_end_x, fuse_end_y), 8)
        
        # Efecto de brillo
        glow = pygame.Surface((self.logo_size + 20, self.logo_size + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 150, 0, 50), 
                          (self.logo_size // 2 + 10, self.logo_size // 2 + 10), 
                          self.logo_size // 3 + 10)
        
        self.JANELA.blit(glow, (center_x - self.logo_size // 2 - 10, center_y - self.logo_size // 2 - 10))
        self.JANELA.blit(bomb_surf, (center_x - self.logo_size // 2, center_y - self.logo_size // 2))
    
    def draw_instructions(self):
        """Dibuja las instrucciones en la parte inferior"""
        self.blink_timer += 1
        if self.blink_timer >= 60:  # Parpadeo cada segundo
            self.blink_timer = 0
            self.blink_visible = not self.blink_visible
        
        if self.blink_visible:
            instructions = [
                "ENTER: Un jugador   |   M: Multijugador   |   ESC: Salir",
                "Usa el ratón o las teclas para navegar"
            ]
            
            for i, text in enumerate(instructions):
                color = (200, 200, 200) if i == 0 else (150, 150, 200)
                font = self.font_small if i == 0 else pygame.font.Font(None, 28)
                
                text_surf = font.render(text, True, color)
                text_rect = text_surf.get_rect(center=(self.LARGURA // 2, self.ALTURA - 40 + i * 30))
                
                # Fondo semitransparente
                bg_width = text_rect.width + 40
                bg_height = text_rect.height + 10
                bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
                bg_surf.fill((0, 0, 0, 100))
                
                self.JANELA.blit(bg_surf, (text_rect.x - 20, text_rect.y - 5))
                self.JANELA.blit(text_surf, text_rect)
    
    def draw_particles(self):
        """Dibuja y actualiza las partículas"""
        for particle in self.particles:
            particle.update()
            particle.draw(self.JANELA)
    
    def draw_version_info(self):
        """Dibuja información de versión"""
        version = "v1.0"
        author = "Desarrollado con PyGame"
        
        version_surf = pygame.font.Font(None, 24).render(version, True, (150, 150, 200))
        author_surf = pygame.font.Font(None, 20).render(author, True, (100, 150, 200))
        
        self.JANELA.blit(version_surf, (self.LARGURA - 80, 20))
        self.JANELA.blit(author_surf, (20, self.ALTURA - 30))
    
    def desenhar(self):
        """Dibuja todo el menú"""
        # 1. Fondo
        self.draw_background()
        
        # 2. Partículas
        self.draw_particles()
        
        # 3. Logo animado
        self.draw_logo()
        
        # 4. Título
        self.draw_title()
        
        # 5. Botones
        mouse_pos = pygame.mouse.get_pos()
        for boton in self.botones.values():
            boton.update(mouse_pos)
            boton.draw(self.JANELA, self.font_medium)
        
        # 6. Instrucciones (con parpadeo)
        self.draw_instructions()
        
        # 7. Info de versión
        self.draw_version_info()
        
        # 8. Efecto de brillo del cursor
        if pygame.mouse.get_focused():
            cursor_radius = 15
            cursor_pos = pygame.mouse.get_pos()
            
            for i in range(3, 0, -1):
                alpha = 100 - i * 30
                size = cursor_radius + i * 3
                cursor_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(cursor_surf, (255, 255, 255, alpha), 
                                 (size, size), size)
                self.JANELA.blit(cursor_surf, (cursor_pos[0] - size, cursor_pos[1] - size))
        
        pygame.display.update()
    
    def executar(self):
        """Ejecuta el loop principal del menú"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Click en botones
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.botones['single'].is_clicked(event):
                        print("Iniciando modo un jugador...")
                        return "single"
                    elif self.botones['multi'].is_clicked(event):
                        print("Iniciando modo multijugador...")
                        return "multi"
                    elif self.botones['exit'].is_clicked(event):
                        pygame.quit()
                        sys.exit()
                
                # Teclas de acceso rápido
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        return "single"
                    if event.key == pygame.K_m:
                        return "multi"
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    # Atajos numéricos
                    if event.key == pygame.K_1:
                        return "single"
                    if event.key == pygame.K_2:
                        return "multi"
            
            # Actualizar partículas cada cierto número de frames
            if pygame.time.get_ticks() % 2 == 0:
                for particle in self.particles:
                    particle.update()
            
            # Dibujar todo
            self.desenhar()
            
            # Controlar FPS
            pygame.time.Clock().tick(60)
        
        return None