"""
将棋ゲームの特殊技を管理するモジュール
"""
import random

class SpecialMove:
    def __init__(self, name, description, duration=1, icon=None):
        self.name = name
        self.description = description
        self.duration = duration  # 効果の持続ターン数
        self.icon = icon  # 技のアイコン画像（オプション）
        
    def can_use(self, board, player):
        """技が使用可能かどうかを判定する"""
        # デフォルトでは常に使用可能
        return True
        
    def execute(self, board, player, target_pos=None):
        """技の効果を実行する"""
        # 継承先で実装
        pass


class Technique1(SpecialMove):
    def __init__(self):
        super().__init__(
            "歩強化", 
            "選択した歩が3ターンの間、最大2マス進めるようになる",
            duration=3
        )
    
    def can_use(self, board, player):
        # プレイヤーが歩を持っているか確認
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == player and piece.name == "pawn" and not piece.is_promoted:
                    return True
        return False
        
    def execute(self, board, player, target_pos=None):
        if not target_pos:
            return False
            
        row, col = target_pos
        piece = board.grid[row][col]
        
        # 選択した駒が自分の歩であるか確認
        if not piece or piece.player != player or piece.name != "pawn" or piece.is_promoted:
            return False
            
        # 歩に強化効果を適用
        piece.apply_effect('enhanced', True, self.duration)
        
        print(f"{self.name}の効果が発動！ {piece.kanji}が強化され、{self.duration}ターン（{self.duration*2}手）の間、2マス進めるようになります！")
        print(f"※成ると効果は消えます")
        return True


class Menko(SpecialMove):
    def __init__(self):
        super().__init__(
            "メンコ",
            "ランダムに3枚の駒を裏返す（成っていない駒は成り、成っている駒は元に戻る）",
            duration=0  # 即時効果なので持続ターンは0
        )
    
    def can_use(self, board, player):
        # 盤上に王と金以外の駒が3枚以上あるか確認
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name not in ["king", "gold"]:
                    valid_pieces.append((row, col))
        
        return len(valid_pieces) >= 3
    
    def execute(self, board, player, target_pos=None):
        # 盤上の王と金以外の駒をリストアップ
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name not in ["king", "gold"]:
                    valid_pieces.append((row, col))
        
        # 3枚以上ない場合は効果発動しない
        if len(valid_pieces) < 3:
            return False
        
        # ランダムに3枚選択
        selected_pieces = random.sample(valid_pieces, 3)
        
        # 効果メッセージ
        print(f"{self.name}の効果が発動！ ランダムに選ばれた3枚の駒が裏返ります！")
        
        # 選択された駒を裏返す（成り/成り戻し）
        for row, col in selected_pieces:
            piece = board.grid[row][col]
            if piece:
                # 成っていない駒は成る、成っている駒は元に戻る
                piece.is_promoted = not piece.is_promoted
                print(f"位置 ({row+1},{col+1}) の {piece.kanji} が{'成りました' if piece.is_promoted else '元に戻りました'}！")
        
        return True


# 利用可能な技のリスト
AVAILABLE_SPECIAL_MOVES = [
    Technique1(),
    Menko(),  # メンコ技を追加
]


def get_special_moves():
    """利用可能な特殊技のリストを返す"""
    return AVAILABLE_SPECIAL_MOVES
