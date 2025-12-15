import pygame
import sys

class MultiplayerMenu:
    def __init__(self, largura=1280, altura=720):
        self.LARGURA = largura
        self.ALTURA = altura
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Bomberman - Multijugador")
        
        # Cores
        self.COR_FUNDO = (30, 30, 60)
        self.COR_TITULO = (255, 255, 0)
        self.COR_TEXTO = (255, 255, 255)
        self.COR_BOTAO = (0, 120, 0)
        self.COR_BOTAO_HOVER = (0, 180, 0)
        self.COR_INPUT = (50, 50, 80)
        self.COR_INPUT_ATIVO = (70, 70, 100)
        
        # Fontes
        self.fonte_titulo = pygame.font.Font(None, 80)
        self.fonte_texto = pygame.font.Font(None, 36)
        self.fonte_pequena = pygame.font.Font(None, 28)
        
        # Botões
        self.botao_host = pygame.Rect(self.LARGURA // 2 - 150, self.ALTURA // 2 - 100, 300, 50)
        self.botao_cliente = pygame.Rect(self.LARGURA // 2 - 150, self.ALTURA // 2 - 30, 300, 50)
        self.botao_voltar = pygame.Rect(self.LARGURA // 2 - 150, self.ALTURA // 2 + 100, 300, 50)
        
        # Input IP
        self.input_ip = "127.0.0.1"  # Default para pruebas locales
        self.input_ip_rect = pygame.Rect(self.LARGURA // 2 - 150, self.ALTURA // 2 + 40, 300, 40)
        self.input_ativo = False
        
        # Instrucciones
        self.instrucciones = [
            "HOST: Crea una partida para que otros se unan",
            "CLIENTE: Únete a una partida existente",
            "Para LAN: Usa la IP local del host (ej: 192.168.1.100)",
            "Para pruebas locales: Usa 127.0.0.1"
        ]
    
    def desenhar(self):
        """Desenha o menu na tela"""
        # Fundo
        self.JANELA.fill(self.COR_FUNDO)
        
        # Título
        titulo = self.fonte_titulo.render("Multijugador", True, self.COR_TITULO)
        titulo_rect = titulo.get_rect(center=(self.LARGURA // 2, self.ALTURA // 4 - 30))
        self.JANELA.blit(titulo, titulo_rect)
        
        # Instrucciones
        for i, instruccion in enumerate(self.instrucciones):
            texto = self.fonte_pequena.render(instruccion, True, (200, 200, 255))
            texto_rect = texto.get_rect(center=(self.LARGURA // 2, self.ALTURA // 4 + 20 + i * 25))
            self.JANELA.blit(texto, texto_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Botão Host
        cor_botao_host = self.COR_BOTAO_HOVER if self.botao_host.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_host, self.botao_host, border_radius=10)
        texto_host = self.fonte_texto.render("CREAR PARTIDA (Host)", True, self.COR_TEXTO)
        texto_host_rect = texto_host.get_rect(center=self.botao_host.center)
        self.JANELA.blit(texto_host, texto_host_rect)
        
        # Botão Cliente
        cor_botao_cliente = self.COR_BOTAO_HOVER if self.botao_cliente.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_cliente, self.botao_cliente, border_radius=10)
        texto_cliente = self.fonte_texto.render("UNIRSE A PARTIDA", True, self.COR_TEXTO)
        texto_cliente_rect = texto_cliente.get_rect(center=self.botao_cliente.center)
        self.JANELA.blit(texto_cliente, texto_cliente_rect)
        
        # Label para input IP
        label_ip = self.fonte_pequena.render("IP del Host:", True, (200, 200, 255))
        label_ip_rect = label_ip.get_rect(midright=(self.input_ip_rect.left - 10, self.input_ip_rect.centery))
        self.JANELA.blit(label_ip, label_ip_rect)
        
        # Input IP
        cor_input = self.COR_INPUT_ATIVO if self.input_ativo else self.COR_INPUT
        pygame.draw.rect(self.JANELA, cor_input, self.input_ip_rect, border_radius=5)
        pygame.draw.rect(self.JANELA, (100, 100, 255) if self.input_ativo else (80, 80, 100), 
                        self.input_ip_rect, 2, border_radius=5)
        
        # Texto del input IP
        texto_ip = self.fonte_texto.render(self.input_ip, True, self.COR_TEXTO)
        
        # Si el texto es muy largo, ajustarlo
        if texto_ip.get_width() > self.input_ip_rect.width - 20:
            # Mostrar con "..." al final
            texto_surface = pygame.Surface((self.input_ip_rect.width - 20, self.input_ip_rect.height - 10), pygame.SRCALPHA)
            texto_surface.blit(texto_ip, (0, 0))
            # Cortar el texto
            clip_rect = pygame.Rect(texto_surface.get_width() - 100, 0, 100, texto_surface.get_height())
            texto_surface.set_clip(clip_rect)
            pygame.draw.rect(texto_surface, (0, 0, 0, 0), clip_rect)
            texto_surface.blit(texto_ip, (0, 0))
            
            # Agregar "..."
            puntos = self.fonte_texto.render("...", True, self.COR_TEXTO)
            texto_surface.blit(puntos, (texto_surface.get_width() - 30, 5))
            
            self.JANELA.blit(texto_surface, (self.input_ip_rect.x + 10, self.input_ip_rect.y + 5))
        else:
            texto_ip_rect = texto_ip.get_rect(center=self.input_ip_rect.center)
            self.JANELA.blit(texto_ip, texto_ip_rect)
        
        # Cursor parpadeante si está activo
        if self.input_ativo:
            tiempo_actual = pygame.time.get_ticks()
            if (tiempo_actual // 500) % 2 == 0:  # Parpadeo cada 500ms
                cursor_x = self.input_ip_rect.x + 10 + texto_ip.get_width()
                if cursor_x > self.input_ip_rect.x + self.input_ip_rect.width - 10:
                    cursor_x = self.input_ip_rect.x + self.input_ip_rect.width - 10
                
                pygame.draw.line(self.JANELA, self.COR_TEXTO, 
                                (cursor_x, self.input_ip_rect.y + 10),
                                (cursor_x, self.input_ip_rect.y + self.input_ip_rect.height - 10), 2)
        
        # Botão Voltar
        cor_botao_voltar = self.COR_BOTAO_HOVER if self.botao_voltar.collidepoint(mouse_pos) else self.COR_BOTAO
        pygame.draw.rect(self.JANELA, cor_botao_voltar, self.botao_voltar, border_radius=10)
        texto_voltar = self.fonte_texto.render("VOLVER AL MENÚ", True, self.COR_TEXTO)
        texto_voltar_rect = texto_voltar.get_rect(center=self.botao_voltar.center)
        self.JANELA.blit(texto_voltar, texto_voltar_rect)
        
        # Instrucciones de teclado
        instrucciones_teclado = [
            "ENTER: Crear partida (Host)",
            "ESC: Volver al menú principal",
            "TAB: Cambiar entre campos"
        ]
        
        for i, instruccion in enumerate(instrucciones_teclado):
            texto_inst = self.fonte_pequena.render(instruccion, True, (150, 150, 200))
            texto_inst_rect = texto_inst.get_rect(center=(self.LARGURA // 2, self.ALTURA - 60 + i * 25))
            self.JANELA.blit(texto_inst, texto_inst_rect)
        
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
    
    def obtener_ip_local(self):
        """Intenta obtener la IP local automáticamente"""
        try:
            import socket
            # Obtener nombre de host
            hostname = socket.gethostname()
            # Obtener IP local
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except:
            return "127.0.0.1"
    
    def ejecutar(self):
        """Executa o loop principal do menu"""
        running = True
        
        # Intentar obtener IP local automáticamente
        ip_local = self.obtener_ip_local()
        if ip_local != "127.0.0.1":
            # Sugerir la IP local si no es localhost
            self.input_ip = ip_local
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Verifica clique nos botões
                    if self.botao_host.collidepoint(mouse_pos):
                        print("🎮 Modo seleccionado: Host")
                        return ("host", None)
                    
                    if self.botao_cliente.collidepoint(mouse_pos):
                        if self.validar_ip(self.input_ip):
                            print(f"🎮 Conectando a: {self.input_ip}")
                            return ("client", self.input_ip.strip())
                        else:
                            print(f"❌ IP inválida: {self.input_ip}")
                            # Podrías mostrar un mensaje de error aquí
                    
                    if self.botao_voltar.collidepoint(mouse_pos):
                        print("↩️ Volviendo al menú principal")
                        return ("back", None)
                    
                    # Ativar/desativar input
                    if self.input_ip_rect.collidepoint(mouse_pos):
                        self.input_ativo = True
                    else:
                        self.input_ativo = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return ("back", None)
                    
                    if event.key == pygame.K_TAB:
                        # Cambiar entre campos con TAB
                        self.input_ativo = not self.input_ativo
                    
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # ENTER: si el input está activo, conectar; si no, crear host
                        if self.input_ativo:
                            if self.validar_ip(self.input_ip):
                                return ("client", self.input_ip.strip())
                        else:
                            # Crear partida como host
                            return ("host", None)
                    
                    elif self.input_ativo:
                        if event.key == pygame.K_BACKSPACE:
                            self.input_ip = self.input_ip[:-1]
                        elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            # Pegar desde portapapeles
                            try:
                                import pyperclip
                                clipboard_text = pyperclip.paste()
                                # Filtrar solo caracteres válidos para IP
                                valid_chars = "0123456789."
                                filtered_text = ''.join(c for c in clipboard_text if c in valid_chars)
                                if filtered_text:
                                    self.input_ip += filtered_text
                            except:
                                # Si no hay pyperclip, ignorar
                                pass
                        elif event.key == pygame.K_c and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            # Copiar al portapapeles
                            try:
                                import pyperclip
                                pyperclip.copy(self.input_ip)
                            except:
                                pass
                        else:
                            # Solo permitir caracteres válidos para IP
                            if event.unicode.isdigit() or event.unicode == '.':
                                # Verificar que no exceda el formato máximo (15 caracteres para IPv4)
                                if len(self.input_ip) < 15:
                                    # Verificar formato básico de IP
                                    if event.unicode == '.':
                                        partes = self.input_ip.split('.')
                                        if len(partes) >= 4:
                                            # Ya tiene 3 puntos, no agregar más
                                            pass
                                        else:
                                            self.input_ip += event.unicode
                                    else:
                                        self.input_ip += event.unicode
                    
                    else:  # Si el input no está activo
                        if event.key == pygame.K_h:
                            # Atajo para host
                            return ("host", None)
                        elif event.key == pygame.K_c:
                            # Atajo para cliente
                            if self.validar_ip(self.input_ip):
                                return ("client", self.input_ip.strip())
            
            self.desenhar()
            pygame.time.Clock().tick(60)
        
        return ("back", None)