import pygame
from constants import WINDOW_BG_COLOR, WINDOW_BORDER_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.button import Button
from special_moves import get_special_moves

class SpecialMoveWindow:
    def __init__(self, font, button_font):
        self.active = False
        self.width = 600  # ウィンドウ幅をさらに広げる
        self.height = 450  # ウィンドウ高さも広げる
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = (SCREEN_HEIGHT - self.height) // 2
        self.font = font
        self.button_font = button_font
        
        # 戻るボタン
        self.back_button = Button(
            self.x + self.width - 120,
            self.y + self.height - 50,
            100, 40,
            "戻る",
            self.close
        )
        
        # 使うボタン
        self.use_button = Button(
            self.x + 20,
            self.y + self.height - 50,
            100, 40,
            "使う",
            self.use_special_move
        )
        
        # 技のリストを取得
        self.special_moves = get_special_moves()
        # 選択された技
        self.selected_move = None
        # 選択された技のインデックス
        self.selected_index = -1
        
        # 技の表示領域
        self.move_list_rect = pygame.Rect(
            self.x + 50,
            self.y + 70,
            self.width - 100,
            self.height - 180
        )
        
        # 技の説明を表示する領域
        self.description_rect = pygame.Rect(
            self.x + 50,
            self.y + self.height - 120,
            self.width - 100,
            70  # 説明領域を広げる
        )
        
    def open(self, board=None, player=None):
        self.active = True
        self.selected_move = None
        self.selected_index = -1
        self.board = board
        self.player = player
        
    def close(self):
        self.active = False
        
    def use_special_move(self):
        if self.selected_move and self.board:
            # 技を使う処理
            if self.selected_move.can_use(self.board, self.player):
                # メンコ、突風、変化の杖の場合は確認ダイアログを表示
                if self.selected_move.name == "メンコ" or self.selected_move.name == "突風" or self.selected_move.name == "変化の杖":
                    self.board.special_move_active = self.selected_move
                    self.board.special_move_confirm = True
                    self.board.special_move_target = None  # 対象を選択しない
                    self.close()
                else:
                    # 対象を選択する必要がある技の場合
                    self.board.special_move_active = self.selected_move
                    self.close()
            else:
                print("この技は現在使用できません")
                # 使用できない場合はウィンドウを閉じない
        
    def draw(self, surface):
        if not self.active:
            return
            
        # ウィンドウの背景
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, WINDOW_BG_COLOR, window_rect)
        pygame.draw.rect(surface, WINDOW_BORDER_COLOR, window_rect, 2)
        
        # タイトル
        title_text = self.font.render("特殊技一覧", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 30))
        surface.blit(title_text, title_rect)
        
        # 技リストの背景
        pygame.draw.rect(surface, (240, 240, 240), self.move_list_rect)
        pygame.draw.rect(surface, (0, 0, 0), self.move_list_rect, 1)
        
        # 技リストの表示
        if self.special_moves:
            for i, move in enumerate(self.special_moves):
                # 技の位置を計算
                move_y = self.move_list_rect.y + 10 + i * 30
                
                # 選択されている技の背景を強調表示
                if i == self.selected_index:
                    highlight_rect = pygame.Rect(
                        self.move_list_rect.x + 5,
                        move_y - 5,
                        self.move_list_rect.width - 10,
                        30
                    )
                    pygame.draw.rect(surface, (200, 220, 255), highlight_rect)
                    pygame.draw.rect(surface, (100, 150, 230), highlight_rect, 1)
                
                # 技の名前を表示
                move_text = self.font.render(move.name, True, (0, 0, 0))
                surface.blit(move_text, (self.move_list_rect.x + 20, move_y))
        else:
            # 技がない場合のメッセージ
            no_moves_text = self.font.render("利用可能な特殊技はありません", True, (100, 100, 100))
            no_moves_rect = no_moves_text.get_rect(center=self.move_list_rect.center)
            surface.blit(no_moves_text, no_moves_rect)
        
        # 選択された技の説明を表示
        if self.selected_move:
            # 説明の背景
            pygame.draw.rect(surface, (240, 240, 240), self.description_rect)
            pygame.draw.rect(surface, (0, 0, 0), self.description_rect, 1)
            
            # 説明テキストを複数行に分割して表示
            description = self.selected_move.description
            # 説明テキストが長い場合は適切な位置で分割
            if len(description) > 20:
                # 適切な分割位置を探す（スペースや句読点の位置）
                split_pos = description.find("、", 10)
                if split_pos == -1:
                    split_pos = description.find("。", 10)
                if split_pos == -1:
                    split_pos = description.find(" ", 10)
                if split_pos == -1:
                    # 適切な分割位置がない場合は半分で分割
                    split_pos = len(description) // 2
                
                line1 = description[:split_pos + 1]
                line2 = description[split_pos + 1:]
                
                # 1行目
                desc_text1 = self.font.render(line1, True, (0, 0, 0))
                desc_rect1 = desc_text1.get_rect(center=(self.description_rect.centerx, self.description_rect.y + 20))
                surface.blit(desc_text1, desc_rect1)
                
                # 2行目
                desc_text2 = self.font.render(line2, True, (0, 0, 0))
                desc_rect2 = desc_text2.get_rect(center=(self.description_rect.centerx, self.description_rect.y + 45))
                surface.blit(desc_text2, desc_rect2)
            else:
                # 短い説明はそのまま中央に表示
                desc_text = self.font.render(description, True, (0, 0, 0))
                desc_rect = desc_text.get_rect(center=self.description_rect.center)
                surface.blit(desc_text, desc_rect)
        
        # 戻るボタンの描画
        self.back_button.draw(surface, self.button_font)
        
        # 使うボタンの描画（技が選択されている場合のみ有効化）
        if self.selected_move:
            self.use_button.draw(surface, self.button_font)
        else:
            # 技が選択されていない場合は半透明で表示
            disabled_rect = pygame.Rect(self.use_button.rect)
            pygame.draw.rect(surface, (200, 200, 200), disabled_rect)
            pygame.draw.rect(surface, (150, 150, 150), disabled_rect, 2)
            
            text_surf = self.button_font.render("使う", True, (150, 150, 150))
            text_rect = text_surf.get_rect(center=disabled_rect.center)
            surface.blit(text_surf, text_rect)
        
    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.handle_event(event):
                return True
                
            if self.selected_move and self.use_button.handle_event(event):
                return True
                
            # 技リストのクリック処理
            if self.move_list_rect.collidepoint(event.pos):
                # クリックされた位置から技のインデックスを計算
                rel_y = event.pos[1] - self.move_list_rect.y - 10
                clicked_index = rel_y // 30
                
                # 有効な技がクリックされたか確認
                if 0 <= clicked_index < len(self.special_moves):
                    self.selected_index = clicked_index
                    self.selected_move = self.special_moves[clicked_index]
                    return True
                
        return False
        
    def update(self, mouse_pos):
        if not self.active:
            return
            
        self.back_button.update(mouse_pos)
        if self.selected_move:
            self.use_button.update(mouse_pos)

