import pygame
import time

class Effect:
    def __init__(self, duration=2.0):
        self.duration = duration
        self.start_time = time.time()
        
    def is_expired(self):
        return time.time() - self.start_time > self.duration
        
    def update(self):
        pass
        
    def draw(self, screen):
        pass

class MessageEffect(Effect):
    def __init__(self, message, font, position=(400, 100), color=(255, 0, 0), duration=2.0):
        super().__init__(duration)
        self.message = message
        self.font = font
        self.position = position
        self.color = color
        self.alpha = 255  # 透明度
        
    def update(self):
        # フェードアウト効果
        time_passed = time.time() - self.start_time
        if time_passed > self.duration * 0.7:
            fade_factor = 1.0 - (time_passed - self.duration * 0.7) / (self.duration * 0.3)
            self.alpha = max(0, int(255 * fade_factor))
    
    def draw(self, screen):
        text_surface = self.font.render(self.message, True, self.color)
        text_surface.set_alpha(self.alpha)
        text_rect = text_surface.get_rect(center=self.position)
        screen.blit(text_surface, text_rect)

class HighlightEffect(Effect):
    def __init__(self, position, cell_size, color=(255, 255, 0, 150), duration=1.0):
        super().__init__(duration)
        self.position = position
        self.cell_size = cell_size
        self.color = color
        self.alpha = color[3] if len(color) > 3 else 150
        
    def update(self):
        # 点滅効果
        time_passed = time.time() - self.start_time
        self.alpha = int(150 * (0.5 + 0.5 * abs(((time_passed * 5) % 2) - 1)))
        
    def draw(self, screen):
        highlight = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], self.alpha)
        highlight.fill(color_with_alpha)
        x, y = self.position
        screen.blit(highlight, (x, y))

class EffectDisplay:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.effects = []
        
    def add_message(self, message, position=(400, 100), color=(255, 0, 0), duration=2.0):
        effect = MessageEffect(message, self.font, position, color, duration)
        self.effects.append(effect)
        
    def add_highlight(self, position, cell_size, color=(255, 255, 0, 150), duration=1.0):
        effect = HighlightEffect(position, cell_size, color, duration)
        self.effects.append(effect)
        
    def update(self):
        # 期限切れのエフェクトを削除
        self.effects = [effect for effect in self.effects if not effect.is_expired()]
        
        # 残りのエフェクトを更新
        for effect in self.effects:
            effect.update()
            
    def draw(self):
        for effect in self.effects:
            effect.draw(self.screen)
