# Copyright Philipp Neufeld, 2021
from chess.game import Game, Player
from chess.ai import AIPlayerRandom

if __name__ == "__main__":
    game = Game(800, 'chess_pieces.png', Player, AIPlayerRandom)
    game.run()
