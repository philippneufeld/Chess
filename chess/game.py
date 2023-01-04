# Copyright Philipp Neufeld, 2021
from typing import Callable, Tuple
import pygame
import time
import threading
from chess.move import Move, PawnTransformMove, PawnTransformKillMove
from chess.piece import Piece, Queen, Rook, Bishop, Knight
from chess.manager import GameManager

class TransformPieceSelector:

    DARK_GREY = (75, 75, 75)
    LIGHT_GREY = (150, 150, 150)

    def __init__(self, size: int, img_pieces, img_piece_size: int):
        self._size = size
        self._img_pieces = img_pieces
        self._img_piece_size = img_piece_size

        self._rects = {
            Queen: None,
            Rook: None,
            Bishop: None,
            Knight: None
        }

    def _create_piece(self, is_black: bool, piece_cls: type) -> Piece:
        if not issubclass(piece_cls, Piece):
            raise RuntimeError("Invalid piece class")
        return piece_cls(is_black, self._img_pieces, self._img_piece_size)

    def draw(self, screen, black: bool) -> None:
        x_rect = self._size // 10
        y_rect = 2 * self._size // 5
        width_rect = self._size - 2*x_rect
        height_rect = self._size - 2*y_rect
        pygame.draw.rect(screen, self.DARK_GREY, (x_rect, y_rect, width_rect, height_rect), border_radius=height_rect // 8)

        x_offset = width_rect // 13
        width = 2*x_offset
        y_offset = y_rect + (height_rect - width) // 2

        self._rects[Queen] = (x_rect + x_offset, y_offset, width, width)
        self._rects[Rook] = (x_rect + 4*x_offset, y_offset, width, width)
        self._rects[Bishop] = (x_rect + 7*x_offset, y_offset, width, width)
        self._rects[Knight] = (x_rect + 10*x_offset, y_offset, width, width)

        pygame.draw.rect(screen, self.LIGHT_GREY, self._rects[Queen], border_radius=width // 8)
        pygame.draw.rect(screen, self.LIGHT_GREY, self._rects[Rook], border_radius=width // 8)
        pygame.draw.rect(screen, self.LIGHT_GREY, self._rects[Bishop], border_radius=width // 8)
        pygame.draw.rect(screen, self.LIGHT_GREY, self._rects[Knight], border_radius=width // 8)
        
        self._create_piece(black, Queen).draw(screen, *self._rects[Queen][:3])
        self._create_piece(black, Rook).draw(screen, *self._rects[Rook][:3])
        self._create_piece(black, Bishop).draw(screen, *self._rects[Bishop][:3])
        self._create_piece(black, Knight).draw(screen, *self._rects[Knight][:3])

    def select_transform_class(self, mouse_pos: Tuple[int, int]) -> type:
        for ty, r in self._rects.items():
            if r is not None and r[0] <= mouse_pos[0] <= r[0] + r[2] and r[1] <= mouse_pos[1] <= r[1] + r[3]:
                return ty
        return None

class PlayerBase(threading.Thread):

    def __init__(self, game_manager, is_black: bool) -> None:
        super().__init__(daemon=True)
        
        self._game_manager = game_manager
        self._is_black = is_black

        self._move_finished_callback = None
        self._wakeup = threading.Event()
        self._wakeup.clear()

    def execute_turn(self) -> None:
        self._wakeup.set()

    def set_turn_finished(self) -> None:
        if callable(self._move_finished_callback):
            self._move_finished_callback()
    
    def set_finished_callback(self, callback: Callable[[], None]):
        self._move_finished_callback = callback

    def run(self) -> None:
        raise NotImplementedError

    def draw(self, screen) -> None:
        pass

    def on_tile_clicked(self, mouse_pos: Tuple[int, int]) -> None:
        pass


class Player(PlayerBase):

    def __init__(self, game_manager, is_black: bool, tile_size, img_pieces, img_piece_size) -> None:
        super().__init__(game_manager, is_black)
        self._tile_size = tile_size

        self._mouse_pos = None

        self._piece_selected = False
        self._selectable_moves = {}

        self._transform_piece_selector = TransformPieceSelector(8*tile_size, img_pieces, img_piece_size)
        self._transform_selection_mode = False
        self._transform_moves = []

    def on_tile_clicked(self, mouse_pos: Tuple[int, int]) -> None:
        if not self._wakeup.is_set() and self._game_manager.black_turn == self._is_black:
            self._mouse_pos = mouse_pos
            self._wakeup.set()

    def run(self):
        while True:
            self._wakeup.wait()
            if self._mouse_pos is not None:
                mouse_pos = self._mouse_pos
                self._mouse_pos = None
                self._run(mouse_pos)
            self._wakeup.clear()

    def _run(self, mouse_pos) -> None:
        pos = mouse_pos[1] // self._tile_size, mouse_pos[0] // self._tile_size

        if self._game_manager.is_game_over or self._is_black != self._game_manager.black_turn:
            return

        execute_move = None
        if self._transform_selection_mode:
            piece_type = self._transform_piece_selector.select_transform_class(mouse_pos)
            
            if piece_type in [Queen, Rook, Bishop, Knight]:
                move = None
                for m in self._transform_moves:
                    if type(m.transform_piece) is piece_type:
                        move = m
                        break
                if move is None:
                    raise RuntimeError("Tranform move not found")
                execute_move = move

                self._transform_moves = []
                self._transform_selection_mode = False
        else:
            try:
                piece = self._game_manager.board.get_tile(pos).piece
            except Exception:
                piece = None

            if piece is not None and piece.is_black == self._is_black and not self._piece_selected:
                self._game_manager.board.get_tile(pos).change_to_selected()

                self._piece_selected = True
                self._selectable_moves = {}

                for move in self._game_manager.generate_moves(pos):
                    activation_pos = move.get_activation_pos()
                    if activation_pos in self._selectable_moves:
                        self._selectable_moves[activation_pos].append(move)
                    else:
                        self._selectable_moves[activation_pos] = [move,]
                    move.color_board(self._game_manager.board)
            else:
                if pos in self._selectable_moves:
                    if len(self._selectable_moves[pos]) == 1:
                        execute_move = self._selectable_moves[pos][0]
                    elif len(self._selectable_moves[pos]) == 4:
                        self._transform_selection_mode = True
                        self._transform_moves = self._selectable_moves[pos]
                    elif len(self._selectable_moves) == 0:
                        pass
                    else:
                        raise RuntimeError("Invalid number of selectable move for one board tile")
                self._piece_selected = False
                self._selectable_moves = {}

        if execute_move is not None:
            self._game_manager.push_move(execute_move)
            self.set_turn_finished()

    def draw(self, screen) -> None:
        if self._transform_selection_mode and self._game_manager.black_turn == self._is_black:
            self._transform_piece_selector.draw(screen, self._is_black)


class Game:

    def __init__(self, size, img_path: str, white_type: type, black_type: type) -> None:
        self._size = size
        self._tile_size = size // 8

        pygame.init()
        img_pieces = pygame.image.load(img_path)
        rect = img_pieces.get_rect()
        if rect.height * 3 != rect.width or rect.height % 2 != 0:
            raise RuntimeError("Invalid image dimensions")
        img_piece_size = rect.height // 2

        self._game_manager = GameManager(self._tile_size, img_pieces, img_piece_size)
        self.white_player = white_type(self._game_manager, False, self._tile_size, img_pieces, img_piece_size)
        self.black_player = black_type(self._game_manager, True, self._tile_size, img_pieces, img_piece_size)

        self.white_player.set_finished_callback(self.black_player.execute_turn)
        self.black_player.set_finished_callback(self.white_player.execute_turn)

    def draw(self, screen) -> None:
        self._game_manager.draw(screen)

        self.white_player.draw(screen)
        self.black_player.draw(screen)

        pygame.display.update()

    @staticmethod
    def mouse_pos_in_rect(mouse_pos, rect):
        if rect[0] <= mouse_pos[0] <= rect[0] + rect[2]:
            if rect[1] <= mouse_pos[1] <= rect[1] + rect[3]:
                return True
        return False

    def on_click(self, mouse_pos: Tuple[int, int]) -> None:
        self._game_manager.reset_board_highlights()
        if self._game_manager.black_turn:
            self.black_player.on_tile_clicked(mouse_pos)
        else:
            self.white_player.on_tile_clicked(mouse_pos)

    def run(self) -> None:
        
        screen = pygame.display.set_mode((self._size, self._size))
        pygame.display.set_caption("Chess")

        self.white_player.start()
        self.black_player.start()
        self.white_player.execute_turn()

        self.draw(screen)

        running = True
        while running:

            pygame.time.delay(10)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click(event.dict['pos'])

            self.draw(screen)
            pygame.time.delay(1)

        pygame.quit()