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
            'rotate': Timer(ROTATE_WAIT_TIME),
            'down move': Timer(DOWN_MOVE_SPEED)
        }
        self.timers['vertical move'].activate()
        self.held_piece = None
        self.can_hold = True

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.tetromino.move_horizontal(-1)
            elif event.key == pygame.K_RIGHT:
                self.tetromino.move_horizontal(1)
            elif event.key == pygame.K_DOWN:
                self.tetromino.move_down()
            elif event.key == pygame.K_UP:
                self.tetromino.rotate()
            elif event.key == pygame.K_SPACE:
                self.place_tetromino()

    def hold_piece(self):
        if not self.can_hold:
            return
        
        self.can_hold = False

        for block in self.tetromino.blocks:
            x, y = int(block.pos.x), int(block.pos.y)
            if 0 <= x < COLUMNS and 0 <= y < ROWS:
                self.field_data[y][x] = 0
            block.kill()

        if self.held_piece is None:
            self.held_piece = self.tetromino.shape
            self.create_new_tetromino()
        else: 
            current_piece = self.tetromino.shape
            self.tetromino = Tetromino(
                self.held_piece, self.sprites, self.create_new_tetromino, self.field_data
            )
            self.held_piece = current_piece
        
    def create_new_tetromino(self):
        self.check_finished_rows()
        self.tetromino = Tetromino(
            self.get_next_shape(),
            self.sprites, 
            self.create_new_tetromino,
            self.field_data
        )
        self.can_hold = True
        self.tetromino.landed = False # Reset landed state

    def timer_update(self):
        for key, timer in self.timers.items():
            if key == 'vertical move' and not self.tetromino.landed:
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

        # Hold piece
        if keys[pygame.K_c]:
            self.hold_piece()

        # Checking horizonal movement
        if not self.timers['horizontal move'].active:
            if keys[pygame.K_LEFT]:
                self.tetromino.move_horizontal(-1)
                self.timers['horizontal move'].activate()
            if keys[pygame.K_RIGHT]:
                self.tetromino.move_horizontal(1)
                self.timers['horizontal move'].activate()

        # Downward movement
        if keys[pygame.K_DOWN]:
            self.tetromino.move_down()

        # Check for rotation
        if not self.timers['rotate'].active:
            if keys[pygame.K_UP]:
                self.tetromino.rotate()
                self.timers['rotate'].activate()

        # Manual placement
        if keys[pygame.K_SPACE] and self.tetromino.landed:
            self.place_tetromino()

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
        #self.timer_update()
        self.sprites.update()

        # Drawing
        self.surface.fill(GRAY)
        self.sprites.draw(self.surface)

        self.draw_grid()
        self.display_surface.blit(self.surface, (PADDING, PADDING))
        pygame.draw.rect(self.display_surface, LINE_COLOR, self.rect, 2, 2)

    def place_tetromino(self):
        for block in self.tetromino.blocks:
            x, y = int(block.pos.x), int(block.pos.y)
            if 0 <= x < COLUMNS and 0 <= y < ROWS:
                self.field_data[y][x] = block
        
        # Create a new tetromino
        self.create_new_tetromino()

class Tetromino:
    def __init__(self, shape, group, create_new_tetromino, field_data):

        # Setup
        self.shape = shape
        self.block_positions = TETROMINOS[shape]['shape']
        self.color = TETROMINOS[shape]['color']
        self.create_new_tetromino = create_new_tetromino
        self.field_data = field_data
        self.landed = False

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
            self.landed = True

    # Rotate
    def rotate(self):
        if self.shape != 'O':

            # 1. Pivot Point
            pivot_pos = self.blocks[0].pos

            # 2. New block positions
            new_block_positions = [block.rotate(pivot_pos) for block in self.blocks]

            # Check for floor collision and adjust upward

            max_y = max(pos.y for pos in new_block_positions)
            if max_y >= ROWS:
                offset_y = max_y - (ROWS - 1)

                # Move all positions upward
                new_block_positions = [
                    pygame.Vector2(pos.x, pos.y - offset_y) for pos in new_block_positions
                ]
            
            # Detect side wall collision and adjust horizontally 
            min_x = min(pos.x for pos in new_block_positions)
            max_x = max(pos.x for pos in new_block_positions)

            if min_x < 0: # Left wall collision
                offset_x = abs(min_x) # Shift right by the amount needed
                new_block_positions = [
                    pygame.Vector2(pos.x - offset_x, pos.y) for pos in new_block_positions
                ]
            elif max_x >= COLUMNS: # Right wall collision
                offset_x = max_x - (COLUMNS - 1) # Shift left by amount needed
                new_block_positions = [
                    pygame.Vector2(pos.x - offset_x, pos.y) for pos in new_block_positions
                ]

            # 3. Collision Check
            valid = True
            for pos in new_block_positions:
                # Horizontal
                if not (0 <= pos.x < COLUMNS and 0 <= pos.y < ROWS):
                    valid = False
                    break

                # Field Check = Collision with other pieces
                if self.field_data[int(pos.y)][int(pos.x)]:
                    valid = False
                    break

            # Apply rotation if valid
            if valid: 
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
