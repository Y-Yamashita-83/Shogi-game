"""
将棋ゲームのAIプレイヤーを実装するモジュール（Phase 1 Step 3: 王手回避強化版）
"""
import random

class PositionEvaluator:
    """局面評価を担当するクラス"""
    
    def __init__(self):
        self.setup_piece_values()
        self.setup_piece_square_tables()
        
    def setup_piece_values(self):
        """駒の基本価値を設定"""
        self.piece_values = {
            "pawn": 100,
            "lance": 300,
            "knight": 350,
            "silver": 500,
            "gold": 600,
            "bishop": 800,
            "rook": 1000,
            "king": 10000
        }
        
        # 成り駒の価値（基本駒 + 成りボーナス）
        self.promoted_bonus = {
            "pawn": 400,    # と金は金と同等
            "lance": 300,   # 成香は金と同等
            "knight": 250,  # 成桂は金と同等
            "silver": 100,  # 成銀は金と同等
            "bishop": 300,  # 馬は角+300
            "rook": 400     # 龍は飛車+400
        }
        
    def setup_piece_square_tables(self):
        """駒の位置による価値テーブルを設定（先手視点）"""
        # 歩の位置価値（前進するほど価値が高い）
        self.pawn_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
            [ 5,  5,  5,  5,  5,  5,  5,  5,  5],
            [10, 10, 10, 10, 10, 10, 10, 10, 10],
            [15, 15, 15, 15, 15, 15, 15, 15, 15],
            [20, 20, 20, 20, 20, 20, 20, 20, 20],
            [25, 25, 25, 25, 25, 25, 25, 25, 25],
            [30, 30, 30, 30, 30, 30, 30, 30, 30],
            [35, 35, 35, 35, 35, 35, 35, 35, 35],
            [40, 40, 40, 40, 40, 40, 40, 40, 40]
        ]
        
        # 香車の位置価値
        self.lance_table = [
            [ 0,  0,  0,  0,  0,  0,  0,  0,  0],
            [ 5,  5,  5,  5,  5,  5,  5,  5,  5],
            [10, 10, 10, 10, 10, 10, 10, 10, 10],
            [15, 15, 15, 15, 15, 15, 15, 15, 15],
            [20, 20, 20, 20, 20, 20, 20, 20, 20],
            [25, 25, 25, 25, 25, 25, 25, 25, 25],
            [30, 30, 30, 30, 30, 30, 30, 30, 30],
            [35, 35, 35, 35, 35, 35, 35, 35, 35],
            [40, 40, 40, 40, 40, 40, 40, 40, 40]
        ]
        
        # 桂馬の位置価値（中央寄りが良い）
        self.knight_table = [
            [-10, -5,  0,  5, 10,  5,  0, -5,-10],
            [-10, -5,  0,  5, 10,  5,  0, -5,-10],
            [ -5,  0,  5, 10, 15, 10,  5,  0, -5],
            [ -5,  0,  5, 10, 15, 10,  5,  0, -5],
            [  0,  5, 10, 15, 20, 15, 10,  5,  0],
            [  0,  5, 10, 15, 20, 15, 10,  5,  0],
            [  5, 10, 15, 20, 25, 20, 15, 10,  5],
            [ 10, 15, 20, 25, 30, 25, 20, 15, 10],
            [ 15, 20, 25, 30, 35, 30, 25, 20, 15]
        ]
        
        # 銀将の位置価値（前進と中央寄りが良い）
        self.silver_table = [
            [-10, -5,  0,  5, 10,  5,  0, -5,-10],
            [ -5,  0,  5, 10, 15, 10,  5,  0, -5],
            [  0,  5, 10, 15, 20, 15, 10,  5,  0],
            [  5, 10, 15, 20, 25, 20, 15, 10,  5],
            [ 10, 15, 20, 25, 30, 25, 20, 15, 10],
            [ 15, 20, 25, 30, 35, 30, 25, 20, 15],
            [ 20, 25, 30, 35, 40, 35, 30, 25, 20],
            [ 25, 30, 35, 40, 45, 40, 35, 30, 25],
            [ 30, 35, 40, 45, 50, 45, 40, 35, 30]
        ]
        
        # 金将の位置価値（王の近くが良い）
        self.gold_table = [
            [ 10, 15, 20, 25, 30, 25, 20, 15, 10],
            [ 15, 20, 25, 30, 35, 30, 25, 20, 15],
            [ 20, 25, 30, 35, 40, 35, 30, 25, 20],
            [ 15, 20, 25, 30, 35, 30, 25, 20, 15],
            [ 10, 15, 20, 25, 30, 25, 20, 15, 10],
            [  5, 10, 15, 20, 25, 20, 15, 10,  5],
            [  0,  5, 10, 15, 20, 15, 10,  5,  0],
            [ -5,  0,  5, 10, 15, 10,  5,  0, -5],
            [-10, -5,  0,  5, 10,  5,  0, -5,-10]
        ]
        
        # 角行の位置価値（中央が良い）
        self.bishop_table = [
            [-10, -5,  0,  5, 10,  5,  0, -5,-10],
            [ -5,  5, 10, 15, 20, 15, 10,  5, -5],
            [  0, 10, 20, 25, 30, 25, 20, 10,  0],
            [  5, 15, 25, 30, 35, 30, 25, 15,  5],
            [ 10, 20, 30, 35, 40, 35, 30, 20, 10],
            [  5, 15, 25, 30, 35, 30, 25, 15,  5],
            [  0, 10, 20, 25, 30, 25, 20, 10,  0],
            [ -5,  5, 10, 15, 20, 15, 10,  5, -5],
            [-10, -5,  0,  5, 10,  5,  0, -5,-10]
        ]
        
        # 飛車の位置価値（中央縦が良い）
        self.rook_table = [
            [ 0,  5, 10, 15, 20, 15, 10,  5,  0],
            [ 5, 10, 15, 20, 25, 20, 15, 10,  5],
            [10, 15, 20, 25, 30, 25, 20, 15, 10],
            [15, 20, 25, 30, 35, 30, 25, 20, 15],
            [20, 25, 30, 35, 40, 35, 30, 25, 20],
            [15, 20, 25, 30, 35, 30, 25, 20, 15],
            [10, 15, 20, 25, 30, 25, 20, 15, 10],
            [ 5, 10, 15, 20, 25, 20, 15, 10,  5],
            [ 0,  5, 10, 15, 20, 15, 10,  5,  0]
        ]
        
        # 王の位置価値（序盤は安全な位置、終盤は中央寄り）
        self.king_table = [
            [-30,-20,-10,  0, 10,  0,-10,-20,-30],
            [-20,-10,  0, 10, 20, 10,  0,-10,-20],
            [-10,  0, 10, 20, 30, 20, 10,  0,-10],
            [-10,  0, 10, 20, 30, 20, 10,  0,-10],
            [-10,  0, 10, 20, 30, 20, 10,  0,-10],
            [-10,  0, 10, 20, 30, 20, 10,  0,-10],
            [-20,-10,  0, 10, 20, 10,  0,-10,-20],
            [-30,-20,-10,  0, 10,  0,-10,-20,-30],
            [-40,-30,-20,-10,  0,-10,-20,-30,-40]
        ]
        
        # 位置テーブルをまとめる
        self.piece_square_tables = {
            "pawn": self.pawn_table,
            "lance": self.lance_table,
            "knight": self.knight_table,
            "silver": self.silver_table,
            "gold": self.gold_table,
            "bishop": self.bishop_table,
            "rook": self.rook_table,
            "king": self.king_table
        }
        
    def get_piece_square_value(self, piece, row, col, player):
        """駒の位置価値を取得"""
        if piece.name not in self.piece_square_tables:
            return 0
            
        table = self.piece_square_tables[piece.name]
        
        # 後手の場合は盤面を反転
        if player == 2:
            row = 8 - row
            
        return table[row][col]


