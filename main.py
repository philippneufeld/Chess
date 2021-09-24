# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
from chess.game import Game


if __name__ == "__main__":
    game = Game(800, 'chess_pieces.png')
    game.run()
