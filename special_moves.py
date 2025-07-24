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
        # 既に使用済みの場合は使用不可
        if is_move_used(self.name):
            return False
            
        # デフォルトでは常に使用可能
        return True
        
    def execute(self, board, player, target_pos=None):
        """技の効果を実行する"""
        # 継承先で実装
        pass
            
        # イベント発火（表示はこのイベントに反応する形で行う）
        if board.event_manager:
            board.event_manager.dispatch(
                "special_move_activated", 
                {
                    "move_name": self.name,
                    "message": f"{self.name}の効果が発動！",
                    "affected_pieces": [(target_pos[0], target_pos[1])]
                }
            )
            
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
        print(f"{self.name}")
        
        # 選択された駒を裏返す（成り/成り戻し）
        for row, col in selected_pieces:
            piece = board.grid[row][col]
            if piece:
                # 成っていない駒は成る、成っている駒は元に戻る
                piece.is_promoted = not piece.is_promoted
                print(f"位置 ({row+1},{col+1}) の {piece.kanji} が{'成った' if piece.is_promoted else '元に戻った'}！")
        
        # イベント発火（表示はこのイベントに反応する形で行う）
        if board.event_manager:
            board.event_manager.dispatch(
                "special_move_activated", 
                {
                    "move_name": self.name,
                    "message": f"{self.name}の効果が発動！ 3枚の駒が裏返りました！",
                    "affected_positions": selected_pieces
                }
            )
        
        return True


class Toppuu(SpecialMove):
    def __init__(self):
        super().__init__(
            "突風",
            "ランダムな駒を最大3枚、横に1マスずらす",
            duration=0  # 即時効果なので持続ターンは0
        )
    
    def can_use(self, board, player):
        # 横に空きマスがある駒が1枚以上あるか確認
        valid_pieces = self._get_valid_pieces(board)
        return len(valid_pieces) > 0
    
    def _get_valid_pieces(self, board):
        """横に空きマスがある駒のリストを返す（王を除く、二歩になる駒も除外）"""
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                # 駒があり、王でない場合
                if piece and piece.name != "king":
                    # 左に空きマスがあるか確認
                    if col > 0 and board.grid[row][col-1] is None:
                        # 歩の場合、移動後に二歩にならないか確認
                        if piece.name == "pawn" and not piece.is_promoted:
                            # 左に移動した場合に同じ筋に自分の歩がないか確認
                            has_pawn_in_same_column = False
                            for r in range(9):
                                if r != row and board.grid[r][col-1] and board.grid[r][col-1].name == "pawn" and \
                                   board.grid[r][col-1].player == piece.player and not board.grid[r][col-1].is_promoted:
                                    has_pawn_in_same_column = True
                                    break
                            if not has_pawn_in_same_column:
                                valid_pieces.append((row, col, "left"))
                        else:
                            valid_pieces.append((row, col, "left"))
                    
                    # 右に空きマスがあるか確認
                    if col < 8 and board.grid[row][col+1] is None:
                        # 歩の場合、移動後に二歩にならないか確認
                        if piece.name == "pawn" and not piece.is_promoted:
                            # 右に移動した場合に同じ筋に自分の歩がないか確認
                            has_pawn_in_same_column = False
                            for r in range(9):
                                if r != row and board.grid[r][col+1] and board.grid[r][col+1].name == "pawn" and \
                                   board.grid[r][col+1].player == piece.player and not board.grid[r][col+1].is_promoted:
                                    has_pawn_in_same_column = True
                                    break
                            if not has_pawn_in_same_column:
                                valid_pieces.append((row, col, "right"))
                        else:
                            valid_pieces.append((row, col, "right"))
        return valid_pieces
    
    def execute(self, board, player, target_pos=None):
        # 横に空きマスがある駒のリストを取得
        valid_pieces = self._get_valid_pieces(board)
        
        # 対象となる駒がない場合
        if not valid_pieces:
            print(f"何も起こらなかった。")
            return True
        
        # 移動方向をランダムに決定（左か右）
        direction = random.choice(["left", "right"])
        direction_text = "左" if direction == "left" else "右"
        
        # 選択した方向に移動可能な駒だけをフィルタリング
        filtered_pieces = [(row, col, dir) for row, col, dir in valid_pieces if dir == direction]
        
        # 対象となる駒がない場合
        if not filtered_pieces:
            print(f"何も起こらなかった")
            return True
        
        # 最大3枚をランダムに選択（対象が3枚未満の場合は全て選択）
        num_to_select = min(3, len(filtered_pieces))
        selected_pieces = random.sample(filtered_pieces, num_to_select)
        
        # 効果メッセージ
        print(f"{self.name}")
        
        # 移動した駒の位置を記録
        moved_positions = []
        
        # 選択された駒を移動
        for row, col, dir in selected_pieces:
            piece = board.grid[row][col]
            if piece:
                # 移動先の列を計算
                new_col = col - 1 if dir == "left" else col + 1
                
                # 駒を移動
                board.grid[row][new_col] = piece
                board.grid[row][col] = None
                
                print(f"位置 ({row+1},{col+1}) の {piece.kanji} が{direction_text}に流された")
                
                # 移動後の位置を記録
                moved_positions.append((row, new_col))
        
        # イベント発火（表示はこのイベントに反応する形で行う）
        if board.event_manager:
            board.event_manager.dispatch(
                "special_move_activated", 
                {
                    "move_name": self.name,
                    "message": f"{self.name}の効果が発動！ {len(moved_positions)}枚の駒が{direction_text}にずれました！",
                    "affected_positions": moved_positions
                }
            )
        
        return True


