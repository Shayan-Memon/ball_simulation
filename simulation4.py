import pygame
import sys
import random as rand
from pygame.math import Vector2
import math

# Initialize pygame and mixer for sound
pygame.init()
pygame.mixer.init()

broken_angle_start = 30
broken_angle_end = 75
rotation_speed = 0.7

class Particle:
    def __init__(self, position, velocity, color, lifespan):
        self.position = Vector2(position)
        self.velocity = Vector2(velocity)
        self.color = color
        self.lifespan = lifespan

    def update(self, color):
        self.velocity += Vector2(0, 0.1)
        self.position += self.velocity
        self.color = color
        self.lifespan -= 1

    def draw(self, surface):
        if self.lifespan > 0:
            pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), 2)

def update_color(current_color, next_color, color_step) -> pygame.Color:
    if isinstance(current_color, pygame.Color):
        r, g, b, _ = current_color.r, current_color.g, current_color.b, 255
    else:
        r, g, b = current_color

    if isinstance(next_color, pygame.Color):
        next_r, next_g, next_b, _ = next_color.r, next_color.g, next_color.b, 255
    else:
        next_r, next_g, next_b = next_color

    r = int(r + color_step * (next_r - r))
    g = int(g + color_step * (next_g - g))
    b = int(b + color_step * (next_b - b))

    new_r = max(0, min(255, r))
    new_g = max(0, min(255, g))
    new_b = max(0, min(255, b))

    return pygame.Color(new_r, new_g, new_b)

