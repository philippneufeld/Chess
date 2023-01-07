# Copyright Philipp Neufeld, 2021
from chess.game import PlayerBase
from chess.board import Board
from chess.piece import *
from chess.move import Move
from chess.manager import GameManager
from random import choice
import time
from tqdm import tqdm
from math import sqrt

class AIPlayerRandom(PlayerBase):

    def __init__(self, game_manager, is_black: bool, *args) -> None:
        super().__init__(game_manager, is_black)

    def _run(self):
        moves = list(self._game_manager._available_moves)
        move = choice(moves)
        self._game_manager.push_move(move)

    def run(self):
        while True:
            self._wakeup.wait()
            if self._game_manager.black_turn == self._is_black:
                self._run()
                self.set_turn_finished()
            self._wakeup.clear()


class AIPlayer(PlayerBase):

    def __init__(self, game_manager, is_black: bool, *args) -> None:
        super().__init__(game_manager, is_black)

    def board_fitness(self, board: Board):
        score = 0
        
        # find pieces
        pieces = {} 
        for x in range(8):
            for y in range(8):
                pos = (x, y)
                piece = board.get_tile(pos).piece
                if piece is not None:
                    pieces[piece] = pos

        piece_score = {
            None: 0,
            King: 100000,
            Queen: 9,
            Rook: 5,
            Bishop: 3,
            Knight: 3,
            Pawn: 1,
        }

        for piece, pos in pieces.items():
            # single piece score and centrality
            ps = piece_score[type(piece)]
            dist = sqrt((pos[0]-3.5)**2 + (pos[1]-3.5)**2)
            myscore = (1 + 0.02*(5-dist))*ps
            score += (1.0 if piece.is_black else -1.0) * myscore

        return score

    def minimax(self, gm: GameManager, depth: int, pbar = lambda x: x) -> Tuple[float, Move]:
        minmax = max if gm.black_turn else min
        score, move = None, None
        for m in pbar(gm._available_moves):
            gm.push_move(m)
            
            if depth > 0:
                s, _ = self.minimax(gm, depth-1)
            else:
                s = self.board_fitness(gm._board)

            if move is None or minmax(s, score) == s:
                score, move = s, m

            gm.pop_move()
        return score, move

    def _run(self):
        gm = self._game_manager
        gm.preserve_board()        
        score, move = self.minimax(gm, 1, tqdm)
        gm.push_move(move)
        gm.release_preserved_board()

    def run(self):
        while True:
            self._wakeup.wait()
            if self._game_manager.black_turn == self._is_black:
                self._run()
                self.set_turn_finished()
            self._wakeup.clear()
