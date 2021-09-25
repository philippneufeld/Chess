# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
import itertools
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

        # create moves array and game metrics
        self._moves = []
        self._black_turn = False
        self._is_game_over = False
        self._attacked_positions = {c: list(self.generate_attacked_positions(c)) for c in [False, True]}
        self._is_in_check = {False: False, True: False}
        self._available_moves = list(self.generate_all_moves(self._black_turn))

        # cache data to allow fast backtracking
        self._cached_available_moves = []
        self._cached_attacked_positions = []
        self._cached_is_in_check = []

    def reset_board_highlights(self) -> None:
        self._board.change_all_to_default()

    @property
    def board(self) -> Board:
        return self._board

    @property
    def moves(self) -> List[Move]:
        return self._moves

    @property
    def black_turn(self) -> bool:
        return self._black_turn

    @property
    def is_game_over(self) -> bool:
        return self._is_game_over

    def try_move(self, move: Move) -> bool:
        try:
            move.execute(self._board)
        except Exception:
            return False

        black = move.piece.is_black
        king_pos = self.get_king_position(black)
        check = king_pos in self.generate_attacked_positions(not black)
        
        move.undo(self._board) # should not fail since execute worked!
        return not check
        
    def push_move(self, move: Move) -> None:
        move.execute(self._board)
        self._moves.append(move)
        
        # cache current game metrics
        self._cached_attacked_positions.append(self._attacked_positions)
        self._cached_is_in_check.append(self._is_in_check)
        self._cached_available_moves.append(self._available_moves)
        
        # update metrics
        self._black_turn = not self._black_turn
        self._attacked_positions = {c: list(self.generate_attacked_positions(c)) for c in [False, True]}
        self._is_in_check = {c: self.get_king_position(c) in self._attacked_positions[not c] for c in [False, True]}
        self._available_moves = list(self.generate_all_moves(self._black_turn))

        # check for check mate
        if len(self._available_moves) == 0:
            self._is_game_over = True
            if self._is_in_check[self._black_turn]:
                print(f"{'black' if not self._black_turn else 'white'} wins!")
            else:
                print("Stalemate!")

    def pop_move(self) -> None:      
        move = self._moves.pop()
        move.undo(self._board)
        
        # restore cached metrics
        self._black_turn = not self._black_turn
        self._is_game_over = False
        self._attacked_positions = self._cached_attacked_positions.pop()
        self._is_in_check = self._cached_is_in_check.pop()
        self._available_moves = self._cached_available_moves.pop()

    def generate_moves(self, pos: Tuple[int, int], check_test: bool=True) -> Generator[Move, None, None]:
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

                    move = None
                    if basis.kill_level == 2 and dst_piece is None:
                        break   # 2 means that the move must kill
                    elif dst_piece is not None and (piece.is_black == dst_piece.is_black or basis.kill_level == 0):
                        break   # cannot kill dst_piece (either friendly or too low kill_level)
                    elif dst_piece is None:
                        move = NormalMove(pos, dst_pos, piece)
                    else:
                        move = KillMove(pos, dst_pos, piece, dst_piece)

                    if move is not None:   
                        if (not check_test) or self.try_move(move):
                            yield move

                    # once another piece is hit the piece cannot go any further
                    if dst_piece is not None:
                        break

    def generate_all_moves(self, black: bool, check_test: bool=True) -> Generator[Move, None, None]:
        for pos in itertools.product(range(8), range(8)):
            piece = self._board.get_tile(pos).piece
            if piece is not None and piece.is_black == black:
                yield from self.generate_moves(pos, check_test)

    def generate_attacked_positions(self, black: bool) -> Generator[Tuple[int, int], None, None]:
        for move in self.generate_all_moves(black, check_test=False):
            if isinstance(move, KillMove):
                yield move.get_attack_pos()

    def get_king_position(self, black: bool) -> Tuple[int, int]:
        for pos in itertools.product(range(8), range(8)):
            piece = self._board.get_tile(pos).piece
            if piece is not None and piece.is_black == black and isinstance(piece, King):
                return pos
        raise RuntimeError("King not found")

    def draw(self, screen) -> None:

        for black in [False, True]:
            if self._is_in_check[black]:
                self._board.get_tile(self.get_king_position(black)).change_to_check()

        self._board.draw(screen)
