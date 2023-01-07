# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple, Optional
import itertools
import threading
from chess.piece import Piece, Rook, Knight, Bishop, Queen, King, Pawn
from chess.board import Board
from chess.move import Move, NormalMove, GeneralKillMove, KillMove, PawnDoubleStepMove, EnPassantMove, PawnTransformMove, PawnTransformKillMove, CastelingMove
from copy import deepcopy
import time

class GameManager:

    def __init__(self, tile_size: int, img_pieces, img_piece_size: int):
        self._board = Board(tile_size)

        self._img_pieces = img_pieces
        self._img_piece_size = img_piece_size

        self._lock = threading.RLock()

        # Initialize pieces to start positions
        for i in [0, 1]:
            is_black = [True, False]
            base_row = [0, 7]
            pawn_row = [1, 6]

            self._board.get_tile((base_row[i], 0)).piece = self._create_piece(is_black[i], Rook)
            self._board.get_tile((base_row[i], 1)).piece = self._create_piece(is_black[i], Knight)
            self._board.get_tile((base_row[i], 2)).piece = self._create_piece(is_black[i], Bishop)
            self._board.get_tile((base_row[i], 3)).piece = self._create_piece(is_black[i], Queen)
            self._board.get_tile((base_row[i], 4)).piece = self._create_piece(is_black[i], King)
            self._board.get_tile((base_row[i], 5)).piece = self._create_piece(is_black[i], Bishop)
            self._board.get_tile((base_row[i], 6)).piece = self._create_piece(is_black[i], Knight)
            self._board.get_tile((base_row[i], 7)).piece = self._create_piece(is_black[i], Rook)

            for j in range(8):
                self._board.get_tile((pawn_row[i], j)).piece = self._create_piece(is_black[i], Pawn)

        # create moves array and game metrics (_attacked positions only gives occupied fields)
        self._moves = []
        self._castle_pieces_move_cnt = {self._board.get_tile(p).piece: 0 for p in [(0,0), (0,4), (0,7), (7, 0), (7, 4), (7, 7)]}
        self._black_turn = False
        self._is_game_over = False
        self._is_in_check = {False: False, True: False}
        self._attacked_positions = {c: list(self.generate_attacked_positions(c)) for c in [False, True]}
        self._available_moves = list(self.generate_all_moves(self._black_turn))

        # cache data to allow fast backtracking
        self._cached_available_moves = []
        self._cached_attacked_positions = []
        self._cached_is_in_check = []

        # preservable state
        self._preserved_board = None
        self._preserved_check = None

    def preserve_board(self) -> None:
        with self._lock:
            self._preserved_board = deepcopy(self._board)
            self._preserved_check = deepcopy(self._is_in_check)

    def release_preserved_board(self) -> None:
        with self._lock:
            self._preserved_board = None
            self._preserved_check = None

    def _create_piece(self, is_black: bool, piece_cls: type) -> Piece:
        if not issubclass(piece_cls, Piece):
            raise RuntimeError("Invalid piece class")
        return piece_cls(is_black, self._img_pieces, self._img_piece_size)

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
        with self._lock:
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
        with self._lock:
            self.board.change_all_to_default()
            move.execute(self._board)
            self._moves.append(move)
            
            # cache current game metrics
            self._cached_attacked_positions.append(self._attacked_positions)
            self._cached_is_in_check.append(self._is_in_check)
            self._cached_available_moves.append(self._available_moves)

            # update metrics
            self._black_turn = not self._black_turn
            if move.piece in self._castle_pieces_move_cnt:
                self._castle_pieces_move_cnt[move.piece] += 1
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
        with self._lock:
            self.board.change_all_to_default()  
            move = self._moves.pop()
            move.undo(self._board)
            
            # restore cached metrics
            self._black_turn = not self._black_turn
            if move.piece in self._castle_pieces_move_cnt:
                self._castle_pieces_move_cnt[move.piece] -= 1
            self._is_game_over = False
            self._attacked_positions = self._cached_attacked_positions.pop()
            self._is_in_check = self._cached_is_in_check.pop()
            self._available_moves = self._cached_available_moves.pop()

    def generate_moves(self, pos: Tuple[int, int], check_test: bool=True) -> Generator[Move, None, None]:
        with self._lock:
            piece: Piece = self._board.get_tile(pos).piece
            if piece is None:
                return
            else:
                # Generate normal moves
                for basis in piece.get_movement_bases(pos):
                    for i in range(1, basis.max_steps + 1):
                        # generate new position
                        dst_pos = pos[0] + i * basis.basis_vec[0], pos[1] + i * basis.basis_vec[1]
                        if not self._board.is_pos_valid(dst_pos):
                            break

                        # if the dst_piece is friendly cannot occupy its tile
                        dst_piece = self._board.get_tile(dst_pos).piece

                        is_pawn_transform = isinstance(piece, Pawn) and dst_pos[0] == (7 if piece.is_black else 0)

                        moves = []
                        if basis.kill_level == 2 and dst_piece is None:
                            break   # 2 means that the move must kill
                        elif dst_piece is not None and (piece.is_black == dst_piece.is_black or basis.kill_level == 0):
                            break   # cannot kill dst_piece (either friendly or too low kill_level)
                        elif dst_piece is None:
                            is_pawn_double_step = isinstance(piece, Pawn) and abs(dst_pos[0] - pos[0]) == 2
                            if is_pawn_double_step:
                                moves.append(PawnDoubleStepMove(pos, dst_pos, piece))
                            elif is_pawn_transform:
                                for ty in [Queen, Rook, Bishop, Knight]:
                                    moves.append(PawnTransformMove(pos, dst_pos, piece, self._create_piece(piece.is_black, ty)))
                            else:
                                moves.append(NormalMove(pos, dst_pos, piece))
                        else:
                            if is_pawn_transform:
                                for ty in [Queen, Rook, Bishop, Knight]:
                                    moves.append(PawnTransformKillMove(pos, dst_pos, piece, dst_piece, self._create_piece(piece.is_black, ty)))
                            else:
                                moves.append(KillMove(pos, dst_pos, piece, dst_piece))

                        for move in moves:
                            if (not check_test) or self.try_move(move):
                                yield move

                        # once another piece is hit the piece cannot go any further
                        if dst_piece is not None:
                            break
                
                # Generate en-passant moves
                if isinstance(piece, Pawn) and pos[0] == (4 if piece.is_black else 3):
                    if len(self.moves) > 0 and isinstance(self.moves[-1], PawnDoubleStepMove) and self.moves[-1].piece.is_black != piece.is_black:
                        check_tiles = [(pos[0], pos[1] + 1), (pos[0], pos[1] - 1)]
                        for kill_pos in check_tiles:
                            dst_pos = (kill_pos[0] + (1 if piece.is_black else -1), kill_pos[1])

                            if not self._board.is_pos_valid(kill_pos) or not self._board.is_pos_valid(dst_pos):
                                continue
                            
                            dst_piece = self._board.get_tile(dst_pos).piece
                            kill_piece = self._board.get_tile(kill_pos).piece
                            
                            if kill_piece is self.moves[-1].piece and dst_piece is None:
                                yield EnPassantMove(pos, dst_pos, kill_pos, piece, kill_piece)
                
                # Generate casteling
                if isinstance(piece, King):
                    for queen_side in [False, True]:
                        row = 0 if piece.is_black else 7

                        if piece in self._castle_pieces_move_cnt:
                            king_original = (pos == (row, 4)) and self._castle_pieces_move_cnt[piece] == 0
                        else:
                            king_original = False

                        rook = self.board.get_tile((row, 0 if queen_side else 7)).piece
                        if rook in self._castle_pieces_move_cnt:
                            rook_original = self._castle_pieces_move_cnt[rook] == 0
                        else:
                            rook_original = False

                        valid = king_original and rook_original and not self._is_in_check[piece.is_black]
                        for dist in [1, 2]:
                            valid = valid and self.try_move(NormalMove(pos, (pos[0], pos[1] - (dist if queen_side else -dist)), piece))
                                        
                        if valid:
                            yield CastelingMove(piece, queen_side)

    def generate_all_moves(self, black: Optional[bool] = None, check_test: bool=True) -> Generator[Move, None, None]:
        with self._lock:
            if black is None:
                black = self.black_turn
            for pos in itertools.product(range(8), range(8)):
                piece = self._board.get_tile(pos).piece
                if piece is not None and piece.is_black == black:
                    yield from self.generate_moves(pos, check_test)

    def generate_attacked_positions(self, black: bool) -> Generator[Tuple[int, int], None, None]:
        with self._lock:
            for move in self.generate_all_moves(black, check_test=False):
                if isinstance(move, GeneralKillMove):
                    yield move.get_attack_pos()

    def get_king_position(self, black: bool) -> Tuple[int, int]:
        with self._lock:
            for pos in itertools.product(range(8), range(8)):
                piece = self._board.get_tile(pos).piece
                if piece is not None and piece.is_black == black and isinstance(piece, King):
                    return pos
            raise RuntimeError("King not found")

    def draw(self, screen) -> None:
        with self._lock:
            if self._preserved_board is not None:
                board = self._preserved_board
                is_check = self._preserved_check
            else:
                board = self._board
                is_check = self._is_in_check

            for black in [False, True]:
                if is_check[black]:
                    board.get_tile(self.get_king_position(black)).change_to_check()
            board.draw(screen)
