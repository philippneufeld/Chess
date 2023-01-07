# Copyright Philipp Neufeld, 2021
from chess.game import PlayerBase
from chess.board import Board
from chess.piece import *
from chess.move import Move
from chess.manager import GameManager
from random import choice
import time
from tqdm import tqdm
import numpy as np

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

    def board_fitness(self, gm: GameManager):
        score = 0.0
        board = gm._board
        
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
            King: 0,
            Queen: 9,
            Rook: 5,
            Bishop: 3,
            Knight: 3,
            Pawn: 1,
        }

        for piece, pos in pieces.items():
            # single piece score and centrality
            ps = piece_score[type(piece)]
            dist = np.sqrt((pos[0]-3.5)**2 + (pos[1]-3.5)**2)
            myscore = (1 + 0.02*(5-dist))*ps
            score += (1.0 if piece.is_black else -1.0) * myscore

        # check for mate
        if gm.is_game_over:
            if gm.black_turn: # white wins
                score = -np.inf
            else: # black wins
                score = np.inf

        return score

    def _alphabeta(self, gm: GameManager, depth: int, alpha: float, beta: float, pbar = lambda x:x) -> Tuple[float, Move]:
        if depth == 0:
            return self.board_fitness(gm), None

        best = None

        maximizing = gm.black_turn
        if maximizing:
            score = -np.inf
            for m in pbar(gm._available_moves):
                gm.push_move(m)
                s, _ = self._alphabeta(gm, depth-1, alpha, beta)
                gm.pop_move()

                if s > score:
                    score, best = s, m
                if score > beta:
                    break
                alpha = max(alpha, score)
        else:
            score = np.inf
            for m in pbar(gm._available_moves):
                gm.push_move(m)
                s, _ = self._alphabeta(gm, depth-1, alpha, beta)
                gm.pop_move()
                
                if s < score:
                    score, best = s, m
                if score < alpha:
                    break
                beta = min(beta, score)
        
        return score, best

    def alphabeta(self, gm: GameManager, depth: int, pbar) -> Tuple[float, Move]:
        return self._alphabeta(gm, depth, -np.inf, np.inf, pbar)

    def _run(self):
        gm = self._game_manager
        gm.preserve_board()
        _, move = self.alphabeta(gm, 2, tqdm)
        gm.push_move(move)
        gm.release_preserved_board()

    def run(self):
        while True:
            self._wakeup.wait()
            if self._game_manager.black_turn == self._is_black \
                and not self._game_manager._is_game_over:
                self._run()
                self.set_turn_finished()
            self._wakeup.clear()
