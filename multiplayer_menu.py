import pygame
import sys
import random
import math
import socket

class Particle:
    """Partículas para el fondo animado"""
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
        self.hover_progress = 0
        
    def update(self, mouse_pos):
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Animación suave de hover
        if self.is_hovered and self.hover_progress < 1.0:
            self.hover_progress = min(1.0, self.hover_progress + 0.15)
        elif not self.is_hovered and self.hover_progress > 0:
            self.hover_progress = max(0.0, self.hover_progress - 0.1)
            
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
        
        # Sombra interior
        shadow_rect = self.rect.inflate(-6, -6)
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=8)
        
        # Texto con sombra
        text_surf = font.render(self.text, True, self.text_color)
        text_shadow = font.render(self.text, True, (0, 0, 0, 150))
        
        text_rect = text_surf.get_rect(center=self.rect.center)
        shadow_rect = text_shadow.get_rect(center=(self.rect.centerx + 2, self.rect.centery + 2))
        
        surface.blit(text_shadow, shadow_rect)
        surface.blit(text_surf, text_rect)

class InputField:
    """Campo de entrada con efectos visuales"""
    def __init__(self, x, y, width, height, default_text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = default_text
        self.active = False
        self.blink_timer = 0
        self.blink_visible = True
        
        # Colores
        self.normal_color = (50, 50, 80)
        self.active_color = (70, 70, 110)
        self.border_color = (100, 100, 150)
        self.active_border_color = (150, 150, 255)
        self.text_color = (255, 255, 255)
        self.placeholder_color = (150, 150, 180)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activar/desactivar campo
            self.active = self.rect.collidepoint(event.pos)
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True  # Enter presionado
            elif event.key == pygame.K_TAB:
                return "TAB"  # Cambiar campo
            elif event.key == pygame.K_ESCAPE:
                self.active = False
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                # Pegar desde portapapeles
                try:
                    import pyperclip
                    clipboard_text = pyperclip.paste()
                    # Filtrar solo caracteres válidos para IP
                    valid_chars = "0123456789."
                    filtered_text = ''.join(c for c in clipboard_text if c in valid_chars)
                    self.text += filtered_text
                except:
                    pass
            else:
                # Solo permitir caracteres válidos para IP
                if event.unicode.isdigit() or event.unicode == '.':
                    # Verificar que no exceda el formato máximo
                    if len(self.text) < 15:
                        # Verificar formato básico de IP
                        if event.unicode == '.':
                            partes = self.text.split('.')
                            if len(partes) < 4:  # Máximo 3 puntos
                                self.text += event.unicode
                        else:
                            self.text += event.unicode
        return False
    
    def update(self):
        """Actualiza el parpadeo del cursor"""
        self.blink_timer += 1
        if self.blink_timer >= 30:  # Parpadeo cada medio segundo
            self.blink_timer = 0
            self.blink_visible = not self.blink_visible
    
    def draw(self, surface, font):
        # Color de fondo
        bg_color = self.active_color if self.active else self.normal_color
        border_color = self.active_border_color if self.active else self.border_color
        
        # Fondo del campo
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=8)
        
        # Texto
        if self.text or self.active:
            text_color = self.text_color
            display_text = self.text
        else:
            text_color = self.placeholder_color
            display_text = "Ej: 192.168.1.100"
        
        # Renderizar texto con recorte si es muy largo
        text_surf = font.render(display_text, True, text_color)
        
        # Si el texto es muy ancho, recortarlo
        if text_surf.get_width() > self.rect.width - 20:
            # Crear una superficie para recortar
            clip_surf = pygame.Surface((self.rect.width - 20, self.rect.height - 10))
            clip_surf.fill(bg_color)
            clip_surf.blit(text_surf, (0, 0))
            
            # Dibujar puntos suspensivos si está recortado
            dots = font.render("...", True, text_color)
            clip_surf.blit(dots, (self.rect.width - 40, 0))
            
            surface.blit(clip_surf, (self.rect.x + 10, self.rect.y + 5))
        else:
            text_rect = text_surf.get_rect(midleft=(self.rect.x + 15, self.rect.centery))
            surface.blit(text_surf, text_rect)
        
        # Cursor parpadeante si está activo
        if self.active and self.blink_visible:
            cursor_x = self.rect.x + 15 + text_surf.get_width()
            if cursor_x > self.rect.right - 15:
                cursor_x = self.rect.right - 15
            
            pygame.draw.line(surface, self.text_color,
                           (cursor_x, self.rect.y + 10),
                           (cursor_x, self.rect.y + self.rect.height - 10), 2)

