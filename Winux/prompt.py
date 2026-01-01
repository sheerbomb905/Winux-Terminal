import pygame
import time

class Prompt:
    def __init__(self, font, initial_path):
        self.font = font
        self.path = initial_path
        self.cursor_visible = True
        self.last_blink_time = time.time()
        self.blink_interval = 0.5

    def update(self):
        current_time = time.time()
        if current_time - self.last_blink_time > self.blink_interval:
            self.cursor_visible = not self.cursor_visible
            self.last_blink_time = current_time

    def set_path(self, path):
        self.path = path

    def render(self, surface, x, y, input_text, text_color=(192, 192, 192), cursor_color=(192, 192, 192)):
        path_surf = self.font.render(self.path, True, text_color)
        surface.blit(path_surf, (x, y))
        path_width = path_surf.get_width()
        prompt_marker = ">"
        marker_surf = self.font.render(prompt_marker, True, text_color)
        surface.blit(marker_surf, (x + path_width, y))
        marker_width = marker_surf.get_width()
        input_surf = self.font.render(input_text, True, text_color)
        input_x = x + path_width + marker_width + 5
        surface.blit(input_surf, (input_x, y))
        input_width = input_surf.get_width()
        if self.cursor_visible:
            cursor_height = self.font.get_height()
            cursor_width = max(10, self.font.size(" ")[0])
            cursor_rect = pygame.Rect(input_x + input_width, y, cursor_width, cursor_height)
            pygame.draw.rect(surface, cursor_color, cursor_rect)