class ShogiAI:
    def __init__(self, board):
        self.board = board
        self.evaluator = PositionEvaluator()
        
    def make_move(self):
        """AIの手を決定して実行する"""
        # 全ての合法手を列挙
        possible_moves = self._get_all_possible_moves()
        
        if not possible_moves:
            return False  # 合法手がない（詰み）
            
        # 合法手を評価してベストな手を選ぶ
        best_move = self._evaluate_moves(possible_moves)
        
        # 選んだ手を実行
        self._execute_move(best_move)
        
    def _get_all_possible_moves(self):
        """全ての合法手を取得"""
        possible_moves = []
        
        # 盤上の駒の移動
        for row in range(9):
            for col in range(9):
                piece = self.board.grid[row][col]
                if piece and piece.player == self.board.player_turn:
                    moves = piece.get_possible_moves(self.board, (row, col))
                    for move_row, move_col in moves:
                        possible_moves.append({
                            'type': 'move',
                            'from': (row, col),
                            'to': (move_row, move_col),
                            'piece': piece
                        })
        
        # 持ち駒の配置
        for i, piece in enumerate(self.board.captured_pieces[self.board.player_turn]):
            drop_positions = self.board.get_valid_drop_positions(piece)
            for drop_row, drop_col in drop_positions:
                possible_moves.append({
                    'type': 'drop',
                    'piece_index': i,
                    'to': (drop_row, drop_col),
                    'piece': piece
                })
        
        return possible_moves
        
    def _evaluate_moves(self, possible_moves):
        """手を評価して最良の手を選択（元のコードと同じ戻り値型）"""
        best_moves = []  # 最高スコアの手のリスト
        best_score = float('-inf')
        
        for move in possible_moves:
            # 新しい評価方法を使用
            score = self._evaluate_move_advanced(move)
            
            # より良い手が見つかった場合
            if score > best_score:
                best_score = score
                best_moves = [move]  # 新しい最高スコアでリストをリセット
            elif score == best_score:
                best_moves.append(move)  # 同じスコアの手を追加
                
        return random.choice(best_moves)  # 元のコードと同じ：リストからランダム選択
        
    def _evaluate_move_advanced(self, move):
        """改良された手の評価"""
        score = 0
        
        # 危険回避評価（最優先）
        danger_avoidance_score = self._get_danger_avoidance_score(move)
        score += danger_avoidance_score
        
        # 王手回避の最優先評価
        check_evasion_score = self._get_check_evasion_score(move)
        score += check_evasion_score
        
        # 詰み判定（最優先）
        mate_score = self._get_mate_score(move)
        score += mate_score
        
        # 先読み評価（2手先まで）
        lookahead_score = self._get_lookahead_score(move)
        score += lookahead_score
        
        # 手の種類による基本評価
        move_score = self._get_move_base_score(move)
        score += move_score
        
        # 位置価値評価
        positional_score = self._get_positional_score(move)
        score += positional_score
        
        # 戦術評価
        tactical_score = self._get_tactical_score(move)
        score += tactical_score
        
        # 王の安全度評価
        safety_score = self._get_safety_score(move)
        score += safety_score
        
        return score
        
    def _get_check_evasion_score(self, move):
        """王手回避の評価（最優先）"""
        # 現在王手をかけられているかチェック
        if not self.board.in_check:
            return 0
            
        score = 0
        
        # 王手回避の手には非常に高いスコアを与える
        if self._is_check_evasion_move(move):
            score += 10000  # 王手回避は最優先
            
            # 王が逃げる手
            if move['type'] == 'move' and move['piece'].name == 'king':
                score += 5000  # 王の移動による回避
                
                # より安全な場所への移動はさらに高評価
                to_row, to_col = move['to']
                if self._is_safe_square(to_row, to_col, move['piece'].player):
                    score += 2000
                    
            # 王手している駒を取る手
            elif self._captures_checking_piece(move):
                score += 8000  # 王手駒を取る
                
            # 王手を遮る手
            elif self._blocks_check(move):
                score += 6000  # 王手を遮る
                
        else:
            # 王手回避にならない手は大幅減点
            score -= 50000
            
        return score
        
    def _is_check_evasion_move(self, move):
        """この手が王手回避になるかどうかの正確な判定"""
        # 現在王手をかけられていない場合は王手回避ではない
        if not self.board.in_check:
            return False
            
        # シミュレーションで手を実行して王手状態が解除されるかチェック
        return self._simulate_move_and_check_safety(move)
        
    def _simulate_move_and_check_safety(self, move):
        """手をシミュレーション実行して王手状態が解除されるかチェック"""
        # 現在の盤面状態を保存
        original_state = self._save_board_state()
        
        try:
            # 手を実行
            self._simulate_move_execution(move)
            
            # 手番を相手に変更（王手チェックのため）
            original_turn = self.board.player_turn
            self.board.player_turn = 3 - self.board.player_turn
            
            # 自分の王が安全かチェック
            is_safe = not self._is_king_in_check(original_turn)
            
            return is_safe
            
        finally:
            # 盤面を元に戻す
            self._restore_board_state(original_state)
            
    def _simulate_move_execution(self, move):
        """手のシミュレーション実行（リストは変更しない）"""
        if move['type'] == 'move':
            from_row, from_col = move['from']
            to_row, to_col = move['to']
            
            # 駒を移動
            piece = self.board.grid[from_row][from_col]
            captured_piece = self.board.grid[to_row][to_col]
            
            self.board.grid[from_row][from_col] = None
            self.board.grid[to_row][to_col] = piece
            
            # 駒を取った場合の処理（シミュレーションなので持ち駒リストは変更しない）
            # 実際の処理では captured_pieces に追加するが、シミュレーションでは省略
                
        elif move['type'] == 'drop':
            piece_index = move['piece_index']
            to_row, to_col = move['to']
            
            # 持ち駒を参照のみ（リストから削除しない）
            if piece_index < len(self.board.captured_pieces[self.board.player_turn]):
                piece = self.board.captured_pieces[self.board.player_turn][piece_index]
                self.board.grid[to_row][to_col] = piece
                # 注意: 持ち駒リストからは削除しない（シミュレーションのため）
            
    def _is_king_in_check(self, player):
        """指定プレイヤーの王が王手をかけられているかチェック"""
        # 王の位置を探す
        king_pos = self._find_king(player)
        if not king_pos:
            return False  # 王がいない場合は王手ではない
            
        king_row, king_col = king_pos
        opponent = 3 - player
        
        # 相手の全ての駒から王が攻撃されているかチェック
        for row in range(9):
            for col in range(9):
                piece = self.board.grid[row][col]
                if piece and piece.player == opponent:
                    try:
                        # この駒が王を攻撃できるかチェック
                        possible_moves = piece.get_possible_moves(self.board, (row, col))
                        if (king_row, king_col) in possible_moves:
                            return True
                    except:
                        # エラーが発生した場合は無視
                        continue
                        
        return False
        
    def _save_board_state(self):
        """盤面状態を保存（簡素化版）"""
        # 盤面のみをコピー（持ち駒リストは変更しないので保存不要）
        grid_copy = []
        for row in self.board.grid:
            row_copy = []
            for piece in row:
                row_copy.append(piece)  # 参照をそのままコピー
            grid_copy.append(row_copy)
        
        state = {
            'grid': grid_copy,
            'player_turn': self.board.player_turn,
            'in_check': self.board.in_check
        }
        return state
        
    def _restore_board_state(self, state):
        """盤面状態を復元（簡素化版）"""
        self.board.grid = state['grid']
        self.board.player_turn = state['player_turn']
        self.board.in_check = state['in_check']
        
    def _captures_checking_piece(self, move):
        """王手している駒を取る手かどうか"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        target_piece = self.board.grid[to_row][to_col]
        
        if target_piece and target_piece.player != self.board.player_turn:
            # 簡易的に、相手の強い駒（飛車、角、金、銀）を取る手を王手駒取りと判定
            if target_piece.name in ['rook', 'bishop', 'gold', 'silver', 'knight', 'lance']:
                return True
                
        return False
        
    def _blocks_check(self, move):
        """王手を遮る手かどうかの簡易判定"""
        # 自分の王の位置を取得
        king_pos = self._find_king(self.board.player_turn)
        if not king_pos:
            return False
            
        king_row, king_col = king_pos
        
        if move['type'] == 'move':
            to_row, to_col = move['to']
        else:  # drop
            to_row, to_col = move['to']
            
        # 王の近く（距離2以内）に駒を配置する手を遮る手と判定
        distance = abs(to_row - king_row) + abs(to_col - king_col)
        if distance <= 2:
            return True
            
        return False
        
    def _is_safe_square(self, row, col, player):
        """指定した位置が安全かどうかの簡易判定"""
        # 盤の端や角は比較的安全
        if row == 0 or row == 8 or col == 0 or col == 8:
            return True
            
        # 自分の駒に囲まれた位置は安全
        adjacent_friendly = 0
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                piece = self.board.grid[new_row][new_col]
                if piece and piece.player == player:
                    adjacent_friendly += 1
                    
        return adjacent_friendly >= 2
        
    def _get_move_base_score(self, move):
        """手の基本スコア（駒を取る価値など）"""
        score = 0
        
        if move['type'] == 'move':
            # 移動先に敵駒がある場合（駒を取る）
            to_row, to_col = move['to']
            target_piece = self.board.grid[to_row][to_col]
            if target_piece and target_piece.player != self.board.player_turn:
                piece_value = self.evaluator.piece_values[target_piece.name]
                if target_piece.is_promoted and target_piece.name in self.evaluator.promoted_bonus:
                    piece_value += self.evaluator.promoted_bonus[target_piece.name]
                score += piece_value
                
                # 王を取る手は最高評価
                if target_piece.name == "king":
                    score += 50000
                
        return score
        
    def _get_positional_score(self, move):
        """位置価値による評価"""
        if move['type'] == 'move':
            from_row, from_col = move['from']
            to_row, to_col = move['to']
            piece = move['piece']
            
            # 移動前の位置価値
            old_value = self.evaluator.get_piece_square_value(piece, from_row, from_col, piece.player)
            # 移動後の位置価値
            new_value = self.evaluator.get_piece_square_value(piece, to_row, to_col, piece.player)
            
            return new_value - old_value
            
        elif move['type'] == 'drop':
            # 持ち駒を打つ場合の位置価値
            to_row, to_col = move['to']
            piece = move['piece']
            
            return self.evaluator.get_piece_square_value(piece, to_row, to_col, piece.player)
            
        return 0
        
    def _get_tactical_score(self, move):
        """戦術的評価"""
        score = 0
        
        # 成りの評価
        if self._can_promote(move):
            piece = move['piece']
            if piece.name in ["pawn", "lance", "knight", "silver"]:
                score += 200  # 金と同じ動きになるので高評価
            elif piece.name in ["bishop", "rook"]:
                score += 300  # 動きが拡張されるので非常に高評価
                
        # 敵陣進出ボーナス
        if move['type'] == 'move':
            to_row, to_col = move['to']
            piece = move['piece']
            
            # 敵陣（上位3段または下位3段）への進出
            if (piece.player == 1 and to_row <= 2) or (piece.player == 2 and to_row >= 6):
                score += 50
                
        # 王手をかける手の評価
        if self._gives_check(move):
            score += 150
            
        # 中央制圧ボーナス
        center_bonus = self._get_center_control_bonus(move)
        score += center_bonus
        
        return score
        
    def _get_safety_score(self, move):
        """王の安全度に関する評価"""
        score = 0
        
        # 自分の王の周りを守る手
        if move['type'] == 'move':
            to_row, to_col = move['to']
            piece = move['piece']
            
            # 自分の王の位置を探す
            king_pos = self._find_king(piece.player)
            if king_pos:
                king_row, king_col = king_pos
                
                # 王の近くに金・銀を配置する手は高評価
                distance = abs(to_row - king_row) + abs(to_col - king_col)
                if piece.name in ["gold", "silver"] and distance <= 2:
                    score += 30
                    
        return score
        
    def _can_promote(self, move):
        """成ることができるかどうか"""
        if move['type'] != 'move':
            return False
            
        piece = move['piece']
        to_row, to_col = move['to']
        
        # 既に成っている駒や成れない駒
        if piece.is_promoted or piece.name in ["king", "gold"]:
            return False
            
        # 敵陣に入る場合
        if (piece.player == 1 and to_row <= 2) or (piece.player == 2 and to_row >= 6):
            return True
            
        return False
        
    def _gives_check(self, move):
        """この手が王手をかけるかどうか（簡易判定）"""
        if move['type'] != 'move':
            return False
            
        # 簡易実装：相手の王の近くに攻撃駒を移動する手を王手と判定
        to_row, to_col = move['to']
        piece = move['piece']
        opponent = 3 - piece.player
        
        # 相手の王の位置を探す
        enemy_king_pos = self._find_king(opponent)
        if enemy_king_pos:
            king_row, king_col = enemy_king_pos
            
            # 移動先から王への距離
            distance = abs(to_row - king_row) + abs(to_col - king_col)
            
            # 飛車・角・金・銀が王の近くに来る場合は王手の可能性が高い
            if piece.name in ["rook", "bishop", "gold", "silver"] and distance <= 3:
                return True
                
        return False
        
    def _get_center_control_bonus(self, move):
        """中央制圧ボーナス"""
        if move['type'] == 'move':
            to_row, to_col = move['to']
        else:
            to_row, to_col = move['to']
            
        # 中央4マス（4,4）（4,5）（5,4）（5,5）への移動・配置
        center_squares = [(4, 4), (4, 5), (5, 4), (5, 5)]
        if (to_row, to_col) in center_squares:
            return 25
            
        # 中央に近い位置
        center_distance = abs(to_row - 4) + abs(to_col - 4)
        if center_distance <= 2:
            return 10
            
        return 0
        
    def _find_king(self, player):
        """指定したプレイヤーの王の位置を探す"""
        for row in range(9):
            for col in range(9):
                piece = self.board.grid[row][col]
                if piece and piece.name == "king" and piece.player == player:
                    return (row, col)
        return None
        
    def _get_mate_score(self, move):
        """詰み判定による評価"""
        score = 0
        
        # 簡易的な詰み判定
        if self._leads_to_mate(move):
            score += 100000  # 詰みに繋がる手は最高評価
            
        # 相手を詰めろ（次に詰み）にする手
        elif self._leads_to_mate_threat(move):
            score += 20000  # 詰めろは非常に高評価
            
        return score
        
    def _leads_to_mate(self, move):
        """この手が詰みに繋がるかどうかの簡易判定"""
        # 相手の王を取る手は詰み
        if move['type'] == 'move':
            to_row, to_col = move['to']
            target_piece = self.board.grid[to_row][to_col]
            if target_piece and target_piece.name == 'king':
                return True
                
        # 王手をかけて、相手に逃げ場がない状況を作る手
        if self._gives_check(move):
            # 簡易的に、相手の王の周囲を制圧する手を詰みと判定
            opponent = 3 - self.board.player_turn
            enemy_king_pos = self._find_king(opponent)
            if enemy_king_pos:
                king_row, king_col = enemy_king_pos
                
                # 王の周囲8マスのうち、逃げられるマスが少ない場合
                escape_squares = self._count_king_escape_squares(king_row, king_col, opponent)
                if escape_squares <= 1:
                    return True
                    
        return False
        
    def _leads_to_mate_threat(self, move):
        """この手が詰めろ（次に詰み）に繋がるかどうか"""
        # 王手をかける手で、相手の逃げ場を制限する手
        if self._gives_check(move):
            opponent = 3 - self.board.player_turn
            enemy_king_pos = self._find_king(opponent)
            if enemy_king_pos:
                king_row, king_col = enemy_king_pos
                escape_squares = self._count_king_escape_squares(king_row, king_col, opponent)
                if escape_squares <= 2:
                    return True
                    
        return False
        
    def _count_king_escape_squares(self, king_row, king_col, player):
        """王の逃げ場の数を数える"""
        escape_count = 0
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            new_row, new_col = king_row + dr, king_col + dc
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                piece = self.board.grid[new_row][new_col]
                # 空きマスまたは相手の駒がある場合は逃げ場の候補
                if piece is None or piece.player != player:
                    escape_count += 1
                    
        return escape_count
        
    def _get_lookahead_score(self, move):
        """先読み評価（2手先まで）"""
        # 簡易的な先読み実装
        score = 0
        
        # この手を実行した後の相手の最善手を予測
        if self._gives_check(move):
            # 王手をかける手は相手の選択肢を制限するので有利
            score += 100
            
        # 重要な駒を安全な場所に移動する手
        if move['type'] == 'move':
            piece = move['piece']
            to_row, to_col = move['to']
            
            # 価値の高い駒を安全な場所に移動
            if piece.name in ['rook', 'bishop'] and self._is_safe_square(to_row, to_col, piece.player):
                score += 80
            elif piece.name in ['gold', 'silver'] and self._is_safe_square(to_row, to_col, piece.player):
                score += 40
                
        # 相手の重要な駒を攻撃する手
        if self._threatens_important_piece(move):
            score += 150
            
        return score
        
    def _threatens_important_piece(self, move):
        """重要な相手の駒を脅かす手かどうか"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 移動先から攻撃できる相手の駒をチェック
        possible_attacks = piece.get_possible_moves(self.board, (to_row, to_col))
        
        for attack_row, attack_col in possible_attacks:
            target = self.board.grid[attack_row][attack_col]
            if target and target.player != piece.player:
                # 重要な駒（飛車、角、金）を攻撃する場合
                if target.name in ['rook', 'bishop', 'gold']:
                    return True
                    
        return False
        
    def _get_danger_avoidance_score(self, move):
        """危険回避評価（自殺手防止）"""
        score = 0
        
        # 王を危険な場所に移動させる手は大幅減点
        if move['type'] == 'move' and move['piece'].name == 'king':
            to_row, to_col = move['to']
            
            # 王が敵の攻撃範囲に入る手は大幅減点
            if self._is_under_attack(to_row, to_col, move['piece'].player):
                score -= 100000  # 王を危険な場所に移動は最悪
                
            # 王が孤立する手も減点
            if self._is_isolated_position(to_row, to_col, move['piece'].player):
                score -= 20000
                
        # 重要な駒を無防備な場所に移動させる手も減点
        elif move['type'] == 'move':
            piece = move['piece']
            to_row, to_col = move['to']
            
            if piece.name in ['rook', 'bishop']:
                # 飛車・角を敵の攻撃範囲に移動
                if self._is_under_attack(to_row, to_col, piece.player):
                    score -= 5000
                    
            elif piece.name in ['gold', 'silver']:
                # 金・銀を敵の攻撃範囲に移動
                if self._is_under_attack(to_row, to_col, piece.player):
                    score -= 2000
                    
        # 駒を取られる手（等価交換でない）を減点
        if self._is_bad_trade(move):
            score -= 10000
            
        # 自分の重要な駒を見捨てる手を減点
        if self._abandons_important_piece(move):
            score -= 8000
            
        return score
        
    def _is_under_attack(self, row, col, player):
        """指定した位置が敵の攻撃範囲にあるかどうか"""
        opponent = 3 - player
        
        # 相手の全ての駒から攻撃されるかチェック
        for r in range(9):
            for c in range(9):
                piece = self.board.grid[r][c]
                if piece and piece.player == opponent:
                    # この駒が(row, col)を攻撃できるかチェック
                    try:
                        possible_moves = piece.get_possible_moves(self.board, (r, c))
                        if (row, col) in possible_moves:
                            return True
                    except:
                        # エラーが発生した場合は安全側に倒す
                        continue
                        
        return False
        
    def _is_isolated_position(self, row, col, player):
        """指定した位置が孤立しているかどうか"""
        # 周囲8マスに味方の駒がいるかチェック
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        friendly_count = 0
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                piece = self.board.grid[new_row][new_col]
                if piece and piece.player == player:
                    friendly_count += 1
                    
        return friendly_count == 0
        
    def _is_bad_trade(self, move):
        """悪い交換（価値の低い駒で価値の高い駒を取られる）かどうか"""
        if move['type'] != 'move':
            return False
            
        from_row, from_col = move['from']
        to_row, to_col = move['to']
        moving_piece = move['piece']
        target_piece = self.board.grid[to_row][to_col]
        
        # 駒を取る手でない場合は判定しない
        if not target_piece or target_piece.player == moving_piece.player:
            return False
            
        # 移動先が敵の攻撃範囲にある場合
        if self._is_under_attack(to_row, to_col, moving_piece.player):
            moving_value = self.evaluator.piece_values[moving_piece.name]
            target_value = self.evaluator.piece_values[target_piece.name]
            
            # 自分の駒の方が価値が高い場合は悪い交換
            if moving_value > target_value + 200:  # 200点以上の差があれば悪い交換
                return True
                
        return False
        
    def _abandons_important_piece(self, move):
        """重要な駒を見捨てる手かどうか"""
        if move['type'] != 'move':
            return False
            
        from_row, from_col = move['from']
        moving_piece = move['piece']
        
        # 移動する駒が重要な駒を守っていたかチェック
        for r in range(9):
            for c in range(9):
                piece = self.board.grid[r][c]
                if piece and piece.player == moving_piece.player and piece.name in ['rook', 'bishop', 'gold', 'king']:
                    # この重要な駒が攻撃されているかチェック
                    if self._is_under_attack(r, c, piece.player):
                        # 移動する駒がこの重要な駒を守っていたかチェック
                        if self._was_protecting(from_row, from_col, r, c, moving_piece):
                            return True
                            
        return False
        
    def _was_protecting(self, protector_row, protector_col, protected_row, protected_col, protector_piece):
        """守っていた駒かどうかの簡易判定"""
        # 距離が近い場合は守っていたと判定
        distance = abs(protector_row - protected_row) + abs(protector_col - protected_col)
        
        # 金・銀が王の近くにいる場合
        if protector_piece.name in ['gold', 'silver'] and distance <= 2:
            protected_piece = self.board.grid[protected_row][protected_col]
            if protected_piece and protected_piece.name == 'king':
                return True
                
        # 一般的な守備関係
        if distance <= 1:
            return True
            
        return False
        
    def _execute_move(self, move):
        """選択した手を実行する"""
        if move['type'] == 'move':
            from_pos = move['from']
            to_pos = move['to']
            
            should_promote = self._should_promote(move)
            self.board.move_piece(from_pos, to_pos)
            
            if self.board.promotion_pending:
                self.board.handle_promotion(should_promote)
                
        elif move['type'] == 'drop':
            to_pos = move['to']
            piece = move['piece']
            self.board.drop_piece(piece, to_pos)
            
    def _should_promote(self, move):
        """成るかどうかを判断する"""
        piece = move['piece']
        to_row, to_col = move['to']
        
        # 成れない駒は成らない
        if piece.name in ["king", "gold"] or piece.is_promoted:
            return False
            
        # 敵陣に入った場合
        if (piece.player == 1 and to_row <= 2) or (piece.player == 2 and to_row >= 6):
            # 歩、香、桂、銀は基本的に成る
            if piece.name in ["pawn", "lance", "knight", "silver"]:
                return True
            # 角、飛車は状況に応じて（今回は常に成る）
            elif piece.name in ["bishop", "rook"]:
                return True
                
        return False
