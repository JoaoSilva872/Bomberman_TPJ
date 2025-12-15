import pygame
import time
import os
from object import Object

class Bomba:
    def __init__(self, x, y, tamaño_jogador, duracion=3, tile_size=20, jugador_id=0):
        self.x = x
        self.y = y
        self.tamaño_jogador = tamaño_jogador
        self.tile_size = tile_size
        self.duracion = duracion
        self.tiempo_creacion = time.time()
        self.explotada = False
        self.recien_explotada = False
        self.color = (0, 0, 0)
        self.explosion_tiles = []
        self.explosion_dur = 0.5
        self.tiempo_explosion = None
        self.causou_dano = False
        
        # Rectángulo para colisiones
        self.rect = pygame.Rect(x, y, tamaño_jogador, tamaño_jogador)
        
        # Sistema de colisión dinámica - MEJORADO PARA MULTIJUGADOR
        self.jugador_id = jugador_id  # ID del jugador que colocó la bomba
        self.jugador_ha_salido = False  # Flag para saber si el jugador ya salió
        self.es_solida_para_otros = False  # Para otros jugadores
        
        # Para bombas remotas: por defecto, son sólidas para todos excepto su dueño
        self.es_remota = False
        
        # Carregar a imagem da bomba
        try:
            self.imagem_bomba = pygame.image.load(os.path.join('Object&Bomb_Sprites', 'bomb.png'))
        except:
            print("⚠️ Advertencia: No se pudo cargar bomb.png. Usando gráfico por defecto.")
            self.imagem_bomba = None

    def actualizar_colision(self, jugador_x, jugador_y, jugador_id, grid_size):
        """Actualiza el estado de colisión basado en la posición del jugador"""
        # Solo actualizar si es bomba local (del jugador actual)
        if self.jugador_id == jugador_id and not self.es_remota:
            # Calcular si el jugador está completamente FUERA del rectángulo de la bomba
            jugador_rect = pygame.Rect(jugador_x, jugador_y, grid_size, grid_size)
            
            # Si el jugador NO se superpone con la bomba
            if not jugador_rect.colliderect(self.rect):
                self.jugador_ha_salido = True
                self.es_solida_para_otros = True  # Ahora la bomba es sólida para todos
                # print(f"🚧 Bomba en ({self.x}, {self.y}) ahora es sólida para todos")
    
    def es_colision_solida(self, jugador_id):
        """Determina si la bomba debe causar colisión para un jugador específico"""
        # Si la bomba está explotando o ya explotó, NO es sólida
        if self.explotada:
            return False
        
        # Si es bomba remota y NO somos el dueño, siempre es sólida
        if self.es_remota and jugador_id != self.jugador_id:
            return True
        
        # Si es bomba local
        if jugador_id == self.jugador_id:
            # Solo es sólida si ya salió completamente
            return self.jugador_ha_salido
        
        # Para otros jugadores, es sólida si el dueño ya salió
        return self.es_solida_para_otros

    def dibujar(self, superficie):
        """Desenha a bomba ou a área da explosão"""
        if not self.explotada:
            if self.imagem_bomba:
                superficie.blit(self.imagem_bomba, (self.x, self.y))
            else:
                # Fallback: dibujo original
                centro_x = self.x + self.tamaño_jogador // 2
                centro_y = self.y + self.tamaño_jogador // 2
                radio = self.tamaño_jogador // 2 - 2
                pygame.draw.circle(superficie, self.color, (centro_x, centro_y), radio)
                pygame.draw.rect(superficie, (255, 0, 0),
                                (centro_x - 3, centro_y - self.tamaño_jogador // 2, 6, 8))
                
            # Dibujar indicador visual del estado de colisión
            if self.es_remota:
                # Borde azul para bombas remotas
                pygame.draw.rect(superficie, (0, 0, 255), self.rect, 2)
            elif self.es_solida_para_otros:
                # Dibujar borde rojo si es sólida para otros
                pygame.draw.rect(superficie, (255, 0, 0), self.rect, 2)
        else:
            # Dibujar explosión
            explosion_color = (255, 100, 0)
            for rect in self.explosion_tiles:
                pygame.draw.rect(superficie, explosion_color, rect)

    def debe_explotar(self):
        """Verifica se debe explodir"""
        return time.time() - self.tiempo_creacion >= self.duracion and not self.explotada

    def explotar(self, objetos):
        """Calcula la área de la explosión y marca el flag"""
        self.explotada = True
        self.recien_explotada = True
        self.tiempo_explosion = time.time()
        self.es_solida_para_otros = False  # Deja de ser sólida al explotar

        p = self.tamaño_jogador
        self.explosion_tiles = []
        
        # Crear rectángulo de la bomba (centro)
        bomba_rect = pygame.Rect(self.x, self.y, p, p)
        self.explosion_tiles.append(bomba_rect)
        
        # Verificar explosión en cada dirección
        direcciones = [
            (p, 0, "derecha"), 
            (-p, 0, "izquierda"),
            (0, -p, "arriba"),
            (0, p, "abajo")
        ]
        
        for dx, dy, direccion in direcciones:
            for distancia in range(1, 2):
                explosion_rect = pygame.Rect(
                    self.x + dx * distancia, 
                    self.y + dy * distancia, 
                    p, p
                )
                
                colision_indestrutivel = False
                objeto_destrutivel_encontrado = None
                
                # Verificar colisión con objetos
                for obj in objetos:
                    if obj.destruido: 
                        continue
                        
                    if explosion_rect.colliderect(obj.rect):
                        if obj.destrutivel:
                            objeto_destrutivel_encontrado = obj
                        else:
                            colision_indestrutivel = True
                            break
                
                if colision_indestrutivel:
                    break
                
                self.explosion_tiles.append(explosion_rect)
                
                if objeto_destrutivel_encontrado:
                    break

    def explosion_activa(self):
        """Retorna True mientras la explosión esté visible"""
        if not self.explotada:
            return False
        return time.time() - self.tiempo_explosion < self.explosion_dur