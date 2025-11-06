import pygame
from object import Object

class Map:
    def __init__(self, ancho, alto, tile_size, cor_clara, cor_escura):
        self.ancho = ancho
        self.alto = alto
        self.tile_size = tile_size
        self.cor_clara = cor_clara
        self.cor_escura = cor_escura
        
        # Sistema de níveis - apenas maze_21x12
        self.levels = {
            "maze_21x12": [
                "XXXXXXXXXXXXXXXXXXXXX",  # 21 colunas - linha 0
                "X  DDDDDXDDDDDDXDD  X",  # linha 1
                "X XDXDXDXDXDXDXXDXX X",  # linha 2
                "XDXDDDXDXDXDXDDDDDDDX",   # linha 3
                "XDXXDXXDDDDDDDXXXXXDX",   # linha 4
                "XDDDDDDDXDXDXDDDDDDDX",   # linha 5
                "XDXXXXXDXDXDXDDXDXXXX",    # linha 6
                "XDDDDDDDDDXDXXDXDDDDX",   # linha 7
                "XDXXXDXXDDDDDDDXXXDXX",    # linha 8
                "XDDDDDDDDDXDDDDDDDDDX",   # linha 9
                "XDXXDDXXDDXDDXXDDXXDX",   # linha 10
                "XXXXXXXXXXXXXXXXXXXXX"   # linha 11 - 12 linhas
            ]
        }
    
    def dibujar(self, superficie):
        """Dibuja el mapa estilo ajedrez"""
        for linha in range(0, self.alto, self.tile_size):
            for coluna in range(0, self.ancho, self.tile_size):
                if (linha // self.tile_size + coluna // self.tile_size) % 2 == 0:
                    cor = self.cor_clara
                else:
                    cor = self.cor_escura
                pygame.draw.rect(superficie, cor, (coluna, linha, self.tile_size, self.tile_size))
    
    def crear_obstaculos(self, level_name="maze_21x12"):
        """Crea obstáculos a partir do mapa definido - canto superior esquerdo"""
        Object.objects.clear()
        
        if level_name not in self.levels:
            print(f"❌ Nível {level_name} não encontrado! Usando 'maze_21x12'.")
            level_name = "maze_21x12"
        
        level_map = self.levels[level_name]
        
        # Criar objetos a partir da matriz
        for row, line in enumerate(level_map):
            for col, char in enumerate(line):
                x = col * self.tile_size*3
                y = row * self.tile_size*3
                
                # Verificar se está dentro da tela
                if 0 <= x < self.ancho and 0 <= y < self.alto:
                    if char == 'X':  # Parede indestrutível
                        Object(x, y, self.tile_size*3, self.tile_size*3, 
                              "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
                    elif char == 'D':  # Obstáculo destrutível
                        Object(x, y, self.tile_size*3, self.tile_size*3, 
                              "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
                    # Espaço vazio (' ') - não cria objeto
                
        print(f"✅ Nível '{level_name}' carregado:")
        print(f"   - {len([obj for obj in Object.objects if not obj.destrutivel])} objetos indestrutíveis")
        print(f"   - {len([obj for obj in Object.objects if obj.destrutivel])} objetos destrutíveis")
        print(f"   - 4 áreas de spawn livres (2x2 tiles cada)")
    
    def get_available_levels(self):
        """Retorna lista de níveis disponíveis"""
        return list(self.levels.keys())