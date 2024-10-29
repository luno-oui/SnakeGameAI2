import pygame
import sys
from snake_game_human import SnakeGame
from game import SnakeGameAI
from agent import Agent
from helper import plot


import os

pygame.init()
current_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(current_dir, 'BlackOpsOne-Regular.ttf')  # Đường dẫn đến font chữ mới
font = pygame.font.Font(font_path, 30)  # Kích thước font

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)

def draw_text(surface, text, size, x, y, color):
    font_bold = pygame.font.Font(font_path, size)  # Sử dụng font chữ mới
    text_surface = font_bold.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)

def main_menu():
    screen = pygame.display.set_mode((824, 724))
    pygame.display.set_caption('Snake Game Menu')

    # Tải hình ảnh nền
    background_image = pygame.image.load('OIG3.jpg')
    background_image = pygame.transform.scale(background_image, (824, 724))  # Thay đổi kích thưc hình ảnh nếu cần

    while True:
        # Vẽ hình ảnh nền
        screen.blit(background_image, (0, 0))
        
        draw_text(screen, "SNAKE GAME", 55, 412, 120, (204, 106, 106))  # Tiêu đề màu đỏ nhạt
        draw_text(screen, "Chơi tự do", 32, 412, 250, (112, 58, 58))  # Hạ thấp 10px
        draw_text(screen, "AI chơi", 32, 412, 320, (112, 58, 58))  # Hạ thấp 10px và cách nhau 5px
        draw_text(screen, "Thoát", 32, 412, 380, (112, 58, 58))  # Hạ thấp 10px và cách nhau 5px

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:  # Thay đổi từ KEYDOWN sang MOUSEBUTTONDOWN
                mouse_pos = event.pos
                if 312 <= mouse_pos[0] <= 512 and 230 <= mouse_pos[1] <= 270:  # Chơi tự do
                    game = SnakeGame(screen)  # Khởi tạo SnakeGame với màn hình hiện tại
                    human_play(game)
                elif 312 <= mouse_pos[0] <= 512 and 310 <= mouse_pos[1] <= 330:  # AI chơi
                    ai_play()
                elif 312 <= mouse_pos[0] <= 512 and 360 <= mouse_pos[1] <= 400:  # Thoát
                    pygame.quit()
                    sys.exit()

def human_play(game):
    while True:
        game_over, score, action = game.play_step()
        if game_over:
            print('Final Score', score)
            game.show_game_over()  # Hiển thị màn hình "Game Over" trước khi chuyển đến bảng điểm
            if action == 'menu':
                break
            else:
                # Hiển thị bảng điểm và chờ người dùng nhấn nút
                action = game.show_scores()
                if action == 'replay':
                    game.reset()
                elif action == 'menu':
                    break



def ai_play():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent() 
    game = SnakeGameAI()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record:', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == "__main__":
    while True:
        main_menu()