from settings import *
from os import path
from pygame.image import load

class Score:
    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self.surface = pygame.Surface((SIDEBAR_WIDTH, GAME_HEIGHT * SCORE_HEIGHT_FRACTION - PADDING))
        self.rect = self.surface.get_rect(bottomright = (WINDOW_WIDTH - PADDING, WINDOW_HEIGHT - PADDING))

        self.shape_surfaces = {shape: load(path.join('..', 'graphics', f'{shape}.png')).convert_alpha() for shape in TETROMINOS.keys()}


    def display_held_piece(self, held_piece):
        if held_piece:
            shape_surface = self.shape_surfaces[held_piece]
            x = self.surface.get_width() / 2
            y = self.surface.get_height() / 2
            rect = shape_surface.get_rect(center=(x,y))
            self.surface.blit(shape_surface, rect)

    def run(self, held_piece):
        self.surface.fill(GRAY)
        self.display_held_piece(held_piece)
        self.display_surface.blit(self.surface, self.rect)
        pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)