class HengeStaff(SpecialMove):
    def __init__(self):
        super().__init__(
            "変化の杖",
            "盤上の駒をランダムに1つ選び、別の駒に変化させる",
            duration=0  # 即時効果なので持続ターンは0
        )
    
    def can_use(self, board, player):
        # 盤上に王以外の駒が1枚以上あるか確認
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name != "king":
                    return True
        return False
    
    def execute(self, board, player, target_pos=None):
        # 盤上の王以外の駒をリストアップ
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name != "king":
                    valid_pieces.append((row, col))
        
        # 対象となる駒がない場合
        if not valid_pieces:
            print("何も起こらなかった")
            return True
        
        # 技発動メッセージ
        print(f"{self.name}")
        
        # ランダムに1枚選択
        selected_pos = random.choice(valid_pieces)
        row, col = selected_pos
        original_piece = board.grid[row][col]
        
        # 変更可能な駒の種類（王と元の駒を除く）
        piece_types = ["pawn", "lance", "knight", "silver", "gold", "bishop", "rook"]
        if original_piece.name in piece_types:
            piece_types.remove(original_piece.name)
        
        # 変更後の駒をランダムに決定
        while True:
            new_piece_type = random.choice(piece_types)
            
            # 歩の場合は二歩チェック
            if new_piece_type == "pawn":
                # 同じ筋に同じプレイヤーの歩があるかチェック
                has_pawn_in_same_column = False
                for r in range(9):
                    if r != row and board.grid[r][col] and board.grid[r][col].name == "pawn" and \
                       board.grid[r][col].player == original_piece.player and not board.grid[r][col].is_promoted:
                        has_pawn_in_same_column = True
                        break
                
                if has_pawn_in_same_column:
                    # 二歩になる場合は別の駒を選択
                    continue
            
            # 問題なければループを抜ける
            break
        
        # 駒の漢字表記
        kanji_map = {
            "pawn": "歩",
            "lance": "香",
            "knight": "桂",
            "silver": "銀",
            "gold": "金",
            "bishop": "角",
            "rook": "飛"
        }
        
        # 元の駒の情報を保存
        original_player = original_piece.player
        original_name = original_piece.name
        original_kanji = original_piece.kanji
        
        # 新しい駒を作成して配置
        from pieces import Piece
        new_piece = Piece(new_piece_type, kanji_map[new_piece_type], is_promoted=False, player=original_player)
        board.grid[row][col] = new_piece
        
        # 効果メッセージ
        print(f"位置 ({row+1},{col+1}) の {original_kanji} が {new_piece.kanji} に変化した")
        
        # イベント発火（表示はこのイベントに反応する形で行う）
        if board.event_manager:
            board.event_manager.dispatch(
                "special_move_activated", 
                {
                    "move_name": self.name,
                    "message": f"{self.name}の効果が発動！ {original_kanji}が{new_piece.kanji}に変化しました！",
                    "affected_positions": [(row, col)]
                }
            )
        
        return True


