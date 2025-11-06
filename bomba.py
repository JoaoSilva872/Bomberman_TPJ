import pygame
import time

class Bomba:
    def __init__(self, x, y, tamaño_jogador, duracion=3, tile_size=20):
        self.x = x
        self.y = y
        self.tamaño_jogador = tamaño_jogador  # Ex: 3 tiles
        self.tile_size = tile_size
        self.duracion = duracion
        self.tiempo_creacion = time.time()
        self.explotada = False
        self.color = (0, 0, 0)
        self.explosion_tiles = []
        self.explosion_dur = 0.5  # segundos que a explosão fica visível
        self.tiempo_explosion = None
        self.causou_dano = False  # Para controlar dano ao jogador

    def dibujar(self, superficie):
        """Desenha a bomba ou a área da explosão"""
        if not self.explotada:
            centro_x = self.x + self.tamaño_jogador // 2
            centro_y = self.y + self.tamaño_jogador // 2
            radio = self.tamaño_jogador // 2 - 2
            pygame.draw.circle(superficie, self.color, (centro_x, centro_y), radio)
            pygame.draw.rect(superficie, (255, 0, 0),
                            (centro_x - 3, centro_y - self.tamaño_jogador // 2, 6, 8))
        else:
            for rect in self.explosion_tiles:
                pygame.draw.rect(superficie, (255, 0, 0), rect)

    def debe_explotar(self):
        """Verifica se deve explodir"""
        return time.time() - self.tiempo_creacion >= self.duracion and not self.explotada

    def explotar(self, objetos):
        """Cria a área da explosão, respeitando obstáculos não destruídos"""
        self.explotada = True
        self.tiempo_explosion = time.time()

        p = self.tamaño_jogador  # tamanho total do jogador (ex: 3 tiles)
        self.explosion_tiles = []
        
        # Crear rectángulo de la bomba (centro - sempre visível)
        bomba_rect = pygame.Rect(self.x, self.y, p, p)
        self.explosion_tiles.append(bomba_rect)
        
        # Verificar explosión en cada dirección
        direcciones = [
            (p, 0, "derecha"),   # direita
            (-p, 0, "izquierda"), # esquerda
            (0, -p, "arriba"),    # cima
            (0, p, "abajo")       # baixo
        ]
        
        for dx, dy, direccion in direcciones:
            # Para cada direção, verificar até onde a explosão pode ir
            for distancia in range(1, 2):  # Explosão de 1 tile além do centro
                explosion_rect = pygame.Rect(
                    self.x + dx * distancia, 
                    self.y + dy * distancia, 
                    p, p
                )
                
                colision_indestrutivel = False
                objeto_destrutivel_encontrado = None
                
                # Verificar colisão com objetos
                for obj in objetos:
                    if obj.destruido:  # Ignorar objetos já destruídos
                        continue
                        
                    if explosion_rect.colliderect(obj.rect):
                        if obj.destrutivel:
                            # Marcar objeto destrutível para ser destruído
                            objeto_destrutivel_encontrado = obj
                        else:
                            # Objeto indestrutível - para a explosão nesta direção
                            colision_indestrutivel = True
                            break
                
                # Se encontrou objeto indestrutível, para nesta direção
                if colision_indestrutivel:
                    break
                
                # Adiciona este tile de explosão
                self.explosion_tiles.append(explosion_rect)
                
                # Se encontrou objeto destrutível, ainda mostra a explosão mas para aqui
                if objeto_destrutivel_encontrado:
                    # Marca o objeto para ser destruído
                    objeto_destrutivel_encontrado.destruido = True
                    print(f"💥 Objeto destrutível atingido na explosão!")
                    break  # A explosão para após atingir um objeto destrutível

        print("💥 Boom! Bomba explodiu!")

    def explosion_activa(self):
        """Retorna True enquanto a explosão estiver visível"""
        if not self.explotada:
            return False
        return time.time() - self.tiempo_explosion < self.explosion_dur