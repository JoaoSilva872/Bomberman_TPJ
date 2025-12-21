import pygame
import os
from object import Object

class Map:
    def __init__(self, ancho, alto, tile_size, cor_clara, cor_escura):
        self.ancho = ancho
        self.alto = alto
        self.tile_size = tile_size
        self.cor_clara = cor_clara
        self.cor_escura = cor_escura
        
        # Pasta onde as imagens dos mapas estão guardadas
        self.maps_folder = "Maps"
        
        # Sistema de níveis - ahora con más niveles
        self.levels = {
            "level1": "Map_2.png",  # Nivel 1 (fácil)
            "level2": "Map_3.png",  # Nivel 2 (medio)
            # Puedes añadir más niveles aquí
            # "level3": "Map_4.png",
            # "level4": "Map_5.png",
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
    
    def crear_obstaculos(self, level_name="level1"):
        """Crea obstáculos a partir da imagem do mapa"""
        Object.objects.clear()
        
        if level_name not in self.levels:
            print(f"❌ Nível {level_name} não encontrado! Usando 'level1'.")
            level_name = "level1"
        
        image_filename = self.levels[level_name]
        image_path = os.path.join(self.maps_folder, image_filename)
        
        try:
            # Carrega a imagem do mapa
            map_image = pygame.image.load(image_path)
            map_image = pygame.transform.scale(map_image, (self.ancho, self.alto))
            
            # Converte para uma superfície que podemos ler os pixels
            map_surface = pygame.Surface((self.ancho, self.alto))
            map_surface.blit(map_image, (0, 0))
            
            # Processa a imagem pixel a pixel (agrupado por tiles)
            for y in range(0, self.alto, self.tile_size * 3):
                for x in range(0, self.ancho, self.tile_size * 3):
                    # Pega la cor del pixel en el centro del tile
                    pixel_x = x + (self.tile_size * 3) // 2
                    pixel_y = y + (self.tile_size * 3) // 2
                    
                    if 0 <= pixel_x < self.ancho and 0 <= pixel_y < self.alto:
                        color = map_surface.get_at((pixel_x, pixel_y))
                        
                        # Converte a cor para formato hexadecimal para comparação
                        color_hex = "{:02x}{:02x}{:02x}".format(color.r, color.g, color.b)
                        
                        # Cria objetos baseado na cor
                        if color_hex == "000000":  # Preto - indestrutível
                            Object(x, y, self.tile_size * 3, self.tile_size * 3, 
                                  "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
                        elif color_hex == "68ff00":  # Verde - destrutível
                            Object(x, y, self.tile_size * 3, self.tile_size * 3, 
                                  "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
            
            print(f"✅ Nível '{level_name}' carregado a partir de {image_filename}:")
            print(f"   - {len([obj for obj in Object.objects if not obj.destrutivel])} objetos indestrutíveis")
            print(f"   - {len([obj for obj in Object.objects if obj.destrutivel])} objetos destrutíveis")
            
        except pygame.error as e:
            print(f"❌ Erro ao carregar imagem do mapa: {e}")
            print(f"📁 Procurando em: {os.path.abspath(image_path)}")
            print("📋 Tentando criar mapa padrão como fallback...")
            self._create_fallback_map(level_name)
    
    def _create_fallback_map(self, level_name):
        """Cria um mapa simples como fallback"""
        # Cria bordas indestrutíveis
        for x in range(0, self.ancho, self.tile_size * 3):
            for y in range(0, self.alto, self.tile_size * 3):
                # Bordas
                if x == 0 or y == 0 or x >= self.ancho - (self.tile_size * 3) or y >= self.alto - (self.tile_size * 3):
                    Object(x, y, self.tile_size * 3, self.tile_size * 3, 
                          "Object&Bomb_Sprites/OBJ_ND.png", destrutivel=False)
                # Patrón diferente según el nivel
                elif level_name == "level1":
                    # Nivel 1: patrón simple
                    if x % (self.tile_size * 9) == 0 and y % (self.tile_size * 9) == 0:
                        Object(x, y, self.tile_size * 3, self.tile_size * 3, 
                              "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
                elif level_name == "level2":
                    # Nivel 2: más obstáculos
                    if (x % (self.tile_size * 6) == 0 and y % (self.tile_size * 6) == 0) or \
                       (x % (self.tile_size * 9) == self.tile_size * 3 and y % (self.tile_size * 9) == self.tile_size * 3):
                        Object(x, y, self.tile_size * 3, self.tile_size * 3, 
                              "Object&Bomb_Sprites/OBJ_D.png", destrutivel=True)
    
    def get_available_levels(self):
        """Retorna lista de níveis disponíveis"""
        return list(self.levels.keys())
    
    def scan_maps_folder(self):
        """Escaneia a pasta de mapas e adiciona automaticamente los arquivos PNG encontrados"""
        if not os.path.exists(self.maps_folder):
            print(f"📁 Pasta '{self.maps_folder}' não encontrada. Criando...")
            os.makedirs(self.maps_folder)
            return
        
        png_files = [f for f in os.listdir(self.maps_folder) if f.lower().endswith('.png')]
        
        for png_file in png_files:
            level_name = os.path.splitext(png_file)[0]
            if level_name not in self.levels:
                self.levels[level_name] = png_file
                print(f"📋 Mapa descoberto: {level_name} -> {png_file}")