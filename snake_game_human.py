import pygame
import random
from enum import Enum
from collections import namedtuple
import time
import os

pygame.init()
# Lấy đường dẫn tuyệt đối đến thư mục chứa script
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, 'BlackOpsOne-Regular.ttf')

font = pygame.font.Font(font_path, 25)
# font = pygame.font.SysFont('arial', 25)

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE2 = (0, 100, 255)
BLACK = (0, 0, 0)  # Định nghĩa màu đen

BLOCK_SIZE = 20
SPEED = 8

class SnakeGame:
    scores = []  # Biến lớp để lưu trữ điểm số

    def __init__(self, display, w=824, h=724):
        self.w = w
        self.h = h
        # init display
        self.display = display  # Sử dụng màn hình được truyền vào thay vì tạo mới
        pygame.display.set_caption('Snake')  # Đặt tiêu đề cửa sổ trò chơi
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load('g.png')

        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(self.w/2, self.h/2)
        self.snake = [self.head,
                      Point(self.head.x-BLOCK_SIZE, self.head.y),
                      Point(self.head.x-(2*BLOCK_SIZE), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()

        # Thêm bộ đếm thời gian thay đổi màu
        self.last_color_change_time = time.time()
        self.snake_colors = [self._get_random_color() for _ in self.snake]

        self.paused = False  # {{ Thêm cờ tạm dừng }}

        self.load_scores_from_file()

        self.control_mode = 'keyboard'  # Mặc định là chơi bằng bàn phím
        self.toggle_button = pygame.Rect(self.w - 230, 10, 40, 40)  # Kích thước nút gạt

        # Tải hình ảnh biểu tượng
        self.mouse_icon = pygame.image.load('mouse_icon.png').convert_alpha()
        self.keyboard_icon = pygame.image.load('keyboard_icon.png').convert_alpha()

    def _get_random_color(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def _place_food(self):
        x = random.randint(0, (self.w-BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()

    def play_step(self):
        if not self.paused:
            # 1. Thu thập đầu vào từ người dùng
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if self.control_mode == 'keyboard':
                        new_direction = self.direction
                        if event.key == pygame.K_LEFT:
                            new_direction = Direction.LEFT
                        elif event.key == pygame.K_RIGHT:
                            new_direction = Direction.RIGHT
                        elif event.key == pygame.K_UP:
                            new_direction = Direction.UP
                        elif event.key == pygame.K_DOWN:
                            new_direction = Direction.DOWN

                        # Kiểm tra nếu hướng mới không phải là ngược lại với hướng hiện tại
                        if not self._is_opposite_direction(new_direction):
                            self.direction = new_direction

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if self.pause_button.collidepoint(mouse_pos):
                        action = self.show_pause_menu()
                        if action == 'menu':
                            return True, self.score, 'menu'
                    if self.toggle_button.collidepoint(mouse_pos):
                        self.control_mode = 'mouse' if self.control_mode == 'keyboard' else 'keyboard'

            # Cập nhật hướng di chuyển dựa trên chế độ điều khiển
            if self.control_mode == 'mouse':
                mouse_pos = pygame.mouse.get_pos()
                new_direction = self._get_mouse_direction(self.head, mouse_pos)
                if not self._is_opposite_direction(new_direction):
                    self.direction = new_direction

            # 2. Di chuyển
            self._move(self.direction)
            self.snake.insert(0, self.head)
            self.snake_colors.insert(0, self._get_random_color())

            # Cập nhật màu sắc của mồi để giống với màu của đầu rắn
            self.food_color = self.snake_colors[0]

            # 3. Kiểm tra nếu game over
            game_over = False
            if self._is_collision():
                game_over = True
                SnakeGame.scores.append(self.score)  # Lưu điểm số vào biến lớp
                self.save_scores_to_file()  # Lưu điểm số vào tệp khi trò chơi kết thúc

                # Giới hạn s lượng điểm số lưu trữ
                if len(SnakeGame.scores) > 8:
                    SnakeGame.scores.pop(0)  # Xóa điểm số cũ nhất nếu vượt quá 8

                return game_over, self.score, None  # {{ Trả về None cho action khi game_over }}

            # 4. Đặt thức ăn mới hoặc chỉ di chuyển
            if self.head == self.food:
                self.score += 1
                self._place_food()
            else:
                self.snake.pop()
                self.snake_colors.pop()

            # 5. Cập nhật giao diện hiển thị
            self._update_ui()
            self.clock.tick(SPEED)

            # 6. Trả về game_over và score
            return False, self.score, None  # {{ Trả về None cho action khi không game_over }}
        else:
            # {{ Nếu đang tạm dừng, không tiến hành bước chơi nào }}
            return False, self.score, None

    def _is_collision(self):
        # chạm biên
        if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
            return True
        # chạm chính nó
        if self.head in self.snake[1:]:
            return True

        return False

    def _update_ui(self):
        self.display.blit(self.background, (0, 0))

        while len(self.snake_colors) < len(self.snake):
            self.snake_colors.append(self._get_random_color())

        for idx, pt in enumerate(self.snake):
            color = self.snake_colors[idx]
            pygame.draw.rect(self.display, color, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, BLUE2, pygame.Rect(pt.x+4, pt.y+4, 12, 12))

        # Vẽ mồi với màu sắc của đầu rắn
        pygame.draw.rect(self.display, self.food_color, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))
    
        # {{ Thay thế nút "Tạm dừng" bằng hình ảnh "nut.png" }}
        try:
            pause_image = pygame.image.load('nut.png').convert_alpha()  # Tải hình ảnh với hỗ trợ chuyển đổi alpha
            pause_image = pygame.transform.scale(pause_image, (100, 40))  # Điều chỉnh kích thước nếu cần
        except pygame.error as e:
            print(f"Không thể tải hình ảnh 'nut.png': {e}")
            # Nếu không thể tải hình ảnh, vẽ nút "Tạm dừng" bằng hình chữ nhật như trước
            button_width, button_height = 100, 40
            button_x, button_y = self.w - button_width - 10, 10
            self.pause_button = pygame.Rect(button_x, button_y, button_width, button_height)
            pygame.draw.rect(self.display, (180, 180, 180), self.pause_button, border_radius=5)
            pause_text = font.render("Tạm dừng", True, (179, 74, 70))
            self.display.blit(
                pause_text,
                (
                    self.pause_button.x + (button_width - pause_text.get_width()) // 2,
                    self.pause_button.y + (button_height - pause_text.get_height()) // 2
                )
            )
        else:
            # Hiển thị hình ảnh "nut.png" tại vị trí nút "Tạm dừng"
            button_width, button_height = pause_image.get_size()
            button_x, button_y = self.w - button_width - 10, 10
            self.pause_button = pygame.Rect(button_x, button_y, button_width, button_height)
            self.display.blit(pause_image, (button_x, button_y))

        text = font.render(f"Score: {self.score}", True, WHITE)
        self.display.blit(text, [0, 0])

        # Hiển thị biểu tượng điều khiển
        if self.control_mode == 'mouse':
            self.display.blit(self.mouse_icon, self.toggle_button.topleft)
        else:
            self.display.blit(self.keyboard_icon, self.toggle_button.topleft)

        pygame.display.flip()

    def show_pause_menu(self):
        self.paused = True  # {{ Đặt cờ tạm dừng }}

        # {{ Vẽ nền trắng mờ }}
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 150))  # Trắng với độ trong suốt 150
        self.display.blit(overlay, (0, 0))

        # {{ Tạo bảng popup }}
        popup_width, popup_height = 400, 300  # Tăng chiều cao để sắp xếp nút dọc
        popup_rect = pygame.Rect(
            (self.w - popup_width) // 2,
            (self.h - popup_height) // 2,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.display, WHITE, popup_rect, border_radius=10)

        # {{ Tiêu đề popup }}
        popup_title = font.render("Trò chơi tạm dừng", True, (204, 106, 106))
        self.display.blit(
            popup_title,
            (
                popup_rect.x + (popup_rect.width - popup_title.get_width()) // 2,
                popup_rect.y + 30
            )
        )

        # {{ Nút "Chơi tiếp" }}
        button_width, button_height = 200, 50
        continue_button = pygame.Rect(
            (self.w - button_width) // 2,
            popup_rect.y + 100,  # Vị trí nút "Chơi tiếp" trên popup
            button_width,
            button_height
        )
        pygame.draw.rect(self.display, (255, 223, 186), continue_button, border_radius=10)
        continue_text = font.render("Chơi tiếp", True, (179, 74, 70))
        self.display.blit(
            continue_text,
            (
                continue_button.x + (button_width - continue_text.get_width()) // 2,
                continue_button.y + (button_height - continue_text.get_height()) // 2
            )
        )

        # {{ Nút "Về menu" }}
        menu_button = pygame.Rect(
            (self.w - button_width) // 2,
            popup_rect.y + 180,  # Vị trí nút "Về menu" dưới nút "Chơi tiếp"
            button_width,
            button_height
        )
        pygame.draw.rect(self.display, (255, 223, 186), menu_button, border_radius=10)
        menu_text = font.render("Về menu", True, (179, 74, 70))
        self.display.blit(
            menu_text,
            (
                menu_button.x + (button_width - menu_text.get_width()) // 2,
                menu_button.y + (button_height - menu_text.get_height()) // 2
            )
        )

        pygame.display.flip()

        # {{ Chờ người dùng nhấn nút }}
        while self.paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if continue_button.collidepoint(mouse_pos):
                        self.paused = False  # {{ Đặt cờ tiếp tục }}
                        return 'continue'  # {{ Trả về 'continue' }}
                    elif menu_button.collidepoint(mouse_pos):
                        self.paused = False  # {{ Đặt cờ tiếp tục trước khi quay lại menu }}
                        return 'menu'  # {{ Trả về 'menu' để quay lại menu chính }}

    def _move(self, direction):
        x = self.head.x
        y = self.head.y
        if direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif direction == Direction.UP:
            y -= BLOCK_SIZE

        # Làm tròn tọa độ của đầu rắn
        self.head = Point(round(x // BLOCK_SIZE) * BLOCK_SIZE, round(y // BLOCK_SIZE) * BLOCK_SIZE)

    def show_scores(self):
        # Sử dụng nền OIG3.jpg thay vì lấp đầy màn hình bằng màu đen
        self.display.blit(pygame.image.load('OIG3.jpg'), (0, 0))  # Sử dụng nền OIG3.jpg

        # Tạo một bề mặt cho bảng điểm với nền màu trắng trong suốt
        score_panel = pygame.Surface((self.w * 0.8, self.h * 0.6), pygame.SRCALPHA)
        score_panel.fill((255, 255, 255, 90))  # Trắng với độ trong suốt

        # Vị trí của bảng điểm trên màn hình (đã nhích lên một chút)
        panel_rect = score_panel.get_rect(center=(self.w // 2, self.h // 2 - 30))  # Nhích lên 30 pixel
        self.display.blit(score_panel, panel_rect)

        # Tiêu đề bảng điểm
        title_font = pygame.font.Font(font_path, 50)
        title_text = title_font.render("BẢNG ĐIỂM", True, (204, 106, 106))  # Đổi màu tiêu đề thành (204, 106, 106)
        self.display.blit(title_text, (self.w // 2 - title_text.get_width() // 2, self.h * 0.1))  # Nhích lên 10%

        # Hiển thị danh sách điểm số
        score_font = pygame.font.Font(font_path, 30)  # Sử dụng kích thước font lớn hơn cho điểm số
        for idx, score in enumerate(SnakeGame.scores[-8:], 1):  # Hiển thị tối đa 8 ván gần nhất
            score_text = score_font.render(f"Ván Số {idx}: {' ' * 56} {score}", True, (204, 106, 106))  # Đổi màu điểm số thành (204, 106, 106)
            self.display.blit(score_text, (self.w // 2 - score_text.get_width() // 2, self.h * 0.2 + idx * 40))  # Căn giữa và giảm khoảng cách

        # Tạo nút "Chơi lại" và "Về menu" nằm theo hàng ngang
        button_width = 180
        button_height = 50
        button_spacing = 40  # Khoảng cách giữa các nút

        # Vị trí của nút "Chơi lại"
        replay_button = pygame.Rect(self.w // 2 - button_width - button_spacing // 2, self.h * 0.75, button_width, button_height)
        pygame.draw.rect(self.display, (255, 223, 186), replay_button, border_radius=10)  # Bỏ cạnh với border_radius
        replay_text = font.render("Chơi lại", True, (179, 74, 70))  # Đổi màu văn bản thành đen
        self.display.blit(
            replay_text,
            (
                replay_button.x + replay_button.width // 2 - replay_text.get_width() // 2,
                replay_button.y + (button_height - replay_text.get_height()) // 2
            )
        )

        # Vị trí của nút "Về menu"
        menu_button = pygame.Rect(self.w // 2 + button_spacing // 2, self.h * 0.75, button_width, button_height)
        pygame.draw.rect(self.display, (255, 223, 186), menu_button, border_radius=10)  # Bỏ cạnh với border_radius
        menu_text = font.render("Về menu", True, (179, 74, 70))  # Đổi màu văn bản thành đen
        self.display.blit(
            menu_text,
            (
                menu_button.x + menu_button.width // 2 - menu_text.get_width() // 2,
                menu_button.y + (button_height - menu_text.get_height()) // 2
            )
        )

        pygame.display.flip()

        # Chờ cho đến khi người chơi nhấn nút
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if replay_button.collidepoint(mouse_pos):  # Nếu nhấn vào nút "Chơi lại"
                        waiting = False
                        return 'replay'  # Trả về hành động 'replay'
                    elif menu_button.collidepoint(mouse_pos):  # Nếu nhấn vào nút "Về menu"
                        waiting = False
                        return 'menu'  # Trả về hành động 'menu'

    def reset(self):
        """Khôi phục trạng thái ban đầu của trò chơi."""
        self.direction = Direction.RIGHT
        self.head = Point(self.w / 2, self.h / 2)
        self.snake = [
            self.head,
            Point(self.head.x - BLOCK_SIZE, self.head.y),
            Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)
        ]
        self.score = 0
        self.food = None
        self._place_food()
        self.snake_colors = [self._get_random_color() for _ in self.snake]


                        
    def show_game_over(self):
        try:
            game_over_background = pygame.image.load('game_over_background.png')
            game_over_background = pygame.transform.scale(game_over_background, (self.w, self.h))
            self.display.blit(game_over_background, (0, 0))
        except pygame.error as e:
            print(f"Không thể tải hình ảnh 'game_over_background.png': {e}")
            self.display.fill(BLACK)

        # Tạo nút 'Next' với màu vàng sáng hơn và căn chỉnh vị trí, kích thước
        button_width, button_height = 200, 60  # Tăng kích thước nút
        next_button = pygame.Rect(
            self.w // 2 - button_width // 2,  # Căn giữa theo chiều ngang
            self.h * 0.6,  # Nhích lên cao hơn (60% chiều cao màn hình)
            button_width, button_height
        )

        # Vẽ nút 'Next' với màu vàng sáng (giống màu đám mây) và bo góc mềm mại
        pygame.draw.rect(self.display, (255, 243, 176), next_button, border_radius=20)  # Màu vàng sáng
        next_text = font.render("Next", True, (179, 74, 70))  # Văn bản với màu nâu đỏ nhạt
        self.display.blit(
            next_text,
            (
                next_button.x + (button_width - next_text.get_width()) // 2,
                next_button.y + (button_height - next_text.get_height()) // 2
            )
        )

        pygame.display.flip()

        # Chờ cho đến khi người chơi nhấn nút 'Next'
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if next_button.collidepoint(mouse_pos):
                        waiting = False  # Thoát khỏi vòng lặp chờ

    def save_scores_to_file(self, filename='scores.txt'):
        with open(filename, 'w') as file:
            for score in SnakeGame.scores:
                file.write(f"{score}\n")

    def load_scores_from_file(self, filename='scores.txt'):
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                SnakeGame.scores = [int(line.strip()) for line in file.readlines()]

    def _get_mouse_direction(self, snake_head, mouse_pos):
        x_diff = mouse_pos[0] - snake_head.x
        y_diff = mouse_pos[1] - snake_head.y
        
        if abs(x_diff) > abs(y_diff):
            if x_diff > 0:
                return Direction.RIGHT
            else:
                return Direction.LEFT
        else:
            if y_diff > 0:
                return Direction.DOWN
            else:
                return Direction.UP

    def _is_opposite_direction(self, new_direction):
        # Kiểm tra nếu hướng mới là ngược lại với hướng hiện tại
        if (self.direction == Direction.LEFT and new_direction == Direction.RIGHT) or \
           (self.direction == Direction.RIGHT and new_direction == Direction.LEFT) or \
           (self.direction == Direction.UP and new_direction == Direction.DOWN) or \
           (self.direction == Direction.DOWN and new_direction == Direction.UP):
            return True
        return False

