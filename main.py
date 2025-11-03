import pygame
from game import Game
from menu import Menu

def main():
    pygame.init()
    
    while True:
        menu = Menu()
        if menu.executar():  # Se usuário escolheu iniciar jogo
            game = Game()
            game.run()  # Quando o jogo terminar, volta automaticamente ao menu

if __name__ == "__main__":
    main()