from settings import *
from random import choice

from timer import Timer

class Game:

    def __init__(self):

        # General
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.rect = self.surface.get_rect(topleft = (PADDING, PADDING))
        self.sprites = pygame.sprite.Group()

        # Lines
        self.line_surface = self.surface.copy()
        # Because we have a black background in our main game screen portion, any objects generated will be hidden by the background
        # To circumvent this, we fill the background color with green, and use set_colorkey() to tell Pygame to ignore this color
        # Allowing whatever is rendered on top of the grid to be visible
        self.line_surface.fill((0,255,0))
        self.line_surface.set_colorkey((0,255,0))
        self.line_surface.set_alpha(120)

        # Tetromino
        self.tetromino = Tetromino(choice(list(TETROMINOS.keys())), self.sprites)

        # Timer
        self.timers = {
            'vertical move': Timer(UPDATE_START_SPEED, True, self.move_down),
            'horizontal move': Timer(MOVE_WAIT_TIME)
        }
        self.timers['vertical move'].activate()

    def timer_update(self):
        for timer in self.timers.values():
            timer.update()

    def move_down(self):
        self.tetromino.move_down()
    
    def draw_grid(self):

        for col in range(1, COLUMNS):
            x = col * CELL_SIZE
            pygame.draw.line(self.surface, LINE_COLOR, (x, 0), (x, self.surface.get_height()), 1)

        for row in range(1, ROWS):
            y = row * CELL_SIZE
            pygame.draw.line(self.surface, LINE_COLOR, (0, y),(self.surface.get_width(), y), 1)

        self.surface.blit(self.line_surface, (0,0))

    def input(self):
        keys = pygame.key.get_pressed()

        if not self.timers['horizontal move'].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers['horizontal move'].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers['horizontal move'].activate()

    def run(self):

        # Update
        self.input()
        self.timer_update()
        self.sprites.update()

        # Drawing
        self.surface.fill(GRAY)
        self.sprites.draw(self.surface)

        self.draw_grid()
        self.display_surface.blit(self.surface, (PADDING, PADDING))
        pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)

class Tetromino:
    def __init__(self, shape, group):

        # Setup
        self.block_positions = TETROMINOS[shape]['shape']
        self.color = TETROMINOS[shape]['color']

        # Create blocks with list comprehension
        self.blocks = [Block(group, pos, self.color) for pos in self.block_positions]

    # Collision
    def next_move_horizontal_collide(self, blocks, amount):
        collision_list = [block.horizontal_collide(int(block.pos.x + amount)) for block in self.blocks]
        return True if any(collision_list) else False

    # Movement
    def move_horizontal(self, amount):
        if not self.next_move_horizontal_collide(self.blocks, amount):    
            for block in self.blocks:
                block.pos.x += amount

    def move_down(self):
        for block in self.blocks:
            block.pos.y += 1

class Block(pygame.sprite.Sprite):
    def __init__(self, group, pos, color):

        # General
        super().__init__(group)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(color)

        # Position
        self.pos = pygame.Vector2(pos) + BLOCK_OFFSET
        self.rect = self.image.get_rect(topleft = self.pos * CELL_SIZE)

    def horizontal_collide(self, x):
        if not 0 <= x < COLUMNS:
            return True

    def update(self):
        self.rect.topleft = self.pos * CELL_SIZE
