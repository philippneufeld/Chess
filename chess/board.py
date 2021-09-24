# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
import pygame
from chess.piece import Piece

class BoardTile:

    WHITE = (255, 255, 255)
    GREY = (128, 128, 128)
    YELLOW = (214, 204, 0)
    BLUE = (50, 255, 255)
    RED = (255, 50, 50)
    BLACK = (0, 0, 0)

    def __init__(self, row: int, col: int, size: int):
        self._x = col * size
        self._y = row * size
        self._size = size
        self._default_color = self.WHITE if (row % 2 == col % 2) else self.GREY
        self._color = self._default_color
        self._piece: Piece = None

    @property
    def piece(self) -> Piece:
        return self._piece

    @piece.setter
    def piece(self, p: Piece) -> None:
        self._piece = p

    def change_to_default(self) -> None:
        self._color = self._default_color

    def change_to_selected(self) -> None:
        self._color = self.YELLOW

    def change_to_movable(self) -> None:
        self._color = self.BLUE

    def change_to_killable(self) -> None:
        self._color = self.RED

    def draw(self, screen) -> None:
        rect_border = (self._x, self._y, self._size, self._size)
        rect = (self._x, self._y, self._size - 1, self._size - 1)
        pygame.draw.rect(screen, self.BLACK, rect_border)
        pygame.draw.rect(screen, self._color, rect)
        if self._piece is not None:
            self._piece.draw(screen, self._x, self._y, self._size)


class Board:

    def __init__(self, tile_size):
        self._tiles = [BoardTile(idx // 8, idx % 8, tile_size) for idx in range(64)]

    def draw(self, screen):
        for tile in self._tiles:
            tile.draw(screen)

    def is_pos_valid(self, pos):
        row, col = pos
        return (0 <= row <= 7 and 0 <= col <= 7)

    def get_tile(self, pos) -> BoardTile:
        if not self.is_pos_valid(pos):
            raise RuntimeError("Invalid position")
        row, col = pos
        return self._tiles[row*8+col]

    def change_all_to_default(self):
        for tile in self._tiles:
            tile.change_to_default()