class PromotionWindow:
    def __init__(self, font, button_font):
        self.active = False
        self.width = 300
        self.height = 150
        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = (SCREEN_HEIGHT - self.height) // 2
        self.font = font
        self.button_font = button_font
        
        # 成るボタン
        self.promote_button = Button(
            self.x + 40,
            self.y + 80,
            100, 40,
            "成る",
            self.promote
        )
        
        # 成らないボタン
        self.dont_promote_button = Button(
            self.x + self.width - 140,
            self.y + 80,
            100, 40,
            "成らない",
            self.dont_promote
        )
        
        self.piece = None
        self.callback = None
        
    def open(self, piece, callback):
        self.active = True
        self.piece = piece
        self.callback = callback
        
    def close(self):
        self.active = False
        
    def promote(self):
        if self.callback:
            self.callback(True)
        self.close()
        
    def dont_promote(self):
        if self.callback:
            self.callback(False)
        self.close()
        
    def draw(self, surface):
        if not self.active:
            return
            
        # ウィンドウの背景
        window_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, WINDOW_BG_COLOR, window_rect)
        pygame.draw.rect(surface, WINDOW_BORDER_COLOR, window_rect, 2)
        
        # タイトル
        title_text = self.font.render("成りますか？", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.x + self.width // 2, self.y + 30))
        surface.blit(title_text, title_rect)
        
        # ボタンの描画
        self.promote_button.draw(surface, self.button_font)
        self.dont_promote_button.draw(surface, self.button_font)
        
    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.promote_button.handle_event(event):
                return True
            if self.dont_promote_button.handle_event(event):
                return True
                
        return False
        
    def update(self, mouse_pos):
        if not self.active:
            return
            
        self.promote_button.update(mouse_pos)
        self.dont_promote_button.update(mouse_pos)