colors = [(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]

class Ball:
    def __init__(self, x, y, vel_x=None, vel_y=None, acceleration=(0, 0.1), ball_radius=30, trail_length=50):
        self.pos = Vector2(x, y)
        self.vel = Vector2(vel_x if vel_x is not None else rand.uniform(-5, 5),
                           vel_y if vel_y is not None else rand.uniform(-5, 5))
        self.acc = Vector2(acceleration)
        self.color_index = 0
        self.ball_radius = ball_radius
        self.color = pygame.Color(255, 0, 0)
        self.next_color = self.color
        self.trail = []
        self.trail_length = trail_length
        self.bounce_points = []
        self.current_sound_index = 0
        self.hit_count = 0
        self.max_speed = 13
        self.point = 0
        self.particles = []
        self.boundary_particles = []

    def play_bounce_sound(self):
        # Get a new channel
        channel = pygame.mixer.find_channel(True)

    def draw_ball(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.ball_radius)

    def draw_particles(self, surface):
        for particle in self.particles:
            particle.draw(surface)
        for particle in self.boundary_particles:
            particle.draw(surface)

    def update_particles(self):
        self.particles = [particle for particle in self.particles if particle.lifespan > 0]
        for particle in self.particles:
            particle.update(self.color)

        self.boundary_particles = [particle for particle in self.boundary_particles if particle.lifespan > 0]
        for particle in self.boundary_particles:
            particle.update(self.color)

    def generate_particles(self, count, position, velocity_range, color, lifespan_range):
        for _ in range(count):
            velocity = Vector2(
                rand.uniform(*velocity_range[0]),
                rand.uniform(*velocity_range[1])
            )
            lifespan = rand.randint(*lifespan_range)
            self.particles.append(Particle(position, velocity, color, lifespan))

    def generate_boundary_particles(self, count, center, radius):
        for _ in range(count):
            angle = rand.uniform(0, 2 * math.pi)
            position = Vector2(center.x + radius * math.cos(angle), center.y + radius * math.sin(angle))
            velocity = Vector2(rand.uniform(-2, 2), rand.uniform(-2, 2))
            lifespan = rand.randint(50, 100)
            self.boundary_particles.append(Particle(position, velocity, (0, 255, 0), lifespan))

    def move(self, center_of_boundary, radius_of_boundary, broken_angle_start, broken_angle_end):
        global ball_angle, ball_angle_speed, fall
        
        self.pos += self.vel
        self.vel += self.acc
        ball_angle += ball_angle_speed

        if ball_angle_speed > 0:
            ball_angle_speed -= 0.00005

        if self.vel.magnitude() > self.max_speed:
            self.vel = self.vel.normalize() * self.max_speed

        distance_to_center = (self.pos - center_of_boundary).magnitude()
        self.update_particles()
        if popper:
            self.generate_particles(
                count=10,
                position=self.pos,
                velocity_range=((-3, 3), (-3, 3)),
                color=self.color,
                lifespan_range=(20, 50)
            )
            
        else:
            if distance_to_center > radius_of_boundary - self.ball_radius:
                ball_angle_speed += 0.001
                angle = (self.pos - center_of_boundary).angle_to(Vector2(1, 0))
                if angle < 0:
                    angle += 360

                # Normalize angles to [0, 360)
                start_angle = broken_angle_start % 360
                end_angle = broken_angle_end % 360

                if start_angle < end_angle:
                    in_broken_range = start_angle <= angle <= end_angle
                else:
                    in_broken_range = angle >= start_angle or angle <= end_angle

                if not in_broken_range:
                    self.play_bounce_sound()
                    self.next_color = pygame.Color(rand.randint(0, 255), rand.randint(0, 255), rand.randint(0, 255))
                    direction = (self.pos - center_of_boundary).normalize()
                    self.vel.reflect_ip(direction)
                    overlap = distance_to_center + self.ball_radius - radius_of_boundary
                    self.pos -= direction * overlap

                    self.next_color = pygame.Color(*colors[self.color_index])
                    self.color_index = (self.color_index + 1) % len(colors)
                    self.bounce_points.append(self.pos + direction * self.ball_radius)
                else:
                    fall = True
                    self.generate_boundary_particles(count=500, center=center_of_boundary, radius=radius_of_boundary)

    def update_color(self, color_smoothness):
        self.color = update_color(self.color, self.next_color, color_smoothness)

win_size = (1400, 1200)
background_color = (0, 0, 0)

window = pygame.display.set_mode(win_size)
boundary_rect = window.get_rect()
pygame.display.set_caption('Bouncing Ball')
clock = pygame.time.Clock()

boundary_center = Vector2(win_size[0] // 2, win_size[1] // 2)
boundary_radius = 200
boundary_color = (0, 255, 0)

next_boundary_color = boundary_color
color_step = 0.02
color_increase = 10

ball = Ball(boundary_center.x, boundary_center.y)
ball_angle = 0
ball_angle_speed = 0.1
fall = False
paused = True

radius_increase = 25

boundaries = []
popper = False

BG = pygame.transform.scale(pygame.image.load("BG2.jpg"),win_size)
for i in range(0, 11):
    boundaries.append([boundary_radius, broken_angle_start, broken_angle_end])
    boundary_radius += radius_increase
    broken_angle_end += radius_increase
    broken_angle_start += radius_increase





### Define broken part for each boundary ###



# 1
boundaries[0][1], boundaries[0][2] = 10, 190
# 2
boundaries[1][1], boundaries[1][2] = 10, 120
# 3
boundaries[2][1], boundaries[2][2] = 90, 190
# 4
# boundaries[3][1], boundaries[3][2] = 10, 190
# # 5
# boundaries[4][1], boundaries[4][2] = 10, 190
# # 6
# boundaries[5][1], boundaries[5][2] = 10, 190
# # 7
# boundaries[6][1], boundaries[6][2] = 10, 190
# # 8
# boundaries[7][1], boundaries[7][2] = 10, 190
# # 9
# boundaries[8][1], boundaries[8][2] = 10, 190
# # 10
# boundaries[9][1], boundaries[9][2] = 10, 190
# # 11
# boundaries[10][1], boundaries[10][2] = 10, 190
# # 12
# boundaries[11][1], boundaries[11][2] = 10, 190
# # 13
# boundaries[12][1], boundaries[12][2] = 10, 190
# # 14
# boundaries[13][1], boundaries[13][2] = 10, 190
# # 15
# boundaries[14][1], boundaries[14][2] = 10, 190



while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_k:
                paused = not paused

    if not paused:
        if boundaries:
            ball.move(boundary_center, boundaries[0][0], boundaries[0][1], boundaries[0][2])
        else:
            ball.move(boundary_center, 2500, 0, 0)
        
        ball.update_color(color_step)
        boundary_color = update_color(boundary_color, next_boundary_color, color_step)

        if ball.next_color != next_boundary_color:
            next_boundary_color = ball.next_color



    
    window.fill("#dc143c")
    # window.blit(BG,(0,0))
    pygame.draw.circle(window,'#ede6d6',(700,600),480)
    
    ball.draw_particles(window)
    color_increase = 0
    for i in boundaries:
        i[1] = (i[1] + rotation_speed) % 360
        i[2] = (i[2] + rotation_speed) % 360

        outer_boundary_radius = i[0] + 20
        inner_boundary_radius = i[0]
        if not fall:
            fake_color = boundary_color[0] + color_increase, boundary_color[1] + color_increase, boundary_color[2] + color_increase

            fake_color = tuple(min(255, c) for c in fake_color)
            color_increase += 10

            pygame.draw.arc(window, fake_color, (boundary_center.x - outer_boundary_radius, boundary_center.y - outer_boundary_radius, 2 * outer_boundary_radius, 2 * outer_boundary_radius), math.radians(i[2]), math.radians(i[1]), 10)
        else:
            boundaries.pop(0)
            fall = False

    ball.draw_ball(window)
    pygame.display.flip()
    clock.tick(120)
