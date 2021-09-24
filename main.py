# Copyright Philipp Neufeld, 2021
from typing import List, Generator, Tuple

import pygame
import time

class MovementBasis:

    def __init__(self, basis_vecs: List[Tuple[int, int]], dist: int, kill_level: int):
        self.basis_vecs = basis_vecs
        self.dist = dist
        self.kill_level = kill_level # 0: cannot kill, 1: can kill, 2: must kill

class Piece:

    straight_basis_vecs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    diagonal_basis_vecs = [(1, 1), (1, -1), (-1, -1), (-1, 1)]

    def __init__(self, is_black, img, img_pos, img_size):
        self.is_black = is_black

        self.size = img_size
        self.full_size_img = pygame.Surface((img_size, img_size), pygame.SRCALPHA)
        self.full_size_img.blit(img, (0, 0), (*img_pos, img_size, img_size))
        self.img = self.full_size_img   

    def draw(self, screen, x, y, size):
        if self.size != size:
            self.size = max(1, size)
            self.img = pygame.transform.smoothscale(self.full_size_img, (self.size, self.size))
        screen.blit(self.img, (x, y))

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        raise NotImplementedError


class King(Piece):

    def __init__(self, is_black, img, img_size):
        img_pos = (0, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        yield MovementBasis(self.straight_basis_vecs, 1, 1)
        yield MovementBasis(self.diagonal_basis_vecs, 1, 1)


class Queen(Piece):

    def __init__(self, is_black, img, img_size):
        img_pos = (img_size, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        yield MovementBasis(self.straight_basis_vecs, 8, 1)
        yield MovementBasis(self.diagonal_basis_vecs, 8, 1)


class Bishop(Piece):

    def __init__(self, is_black, img, img_size):
        img_pos = (2 * img_size, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        yield MovementBasis(self.diagonal_basis_vecs, 8, 1)


class Knight(Piece):

    knight_basis_vecs = [(2, -1), (2, 1), (-2, -1), (-2, 1), (1, 2), (1, -2), (-1, 2), (-1, -2)]

    def __init__(self, is_black, img, img_size):
        img_pos = (3 * img_size, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        yield MovementBasis(self.knight_basis_vecs, 1, 1)


class Rook(Piece):

    def __init__(self, is_black, img, img_size):
        img_pos = (4 * img_size, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        yield MovementBasis(self.straight_basis_vecs, 8, 1)


class Pawn(Piece):

    def __init__(self, is_black, img, img_size):
        img_pos = (5 * img_size, img_size if is_black else 0)
        super().__init__(is_black, img, img_pos, img_size)

    def get_movement_bases(self, pos) -> Generator[MovementBasis, None, None]:
        is_base_row = pos[0] == (1 if self.is_black else 6)
        mv_dir = 1 if self.is_black else -1
        yield MovementBasis([(mv_dir, 0)], 2 if is_base_row else 1, 0)
        yield MovementBasis([(mv_dir, -1), (mv_dir, 1)], 1, 2)


class BoardTile:

    WHITE = (255, 255, 255)
    GREY = (128, 128, 128)
    YELLOW = (214, 204, 0)
    BLUE = (50, 255, 255)
    RED = (255, 50, 50)
    BLACK = (0, 0, 0)

    def __init__(self, row, col, size):
        self.x = col * size
        self.y = row * size
        self.size = size
        self.default_color = self.WHITE if (row % 2 == col % 2) else self.GREY
        self.color = self.default_color
        self.piece: Piece = None

    def change_to_default(self):
        self.color = self.default_color

    def change_to_selected(self):
        self.color = self.YELLOW

    def change_to_movable(self):
        self.color = self.BLUE

    def change_to_killable(self):
        self.color = self.RED

    def draw(self, screen):
        rect = (self.x, self.y, self.size, self.size)
        pygame.draw.rect(screen, self.color, rect)

        if self.piece is not None:
            self.piece.draw(screen, self.x, self.y, self.size)


class Board:

    def __init__(self, tile_size):
        self.tiles = [BoardTile(idx // 8, idx % 8, tile_size) for idx in range(64)]

    def draw(self, screen):
        for tile in self.tiles:
            tile.draw(screen)

    def is_pos_valid(self, pos):
        row, col = pos
        return (0 <= row <= 7 and 0 <= col <= 7)

    def get_tile(self, pos) -> BoardTile:
        if not self.is_pos_valid(pos):
            raise RuntimeError("Invalid position")
        row, col = pos
        return self.tiles[row*8+col]

    def change_all_to_default(self):
        for tile in self.tiles:
            tile.change_to_default()


class PartialMove:

    def __init__(self, pos, src_piece: Piece, dst_piece: Piece):
        self.pos = pos
        self.src_piece = src_piece
        self.dst_piece = dst_piece

class Move:

    def __init__(self):
        pass

    def __repr__(self):
        return "Unknown move"

    def get_partial_moves(self):
        return []
    
    def get_kill_pos(self):
        return None 

    def get_non_kill_pos(self):
        return None

    def color_board(self):
        pass


class NormalMove(Move):

    def __init__(self, src_pos, dst_pos, piece, kill_piece):
        super().__init__()
        self.src_pos = src_pos
        self.dst_pos = dst_pos
        self.piece = piece
        self.kill_piece = kill_piece

        self.partial_moves = []
        self.partial_moves.append(PartialMove(self.src_pos, self.piece, None))
        self.partial_moves.append(PartialMove(self.dst_pos, self.kill_piece, self.piece))

    def get_partial_moves(self):
        return self.partial_moves

    def get_kill_pos(self):
        return self.dst_pos if self.kill_piece is not None else None 

    def get_non_kill_pos(self):
        return self.dst_pos if self.kill_piece is None else None 


class Game:

    def __init__(self, size, img_path):
        self.tile_size = size // 8
        self.board = Board(self.tile_size)

        img_pieces = pygame.image.load(img_path)
        rect = img_pieces.get_rect()
        if rect.height * 3 != rect.width or rect.height % 2 != 0:
            raise RuntimeError("Invalid image dimensions")
        img_piece_size = rect.height // 2

        # Initialize pieces to start positions
        for i in [0, 1]:
            is_black = [True, False]
            base_row = [0, 7]
            pawn_row = [1, 6]

            self.board.get_tile((base_row[i], 0)).piece = Rook(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 1)).piece = Knight(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 2)).piece = Bishop(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 3)).piece = Queen(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 4)).piece = King(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 5)).piece = Bishop(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 6)).piece = Knight(is_black[i], img_pieces, img_piece_size)
            self.board.get_tile((base_row[i], 7)).piece = Rook(is_black[i], img_pieces, img_piece_size)

            for j in range(8):
                self.board.get_tile((pawn_row[i], j)).piece = Pawn(is_black[i], img_pieces, img_piece_size)

        # create moves array
        self.moves = []
        
        self.piece_selected = False
        self.black_turn = False
        self.selectable_moves = {}

    def draw_board(self, screen):
        self.board.draw(screen)

    def push_move(self, move: Move):      
        for pm in move.get_partial_moves():
            tile = self.board.get_tile(pm.pos)
            if tile.piece is not pm.src_piece:
                raise RuntimeError("Invalid move")
            tile.piece = pm.dst_piece 
        self.moves.append(move)
        self.black_turn = not self.black_turn

    def pop_move(self):      
        if len(self.moves) == 0:
            raise RuntimeError("No move to pop")

        move = self.moves.pop()
        for pm in reversed(move.get_partial_moves()):
            tile = self.board.get_tile(pm.pos)
            if tile.piece is not pm.dst_piece:
                raise RuntimeError("Invalid move")
            tile.piece = pm.src_piece

        self.black_turn = not self.black_turn

    def generate_moves(self, pos):
        piece: Piece = self.board.get_tile(pos).piece
        if piece is None:
            return
        else:
            for basis in piece.get_movement_bases(pos):
                for vec in basis.basis_vecs:
                    for i in range(1, basis.dist + 1):

                        # generate new position
                        dst_pos = pos[0] + i * vec[0], pos[1] + i * vec[1]
                        if not self.board.is_pos_valid(dst_pos):
                            break

                        # if the dst_piece is friendly cannot occupy its tile
                        dst_piece = self.board.get_tile(dst_pos).piece

                        if basis.kill_level == 2 and dst_piece is None:
                            break   # 2 means that the move must kill
                        elif dst_piece is not None and (piece.is_black == dst_piece.is_black or basis.kill_level == 0):
                            break   # cannot kill dst_piece (either friendly or too low kill_level)
                        else:
                            yield NormalMove(pos, dst_pos, piece, dst_piece)

                        # once another piece is hit the piece cannot go any further
                        if dst_piece is not None:
                            break

    def on_click(self, mouse_pos):
        pos = mouse_pos[1] // self.tile_size, mouse_pos[0] // self.tile_size

        self.board.change_all_to_default()

        try:
            piece = self.board.get_tile(pos).piece
        except Exception:
            piece = None

        if piece is not None and piece.is_black == self.black_turn and not self.piece_selected:
            self.board.get_tile(pos).change_to_selected()

            self.piece_selected = True
            self.selectable_moves = {}

            for move in self.generate_moves(pos):

                kill_pos = move.get_kill_pos()
                if kill_pos is not None:
                    if kill_pos in self.selectable_moves:
                        raise RuntimeError(f"Move to {kill_pos} already present")
                    self.board.get_tile(kill_pos).change_to_killable()
                    self.selectable_moves[kill_pos] = move

                non_kill_pos = move.get_non_kill_pos()
                if non_kill_pos is not None:
                    if non_kill_pos in self.selectable_moves:
                        raise RuntimeError(f"Move to {kill_pos} already present")
                    self.board.get_tile(non_kill_pos).change_to_movable()
                    self.selectable_moves[non_kill_pos] = move
        else:
            if pos in self.selectable_moves:
                self.push_move(self.selectable_moves[pos])
            self.piece_selected = False
            self.selectable_moves = {}


if __name__ == "__main__":

    pygame.init()

    width = 800
    screen = pygame.display.set_mode((width, width))
    pygame.display.set_caption("Chess")

    game = Game(width, 'chess_pieces.png')
    game.draw_board(screen)

    running = True
    while running:

        pygame.time.delay(10)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                game.on_click(event.dict['pos'])

        game.draw_board(screen)
        pygame.display.update()
        time.sleep(.01)

    pygame.quit()

    print("Application exit")
