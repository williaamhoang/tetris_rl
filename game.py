from settings import *
from random import choice

from timer import Timer

class Game:

    def __init__(self, get_next_shape):

        # General
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.rect = self.surface.get_rect(topleft = (PADDING, PADDING))
        self.sprites = pygame.sprite.Group()

        # Game connection
        self.get_next_shape = get_next_shape

        # Lines
        self.line_surface = self.surface.copy()
        # Because we have a black background in our main game screen portion, any objects generated will be hidden by the background
        # To circumvent this, we fill the background color with green, and use set_colorkey() to tell Pygame to ignore this color
        # Allowing whatever is rendered on top of the grid to be visible
        self.line_surface.fill((0,255,0))
        self.line_surface.set_colorkey((0,255,0))
        self.line_surface.set_alpha(120)

        # Tetromino
        self.field_data = [[0 for x in range(COLUMNS)] for y in range(ROWS)]
        self.tetromino = Tetromino(
            choice(list(TETROMINOS.keys())), 
            self.sprites, 
            self.create_new_tetromino,
            self.field_data)

        # Timer
        self.timers = {
            'vertical move': Timer(UPDATE_START_SPEED, True, self.move_down),
            'horizontal move': Timer(MOVE_WAIT_TIME),
            'rotate': Timer(ROTATE_WAIT_TIME)
        }
        self.timers['vertical move'].activate()

    def create_new_tetromino(self):
        
        self.check_finished_rows()
        self.tetromino = Tetromino(
            self.get_next_shape(),
            self.sprites, 
            self.create_new_tetromino,
            self.field_data)

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

        # Checking horizonal movement
        if not self.timers['horizontal move'].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers['horizontal move'].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers['horizontal move'].activate()

        # Check for rotation
        if not self.timers['rotate'].active:
            if keys[pygame.K_UP]:
                self.tetromino.rotate()
                self.timers['rotate'].activate()

    def check_finished_rows(self):

        # Get the full row indexes
        delete_rows = []
        for i, row in enumerate(self.field_data):
            if all(row):
                delete_rows.append(i)
        
        if delete_rows:
            for delete_row in delete_rows:

                # Delete the full rows
                for block in self.field_data[delete_row]:
                    block.kill()

                # Move down the blocks
                for row in self.field_data:
                    for block in row:
                        if block and block.pos.y < delete_row:
                            block.pos.y += 1
            
            # Rebuild the field data
            self.field_data = [[0 for x in range(COLUMNS)] for y in range(ROWS)]
            for block in self.sprites:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block

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
    def __init__(self, shape, group, create_new_tetromino, field_data):

        # Setup
        self.shape = shape
        self.block_positions = TETROMINOS[shape]['shape']
        self.color = TETROMINOS[shape]['color']
        self.create_new_tetromino = create_new_tetromino
        self.field_data = field_data


        # Create blocks with list comprehension
        self.blocks = [Block(group, pos, self.color) for pos in self.block_positions]

    # Collision
    def next_move_horizontal_collide(self, blocks, amount):
        collision_list = [block.horizontal_collide(int(block.pos.x + amount), self.field_data) for block in self.blocks]
        return True if any(collision_list) else False

    def next_move_vertical_collide(self, blocks, amount):
        collision_list = [block.vertical_collide(int(block.pos.y + amount), self.field_data) for block in self.blocks]
        return True if any(collision_list) else False

    # Movement
    def move_horizontal(self, amount):
        if not self.next_move_horizontal_collide(self.blocks, amount):    
            for block in self.blocks:
                block.pos.x += amount

    def move_down(self):
        if not self.next_move_vertical_collide(self.blocks, 1):
            for block in self.blocks:
                block.pos.y += 1
        else:
            for block in self.blocks:
                self.field_data[int(block.pos.y)][int(block.pos.x)] = block
            self.create_new_tetromino()

    # Rotate
    def rotate(self):
        if self.shape != 'O':

            # 1. Pivot Point
            pivot_pos = self.blocks[0].pos

            # 2. New block positions
            new_block_positions = [block.rotate(pivot_pos) for block in self.blocks]

            # 3. Collision Check
            for pos in new_block_positions:
                # Horizontal
                if pos.x < 0 or pos.x >= COLUMNS:
                    return

                # Field Check = Collision with other pieces
                if self.field_data[int(pos.y)][int(pos.x)]:
                    return

                # Vertical / Floor check
                if pos.y > ROWS:
                    return

            # 4. Implement new positions
            for i, block in enumerate(self.blocks):
                block.pos = new_block_positions[i]

class Block(pygame.sprite.Sprite):
    def __init__(self, group, pos, color):

        # General
        super().__init__(group)
        self.image = pygame.Surface((CELL_SIZE, CELL_SIZE))
        self.image.fill(color)

        # Position
        self.pos = pygame.Vector2(pos) + BLOCK_OFFSET
        self.rect = self.image.get_rect(topleft = self.pos * CELL_SIZE)

    def rotate(self, pivot_pos):
        return pivot_pos + (self.pos - pivot_pos).rotate(90)

    def horizontal_collide(self, x, field_data):
        if not 0 <= x < COLUMNS:
            return True

        if field_data[int(self.pos.y)][x]: 
            return True

    def vertical_collide(self, y, field_data):
        if y >= ROWS:
            return True

        if y >= 0 and field_data[y][int(self.pos.x)]:
            return True

    def update(self):
        self.rect.topleft = self.pos * CELL_SIZE