class Teleporter(SpecialMove):
    def __init__(self):
        super().__init__(
            "転送装置",
            "ランダムに選ばれた2つの駒の位置を入れ替える",
            duration=0  # 即時効果なので持続ターンは0
        )
    
    def can_use(self, board, player):
        # 盤上に王以外の駒が2枚以上あるか確認
        valid_pieces = self._get_valid_pieces(board)
        return len(valid_pieces) >= 2
    
    def _get_valid_pieces(self, board):
        """入れ替え可能な駒のリストを返す（王を除く）"""
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name != "king":
                    valid_pieces.append((row, col))
        return valid_pieces
    
    def _check_nifu(self, board, pos1, pos2):
        """入れ替えた後に二歩になるかチェック"""
        row1, col1 = pos1
        row2, col2 = pos2
        piece1 = board.grid[row1][col1]
        piece2 = board.grid[row2][col2]
        
        # どちらかが歩でない場合は二歩にならない
        if piece1.name != "pawn" or piece1.is_promoted or piece2.name != "pawn" or piece2.is_promoted:
            return False
            
        # 同じ列でない場合は二歩にならない
        if col1 != col2:
            return False
            
        # 同じプレイヤーの駒でない場合は二歩にならない
        if piece1.player != piece2.player:
            return False
            
        # 同じプレイヤーの歩が同じ列に2枚以上ある場合は二歩になる
        return True
    
    def execute(self, board, player, target_pos=None):
        # 技発動メッセージ
        print(f"{self.name}")
        
        # 入れ替え可能な駒のリストを取得
        valid_pieces = self._get_valid_pieces(board)
        
        # 対象となる駒が2枚未満の場合
        if len(valid_pieces) < 2:
            print(f"何も起こらなかった")
            return True
        
        # 入れ替え可能な組み合わせを見つける
        max_attempts = 50  # 最大試行回数
        for _ in range(max_attempts):
            # ランダムに2枚選択
            pos1, pos2 = random.sample(valid_pieces, 2)
            row1, col1 = pos1
            row2, col2 = pos2
            piece1 = board.grid[row1][col1]
            piece2 = board.grid[row2][col2]
            
            # 二歩チェック
            if self._check_nifu(board, pos1, pos2):
                continue  # 二歩になる場合は別の組み合わせを試す
                
            # 歩の場合、入れ替え後に二歩にならないかチェック
            if piece1.name == "pawn" and not piece1.is_promoted:
                # 同じ筋に同じプレイヤーの歩があるかチェック
                has_pawn_in_same_column = False
                for r in range(9):
                    if r != row2 and board.grid[r][col2] and board.grid[r][col2].name == "pawn" and \
                       board.grid[r][col2].player == piece1.player and not board.grid[r][col2].is_promoted:
                        has_pawn_in_same_column = True
                        break
                if has_pawn_in_same_column:
                    continue  # 二歩になる場合は別の組み合わせを試す
            
            if piece2.name == "pawn" and not piece2.is_promoted:
                # 同じ筋に同じプレイヤーの歩があるかチェック
                has_pawn_in_same_column = False
                for r in range(9):
                    if r != row1 and board.grid[r][col1] and board.grid[r][col1].name == "pawn" and \
                       board.grid[r][col1].player == piece2.player and not board.grid[r][col1].is_promoted:
                        has_pawn_in_same_column = True
                        break
                if has_pawn_in_same_column:
                    continue  # 二歩になる場合は別の組み合わせを試す
            
            # 入れ替え可能な組み合わせが見つかった
            # 駒を入れ替え
            board.grid[row1][col1], board.grid[row2][col2] = board.grid[row2][col2], board.grid[row1][col1]
            
            # 効果メッセージ
            print(f"位置 ({row1+1},{col1+1}) の {piece1.kanji} と位置 ({row2+1},{col2+1}) の {piece2.kanji} が入れ替わった")
            
            # イベント発火（表示はこのイベントに反応する形で行う）
            if board.event_manager:
                board.event_manager.dispatch(
                    "special_move_activated", 
                    {
                        "move_name": self.name,
                        "message": f"{self.name}の効果が発動！ {piece1.kanji}と{piece2.kanji}が入れ替わりました！",
                        "affected_positions": [(row1, col1), (row2, col2)]
                    }
                )
            
            return True
        
        # 入れ替え可能な組み合わせが見つからなかった場合
        print(f"何も起こらなかった")
        return True


