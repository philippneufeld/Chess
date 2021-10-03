# Copyright Philipp Neufeld, 2021
from typing import Tuple
from chess.board import Board
from chess.piece import Piece, Pawn

class Move:

    def __init__(self, piece: Piece):
        self._piece = piece
        if not isinstance(self._piece, Piece):
            raise RuntimeError("Invalid piece object for move")

    @staticmethod
    def board_pos_repr(pos: Tuple[int, int]) -> str:
        return f"{chr(97 + pos[1])}{8-pos[0]}"

    @property
    def piece(self) -> Piece:
        return self._piece

    def __repr__(self) -> str:
        return f"Unknown move ({self._piece})"

    def get_activation_pos(self) -> Tuple[int, int]:
        raise NotImplementedError

    def execute(self, board: Board) -> None:
        raise NotImplementedError

    def undo(self, board: Board) -> None:
        raise NotImplementedError

    def color_board(self, board: Board) -> None:
        raise NotImplementedError


class NormalMove(Move):

    def __init__(self, src_pos: Tuple[int, int], dst_pos: Tuple[int, int], piece: Piece):
        super().__init__(piece)
        self._src_pos = src_pos
        self._dst_pos = dst_pos

    def __repr__(self) -> str:
        return f"{self._piece}{self.board_pos_repr(self._src_pos)}-{self.board_pos_repr(self._dst_pos)}"

    def get_activation_pos(self) -> Tuple[int, int]:
        return self._dst_pos

    def execute(self, board: Board) -> None:
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        # sanity check
        if src_tile.piece is not self._piece or dst_tile.piece is not None:
            raise RuntimeError("Cannot execute move")

        # execute
        src_tile.piece = None
        dst_tile.piece = self._piece

    def undo(self, board: Board) -> None:
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)

        # sanity check
        if dst_tile.piece is not self._piece or src_tile.piece is not None:
            raise RuntimeError("Cannot undo move")
        
        # execute
        dst_tile.piece = None
        src_tile.piece = self._piece

    def color_board(self, board: Board) -> None:
        dst_tile = board.get_tile(self._dst_pos)
        dst_tile.change_to_movable()

    
class PawnDoubleStepMove(NormalMove):
    
    def __init__(self, src_pos: Tuple[int, int], dst_pos: Tuple[int, int], piece: Pawn):
        super().__init__(src_pos, dst_pos, piece)

        if not isinstance(piece, Pawn):
            raise RuntimeError("Piece must be a pawn")

        if (dst_pos[0] - src_pos[0]) != (2 if piece.is_black else -2) or src_pos[1] != dst_pos[1]:
            raise RuntimeError("Invalid move distance")

        
class GeneralKillMove(Move):

    def __init__(self, src_pos: Tuple[int, int], dst_pos: Tuple[int, int], kill_pos: Tuple[int, int], piece: Piece, kill_piece: Piece):
        super().__init__(piece)
        self._src_pos = src_pos
        self._dst_pos = dst_pos
        self._kill_pos = kill_pos
        self._kill_piece = kill_piece

        if self._kill_piece is None:
            raise RuntimeError("Invalid move")

    def __repr__(self) -> str:
        return f"{self._piece}{self.board_pos_repr(self._src_pos)}-x{self.board_pos_repr(self._dst_pos)}"

    def get_activation_pos(self) -> Tuple[int, int]:
        return self._dst_pos

    def get_attack_pos(self) -> Tuple[int, int]:
        return self._kill_pos

    def execute(self, board: Board) -> None:
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)
        kill_tile = board.get_tile(self._kill_pos)

        #sanity check
        if src_tile.piece is not self._piece or kill_tile.piece is not self._kill_piece or (dst_tile is not kill_tile and dst_tile.piece is not None):
            raise RuntimeError("Cannot execute move")
        
        #execute
        src_tile.piece = None
        kill_tile.piece = None
        dst_tile.piece = self._piece

    def undo(self, board: Board) -> None:
        src_tile = board.get_tile(self._src_pos)
        dst_tile = board.get_tile(self._dst_pos)
        kill_tile = board.get_tile(self._kill_pos)

        #sanity check
        if src_tile.piece is not None or dst_tile.piece is not self._piece or (dst_tile is not kill_tile and kill_tile.piece is not None):
            raise RuntimeError("Cannot undo move")

        dst_tile.piece = None
        kill_tile.piece = self._kill_piece
        src_tile.piece = self._piece

    def color_board(self, board: Board) -> None:
        dst_tile = board.get_tile(self._dst_pos)
        dst_tile.change_to_killable()


class KillMove(GeneralKillMove):

    def __init__(self, src_pos: Tuple[int, int], dst_pos: Tuple[int, int], piece, kill_piece: Piece):
        super().__init__(src_pos, dst_pos, dst_pos, piece, kill_piece)
 

class EnPassantMove(GeneralKillMove):

    def __init__(self, src_pos: Tuple[int, int], dst_pos: Tuple[int, int], kill_pos: Tuple[int, int], piece, kill_piece: Piece):
        super().__init__(src_pos, dst_pos, kill_pos, piece, kill_piece)

    def color_board(self, board: Board):
        dst_tile = board.get_tile(self._dst_pos)
        dst_tile.change_to_special()
        