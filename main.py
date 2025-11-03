import pygame
from game import Game
from menu import Menu

def main():
    pygame.init()
    
    while True:
        menu = Menu()
        if menu.executar(): 
            game = Game()
            game.run()  

if __name__ == "__main__":
    main()