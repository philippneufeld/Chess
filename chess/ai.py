# Copyright Philipp Neufeld, 2021
from chess.game import PlayerBase
from random import choice

class AIPlayerRandom(PlayerBase):

    def __init__(self, game_manager, is_black: bool, *args) -> None:
        super().__init__(game_manager, is_black)

    def _run(self):
        moves = list(self._game_manager.generate_all_moves(self._is_black))
        move = choice(moves)
        self._game_manager.push_move(move)

    def run(self):
        while True:
            self._wakeup.wait()
            if self._game_manager.black_turn == self._is_black:
                self._run()
                self.set_turn_finished()
            self._wakeup.clear()
