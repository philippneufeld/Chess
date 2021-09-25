# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
import pygame
import time
from chess.manager import GameManager

class Game:

    def __init__(self, size, img_path):
        self._size = size
        self._tile_size = size // 8

        pygame.init()
        img_pieces = pygame.image.load(img_path)
        rect = img_pieces.get_rect()
        if rect.height * 3 != rect.width or rect.height % 2 != 0:
            raise RuntimeError("Invalid image dimensions")
        img_piece_size = rect.height // 2

        self._game_manager = GameManager(self._tile_size, img_pieces, img_piece_size)

        self._piece_selected = False
        self._selectable_moves = {}

    def draw(self, screen) -> None:
        self._game_manager.draw(screen)
        pygame.display.update()

    def on_click(self, mouse_pos: Tuple[int, int]) -> None:
        pos = mouse_pos[1] // self._tile_size, mouse_pos[0] // self._tile_size

        self._game_manager.reset_board_highlights()

        if self._game_manager.is_game_over:
            return

        try:
            piece = self._game_manager.board.get_tile(pos).piece
        except Exception:
            piece = None

        if piece is not None and piece.is_black == self._game_manager.black_turn and not self._piece_selected:
            self._game_manager.board.get_tile(pos).change_to_selected()

            self._piece_selected = True
            self._selectable_moves = {}

            for move in self._game_manager.generate_moves(pos):
                activation_pos = move.get_activation_pos()
                if activation_pos in self._selectable_moves:
                    raise RuntimeError(f"Move to {activation_pos} already present")
                move.color_board(self._game_manager.board)
                self._selectable_moves[activation_pos] = move
        else:
            if pos in self._selectable_moves:
                self._game_manager.push_move(self._selectable_moves[pos])
            self._piece_selected = False
            self._selectable_moves = {}

    def run(self) -> None:
        
        screen = pygame.display.set_mode((self._size, self._size))
        pygame.display.set_caption("Chess")

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
            time.sleep(.01)

        pygame.quit()