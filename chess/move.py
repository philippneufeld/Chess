# Copyright Philipp Neufeld, 2021
from chess.board import Board

class Move:

    def __init__(self):
        pass

    def __repr__(self):
        return "Unknown move"

    def get_activation_pos(self):
        raise NotImplementedError

    def execute(self, board: Board):
        raise NotImplementedError

    def undo(self, board: Board):
        raise NotImplementedError

    def color_board(self, board: Board):
        raise NotImplementedError


class NormalMove(Move):

    def __init__(self, src_pos, dst_pos, piece):
        self._src_pos = src_pos
        self._dst_pos = dst_pos
        self._piece = piece

        if self._piece is None:
            raise RuntimeError("Invalid move")

    def get_activation_pos(self):
        return self._dst_pos

    def execute(self, board: Board):
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        # sanity check
        if src_tile.piece is not self._piece or dst_tile.piece is not None:
            raise RuntimeError("Cannot execute move")

        # execute
        src_tile.piece = None
        dst_tile.piece = self._piece

    def undo(self, board: Board):
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        # sanity check
        if dst_tile.piece is not self._piece or src_tile.piece is not None:
            raise RuntimeError("Cannot undo move")
        
        # execute
        dst_tile.piece = None
        src_tile.piece = self._piece

    def color_board(self, board: Board):
        dst_tile = board.get_tile(self._dst_pos)
        dst_tile.change_to_movable()

        
class KillMove(Move):

    def __init__(self, src_pos, dst_pos, piece, kill_piece):
        self._src_pos = src_pos
        self._dst_pos = dst_pos
        self._piece = piece
        self._kill_piece = kill_piece

        if self._piece is None or self._kill_piece is None:
            raise RuntimeError("Invalid move")

    def get_activation_pos(self):
        return self._dst_pos

    def execute(self, board: Board):
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        #sanity check
        if src_tile.piece is not self._piece or dst_tile.piece is not self._kill_piece:
            raise RuntimeError("Cannot execute move")
        
        #execute
        src_tile.piece = None
        dst_tile.piece = self._piece

    def undo(self, board: Board):
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        #sanity check
        if src_tile.piece is not None or dst_tile.piece is not self._piece:
            raise RuntimeError("Cannot undo move")

        dst_tile.piece = self._kill_piece
        src_tile.piece = self._piece

    def color_board(self, board: Board):
        dst_tile = board.get_tile(self._dst_pos)
        dst_tile.change_to_killable()
        