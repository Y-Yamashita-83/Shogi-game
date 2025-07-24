"""
将棋ゲームのAIプレイヤーを実装するモジュール（レベル2: 簡易評価）
"""
import random

class ShogiAI:
    def __init__(self, board):
        self.board = board
        # 駒の価値（簡易評価用）
        self.piece_values = {
            "pawn": 1,
            "lance": 3,
            "knight": 4,
            "silver": 5,
            "gold": 6,
            "bishop": 8,
            "rook": 10,
            "king": 1000
        }
        
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
        
        # 手実行後の状態をログ出力（デバッグ用）
        move_type = best_move['type']
        if move_type == 'move':
            print(f"AI executed move: {move_type} from {best_move['from']} to {best_move['to']}")
        else:
            print(f"AI executed move: {move_type} piece to {best_move['to']}")
        
        return True
        
    def _get_all_possible_moves(self):
        """AIプレイヤー（先手）の全ての合法手を取得"""
        moves = []
        
        # 盤上の駒の移動
        for row in range(9):
            for col in range(9):
                piece = self.board.grid[row][col]
                if piece and piece.player == 1:  # 先手の駒
                    valid_moves = piece.get_possible_moves(self.board, (row, col))
                    for move in valid_moves:
                        moves.append({
                            'type': 'move',
                            'from': (row, col),
                            'to': move,
                            'piece': piece
                        })
        
        # 持ち駒を打つ手 - 既存の関数を活用
        for i, piece in enumerate(self.board.captured_pieces[1]):
            # 既存の関数を使用
            valid_drops = self.board.get_valid_drop_positions(piece)
            for drop in valid_drops:
                moves.append({
                    'type': 'drop',
                    'piece': piece,
                    'to': drop,
                    'index': i
                })
                
        return moves
    
    def _evaluate_moves(self, moves):
        """手を評価して最善手を返す"""
        # レベル2: 簡易評価
        best_score = -float('inf')
        best_moves = []
        
        for move in moves:
            score = self._evaluate_single_move(move)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        # 同点の手からランダムに選択
        return random.choice(best_moves)
    
    def _evaluate_single_move(self, move):
        """1つの手を評価してスコアを返す"""
        score = 0
        
        # 駒を取る手は高評価
        if move['type'] == 'move':
            to_row, to_col = move['to']
            target_piece = self.board.grid[to_row][to_col]
            
            if target_piece:  # 相手の駒を取る手
                piece_value = self.piece_values.get(target_piece.name, 0)
                if target_piece.is_promoted:
                    piece_value *= 1.5  # 成り駒は価値が高い
                score += piece_value * 10  # 駒を取る手は優先度高
                
                # 王を取る手は最高評価
                if target_piece.name == "king":
                    score += 10000
                
            # 成れる場所への移動は評価アップ
            if self._can_promote(move):
                piece = move['piece']
                # 成ることで価値が上がる駒は高評価
                if piece.name in ["pawn", "lance", "knight", "silver"]:
                    score += 15  # 金と同じ動きになるので高評価
                elif piece.name in ["bishop", "rook"]:
                    score += 20  # 動きが拡張されるので非常に高評価
                    
            # 中央に近い位置への移動は少し評価アップ
            center_bonus = self._get_center_bonus(move['to'])
            score += center_bonus
            
            # 自分の駒を守る位置への移動
            defense_bonus = self._get_defense_bonus(move)
            score += defense_bonus
                
        # 持ち駒を打つ評価
        elif move['type'] == 'drop':
            piece = move['piece']
            to_row, to_col = move['to']
            
            # 重要な駒（飛車、角）を打つ手は高評価
            if piece.name in ["rook", "bishop"]:
                score += 8
            elif piece.name == "gold":
                score += 6
            elif piece.name in ["silver", "knight"]:
                score += 4
            elif piece.name in ["lance", "pawn"]:
                score += 2
                
            # 中央に近い位置に打つ手は評価アップ
            center_bonus = self._get_center_bonus((to_row, to_col))
            score += center_bonus
            
            # 相手の王に近い位置に打つ手は評価アップ
            king_distance_bonus = self._get_king_distance_bonus((to_row, to_col))
            score += king_distance_bonus
                
        return score
    
    def _get_center_bonus(self, position):
        """中央に近いほど高いボーナスを返す"""
        row, col = position
        # 盤の中央（4,4）からの距離を計算
        center_distance = abs(row - 4) + abs(col - 4)
        # 距離が近いほど高いボーナス（最大3点）
        return max(0, 3 - center_distance // 2)
    
    def _get_defense_bonus(self, move):
        """自分の重要な駒を守る手にボーナスを与える"""
        # 簡易実装：自分の王の近くに移動する手は少し評価アップ
        to_row, to_col = move['to']
        
        # 自分の王の位置を探す
        king_pos = None
        for row in range(9):
            for col in range(9):
                piece = self.board.grid[row][col]
                if piece and piece.player == 1 and piece.name == "king":
                    king_pos = (row, col)
                    break
            if king_pos:
                break
                
        if king_pos:
            king_row, king_col = king_pos
            distance_to_king = abs(to_row - king_row) + abs(to_col - king_col)
            # 王の近く（距離2以内）に移動する手は少しボーナス
            if distance_to_king <= 2:
                return 2
                
        return 0
    
    def _get_king_distance_bonus(self, position):
        """相手の王に近い位置にボーナスを与える"""
        row, col = position
        
        # 相手の王の位置を探す
        enemy_king_pos = None
        for r in range(9):
            for c in range(9):
                piece = self.board.grid[r][c]
                if piece and piece.player == 2 and piece.name == "king":
                    enemy_king_pos = (r, c)
                    break
            if enemy_king_pos:
                break
                
        if enemy_king_pos:
            king_row, king_col = enemy_king_pos
            distance_to_enemy_king = abs(row - king_row) + abs(col - king_col)
            # 相手の王に近いほど高いボーナス（最大5点）
            return max(0, 5 - distance_to_enemy_king)
            
        return 0
    
    def _can_promote(self, move):
        """成れるかどうかをチェック"""
        if move['type'] != 'move':
            return False
            
        piece = move['piece']
        to_row, to_col = move['to']
        
        # 既に成っている駒や、成れない駒はfalse
        if piece.is_promoted or piece.name in ["king", "gold"]:
            return False
            
        # 先手の場合、敵陣（0-2行目）に入るか、敵陣から出る場合
        if piece.player == 1:
            from_row, from_col = move['from']
            return to_row <= 2 or from_row <= 2
        # 後手の場合、敵陣（6-8行目）に入るか、敵陣から出る場合
        else:
            from_row, from_col = move['from']
            return to_row >= 6 or from_row >= 6
    
    def _should_promote(self, move):
        """成るべきかどうかを判断"""
        if not self._can_promote(move):
            return False
            
        piece = move['piece']
        
        # 歩、香、桂、銀は基本的に成る
        if piece.name in ["pawn", "lance", "knight", "silver"]:
            return True
            
        # 角、飛車は状況に応じて（簡易実装では成る）
        if piece.name in ["bishop", "rook"]:
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
