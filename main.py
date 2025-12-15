import pygame
from game import Game
from menu import Menu
from multiplayer_menu import MultiplayerMenu
from multiplayer_game import MultiplayerGame

def main():
    pygame.init()
    
    while True:
        menu = Menu()
        tipo_juego = menu.executar()
        
        if tipo_juego == "single":
            # Juego individual
            print("🎮 Iniciando juego individual...")
            game = Game()
            game.run()
        
        elif tipo_juego == "multi":
            # Mostrar menú multijugador
            menu_multi = MultiplayerMenu()
            modo_multijugador, ip = menu_multi.ejecutar()
            
            if modo_multijugador == "back":
                continue  # Volver al menú principal
            elif modo_multijugador == "host":
                print("🎮 Iniciando como Host...")
                game = MultiplayerGame(is_host=True, host_ip='172.20.10.2')
                game.run()
            elif modo_multijugador == "client":
                if ip:
                    print(f"🎮 Conectando a {ip}...")
                    game = MultiplayerGame(is_host=False, host_ip=ip)
                    game.run()
                else:
                    print("❌ Debes ingresar una IP válida")
            else:
                # Fallback a juego individual
                print("🎮 Iniciando juego individual (fallback)...")
                game = Game()
                game.run()
        else:
            # Salir
            break

if __name__ == "__main__":
    main()