class MultiplayerMenu:
    def __init__(self, largura=1280, altura=720):
        self.LARGURA = largura
        self.ALTURA = altura
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Bomberman - Multijugador")
        
        # Cargar fuentes
        try:
            self.font_large = pygame.font.Font(None, 80)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_small = pygame.font.Font(None, 28)
        except:
            self.font_large = pygame.font.SysFont('Arial', 80, bold=True)
            self.font_medium = pygame.font.SysFont('Arial', 36, bold=True)
            self.font_small = pygame.font.SysFont('Arial', 28)
        
        # Colores
        self.colors = {
            'background': (20, 30, 50),
            'title_gradient_start': (100, 150, 255),
            'title_gradient_end': (150, 200, 255),
            'panel_bg': (30, 40, 70, 220),
            'panel_border': (80, 120, 200),
            'button_host_normal': (40, 100, 40),
            'button_host_hover': (60, 160, 60),
            'button_client_normal': (40, 60, 120),
            'button_client_hover': (60, 100, 200),
            'button_back_normal': (120, 40, 40),
            'button_back_hover': (180, 60, 60),
            'text': (255, 255, 255),
            'text_highlight': (255, 255, 150),
            'text_dim': (180, 180, 220)
        }
        
        # Botones
        button_width = 350
        button_height = 60
        panel_x = self.LARGURA // 2 - 200
        
        self.botones = {
            'host': Button(panel_x, 300, button_width, button_height,
                         "CREAR PARTIDA (Host)",
                         self.colors['button_host_normal'],
                         self.colors['button_host_hover']),
            
            'client': Button(panel_x, 370, button_width, button_height,
                           "UNIRSE A PARTIDA",
                           self.colors['button_client_normal'],
                           self.colors['button_client_hover']),
            
            'back': Button(panel_x, 440, button_width, button_height,
                         "VOLVER AL MENÚ",
                         self.colors['button_back_normal'],
                         self.colors['button_back_hover'])
        }
        
        # Campo de entrada para IP
        self.input_ip = InputField(panel_x, 250, button_width, 40, "127.0.0.1")
        
        # Partículas para el fondo
        self.particles = [Particle(self.LARGURA, self.ALTURA) for _ in range(40)]
        
        # Animaciones
        self.title_offset = 0
        self.title_direction = 1
        self.title_speed = 0.04
        
        # Información de red
        self.network_info = self.get_network_info()
        
        # Estado
        self.active_field = 'input_ip'
        self.selected_button = None
        self.connection_animation = 0
        self.show_network_info = False
        
    def get_network_info(self):
        """Obtiene información de red del sistema"""
        info = {
            'local_ip': '127.0.0.1',
            'public_ip': 'No disponible',
            'hostname': 'localhost'
        }
        
        try:
            # Obtener IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info['local_ip'] = s.getsockname()[0]
            s.close()
            
            # Obtener nombre de host
            info['hostname'] = socket.gethostname()
            
        except:
            pass
            
        return info
    
    def draw_background(self):
        """Dibuja el fondo con gradiente y efectos"""
        # Gradiente vertical
        for y in range(self.ALTURA):
            # Color que va de oscuro a más claro
            r = int(15 + (y / self.ALTURA) * 20)
            g = int(25 + (y / self.ALTURA) * 30)
            b = int(40 + (y / self.ALTURA) * 50)
            pygame.draw.line(self.JANELA, (r, g, b), (0, y), (self.LARGURA, y))
        
        # Líneas de conexión animadas
        self.connection_animation += 0.02
        line_color = (50, 100, 200, 80)
        
        for i in range(10):
            y_offset = i * 80 + (self.connection_animation * 20) % 80
            start_x = 0
            end_x = self.LARGURA
            
            # Crear línea con gradiente de transparencia
            line_surf = pygame.Surface((self.LARGURA, 2), pygame.SRCALPHA)
            for x in range(self.LARGURA):
                alpha = int(80 * (0.5 + 0.5 * math.sin(x / 50 + self.connection_animation)))
                color = (*line_color[:3], alpha)
                pygame.draw.line(line_surf, color, (x, 0), (x, 2))
            
            self.JANELA.blit(line_surf, (0, y_offset))
    
    def draw_title(self):
        """Dibuja el título con efectos"""
        title_text = "MULTIJUGADOR"
        
        # Efecto de flotación
        self.title_offset += self.title_speed * self.title_direction
        if abs(self.title_offset) > 4:
            self.title_direction *= -1
        
        y_offset = 80 + self.title_offset
        
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
            
            # Efecto de conexión en algunas letras
            if i % 2 == 0:
                glow = pygame.Surface((letter_surf.get_width() + 4, letter_surf.get_height() + 4), pygame.SRCALPHA)
                glow.fill((r, g, b, 30))
                self.JANELA.blit(glow, (letter_pos[0] - 2, letter_pos[1] - 2))
    
    def draw_main_panel(self):
        """Dibuja el panel principal con opciones"""
        panel_width = 500
        panel_height = 400
        panel_x = self.LARGURA // 2 - panel_width // 2
        panel_y = 150
        
        # Panel principal
        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surf.fill(self.colors['panel_bg'])
        pygame.draw.rect(panel_surf, self.colors['panel_border'], 
                        panel_surf.get_rect(), 4, border_radius=15)
        
        # Efecto de brillo en el borde
        for i in range(3):
            border_rect = pygame.Rect(i, i, panel_width - 2*i, panel_height - 2*i)
            alpha = 30 - i * 10
            pygame.draw.rect(panel_surf, (255, 255, 255, alpha), border_rect, 2, border_radius=15-i)
        
        self.JANELA.blit(panel_surf, (panel_x, panel_y))
        
        # Título del panel
        panel_title = "CONFIGURACIÓN DE RED"
        title_surf = self.font_medium.render(panel_title, True, self.colors['text_highlight'])
        title_rect = title_surf.get_rect(center=(self.LARGURA // 2, panel_y + 30))
        self.JANELA.blit(title_surf, title_rect)
        
        # Etiqueta para campo IP
        label = self.font_small.render("IP DEL HOST:", True, self.colors['text'])
        label_rect = label.get_rect(midright=(panel_x + 170, panel_y + 95))
        self.JANELA.blit(label, label_rect)
        
        # Campo de entrada
        self.input_ip.update()
        self.input_ip.draw(self.JANELA, self.font_medium)
        
        # Dibujar botones
        mouse_pos = pygame.mouse.get_pos()
        for boton in self.botones.values():
            boton.update(mouse_pos)
            boton.draw(self.JANELA, self.font_medium)
    
    def draw_network_status(self):
        """Dibuja el estado de la red en la esquina superior derecha"""
        status_x = self.LARGURA - 250
        status_y = 20
        
        # Panel de estado
        status_panel = pygame.Surface((230, 100), pygame.SRCALPHA)
        status_panel.fill((0, 0, 0, 150))
        pygame.draw.rect(status_panel, (50, 100, 200), status_panel.get_rect(), 2, border_radius=8)
        
        self.JANELA.blit(status_panel, (status_x, status_y))
        
        # Título del estado
        status_title = self.font_small.render("ESTADO DE RED", True, (180, 220, 255))
        self.JANELA.blit(status_title, (status_x + 10, status_y + 10))
        
        # IP local
        ip_text = pygame.font.Font(None, 20).render(f"IP Local: {self.network_info['local_ip']}", 
                                                   True, (200, 200, 200))
        self.JANELA.blit(ip_text, (status_x + 10, status_y + 40))
        
        # Nombre de host
        host_text = pygame.font.Font(None, 20).render(f"Host: {self.network_info['hostname']}", 
                                                     True, (200, 200, 200))
        self.JANELA.blit(host_text, (status_x + 10, status_y + 65))
    
    def draw_particles(self):
        """Dibuja y actualiza las partículas"""
        for particle in self.particles:
            particle.update()
            particle.draw(self.JANELA)
    
    def draw_instructions(self):
        """Dibuja las instrucciones en la parte inferior"""
        instructions = [
            "ENTER: Crear/Unirse  |  TAB: Cambiar campo  |  ESC: Volver",
            "CTRL+V: Pegar IP  |  F1: Mostrar ayuda de red"
        ]
        
        for i, text in enumerate(instructions):
            color = (200, 200, 255) if i == 0 else (150, 150, 200)
            font = self.font_small if i == 0 else pygame.font.Font(None, 24)
            
            text_surf = font.render(text, True, color)
            text_rect = text_surf.get_rect(center=(self.LARGURA // 2, self.ALTURA - 40 + i * 30))
            
            # Fondo semitransparente
            bg_width = text_rect.width + 40
            bg_height = text_rect.height + 10
            bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 100))
            
            self.JANELA.blit(bg_surf, (text_rect.x - 20, text_rect.y - 5))
            self.JANELA.blit(text_surf, text_rect)
    
    def draw_connection_visualization(self):
        """Dibuja una visualización de conexión entre hosts"""
        center_x = self.LARGURA // 2
        center_y = self.ALTURA // 2 - 50
        
        # Nodos de conexión
        node_radius = 20
        node_spacing = 150
        
        # Nodo izquierdo (Host)
        left_node = (center_x - node_spacing, center_y)
        pygame.draw.circle(self.JANELA, (60, 180, 60), left_node, node_radius)
        pygame.draw.circle(self.JANELA, (100, 255, 100), left_node, node_radius - 5)
        
        # Nodo derecho (Cliente)
        right_node = (center_x + node_spacing, center_y)
        pygame.draw.circle(self.JANELA, (60, 100, 200), right_node, node_radius)
        pygame.draw.circle(self.JANELA, (100, 150, 255), right_node, node_radius - 5)
        
        # Etiquetas
        host_label = self.font_small.render("HOST", True, (100, 255, 100))
        client_label = self.font_small.render("CLIENTE", True, (100, 150, 255))
        
        self.JANELA.blit(host_label, (left_node[0] - 30, left_node[1] + 30))
        self.JANELA.blit(client_label, (right_node[0] - 40, right_node[1] + 30))
        
        # Línea de conexión animada
        line_progress = (math.sin(self.connection_animation * 2) + 1) / 2
        
        # Punto que viaja por la línea
        travel_x = left_node[0] + (right_node[0] - left_node[0]) * line_progress
        travel_y = center_y
        
        # Dibujar línea
        pygame.draw.line(self.JANELA, (100, 100, 200, 100), left_node, right_node, 3)
        
        # Dibujar punto viajero
        pygame.draw.circle(self.JANELA, (255, 255, 100), (int(travel_x), int(travel_y)), 8)
        pygame.draw.circle(self.JANELA, (255, 200, 0), (int(travel_x), int(travel_y)), 5)
    
    def desenhar(self):
        """Dibuja todo el menú"""
        # 1. Fondo
        self.draw_background()
        
        # 2. Partículas
        self.draw_particles()
        
        # 3. Título
        self.draw_title()
        
        # 4. Visualización de conexión (solo decorativa)
        self.draw_connection_visualization()
        
        # 5. Panel principal
        self.draw_main_panel()
        
        # 6. Estado de red
        self.draw_network_status()
        
        # 7. Instrucciones
        self.draw_instructions()
        
        pygame.display.update()
    
    def validar_ip(self, ip):
        """Valida si la IP tiene formato válido"""
        partes = ip.split('.')
        if len(partes) != 4:
            return False
        
        for parte in partes:
            if not parte.isdigit():
                return False
            num = int(parte)
            if num < 0 or num > 255:
                return False
        
        return True
    
    def ejecutar(self):
        """Ejecuta el loop principal del menú"""
        running = True
        
        # Intentar obtener IP local automáticamente
        if self.network_info['local_ip'] != "127.0.0.1":
            self.input_ip.text = self.network_info['local_ip']
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # Manejar campo de entrada
                input_result = self.input_ip.handle_event(event)
                if input_result == True:  # Enter presionado
                    if self.validar_ip(self.input_ip.text):
                        return ("client", self.input_ip.text.strip())
                elif input_result == "TAB":  # Cambiar campo
                    self.input_ip.active = not self.input_ip.active
                
                # Click en botones
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.botones['host'].rect.collidepoint(mouse_pos):
                        print("Modo seleccionado: Host")
                        return ("host", None)
                    
                    if self.botones['client'].rect.collidepoint(mouse_pos):
                        if self.validar_ip(self.input_ip.text):
                            print(f"Conectando a: {self.input_ip.text}")
                            return ("client", self.input_ip.text.strip())
                        else:
                            print(f"IP inválida: {self.input_ip.text}")
                    
                    if self.botones['back'].rect.collidepoint(mouse_pos):
                        print("Volviendo al menú principal")
                        return ("back", None)
                
                # Teclas de acceso rápido
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return ("back", None)
                    
                    if event.key == pygame.K_TAB:
                        self.input_ip.active = not self.input_ip.active
                    
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Si el campo está activo, conectar; si no, crear host
                        if self.input_ip.active:
                            if self.validar_ip(self.input_ip.text):
                                return ("client", self.input_ip.text.strip())
                        else:
                            # Crear partida como host
                            return ("host", None)
                    
                    if event.key == pygame.K_F1:
                        self.show_network_info = not self.show_network_info
                    
                    # Atajos directos
                    if event.key == pygame.K_h:
                        return ("host", None)
                    if event.key == pygame.K_c:
                        if self.validar_ip(self.input_ip.text):
                            return ("client", self.input_ip.text.strip())
                    
                    # Atajos numéricos
                    if event.key == pygame.K_1:
                        return ("host", None)
                    if event.key == pygame.K_2:
                        if self.validar_ip(self.input_ip.text):
                            return ("client", self.input_ip.text.strip())
            
            # Actualizar animaciones
            self.connection_animation += 0.02
            
            # Dibujar todo
            self.desenhar()
            
            # Controlar FPS
            pygame.time.Clock().tick(60)
        
        return ("back", None)