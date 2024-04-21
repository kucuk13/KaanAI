import pygame
import random

# Pygame başlatma
pygame.init()

# Ekran boyutları
width = 800
height = 600
screen = pygame.display.set_mode((width, height))

# Renkler
white = (255, 255, 255)
black = (0, 0, 0)

# Oyun elemanları
paddle_width, paddle_height = 10, 100
ball_size = 10

# Oyuncu pozisyonları
player_x = 30
player_y = height // 2 - paddle_height // 2
opponent_x = width - 30 - paddle_width
opponent_y = height // 2 - paddle_height // 2

# Topun başlangıç pozisyonu ve hızı
ball_x = width // 2
ball_y = height // 2
ball_x_vel = 7 * random.choice((1, -1))
ball_y_vel = 7 * random.choice((1, -1))

# Skor
player_score = 0
opponent_score = 0

# Saat nesnesi
clock = pygame.time.Clock()

# Font
font = pygame.font.Font(None, 36)

def draw_objects():
    screen.fill(black)
    pygame.draw.rect(screen, white, (player_x, player_y, paddle_width, paddle_height))
    pygame.draw.rect(screen, white, (opponent_x, opponent_y, paddle_width, paddle_height))
    pygame.draw.ellipse(screen, white, (ball_x, ball_y, ball_size, ball_size))
    player_text = font.render(str(player_score), True, white)
    opponent_text = font.render(str(opponent_score), True, white)
    screen.blit(player_text, (width / 4, 20))
    screen.blit(opponent_text, (3 * width / 4, 20))

def move_ball():
    global ball_x, ball_y, ball_x_vel, ball_y_vel, player_score, opponent_score

    ball_x += ball_x_vel
    ball_y += ball_y_vel

    if ball_y <= 0 or ball_y + ball_size >= height:
        ball_y_vel *= -1
    
    if ball_x <= 0:
        opponent_score += 1
        reset_ball()
    
    if ball_x + ball_size >= width:
        player_score += 1
        reset_ball()

    # Çarpışma kontrolü
    if (ball_x <= player_x + paddle_width and player_y < ball_y < player_y + paddle_height) or \
       (ball_x + ball_size >= opponent_x and opponent_y < ball_y < opponent_y + paddle_height):
        ball_x_vel *= -1

def reset_ball():
    global ball_x, ball_y, ball_x_vel, ball_y_vel
    ball_x = width // 2
    ball_y = height // 2
    ball_x_vel = 7 * random.choice((1, -1))
    ball_y_vel = 7 * random.choice((1, -1))

def move_paddle():
    global player_y, opponent_y
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP] and player_y > 0:
        player_y -= 10
    if keys[pygame.K_DOWN] and player_y + paddle_height < height:
        player_y += 10
    
    # Basit yapay zeka
    if opponent_y + paddle_height // 2 < ball_y:
        opponent_y += 7
    if opponent_y + paddle_height // 2 > ball_y:
        opponent_y -= 7

# Oyun döngüsü
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    move_paddle()
    move_ball()
    draw_objects()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
