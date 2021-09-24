# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
from chess.piece import Piece, Rook, Knight, Bishop, Queen, King, Pawn
from chess.board import Board
from chess.move import Move, NormalMove, KillMove


class GameManager:

    def __init__(self, tile_size: int, img_pieces, img_piece_size: int):
        self._board = Board(tile_size)

        # Initialize pieces to start positions
        for i in [0, 1]:
            is_black = [True, False]
            base_row = [0, 7]
            pawn_row = [1, 6]

            self._board.get_tile((base_row[i], 0)).piece = Rook(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 1)).piece = Knight(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 2)).piece = Bishop(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 3)).piece = Queen(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 4)).piece = King(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 5)).piece = Bishop(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 6)).piece = Knight(is_black[i], img_pieces, img_piece_size)
            self._board.get_tile((base_row[i], 7)).piece = Rook(is_black[i], img_pieces, img_piece_size)

            for j in range(8):
                self._board.get_tile((pawn_row[i], j)).piece = Pawn(is_black[i], img_pieces, img_piece_size)

        # create moves array and turn indicator
        self._moves = []
        self._black_turn = False

    def reset_board_highlights(self) -> None:
        self._board.change_all_to_default()

    @property
    def board(self) -> Board:
        return self._board

    @property
    def black_turn(self) -> bool:
        return self._black_turn

    def push_move(self, move: Move) -> None:
        move.execute(self._board)
        self._moves.append(move)
        self._black_turn = not self._black_turn

    def pop_move(self) -> None:      
        if len(self._moves) == 0:
            raise RuntimeError("No move to pop")

        move = self._moves.pop()
        move.undo(self._board)
        self._black_turn = not self._black_turn

    def generate_moves(self, pos) -> Generator[Move, None, None]:
        piece: Piece = self._board.get_tile(pos).piece
        if piece is None:
            return
        else:
            for basis in piece.get_movement_bases(pos):
                for i in range(1, basis.max_steps + 1):

                    # generate new position
                    dst_pos = pos[0] + i * basis.basis_vec[0], pos[1] + i * basis.basis_vec[1]
                    if not self._board.is_pos_valid(dst_pos):
                        break

                    # if the dst_piece is friendly cannot occupy its tile
                    dst_piece = self._board.get_tile(dst_pos).piece

                    if basis.kill_level == 2 and dst_piece is None:
                        break   # 2 means that the move must kill
                    elif dst_piece is not None and (piece.is_black == dst_piece.is_black or basis.kill_level == 0):
                        break   # cannot kill dst_piece (either friendly or too low kill_level)
                    elif dst_piece is None:
                        yield NormalMove(pos, dst_pos, piece)
                    else:
                        yield KillMove(pos, dst_pos, piece, dst_piece)

                    # once another piece is hit the piece cannot go any further
                    if dst_piece is not None:
                        break

    def draw(self, screen) -> None:
        self._board.draw(screen)
