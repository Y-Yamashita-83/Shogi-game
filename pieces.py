import pygame
from constants import CELL_SIZE

class Piece:
    def __init__(self, name, kanji, is_promoted=False, player=1):
        self.name = name
        self.kanji = kanji
        self.is_promoted = is_promoted
        self.player = player  # 1: 先手(下側), 2: 後手(上側)
        self.selected = False
        self.moved = False
        
        # 特殊効果の状態を管理する変数
        self.effects = {}  # 適用されている効果を辞書で管理
        
        # 成った時の漢字
        self.promoted_kanji = {
            "pawn": "と",
            "lance": "杏",
            "knight": "圭",
            "silver": "全",
            "bishop": "馬",
            "rook": "龍"
        }.get(name, kanji)

    def draw(self, screen, x, y, piece_images, font, selected_color):
        # 画像がある場合は画像を使用
        image_key = (self.name, self.player, self.is_promoted)
        if image_key in piece_images:
            piece_image = piece_images[image_key]
            # 画像のサイズをCELL_SIZEに合わせる
            scaled_image = pygame.transform.scale(piece_image, (CELL_SIZE, CELL_SIZE))
            screen.blit(scaled_image, (x, y))
        else:
            # 画像がない場合は従来の描画方法を使用
            # 駒の背景（木の色）
            piece_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (210, 180, 140), piece_rect)
            pygame.draw.rect(screen, (0, 0, 0), piece_rect, 1)
            
            # 駒の文字
            text_color = (0, 0, 0) if self.player == 1 else (200, 0, 0)
            display_kanji = self.promoted_kanji if self.is_promoted else self.kanji
            text = font.render(display_kanji, True, text_color)
            text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
            screen.blit(text, text_rect)
        
        # 選択されている場合はハイライト
        if self.selected:
            highlight = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            highlight.fill(selected_color)
            screen.blit(highlight, (x, y))
            
        # 特殊効果の視覚表現
        if 'enhanced' in self.effects and self.effects['enhanced']:
            # 強化効果の表示（赤い輝き）
            glow = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            glow.fill((255, 0, 0, 50))
            screen.blit(glow, (x, y))
            
            # 残りターン数を表示
            if 'enhanced_duration' in self.effects:
                duration_text = font.render(str(self.effects['enhanced_duration']), True, (255, 0, 0))
                small_text_rect = duration_text.get_rect(bottomright=(x + CELL_SIZE - 2, y + CELL_SIZE - 2))
                screen.blit(duration_text, small_text_rect)
    def get_possible_moves(self, board, pos):
        """駒の種類に応じた移動可能なマスのリストを返す"""
        row, col = pos
        moves = []
        
        if self.name == "pawn":  # 歩兵
            if not self.is_promoted:
                # 歩は前にのみ1マス進める
                # 先手（player=1）は下に進む（row+1）、後手（player=2）は上に進む（row-1）
                new_row = row + 1 if self.player == 1 else row - 1
                if 0 <= new_row < 9:
                    moves.append((new_row, col))
            else:  # 成った歩（と金）は金と同じ動き
                moves = self._gold_moves(board, row, col)
                
        elif self.name == "lance":  # 香車
            if not self.is_promoted:
                # 香車は前方向に何マスでも進める
                # 先手は下方向、後手は上方向
                direction = 1 if self.player == 1 else -1
                for i in range(1, 9):
                    new_row = row + direction * i
                    if not (0 <= new_row < 9):
                        break
                    if board.grid[new_row][col] is None:
                        moves.append((new_row, col))
                    elif board.grid[new_row][col].player != self.player:
                        moves.append((new_row, col))
                        break
                    else:
                        break
            else:  # 成った香（杏）は金と同じ動き
                moves = self._gold_moves(board, row, col)
                
        elif self.name == "knight":  # 桂馬
            if not self.is_promoted:
                # 桂馬は前に2マス、横に1マス進める（L字）
                # 先手は下方向、後手は上方向
                if self.player == 1:
                    knight_moves = [(2, -1), (2, 1)]  # 先手の桂馬の動き
                else:
                    knight_moves = [(-2, -1), (-2, 1)]  # 後手の桂馬の動き
                
                for dr, dc in knight_moves:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 9 and 0 <= new_col < 9:
                        if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                            moves.append((new_row, new_col))
            else:  # 成った桂（圭）は金と同じ動き
                moves = self._gold_moves(board, row, col)
                
        elif self.name == "silver":  # 銀将
            if not self.is_promoted:
                # 銀は斜め前3方向と斜め後ろ2方向に進める
                if self.player == 1:
                    # 先手の銀の動き（下が前方向）
                    silver_moves = [(1, -1), (1, 0), (1, 1), (-1, -1), (-1, 1)]
                else:
                    # 後手の銀の動き（上が前方向）
                    silver_moves = [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 1)]
                
                for dr, dc in silver_moves:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 9 and 0 <= new_col < 9:
                        if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                            moves.append((new_row, new_col))
            else:  # 成った銀（全）は金と同じ動き
                moves = self._gold_moves(board, row, col)
                
        elif self.name == "gold":  # 金将
            moves = self._gold_moves(board, row, col)
                
        elif self.name == "king":  # 王将・玉将
            # 王は周囲8マスに進める
            king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in king_moves:
                new_row = row + dr
                new_col = col + dc
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        moves.append((new_row, new_col))
                        
        elif self.name == "bishop":  # 角行
            # 角は斜め方向に何マスでも進める
            bishop_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            for dr, dc in bishop_dirs:
                for i in range(1, 9):
                    new_row = row + dr * i
                    new_col = col + dc * i
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        moves.append((new_row, new_col))
                        break
                    else:
                        break
            
            # 成った角（馬）は角の動き + 十字1マス
            if self.is_promoted:
                horse_moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
                for dr, dc in horse_moves:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 9 and 0 <= new_col < 9:
                        if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                            moves.append((new_row, new_col))
                            
        elif self.name == "rook":  # 飛車
            # 飛車は縦横方向に何マスでも進める
            rook_dirs = [(-1, 0), (0, -1), (0, 1), (1, 0)]
            for dr, dc in rook_dirs:
                for i in range(1, 9):
                    new_row = row + dr * i
                    new_col = col + dc * i
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        moves.append((new_row, new_col))
                        break
                    else:
                        break
            
            # 成った飛車（龍）は飛車の動き + 斜め1マス
            if self.is_promoted:
                dragon_moves = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dr, dc in dragon_moves:
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < 9 and 0 <= new_col < 9:
                        if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                            moves.append((new_row, new_col))
        
        return moves
    
    def _gold_moves(self, board, row, col):
        """金将の動きを計算する（成り駒の多くが金と同じ動きをする）"""
        moves = []
        # 金は前後左右と斜め前に進める（6方向）
        if self.player == 1:
            # 先手の金の動き（下が前方向）
            gold_moves = [(1, -1), (1, 0), (1, 1), (0, -1), (0, 1), (-1, 0)]
        else:
            # 後手の金の動き（上が前方向）
            gold_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0)]
            
        for dr, dc in gold_moves:
            new_row = row + dr
            new_col = col + dc
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                    moves.append((new_row, new_col))
        return moves
    def get_move_type(self):
        """現在の駒の動きタイプを返す（特殊効果を考慮）"""
        # 一時的な動きタイプが設定されている場合はそれを返す
        if 'temp_move_type' in self.effects:
            return self.effects['temp_move_type']
        
        # 通常の動きタイプを返す
        if self.is_promoted:
            if self.name in ["pawn", "lance", "knight", "silver"]:
                return "gold"  # 成った歩、香、桂、銀は金と同じ動き
            elif self.name == "bishop":
                return "horse"  # 馬
            elif self.name == "rook":
                return "dragon"  # 龍
        return self.name
        
    def apply_effect(self, effect_name, value=True, duration=1):
        """駒に特殊効果を適用する"""
        self.effects[effect_name] = value
        self.effects[f"{effect_name}_duration"] = duration
        self.effects[f"{effect_name}_new"] = True  # 新しく適用された効果のフラグ
        
    def remove_effect(self, effect_name):
        """駒から特殊効果を削除する"""
        if effect_name in self.effects:
            del self.effects[effect_name]
            if f"{effect_name}_duration" in self.effects:
                del self.effects[f"{effect_name}_duration"]
                
    def update_effects(self):
        """ターン終了時に効果の持続時間を減らす"""
        effects_to_remove = []
        for effect_name in list(self.effects.keys()):
            if effect_name.endswith("_duration"):
                base_effect = effect_name[:-9]  # "_duration"の部分を除く
                
                # 新しく適用された効果かどうかを確認
                new_effect_flag = f"{base_effect}_new"
                if new_effect_flag in self.effects:
                    # 新しく適用された効果の場合はフラグを削除するだけ
                    del self.effects[new_effect_flag]
                    print(f"{base_effect}効果が適用されました。次のターンからカウントダウンが始まります。")
                else:
                    # 既存の効果の場合は持続時間を減らす
                    self.effects[effect_name] -= 1
                    if self.effects[effect_name] <= 0:
                        effects_to_remove.append(base_effect)
                        effects_to_remove.append(effect_name)
        
        for effect_name in effects_to_remove:
            if effect_name in self.effects:
                del self.effects[effect_name]
                print(f"効果 {effect_name} が切れました")
    def get_possible_moves(self, board, pos):
        """駒の移動可能なマスのリストを返す（特殊効果を考慮）"""
        row, col = pos
        valid_moves = []
        
        # 駒の種類に応じた移動可能マスの計算
        move_type = self.get_move_type()
        
        # 強化効果があるかどうか
        enhanced = 'enhanced' in self.effects and self.effects['enhanced']
        
        # 歩兵
        if move_type == "pawn":
            direction = 1 if self.player == 1 else -1
            new_row = row + direction
            if 0 <= new_row < 9:
                # 自分の駒がない場合のみ移動可能
                if board.grid[new_row][col] is None or board.grid[new_row][col].player != self.player:
                    valid_moves.append((new_row, col))
            
            # 強化効果：前に2マス移動可能
            if enhanced:
                new_row = row + 2 * direction
                if 0 <= new_row < 9:
                    # 途中と目的地に自分の駒がない場合のみ移動可能
                    if (board.grid[row + direction][col] is None and 
                        (board.grid[new_row][col] is None or board.grid[new_row][col].player != self.player)):
                        valid_moves.append((new_row, col))
        
        # 香車
        elif move_type == "lance":
            direction = 1 if self.player == 1 else -1
            for i in range(1, 9):
                new_row = row + i * direction
                if not (0 <= new_row < 9):
                    break
                if board.grid[new_row][col] is None:
                    valid_moves.append((new_row, col))
                elif board.grid[new_row][col].player != self.player:
                    valid_moves.append((new_row, col))
                    break
                else:
                    break
        
        # 桂馬
        elif move_type == "knight":
            direction = 1 if self.player == 1 else -1
            knight_moves = [
                (row + 2 * direction, col - 1),
                (row + 2 * direction, col + 1)
            ]
            for move in knight_moves:
                new_row, new_col = move
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
        
        # 銀将
        elif move_type == "silver":
            direction = 1 if self.player == 1 else -1
            silver_moves = [
                (row + direction, col - 1),  # 前斜め左
                (row + direction, col),      # 前
                (row + direction, col + 1),  # 前斜め右
                (row - direction, col - 1),  # 後ろ斜め左
                (row - direction, col + 1)   # 後ろ斜め右
            ]
            for move in silver_moves:
                new_row, new_col = move
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
        
        # 金将（と金、成香、成桂、成銀も同じ動き）
        elif move_type == "gold":
            direction = 1 if self.player == 1 else -1
            gold_moves = [
                (row + direction, col - 1),  # 前斜め左
                (row + direction, col),      # 前
                (row + direction, col + 1),  # 前斜め右
                (row, col - 1),             # 左
                (row, col + 1),             # 右
                (row - direction, col)       # 後ろ
            ]
            for move in gold_moves:
                new_row, new_col = move
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
        
        # 王将・玉将
        elif move_type == "king":
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 9 and 0 <= new_col < 9:
                        if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                            valid_moves.append((new_row, new_col))
        
        # 角行
        elif move_type == "bishop":
            # 斜め方向の移動
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 9):
                    new_row, new_col = row + i * dr, col + i * dc
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
                        break
                    else:
                        break
        
        # 飛車
        elif move_type == "rook":
            # 縦横方向の移動
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 9):
                    new_row, new_col = row + i * dr, col + i * dc
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
                        break
                    else:
                        break
        
        # 馬（成角）
        elif move_type == "horse":
            # 角の動き
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 9):
                    new_row, new_col = row + i * dr, col + i * dc
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
                        break
                    else:
                        break
            
            # 王の動き（1マス）を追加
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
        
        # 龍（成飛）
        elif move_type == "dragon":
            # 飛車の動き
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 9):
                    new_row, new_col = row + i * dr, col + i * dc
                    if not (0 <= new_row < 9 and 0 <= new_col < 9):
                        break
                    if board.grid[new_row][new_col] is None:
                        valid_moves.append((new_row, new_col))
                    elif board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
                        break
                    else:
                        break
            
            # 斜め1マスの動き
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    if board.grid[new_row][new_col] is None or board.grid[new_row][new_col].player != self.player:
                        valid_moves.append((new_row, new_col))
        
        return valid_moves
    def reset_effects(self):
        """駒の特殊効果をすべてリセットする"""
        self.effects = {}  # 効果をすべて削除
