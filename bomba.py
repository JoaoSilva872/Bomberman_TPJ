import pygame
import time
import os
from object import Object # Necesario para acceder a la lista global de objetos

class Bomba:
    def __init__(self, x, y, tamaño_jogador, duracion=3, tile_size=20):
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
        
        # Carregar a imagem da bomba
        try:
            self.imagem_bomba = pygame.image.load(os.path.join('Object&Bomb_Sprites', 'bomb.png'))
        except:
            print("⚠️ Advertencia: No se pudo cargar bomb.png. Usando gráfico por defecto.")
            self.imagem_bomba = None
    def dibujar(self, superficie):
        """Desenha a bomba ou a área da explosão"""
        if not self.explotada:
            if self.imagem_bomba:
                # Desenhar a imagen de la bomba
                superficie.blit(self.imagem_bomba, (self.x, self.y))
            else:
                # Fallback: dibujo original
                centro_x = self.x + self.tamaño_jogador // 2
                centro_y = self.y + self.tamaño_jogador // 2
                radio = self.tamaño_jogador // 2 - 2
                pygame.draw.circle(superficie, self.color, (centro_x, centro_y), radio)
                pygame.draw.rect(superficie, (255, 0, 0),
                                (centro_x - 3, centro_y - self.tamaño_jogador // 2, 6, 8))
        else:
            # Dibujar explosión
            explosion_color = (255, 100, 0) # Naranja/Rojo para la explosión
            for rect in self.explosion_tiles:
                pygame.draw.rect(superficie, explosion_color, rect)

    def debe_explotar(self):
        """Verifica se debe explodir"""
        return time.time() - self.tiempo_creacion >= self.duracion and not self.explotada

    def explotar(self, objetos):
        """Calcula la área de la explosión y marca el flag. NO destruye objetos."""
        self.explotada = True
        self.recien_explotada = True # <--- CLAVE: Marcar para que MultiplayerGame.update lo procese
        self.tiempo_explosion = time.time()

        p = self.tamaño_jogador  # tamaño total del jugador (ex: 3 tiles * TILE_SIZE)
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
            for distancia in range(1, 2):  # Radio de explosión
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
                
                # Adiciona este tile de explosión
                self.explosion_tiles.append(explosion_rect)
                
                # La explosión para si hay objeto destructible
                if objeto_destrutivel_encontrado:
                    # NOTA: EL objeto ya NO se destruye aquí. La red lo hará en multiplayer_game.update()
                    break

    def explosion_activa(self):
        """Retorna True mientras la explosión esté visible"""
        if not self.explotada:
            return False
        return time.time() - self.tiempo_explosion < self.explosion_dur