class KomaOchi(SpecialMove):
    def __init__(self):
        super().__init__(
            "駒落ち",
            "ランダムに選ばれた1つの駒を消滅させる",
            duration=0  # 即時効果なので持続ターンは0
        )
    
    def can_use(self, board, player):
        # 盤上に王以外の駒が1枚以上あるか確認
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name != "king":
                    return True
        return False
    
    def execute(self, board, player, target_pos=None):
        # 技発動メッセージ
        print(f"{self.name}")
        
        # 盤上の王以外の駒をリストアップ
        valid_pieces = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name != "king":
                    valid_pieces.append((row, col))
        
        # 対象となる駒がない場合
        if not valid_pieces:
            print(f"何も起こらなかった")
            return True
        
        # ランダムに1枚選択
        selected_pos = random.choice(valid_pieces)
        row, col = selected_pos
        piece = board.grid[row][col]
        
        # 駒の情報を保存（メッセージ用）
        piece_kanji = piece.kanji
        piece_player = "先手" if piece.player == 1 else "後手"
        
        # 駒を消滅させる
        board.grid[row][col] = None
        
        # 効果メッセージ
        print(f"位置 ({row+1},{col+1}) の {piece_player}の{piece_kanji} が消滅した")
        
        # イベント発火（表示はこのイベントに反応する形で行う）
        if board.event_manager:
            board.event_manager.dispatch(
                "special_move_activated", 
                {
                    "move_name": self.name,
                    "message": f"{self.name}の効果が発動！ {piece_kanji}が消滅しました！",
                    "affected_positions": [(row, col)]
                }
            )
        
        return True


# 利用可能な技のリスト
AVAILABLE_SPECIAL_MOVES = [
    Menko(),  # メンコ技
    Toppuu(),  # 突風技
    HengeStaff(),  # 変化の杖
    Teleporter(),  # 転送装置
    KomaOchi(),  # 駒落ち
]

# 特殊技の使用状態を管理する辞書
# キー: 技の名前、値: 使用済みかどうか（True/False）
used_special_moves = {}

def get_special_moves():
    """利用可能な特殊技のリストを返す"""
    return AVAILABLE_SPECIAL_MOVES

def reset_special_moves():
    """特殊技の使用状態をリセットする"""
    global used_special_moves
    used_special_moves = {move.name: False for move in get_special_moves()}

def mark_as_used(move_name):
    """特殊技を使用済みとしてマークする"""
    global used_special_moves
    used_special_moves[move_name] = True

def is_move_used(move_name):
    """特殊技が使用済みかどうかを返す"""
    global used_special_moves
    return used_special_moves.get(move_name, False)
