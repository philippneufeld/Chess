# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple
import pygame
from copy import deepcopy


class PieceMovementDescriptor:

    def __init__(self, basis_vec: Tuple[int, int], max_steps: int, kill_level: int):
        self._basis_vec = basis_vec
        self._max_steps = max_steps
        self._kill_level = kill_level # 0: cannot kill, 1: can kill, 2: must kill

    @property
    def basis_vec(self) -> Tuple[int, int]:
        return self._basis_vec

    @property
    def max_steps(self) -> int:
        return self._max_steps

    @property
    def kill_level(self) -> int:
        return self._kill_level


class Piece:

    def __init__(self, is_black: bool, img, img_idx_x: int, img_size: int):
        self._is_black = is_black

        # Handle image
        img_pos = (img_idx_x * img_size, img_size if is_black else 0)
        self._size = img_size
        self._full_size_img = pygame.Surface((img_size, img_size), pygame.SRCALPHA)
        self._full_size_img.blit(img, (0, 0), (*img_pos, img_size, img_size))
        self._img = self._full_size_img   

    def __deepcopy__(self, memo):
        # has to be defined bcause pygame.Surface is incompatible with deepcopy
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if type(v) == pygame.Surface and id(v) not in memo:
                cv = v.copy()
                memo[id(v)] = cv
                setattr(result, k, cv)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result
     
    def __repr__(self) -> str:
        return "?"

    @property
    def is_black(self) -> bool:
        return self._is_black

    def draw(self, screen, x: int, y: int, size: int) -> None:
        if self._size != size:
            self._size = max(1, size)
            self._img = pygame.transform.smoothscale(self._full_size_img, (self._size, self._size))
        screen.blit(self._img, (x, y))

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        raise NotImplementedError


class King(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 0, img_size)

    def __repr__(self) -> str:
        return "K"

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        for vec in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]:
            yield PieceMovementDescriptor(vec, 1, 1)


class Queen(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 1, img_size)

    def __repr__(self) -> str:
        return "Q"

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        for vec in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, -1), (-1, 1)]:
            yield PieceMovementDescriptor(vec, 8, 1)


class Bishop(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 2, img_size)

    def __repr__(self) -> str:
        return "B"

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        for vec in [(1, 1), (1, -1), (-1, -1), (-1, 1)]:
            yield PieceMovementDescriptor(vec, 8, 1)


class Knight(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 3, img_size)

    def __repr__(self) -> str:
        return "N"

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        for vec in [(2, -1), (2, 1), (-2, -1), (-2, 1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            yield PieceMovementDescriptor(vec, 1, 1)


class Rook(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 4, img_size)

    def __repr__(self) -> str:
        return "R"

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        for vec in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            yield PieceMovementDescriptor(vec, 8, 1)


class Pawn(Piece):

    def __init__(self, is_black: bool, img, img_size: int):
        super().__init__(is_black, img, 5, img_size)

    def __repr__(self) -> str:
        return ""

    def get_movement_bases(self, pos: Tuple[int, int]) -> Generator[PieceMovementDescriptor, None, None]:
        is_base_row = pos[0] == (1 if self.is_black else 6)
        mv_dir = 1 if self.is_black else -1
        yield PieceMovementDescriptor((mv_dir, 0), 2 if is_base_row else 1, 0)
        yield PieceMovementDescriptor((mv_dir, 1), 1, 2)
        yield PieceMovementDescriptor((mv_dir, -1), 1, 2)
