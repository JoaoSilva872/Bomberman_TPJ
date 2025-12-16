import pygame
import sys
import time
import random
from map import Map
from player import Player
from object import Object
from bomba import Bomba
from powerup import PowerUpSystem, PowerUpType
from enemy import Enemy
from exit_point import ExitPoint

class Game:
    def __init__(self):
        # Configurações da janela
        self.LARGURA = 1260
        self.ALTURA = 720
        self.JANELA = pygame.display.set_mode((self.LARGURA, self.ALTURA))
        pygame.display.set_caption("Protótipo Bomber - Nivel 1")
        
        # Configurações do tabuleiro
        self.TILE_SIZE = 20
        self.COR_CLARA = (0, 140, 0)
        self.COR_ESCURA = (0, 120, 0)
        
        # Configurações do jogador
        self.PLAYER_TILES = 3
        self.player_size = self.TILE_SIZE * self.PLAYER_TILES
        self.player_vel = self.TILE_SIZE * 1.5
        
        # NUEVO: Sistema de niveles
        self.niveles = ["level1", "level2"]  # Puedes añadir más niveles
        self.nivel_actual = 0
        self.num_enemigos_base = 3  # Enemigos base por nivel
        self.enemigos_extra_por_nivel = 1  # Enemigos extra que se añaden por nivel
        
        # Inicializar componentes (se reinician en iniciar_nivel)
        self.mapa = Map(self.LARGURA, self.ALTURA, self.TILE_SIZE, self.COR_CLARA, self.COR_ESCURA)
        self.jugador = Player(self.LARGURA, self.ALTURA, self.player_size, self.player_vel, id=0)
        self.jugador.life_max = 3
        self.jugador.life = 3
        self.bombas = []
        
        # Sistema de power-ups
        self.powerup_system = PowerUpSystem(probabilidad_spawn=0.35)
        
        # NUEVO: Enemigos y punto de salida
        self.enemigos = []
        self.enemigos_eliminados = 0
        self.exit_point = None
        self.nivel_completado = False
        
        # Iniciar primer nivel
        self.iniciar_nivel()
        
        # Controladores de tempo
        self.move_cooldown = 200  # Tiempo entre movimientos en ms
        self.last_move_time = pygame.time.get_ticks()
        self.clock = pygame.time.Clock()
        self.tiempo_inicio = pygame.time.get_ticks()
        
        # Control de teclas
        self.bomba_presionada = False
        self.tecla_r_presionada = False
        
        # Control de teclas para evitar movimiento continuo
        self.key_pressed = {
            'up': False,
            'down': False,
            'left': False,
            'right': False
        }

    def iniciar_nivel(self):
        """Inicia un nuevo nivel"""
        print(f"\n=== NIVEL {self.nivel_actual + 1} ===")
        
        # Limpiar elementos del nivel anterior
        self.bombas.clear()
        self.enemigos.clear()
        self.enemigos_eliminados = 0
        self.powerup_system.limpiar()
        Object.objects.clear()  # Limpiar objetos anteriores
        
        # Actualizar título
        pygame.display.set_caption(f"Bomberman - Nivel {self.nivel_actual + 1}")
        
        # Cargar mapa del nivel actual
        if self.nivel_actual < len(self.niveles):
            nivel = self.niveles[self.nivel_actual]
            self.mapa.crear_obstaculos(nivel)
        else:
            # Si no hay más niveles, repetir el último
            nivel = self.niveles[-1]
            self.mapa.crear_obstaculos(nivel)
        
        # Colocar jugador en posición inicial (esquina superior izquierda)
        self.jugador.x = 60
        self.jugador.y = 60
        self.jugador.bomba_colocada = False
        self.jugador.bomba_actual = None
        self.jugador.bombas_colocadas_actual = 0
        
        # Crear enemigos (número fijo por nivel)
        self.crear_enemigos()
        
        # Crear punto de salida
        self.crear_punto_salida()
        
        # Resetear estado del nivel
        self.nivel_completado = False
        
        print(f"Mapa: {nivel}")
        print(f"Enemigos: {len(self.enemigos)}")
        print(f"¡Comienza el nivel {self.nivel_actual + 1}!")

    def crear_enemigos(self):
        """Crea un número fijo de enemigos por nivel"""
        # Calcular número de enemigos para este nivel
        num_enemigos = self.num_enemigos_base + (self.nivel_actual * self.enemigos_extra_por_nivel)
        num_enemigos = min(num_enemigos, 8)  # Máximo 8 enemigos
        
        for _ in range(num_enemigos):
            self.spawn_enemigo_aleatorio()
    
    def spawn_enemigo_aleatorio(self):
        """Crea un enemigo en una posición aleatoria válida"""
        intentos = 0
        while intentos < 100:
            # Generar posición aleatoria en la cuadrícula
            grid_x = random.randint(0, (self.LARGURA // self.player_size) - 1) * self.player_size
            grid_y = random.randint(0, (self.ALTURA // self.player_size) - 1) * self.player_size
            
            # Verificar que no esté en la posición del jugador
            if abs(grid_x - self.jugador.x) < self.player_size * 2 and abs(grid_y - self.jugador.y) < self.player_size * 2:
                intentos += 1
                continue
            
            # Verificar que no colisione con objetos no destruidos
            enemigo_rect = pygame.Rect(grid_x, grid_y, self.player_size, self.player_size)
            colision = False
            
            for obj in Object.objects:
                if not obj.destruido and enemigo_rect.colliderect(obj.rect):
                    colision = True
                    break
            
            if not colision:
                # Crear enemigo con vida progresiva (más difícil cada nivel)
                vida_base = 1
                vida_extra = min(self.nivel_actual // 2, 2)  # Máximo +2 de vida
                vida = vida_base + vida_extra
                
                # Velocidad progresiva
                velocidad_base = 1.0
                velocidad_extra = min(self.nivel_actual * 0.2, 1.0)  # Máximo +1.0 de velocidad
                velocidad = velocidad_base + velocidad_extra
                
                enemigo = Enemy(grid_x, grid_y, self.player_size, velocidad, vida)
                self.enemigos.append(enemigo)
                print(f"👾 Enemigo nivel {self.nivel_actual + 1} apareció en ({grid_x}, {grid_y}) - Vida: {vida}")
                break
            
            intentos += 1
    
    def crear_punto_salida(self):
        """Crea el punto de salida en una posición fija (esquina inferior derecha)"""
        # Posición fija en esquina inferior derecha
        grid_x = self.LARGURA - self.player_size * 2
        grid_y = self.ALTURA - self.player_size * 2
        
        # Verificar que no colisione con objetos
        exit_rect = pygame.Rect(grid_x, grid_y, self.player_size, self.player_size)
        colision = False
        
        for obj in Object.objects:
            if not obj.destruido and exit_rect.colliderect(obj.rect):
                colision = True
                break
        
        if not colision:
            self.exit_point = ExitPoint(grid_x, grid_y, self.player_size)
            print(f"🚪 Punto de salida en ({grid_x}, {grid_y})")
        else:
            # Si hay colisión, buscar posición alternativa cerca
            print("⚠️ Buscando posición alternativa para la salida...")
            posiciones_posibles = [
                (self.player_size * 2, self.ALTURA - self.player_size * 2),  # Esquina inferior izquierda
                (self.LARGURA // 2 - self.player_size, self.ALTURA - self.player_size * 2),  # Centro abajo
                (self.player_size * 2, self.player_size * 2),  # Esquina superior izquierda
            ]
            
            for pos_x, pos_y in posiciones_posibles:
                exit_rect = pygame.Rect(pos_x, pos_y, self.player_size, self.player_size)
                colision = False
                
                for obj in Object.objects:
                    if not obj.destruido and exit_rect.colliderect(obj.rect):
                        colision = True
                        break
                
                if not colision:
                    self.exit_point = ExitPoint(pos_x, pos_y, self.player_size)
                    print(f"🚪 Punto de salida alternativo en ({pos_x}, {pos_y})")
                    return
            
            # Si no se encontró posición, usar la del jugador
            self.exit_point = ExitPoint(self.jugador.x, self.jugador.y, self.player_size)
            print(f"⚠️ Punto de salida en posición del jugador ({self.jugador.x}, {self.jugador.y})")

    def siguiente_nivel(self):
        """Pasa al siguiente nivel"""
        print(f"\n🎉 ¡Nivel {self.nivel_actual + 1} completado!")
        
        # Estadísticas del nivel
        enemigos_restantes = len([e for e in self.enemigos if e.activo])
        print(f"Enemigos eliminados: {self.enemigos_eliminados}")
        print(f"Enemigos restantes: {enemigos_restantes}")
        
        # Pequeña pausa para mostrar mensaje
        pygame.time.delay(1000)
        
        # Pasar al siguiente nivel
        self.nivel_actual += 1
        
        # Si hay más niveles, iniciar el siguiente
        if self.nivel_actual < len(self.niveles):
            print(f"\n🎮 Cargando nivel {self.nivel_actual + 1}...")
            self.iniciar_nivel()
        else:
            # Si no hay más niveles, victoria total
            print("\n🏆 ¡HAS COMPLETADO TODOS LOS NIVELES!")
            self.mostrar_victoria_final()

    def mostrar_victoria_final(self):
        """Muestra pantalla de victoria final"""
        self.nivel_completado = True
        
        font_large = pygame.font.Font(None, 100)
        font_medium = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 28)
        
        # Título
        victoria_text = font_large.render("¡VICTORIA TOTAL!", True, (0, 255, 0))
        victoria_rect = victoria_text.get_rect(center=(self.LARGURA//2, self.ALTURA//2 - 100))
        
        # Mensaje
        mensaje_text = font_medium.render("¡Has completado todos los niveles!", True, (255, 255, 255))
        mensaje_rect = mensaje_text.get_rect(center=(self.LARGURA//2, self.ALTURA//2))
        
        # Estadísticas finales
        tiempo_total = (pygame.time.get_ticks() - self.tiempo_inicio) / 1000
        stats_texts = [
            f"Niveles completados: {len(self.niveles)}",
            f"Enemigos eliminados totales: {self.enemigos_eliminados}",
            f"Tiempo total: {tiempo_total:.1f} segundos",
            f"Vidas restantes: {self.jugador.life}"
        ]
        
        # Instrucción
        instruccion_text = font_small.render("Presiona cualquier tecla para volver al menú", True, (200, 200, 200))
        instruccion_rect = instruccion_text.get_rect(center=(self.LARGURA//2, self.ALTURA - 50))
        
        # Dibujar todo
        self.JANELA.fill((0, 0, 0))
        self.JANELA.blit(victoria_text, victoria_rect)
        self.JANELA.blit(mensaje_text, mensaje_rect)
        self.JANELA.blit(instruccion_text, instruccion_rect)
        
        # Dibujar estadísticas
        y_offset = self.ALTURA//2 + 40
        for stat_text in stats_texts:
            stat = font_small.render(stat_text, True, (180, 180, 180))
            stat_rect = stat.get_rect(center=(self.LARGURA//2, y_offset))
            self.JANELA.blit(stat, stat_rect)
            y_offset += 30
        
        pygame.display.update()
        
        # Esperar entrada del usuario
        esperando = True
        while esperando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    esperando = False
        
        # Volver al menú principal
        from menu import Menu
        menu = Menu()
        menu.executar()

    def handle_events(self):
        """Maneja los eventos del juego"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Actualizar estado de teclas para movimiento
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.key_pressed['up'] = True
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.key_pressed['down'] = True
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.key_pressed['left'] = True
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.key_pressed['right'] = True
                
                # Colocar bomba
                if event.key == pygame.K_SPACE and not self.bomba_presionada:
                    if not self.jugador.puede_colocar_bomba():
                        print("⚠️ Ya tienes una bomba activa - espera a que explote")
                        return True
                    
                    grid_x, grid_y = self.ajustar_a_grid(self.jugador.x, self.jugador.y)
                    bomba_en_posicion = False
                    for b in self.bombas:
                        if not b.explotada and b.x == grid_x and b.y == grid_y:
                            bomba_en_posicion = True
                            break
                    
                    if not bomba_en_posicion:
                        nueva_bomba = Bomba(grid_x, grid_y, self.player_size, 
                                          jugador_id=self.jugador.id,
                                          rango_explosion=self.jugador.rango_explosion)
                        self.bombas.append(nueva_bomba)
                        self.jugador.colocar_bomba(nueva_bomba)
                        self.bomba_presionada = True
                        print(f"💣 Bomba colocada en ({grid_x}, {grid_y}) - Rango: {self.jugador.rango_explosion}")
                
                # Control remoto
                if event.key == pygame.K_r and not self.tecla_r_presionada:
                    if self.jugador.tiene_control_remoto:
                        self.detonar_bombas_remotamente()
                        self.tecla_r_presionada = True

                # Testing
                if event.key == pygame.K_k:
                    self.jugador.take_damage(1)
                    print(f"Player take damage! Life: {self.jugador.life}/{self.jugador.life_max}")

                elif event.key == pygame.K_h:
                    self.jugador.heal(self.jugador.life_max)
                    print(f"Player heald! Life: {self.jugador.life}/{self.jugador.life_max}")
                    
                # Debug
                if event.key == pygame.K_p:
                    print("=== INFO DEL JUEGO ===")
                    print(f"Nivel: {self.nivel_actual + 1}/{len(self.niveles)}")
                    print(f"Enemigos vivos: {len([e for e in self.enemigos if e.activo])}")
                    print(f"Enemigos eliminados: {self.enemigos_eliminados}")
                    print(f"Salida activada: {self.exit_point.activado if self.exit_point else False}")
                    
            if event.type == pygame.KEYUP:
                # Actualizar estado de teclas para movimiento
                if event.key == pygame.K_w or event.key == pygame.K_UP:
                    self.key_pressed['up'] = False
                elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                    self.key_pressed['down'] = False
                elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.key_pressed['left'] = False
                elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.key_pressed['right'] = False
                
                if event.key == pygame.K_SPACE:
                    self.bomba_presionada = False
                if event.key == pygame.K_r:
                    self.tecla_r_presionada = False
        
        return True
    
    def ajustar_a_grid(self, x, y):
        """Ajusta las coordenadas a la cuadrícula"""
        grid_size = self.player_size
        grid_x = (x // grid_size) * grid_size
        grid_y = (y // grid_size) * grid_size
        return grid_x, grid_y
    
    def detonar_bombas_remotamente(self):
        """Detona todas las bombas del jugador remotamente"""
        print("🎮 Activando control remoto...")
        bombas_detonadas = 0
        
        for bomba in self.bombas:
            if not bomba.explotada and bomba.jugador_id == self.jugador.id:
                bomba.explotar(Object.objects)
                bombas_detonadas += 1
        
        if bombas_detonadas > 0:
            print(f"💥 ¡{bombas_detonadas} bombas detonadas remotamente!")
        else:
            print("⚠️ No hay bombas para detonar")
    
    def update(self, tiempo_actual):
        """Actualiza el estado del juego"""
        # Si el nivel está completado, no actualizar
        if self.nivel_completado:
            return
        
        # Actualizar movimiento del jugador con cooldown
        current_time = pygame.time.get_ticks()
        
        if current_time - self.last_move_time >= self.move_cooldown:
            movimiento_solicitado = any([
                self.key_pressed['up'],
                self.key_pressed['down'], 
                self.key_pressed['left'],
                self.key_pressed['right']
            ])
            
            if movimiento_solicitado:
                self.jugador.actualizar_movimiento(self.LARGURA, self.ALTURA, self.bombas)
                self.last_move_time = current_time
        
        # Actualizar animación del jugador
        keys = pygame.key.get_pressed()
        self.jugador.actualizar_animacion(tiempo_actual, keys)
        
        # Actualizar estado de colisión de las bombas
        for bomba in self.bombas:
            bomba.actualizar_colision(self.jugador.x, self.jugador.y, self.jugador.id, self.player_size)
        
        # Actualizar bombas
        self.actualizar_bombas()
        
        # Verificar colisiones con power-ups
        jugador_rect = pygame.Rect(self.jugador.x, self.jugador.y, 
                                 self.player_size, self.player_size)
        powerups_recogidos = self.powerup_system.verificar_colisiones(jugador_rect, self.jugador)
        
        # Aplicar power-ups recogidos
        for tipo_powerup in powerups_recogidos:
            self.jugador.aplicar_powerup(tipo_powerup)
        
        # Actualizar objetos destruibles
        Object.atualizar_objetos_destrutiveis(self.bombas)
        
        # Actualizar enemigos
        self.actualizar_enemigos(tiempo_actual)
        
        # Verificar colisión con enemigos
        self.verificar_colision_enemigos()
        
        # Verificar si todos los enemigos fueron eliminados
        if self.exit_point and not self.exit_point.activado:
            enemigos_vivos = [e for e in self.enemigos if e.activo]
            if len(enemigos_vivos) == 0:
                self.exit_point.activar()
                print("🎉 ¡Todos los enemigos eliminados! La salida está activada.")
        
        # Verificar si el jugador llega a la salida
        if self.exit_point and self.exit_point.activado:
            if self.exit_point.colisiona_con(jugador_rect):
                print("🏁 ¡Has llegado a la salida! Pasando al siguiente nivel...")
                self.siguiente_nivel()
    
    def actualizar_enemigos(self, tiempo_actual):
        """Actualiza todos los enemigos"""
        enemigos_a_remover = []
        
        for enemigo in self.enemigos:
            if enemigo.activo:
                enemigo.actualizar(Object.objects, self.bombas, self.LARGURA, self.ALTURA)
                enemigo.actualizar_animacion(tiempo_actual)
            else:
                enemigos_a_remover.append(enemigo)
        
        # Remover enemigos inactivos
        for enemigo in enemigos_a_remover:
            self.enemigos.remove(enemigo)
    
    def verificar_colision_enemigos(self):
        """Verifica colisiones entre jugador y enemigos"""
        jugador_rect = pygame.Rect(self.jugador.x, self.jugador.y, 
                                 self.player_size, self.player_size)
        
        for enemigo in self.enemigos:
            if enemigo.activo and enemigo.colisiona_con(jugador_rect):
                if self.jugador.take_damage(1):
                    print(f"👾 ¡Enemigo golpeó al jugador! Vida: {self.jugador.life}")
                break
    
    def actualizar_bombas(self):
        """Actualiza el estado de las bombas"""
        bombas_a_remover = []

        for bomba in self.bombas:
            if bomba.debe_explotar():
                bomba.explotar(Object.objects)
                bomba.causou_dano = False
            
            if bomba.recien_explotada:
                bomba.recien_explotada = False
                self.procesar_explosion_destruccion(bomba)
            
            # Verificar daño a enemigos
            if bomba.explotada and bomba.explosion_activa() and not bomba.causou_dano:
                self.verificar_dano_enemigos(bomba)

            if bomba.explosion_activa():
                player_rect = pygame.Rect(self.jugador.x, self.jugador.y,
                                        self.player_size, self.player_size)

                if not getattr(bomba, "causou_dano", False):
                    for rect in bomba.explosion_tiles:
                        if player_rect.colliderect(rect):
                            self.jugador.take_damage(1)
                            bomba.causou_dano = True
                            print(f"🔥 Jogador atingido pela explosão! Vida: {self.jugador.life}")
                            break

            if bomba.explotada and not bomba.explosion_activa():
                bombas_a_remover.append(bomba)
                # Notificar al jugador que su bomba fue destruida
                self.jugador.bomba_destruida()

        for bomba in bombas_a_remover:
            self.bombas.remove(bomba)
    
    def verificar_dano_enemigos(self, bomba):
        """Verifica si la explosión daña a los enemigos"""
        for enemigo in self.enemigos:
            if enemigo.activo:
                for rect in bomba.explosion_tiles:
                    if enemigo.rect.colliderect(rect):
                        if enemigo.recibir_dano(1):
                            print(f"💥 ¡Enemigo eliminado!")
                            self.enemigos_eliminados += 1
                        bomba.causou_dano = True
                        break
    
    def procesar_explosion_destruccion(self, bomba):
        """Procesa la destrucción de objetos por una explosión"""
        objetos_destruidos = []
        
        for obj in Object.objects:
            if obj.destrutivel and not obj.destruido:
                for rect in bomba.explosion_tiles:
                    if obj.rect.colliderect(rect):
                        obj.destruido = True
                        objetos_destruidos.append(obj)
                        print(f"💥 Objeto destruido en ({obj.rect.x}, {obj.rect.y})")
                        
                        # Intentar spawnear power-up
                        self.powerup_system.intentar_spawn(
                            obj.rect.x, obj.rect.y, 
                            self.player_size
                        )
                        break
        
        return objetos_destruidos
    
    def draw_lives(self):
        """Dibuja interfaz compacta en 60px de altura"""
        # Fondo semitransparente para toda la franja superior
        hud_bg = pygame.Surface((self.LARGURA, 60), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 180))
        self.JANELA.blit(hud_bg, (0, 0))
        
        font = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 20)
        
        # Vida del jugador (izquierda)
        vida_text = font.render(f"Lives {self.jugador.life}", True, (255, 100, 100))
        self.JANELA.blit(vida_text, (10, 10))
        
        # Bombas disponibles (debajo de vida)
        bombas_text = font_small.render(f"Bombs {self.jugador.bombas_colocadas_actual}/{self.jugador.max_bombas}", 
                                    True, (220, 220, 220))
        self.JANELA.blit(bombas_text, (10, 35))
        
        # Rango explosión (al lado de bombas)
        rango_text = font_small.render(f"Lvl {self.jugador.rango_explosion}", True, (255, 150, 50))
        self.JANELA.blit(rango_text, (80, 35))
        
        # Nivel actual (centro superior)
        nivel_text = font.render(f"Level {self.nivel_actual + 1}/{len(self.niveles)}", True, (255, 215, 0))
        nivel_rect = nivel_text.get_rect(center=(self.LARGURA//2, 20))
        self.JANELA.blit(nivel_text, nivel_rect)
        
        # Enemigos restantes (centro inferior)
        enemigos_vivos = len([e for e in self.enemigos if e.activo])
        enemigos_text = font_small.render(f"Enemies: {enemigos_vivos}", True, (255, 150, 150))
        enemigos_rect = enemigos_text.get_rect(center=(self.LARGURA//2, 40))
        self.JANELA.blit(enemigos_text, enemigos_rect)
        
        # Estado salida (derecha superior)
        if self.exit_point:
            estado_icon = "Salida Abierta" if self.exit_point.activado else "Salida Cerrada"
            estado_color = (0, 255, 100) if self.exit_point.activado else (255, 100, 100)
            estado_text = font.render(f" {estado_icon}", True, estado_color)
            estado_rect = estado_text.get_rect(right=self.LARGURA - 10, top=10)
            self.JANELA.blit(estado_text, estado_rect)
        
        # Power-ups activos (derecha inferior - solo iconos pequeños)
        y_offset = 35
        icon_spacing = 30
        
        if self.jugador.tiene_escudo:
            escudo_text = font_small.render("🛡️", True, (100, 180, 255))
            escudo_rect = escudo_text.get_rect(right=self.LARGURA - 10, top=y_offset)
            self.JANELA.blit(escudo_text, escudo_rect)
            y_offset += icon_spacing
        
        if self.jugador.tiene_control_remoto:
            control_text = font_small.render("🎮", True, (180, 50, 230))
            control_rect = control_text.get_rect(right=self.LARGURA - 10, top=y_offset)
            self.JANELA.blit(control_text, control_rect)
        
        # Indicador de bomba activa (solo cuando hay bomba)
        if self.jugador.bomba_colocada:
            bomba_indicator = pygame.Surface((60, 4), pygame.SRCALPHA)
            bomba_indicator.fill((255, 50, 0, 200))
            self.JANELA.blit(bomba_indicator, (self.LARGURA//2 - 30, 56))

    def render(self):
        """Renderiza todos los elementos del juego"""
        # 1. Dibujar mapa
        self.mapa.dibujar(self.JANELA)
        
        # 2. Dibujar objetos no destruidos
        for obj in Object.objects:
            if not obj.destruido:
                obj.draw(self.JANELA)
        
        # 3. Dibujar power-ups
        self.powerup_system.dibujar_todos(self.JANELA)
        
        # 4. Dibujar bombas
        for bomba in self.bombas:
            bomba.dibujar(self.JANELA)
        
        # 5. Dibujar enemigos
        tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
        for enemigo in self.enemigos:
            enemigo.dibujar(self.JANELA, tiempo_actual)
        
        # 6. Dibujar punto de salida
        if self.exit_point:
            self.exit_point.dibujar(self.JANELA, tiempo_actual)
        
        # 7. Dibujar jugador
        self.jugador.dibujar(self.JANELA, tiempo_actual)
        
        # 8. Dibujar HUD
        self.draw_lives()
        
        # 9. Indicador de bomba activa
        if self.jugador.bomba_colocada:
            font = pygame.font.Font(None, 24)
            text = font.render("¡Bomba activa!", True, (255, 255, 0))
            text_rect = text.get_rect(center=(self.LARGURA // 2, self.ALTURA - 70))
            self.JANELA.blit(text, text_rect)
        
        pygame.display.update()
        
    def game_over(self, victoria=False):
        """Muestra pantalla de fin de juego compacta"""
        # Fondo semitransparente
        overlay = pygame.Surface((self.LARGURA, self.ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.JANELA.blit(overlay, (0, 0))
        
        font_large = pygame.font.Font(None, 60)
        font_medium = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 24)
        
        # Resultado
        if victoria:
            resultado = font_large.render("¡VICTORIA!", True, (0, 255, 0))
        else:
            resultado = font_large.render("GAME OVER", True, (255, 0, 0))
        
        resultado_rect = resultado.get_rect(center=(self.LARGURA//2, self.ALTURA//2 - 50))
        self.JANELA.blit(resultado, resultado_rect)
        
        # Estadísticas breves
        tiempo = (pygame.time.get_ticks() - self.tiempo_inicio) / 1000
        stats = font_medium.render(
            f"Nivel {self.nivel_actual + 1} | Enemigos: {self.enemigos_eliminados} | Tiempo: {tiempo:.1f}s",
            True, (255, 255, 255)
        )
        stats_rect = stats.get_rect(center=(self.LARGURA//2, self.ALTURA//2))
        self.JANELA.blit(stats, stats_rect)
        
        # Instrucción pequeña
        instruccion = font_small.render("Presiona cualquier tecla para continuar", 
                                    True, (200, 200, 200))
        instr_rect = instruccion.get_rect(center=(self.LARGURA//2, self.ALTURA//2 + 50))
        self.JANELA.blit(instruccion, instr_rect)
        
        pygame.display.update()
        
        # **CORRECCIÓN: Esperar entrada del usuario correctamente**
        esperando = True
        while esperando:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    esperando = False
                    break
            pygame.time.Clock().tick(30)
        
        # Ahora sí volver al menú principal
        from menu import Menu
        menu = Menu()
        menu.executar()

    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            tiempo_actual = pygame.time.get_ticks() - self.tiempo_inicio
            
            # Si el nivel está completado, no procesar eventos normales
            if self.nivel_completado:
                # Solo procesar eventos de salida
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
                continue
            
            running = self.handle_events()
            self.update(tiempo_actual)
            self.render()
            self.clock.tick(60)
            
            # **CORRECCIÓN: Verificar si el jugador murió**
            if not self.jugador.is_alive():
                self.game_over(victoria=False)
                return  # Salir del bucle run
        
        pygame.quit()
        sys.exit()