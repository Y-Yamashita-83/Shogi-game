"""
将棋ゲームのAIプレイヤーを実装するモジュール（Phase C: 高度な機能版）
"""
import random
import time

class TacticsEngine:
    """戦術パターン認識エンジン"""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.setup_tactical_patterns()
        
    def setup_tactical_patterns(self):
        """戦術パターンの定義"""
        self.tactical_bonuses = {
            "fork": 300,           # フォーク（両取り）
            "pin": 200,            # ピン（釘付け）
            "skewer": 250,         # スキュワー（串刺し）
            "discovered_attack": 180,  # 開き王手・開き攻撃
            "double_attack": 220,  # 両王手
            "sacrifice": 400,      # 捨て駒戦術
            "promotion_threat": 150, # 成り込み脅威
        }
        
    def evaluate_tactics(self, board, move):
        """戦術的価値を総合評価"""
        total_score = 0
        
        # 各戦術パターンをチェック
        if self._detect_fork(board, move):
            total_score += self.tactical_bonuses["fork"]
            
        if self._detect_pin(board, move):
            total_score += self.tactical_bonuses["pin"]
            
        if self._detect_skewer(board, move):
            total_score += self.tactical_bonuses["skewer"]
            
        if self._detect_discovered_attack(board, move):
            total_score += self.tactical_bonuses["discovered_attack"]
            
        if self._detect_double_attack(board, move):
            total_score += self.tactical_bonuses["double_attack"]
            
        if self._detect_sacrifice_pattern(board, move):
            total_score += self.tactical_bonuses["sacrifice"]
            
        if self._detect_promotion_threat(board, move):
            total_score += self.tactical_bonuses["promotion_threat"]
            
        return total_score
        
    def _detect_fork(self, board, move):
        """フォーク（両取り）の検出"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 移動後の攻撃可能位置を取得
        try:
            attack_positions = piece.get_possible_moves(board, (to_row, to_col))
        except:
            return False
            
        # 攻撃可能な敵駒をカウント
        valuable_targets = 0
        for attack_row, attack_col in attack_positions:
            target = board.grid[attack_row][attack_col]
            if target and target.player != piece.player:
                # 価値の高い駒（金以上）を対象とする
                if target.name in ["gold", "bishop", "rook", "king"]:
                    valuable_targets += 1
                    
        return valuable_targets >= 2
        
    def _detect_pin(self, board, move):
        """ピン（釘付け）の検出"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 飛車・角・香車のみがピンを作れる
        if piece.name not in ["rook", "bishop", "lance"]:
            return False
            
        # 移動後の攻撃ライン上に敵の重要駒があるかチェック
        return self._check_pin_line(board, (to_row, to_col), piece)
        
    def _check_pin_line(self, board, pos, piece):
        """ピンラインの確認"""
        row, col = pos
        directions = []
        
        # 駒種別の攻撃方向
        if piece.name == "rook":
            directions = [(0,1), (0,-1), (1,0), (-1,0)]
        elif piece.name == "bishop":
            directions = [(1,1), (1,-1), (-1,1), (-1,-1)]
        elif piece.name == "lance":
            if piece.player == 1:
                directions = [(-1,0)]  # 先手香車は上方向
            else:
                directions = [(1,0)]   # 後手香車は下方向
                
        for dr, dc in directions:
            if self._check_direction_for_pin(board, row, col, dr, dc, piece.player):
                return True
                
        return False
        
    def _check_direction_for_pin(self, board, start_row, start_col, dr, dc, player):
        """特定方向のピンチェック"""
        pieces_found = []
        
        row, col = start_row + dr, start_col + dc
        while 0 <= row < 9 and 0 <= col < 9:
            piece = board.grid[row][col]
            if piece:
                pieces_found.append(piece)
                if len(pieces_found) >= 2:
                    break
            row += dr
            col += dc
            
        # ピン成立条件：敵駒→敵の重要駒の順
        if len(pieces_found) >= 2:
            first_piece, second_piece = pieces_found[0], pieces_found[1]
            if (first_piece.player != player and 
                second_piece.player != player and
                second_piece.name in ["king", "rook", "bishop"]):
                return True
                
        return False
        
    def _detect_skewer(self, board, move):
        """スキュワー（串刺し）の検出"""
        # ピンと似ているが、重要駒→価値の低い駒の順
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        if piece.name not in ["rook", "bishop", "lance"]:
            return False
            
        return self._check_skewer_line(board, (to_row, to_col), piece)
        
    def _check_skewer_line(self, board, pos, piece):
        """スキュワーラインの確認"""
        row, col = pos
        directions = []
        
        if piece.name == "rook":
            directions = [(0,1), (0,-1), (1,0), (-1,0)]
        elif piece.name == "bishop":
            directions = [(1,1), (1,-1), (-1,1), (-1,-1)]
        elif piece.name == "lance":
            if piece.player == 1:
                directions = [(-1,0)]
            else:
                directions = [(1,0)]
                
        for dr, dc in directions:
            pieces_found = []
            r, c = row + dr, col + dc
            
            while 0 <= r < 9 and 0 <= c < 9:
                p = board.grid[r][c]
                if p and p.player != piece.player:
                    pieces_found.append(p)
                    if len(pieces_found) >= 2:
                        break
                elif p:  # 味方駒で遮られる
                    break
                r += dr
                c += dc
                
            # スキュワー成立：重要駒→価値の低い駒
            if len(pieces_found) >= 2:
                first, second = pieces_found[0], pieces_found[1]
                if (first.name in ["king", "rook", "bishop"] and
                    self.evaluator.piece_values[first.name] > self.evaluator.piece_values[second.name]):
                    return True
                    
        return False
        
    def _detect_discovered_attack(self, board, move):
        """開き攻撃の検出"""
        if move['type'] != 'move':
            return False
            
        from_row, from_col = move['from']
        
        # 移動元から味方の大駒（飛車・角・香）への直線上に敵駒があるかチェック
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if (piece and piece.player == move['piece'].player and 
                    piece.name in ["rook", "bishop", "lance"]):
                    
                    if self._is_on_attack_line(from_row, from_col, row, col, piece):
                        # 開き攻撃の可能性をチェック
                        if self._check_discovered_line(board, (row, col), (from_row, from_col), piece):
                            return True
                            
        return False
        
    def _is_on_attack_line(self, from_row, from_col, piece_row, piece_col, piece):
        """駒が攻撃ライン上にあるかチェック"""
        dr = from_row - piece_row
        dc = from_col - piece_col
        
        if dr == 0 and dc == 0:
            return False
            
        # 駒種別の攻撃方向チェック
        if piece.name == "rook":
            return dr == 0 or dc == 0
        elif piece.name == "bishop":
            return abs(dr) == abs(dc)
        elif piece.name == "lance":
            if piece.player == 1:
                return dc == 0 and dr > 0
            else:
                return dc == 0 and dr < 0
                
        return False
        
    def _check_discovered_line(self, board, piece_pos, blocking_pos, piece):
        """開き攻撃ラインの確認"""
        # 実装簡略化：基本的な開き攻撃のみ検出
        return True  # 詳細実装は省略
        
    def _detect_double_attack(self, board, move):
        """両王手・両攻撃の検出"""
        if move['type'] != 'move':
            return False
            
        # 移動する駒と開き攻撃で同時に攻撃
        return (self._gives_check_directly(board, move) and 
                self._detect_discovered_attack(board, move))
        
    def _gives_check_directly(self, board, move):
        """直接王手をかけるかチェック"""
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 相手の王の位置を探す
        enemy_king_pos = None
        for row in range(9):
            for col in range(9):
                p = board.grid[row][col]
                if p and p.name == "king" and p.player != piece.player:
                    enemy_king_pos = (row, col)
                    break
                    
        if not enemy_king_pos:
            return False
            
        # 移動後に王を攻撃できるかチェック
        try:
            attack_positions = piece.get_possible_moves(board, (to_row, to_col))
            return enemy_king_pos in attack_positions
        except:
            return False
            
    def _detect_sacrifice_pattern(self, board, move):
        """捨て駒戦術の検出"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 移動先が敵の攻撃範囲にある場合
        if self._is_square_attacked(board, (to_row, to_col), 3 - piece.player):
            # 捨て駒による利益があるかチェック
            return self._evaluate_sacrifice_benefit(board, move)
            
        return False
        
    def _is_square_attacked(self, board, pos, by_player):
        """指定位置が指定プレイヤーに攻撃されているかチェック"""
        row, col = pos
        
        for r in range(9):
            for c in range(9):
                piece = board.grid[r][c]
                if piece and piece.player == by_player:
                    try:
                        attacks = piece.get_possible_moves(board, (r, c))
                        if (row, col) in attacks:
                            return True
                    except:
                        continue
                        
        return False
        
    def _evaluate_sacrifice_benefit(self, board, move):
        """捨て駒による利益を評価"""
        # 簡易実装：王手や重要駒への攻撃があれば利益ありと判定
        return (self._gives_check_directly(board, move) or 
                self._detect_fork(board, move))
        
    def _detect_promotion_threat(self, board, move):
        """成り込み脅威の検出"""
        if move['type'] != 'move':
            return False
            
        to_row, to_col = move['to']
        piece = move['piece']
        
        # 成れる駒かチェック
        if piece.name in ["king", "gold"] or piece.is_promoted:
            return False
            
        # 敵陣に入るかチェック
        if ((piece.player == 1 and to_row <= 2) or 
            (piece.player == 2 and to_row >= 6)):
            
            # 成ることで大幅に価値が上がる駒
            if piece.name in ["pawn", "lance", "knight", "silver", "bishop", "rook"]:
                return True
                
        return False


class EndgameEngine:
    """終盤特化エンジン"""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.mate_search_depth = 7  # 詰み探索の深度
        
    def search_mate(self, board, max_depth=None):
        """詰み探索"""
        if max_depth is None:
            max_depth = self.mate_search_depth
            
        return self._mate_search_recursive(board, max_depth, True)
        
    def _mate_search_recursive(self, board, depth, is_attacking):
        """再帰的詰み探索"""
        if depth == 0:
            return None
            
        if is_attacking:
            # 攻撃側：王手をかける手を探す
            possible_moves = self._get_checking_moves(board)
            
            for move in possible_moves:
                # 手を実行
                original_state = self._save_state(board)
                self._execute_move_simple(board, move)
                
                try:
                    # 相手の応手を確認
                    board.player_turn = 3 - board.player_turn
                    defense_moves = self._get_all_legal_moves(board)
                    
                    if not defense_moves:
                        # 詰み発見
                        return [move]
                        
                    # 全ての応手に対して詰みが続くかチェック
                    mate_continues = True
                    for defense_move in defense_moves:
                        defense_state = self._save_state(board)
                        self._execute_move_simple(board, defense_move)
                        
                        try:
                            board.player_turn = 3 - board.player_turn
                            continuation = self._mate_search_recursive(board, depth - 1, True)
                            if continuation is None:
                                mate_continues = False
                                self._restore_state(board, defense_state)
                                break
                        finally:
                            self._restore_state(board, defense_state)
                            
                    if mate_continues:
                        # 詰み手順発見
                        return [move]
                        
                finally:
                    self._restore_state(board, original_state)
                    
        return None
        
    def _get_checking_moves(self, board):
        """王手をかける手のみを取得"""
        checking_moves = []
        
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == board.player_turn:
                    try:
                        moves = piece.get_possible_moves(board, (row, col))
                        for move_row, move_col in moves:
                            move = {
                                'type': 'move',
                                'from': (row, col),
                                'to': (move_row, move_col),
                                'piece': piece
                            }
                            if self._gives_check(board, move):
                                checking_moves.append(move)
                    except:
                        continue
                        
        # 持ち駒による王手
        for i, piece in enumerate(board.captured_pieces[board.player_turn]):
            try:
                drop_positions = board.get_valid_drop_positions(piece)
                for drop_row, drop_col in drop_positions:
                    move = {
                        'type': 'drop',
                        'piece_index': i,
                        'to': (drop_row, drop_col),
                        'piece': piece
                    }
                    if self._gives_check_after_drop(board, move):
                        checking_moves.append(move)
            except:
                continue
                
        return checking_moves
        
    def _gives_check(self, board, move):
        """手が王手をかけるかチェック"""
        to_row, to_col = move['to']
        piece = move['piece']
        
        enemy_king_pos = self._find_enemy_king(board, piece.player)
        if not enemy_king_pos:
            return False
            
        try:
            attack_positions = piece.get_possible_moves(board, (to_row, to_col))
            return enemy_king_pos in attack_positions
        except:
            return False
            
    def _gives_check_after_drop(self, board, move):
        """持ち駒配置後に王手をかけるかチェック"""
        to_row, to_col = move['to']
        piece = move['piece']
        
        enemy_king_pos = self._find_enemy_king(board, piece.player)
        if not enemy_king_pos:
            return False
            
        try:
            attack_positions = piece.get_possible_moves(board, (to_row, to_col))
            return enemy_king_pos in attack_positions
        except:
            return False
            
    def _find_enemy_king(self, board, player):
        """敵の王の位置を探す"""
        enemy_player = 3 - player
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == "king" and piece.player == enemy_player:
                    return (row, col)
        return None
        
    def _get_all_legal_moves(self, board):
        """全ての合法手を取得（簡易版）"""
        moves = []
        
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == board.player_turn:
                    try:
                        piece_moves = piece.get_possible_moves(board, (row, col))
                        for move_row, move_col in piece_moves:
                            moves.append({
                                'type': 'move',
                                'from': (row, col),
                                'to': (move_row, move_col),
                                'piece': piece
                            })
                    except:
                        continue
                        
        for i, piece in enumerate(board.captured_pieces[board.player_turn]):
            try:
                drop_positions = board.get_valid_drop_positions(piece)
                for drop_row, drop_col in drop_positions:
                    moves.append({
                        'type': 'drop',
                        'piece_index': i,
                        'to': (drop_row, drop_col),
                        'piece': piece
                    })
            except:
                continue
                
        return moves
        
    def _save_state(self, board):
        """簡易状態保存"""
        grid_copy = []
        for row in board.grid:
            grid_copy.append(row[:])
            
        return {
            'grid': grid_copy,
            'player_turn': board.player_turn,
            'captured_pieces': {
                1: board.captured_pieces[1][:],
                2: board.captured_pieces[2][:]
            }
        }
        
    def _restore_state(self, board, state):
        """簡易状態復元"""
        board.grid = state['grid']
        board.player_turn = state['player_turn']
        board.captured_pieces = state['captured_pieces']
        
    def _execute_move_simple(self, board, move):
        """簡易手実行"""
        if move['type'] == 'move':
            from_row, from_col = move['from']
            to_row, to_col = move['to']
            
            piece = board.grid[from_row][from_col]
            captured = board.grid[to_row][to_col]
            
            board.grid[from_row][from_col] = None
            board.grid[to_row][to_col] = piece
            
            if captured:
                captured.is_promoted = False
                board.captured_pieces[board.player_turn].append(captured)
                
        elif move['type'] == 'drop':
            piece_index = move['piece_index']
            to_row, to_col = move['to']
            
            if piece_index < len(board.captured_pieces[board.player_turn]):
                piece = board.captured_pieces[board.player_turn][piece_index]
                board.grid[to_row][to_col] = piece
                
    def evaluate_endgame_position(self, board, player):
        """終盤局面の特別評価"""
        score = 0
        
        if self._is_near_mate(board, player):
            score += 1000
        elif self._is_near_mate(board, 3 - player):
            score -= 1000
            
        score += self._evaluate_king_safety_endgame(board, player)
        score += self._evaluate_captured_pieces_endgame(board, player)
        
        return score
        
    def _is_near_mate(self, board, player):
        """詰みに近い状況かチェック"""
        enemy_king_pos = self._find_enemy_king(board, player)
        if not enemy_king_pos:
            return False
            
        king_row, king_col = enemy_king_pos
        escape_squares = 0
        
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = king_row + dr, king_col + dc
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    piece = board.grid[new_row][new_col]
                    if piece is None or piece.player == player:
                        escape_squares += 1
                        
        return escape_squares <= 2
        
    def _evaluate_king_safety_endgame(self, board, player):
        """終盤の王の安全度評価"""
        king_pos = self._find_king_position(board, player)
        if not king_pos:
            return -10000
            
        king_row, king_col = king_pos
        safety_score = 0
        
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                new_row, new_col = king_row + dr, king_col + dc
                if 0 <= new_row < 9 and 0 <= new_col < 9:
                    piece = board.grid[new_row][new_col]
                    if piece and piece.player == player:
                        safety_score += 20
                        
        return safety_score
        
    def _evaluate_captured_pieces_endgame(self, board, player):
        """終盤の持ち駒評価"""
        score = 0
        
        for piece in board.captured_pieces[player]:
            base_value = self.evaluator.piece_values[piece.name]
            score += base_value * 1.2
            
        for piece in board.captured_pieces[3 - player]:
            base_value = self.evaluator.piece_values[piece.name]
            score -= base_value * 1.2
            
        return score
        
    def _find_king_position(self, board, player):
        """王の位置を探す"""
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == "king" and piece.player == player:
                    return (row, col)
        return None


class OpeningBook:
    """序盤定跡を管理するクラス"""
    
    def __init__(self):
        self.setup_opening_patterns()
        self.setup_piece_development_targets()
        
    def setup_opening_patterns(self):
        """基本定跡パターンを設定"""
        # 居飛車系定跡
        self.居飛車_基本 = [
            {"move": "7六歩", "from": (2, 6), "to": (3, 6), "priority": 100},
            {"move": "2六歩", "from": (2, 2), "to": (3, 2), "priority": 90},
            {"move": "2五歩", "from": (3, 2), "to": (4, 2), "priority": 85},
            {"move": "6八銀", "from": (0, 5), "to": (1, 5), "priority": 80},
            {"move": "7七銀", "from": (1, 5), "to": (2, 5), "priority": 75},
            {"move": "4八金", "from": (0, 3), "to": (1, 3), "priority": 70},
        ]
        
        # 振り飛車系定跡
        self.振り飛車_基本 = [
            {"move": "7六歩", "from": (2, 6), "to": (3, 6), "priority": 100},
            {"move": "6六歩", "from": (2, 5), "to": (3, 5), "priority": 95},
            {"move": "飛車6八", "from": (1, 1), "to": (1, 5), "priority": 90},
            {"move": "6七銀", "from": (0, 5), "to": (2, 5), "priority": 85},
            {"move": "5八金左", "from": (0, 3), "to": (1, 4), "priority": 80},
        ]
        
        # 角換わり系定跡
        self.角換わり_基本 = [
            {"move": "2六歩", "from": (2, 2), "to": (3, 2), "priority": 100},
            {"move": "2五歩", "from": (3, 2), "to": (4, 2), "priority": 95},
            {"move": "7六歩", "from": (2, 6), "to": (3, 6), "priority": 90},
            {"move": "8八角", "from": (1, 7), "to": (0, 7), "priority": 85},
        ]
        
        self.opening_patterns = {
            "居飛車": self.居飛車_基本,
            "振り飛車": self.振り飛車_基本,
            "角換わり": self.角換わり_基本
        }
        
    def setup_piece_development_targets(self):
        """駒組みの理想的配置を設定"""
        # 先手の理想的駒組み
        self.ideal_positions_sente = {
            "silver": [(2, 5), (2, 3)],  # 銀の理想位置
            "gold": [(1, 3), (1, 5)],    # 金の理想位置
            "knight": [(2, 1), (2, 7)],  # 桂の理想位置
            "bishop": [(2, 6), (3, 5)],  # 角の理想位置
            "rook": [(1, 1), (1, 5)],    # 飛車の理想位置
        }
        
        # 後手の理想的駒組み（先手を反転）
        self.ideal_positions_gote = {}
        for piece_type, positions in self.ideal_positions_sente.items():
            self.ideal_positions_gote[piece_type] = [(8-row, col) for row, col in positions]
            
    def get_opening_move(self, board, move_count):
        """現在の局面に適した定跡手を返す"""
        if move_count > 12:  # 序盤12手まで
            return None
            
        # 戦型を判定
        opening_type = self._analyze_opening_type(board)
        
        if opening_type in self.opening_patterns:
            pattern = self.opening_patterns[opening_type]
            
            # パターンから実行可能な手を探す
            for opening_move in pattern:
                if self._is_opening_move_valid(board, opening_move):
                    return self._convert_to_move_format(board, opening_move)
                    
        return None
        
    def _analyze_opening_type(self, board):
        """現在の局面から適切な戦型を判断"""
        # 飛車の位置をチェック
        rook_pos = self._find_piece_position(board, "rook", board.player_turn)
        
        if rook_pos:
            rook_row, rook_col = rook_pos
            
            # 振り飛車判定（飛車が中央寄りにある）
            if board.player_turn == 1 and rook_col >= 4:  # 先手
                return "振り飛車"
            elif board.player_turn == 2 and rook_col <= 4:  # 後手
                return "振り飛車"
                
        # 角の交換があったかチェック
        if self._is_bishop_exchanged(board):
            return "角換わり"
            
        # デフォルトは居飛車
        return "居飛車"
        
    def _find_piece_position(self, board, piece_name, player):
        """指定した駒の位置を探す"""
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == piece_name and piece.player == player:
                    return (row, col)
        return None
        
    def _is_bishop_exchanged(self, board):
        """角の交換が行われたかチェック"""
        # 簡易実装：両者の持ち駒に角があるかチェック
        player1_has_bishop = any(piece.name == "bishop" for piece in board.captured_pieces[1])
        player2_has_bishop = any(piece.name == "bishop" for piece in board.captured_pieces[2])
        
        return player1_has_bishop or player2_has_bishop
        
    def _is_opening_move_valid(self, board, opening_move):
        """定跡手が実行可能かチェック"""
        from_pos = opening_move["from"]
        to_pos = opening_move["to"]
        
        # 移動元に駒があるかチェック
        piece = board.grid[from_pos[0]][from_pos[1]]
        if not piece or piece.player != board.player_turn:
            return False
            
        # 移動先が空いているかチェック
        target = board.grid[to_pos[0]][to_pos[1]]
        if target and target.player == board.player_turn:
            return False
            
        # 合法手かチェック
        try:
            possible_moves = piece.get_possible_moves(board, from_pos)
            return to_pos in possible_moves
        except:
            return False
            
    def _convert_to_move_format(self, board, opening_move):
        """定跡手を標準の手形式に変換"""
        return {
            'type': 'move',
            'from': opening_move["from"],
            'to': opening_move["to"],
            'piece': board.grid[opening_move["from"][0]][opening_move["from"][1]],
            'priority': opening_move["priority"]
        }
        
    def evaluate_piece_development(self, board, player):
        """駒組みの進行度を評価"""
        score = 0
        
        # 理想位置を取得
        if player == 1:
            ideal_positions = self.ideal_positions_sente
        else:
            ideal_positions = self.ideal_positions_gote
            
        # 各駒種の配置を評価
        for piece_type, ideal_pos_list in ideal_positions.items():
            current_positions = self._find_all_piece_positions(board, piece_type, player)
            
            for current_pos in current_positions:
                # 最も近い理想位置との距離を計算
                min_distance = min(
                    abs(current_pos[0] - ideal[0]) + abs(current_pos[1] - ideal[1])
                    for ideal in ideal_pos_list
                )
                
                # 距離が近いほど高評価
                score += max(0, 10 - min_distance * 2)
                
        return score
        
    def _find_all_piece_positions(self, board, piece_name, player):
        """指定した駒の全ての位置を探す"""
        positions = []
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == piece_name and piece.player == player:
                    positions.append((row, col))
        return positions


class MoveSearcher:
    """ミニマックス探索を担当するクラス（アルファベータ枝刈り対応）"""
    
    def __init__(self, evaluator, max_depth=4):  # 深度を4に増加
        self.evaluator = evaluator
        self.max_depth = max_depth
        self.tactics_engine = TacticsEngine(evaluator)
        self.endgame_engine = EndgameEngine(evaluator)
        
    def search_best_move(self, board, possible_moves, time_limit=10.0):  # 時間制限を10秒に変更
        """制限時間内で最適手を探索（アルファベータ枝刈り）"""
        start_time = time.time()
        
        # 時間に応じて探索深度を調整
        if time_limit <= 1.0:
            max_depth = 2  # 時間が少ない場合は浅く
        elif time_limit <= 3.0:
            max_depth = 3
        elif time_limit <= 7.0:
            max_depth = 4
        else:
            max_depth = 5  # 時間に余裕がある場合は深く
            
        print(f"探索深度: {max_depth}, 制限時間: {time_limit:.1f}秒")
        
        # 終盤では詰み探索を優先
        if self._is_endgame(board):
            mate_move = self.endgame_engine.search_mate(board, 5)
            if mate_move:
                return [mate_move]
        
        # 手の順序付け（良い手を先に評価）
        ordered_moves = self._order_moves(board, possible_moves)
        
        best_moves = []
        best_score = float('-inf')
        
        for i, move in enumerate(ordered_moves):
            # 時間制限チェック（90%の時間を使ったら終了）
            elapsed = time.time() - start_time
            if elapsed > time_limit * 0.9:
                print(f"時間制限により探索終了 ({i+1}/{len(ordered_moves)}手評価済み)")
                break
                
            # 残り時間に応じて探索深度を調整
            remaining_time = time_limit - elapsed
            if remaining_time < time_limit * 0.3:  # 残り30%以下なら深度を下げる
                current_depth = max(1, max_depth - 1)
            else:
                current_depth = max_depth
                
            # アルファベータ探索で手を評価
            score = self._alpha_beta_search(board, move, current_depth - 1, 
                                          float('-inf'), float('inf'), False, 
                                          start_time, time_limit)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        return best_moves if best_moves else [ordered_moves[0]]
        
    def _alpha_beta_search(self, board, move, depth, alpha, beta, is_maximizing, start_time, time_limit):
        """アルファベータ枝刈り探索"""
        # 時間制限チェック（95%の時間を使ったら即座に終了）
        elapsed = time.time() - start_time
        if elapsed > time_limit * 0.95:
            return self._quick_evaluate(board, move)
            
        # 手を実行
        original_state = self._save_simple_state(board)
        self._execute_move_simple(board, move)
        
        try:
            # 終端条件
            if depth == 0 or self._is_terminal_position(board):
                score = self.evaluator.evaluate_position(board, original_state['original_player'])
                
                # 戦術ボーナスを追加
                tactical_bonus = self.tactics_engine.evaluate_tactics(board, move)
                score += tactical_bonus
                
                # 終盤では特別評価を追加
                if self._is_endgame(board):
                    endgame_bonus = self.endgame_engine.evaluate_endgame_position(board, original_state['original_player'])
                    score += endgame_bonus * 0.3
                
                return score
                
            # 手番を交代
            board.player_turn = 3 - board.player_turn
            
            # 次の手の候補を取得
            next_moves = self._get_possible_moves_simple(board)
            
            if not next_moves:
                # 合法手がない場合（詰み）
                if is_maximizing:
                    return float('-inf')
                else:
                    return float('inf')
            
            # 手の順序付け（時間に応じて探索数を制限）
            remaining_time = time_limit - elapsed
            if remaining_time < time_limit * 0.5:  # 残り時間が50%以下
                max_moves = 6  # 上位6手のみ
            elif remaining_time < time_limit * 0.7:  # 残り時間が70%以下
                max_moves = 10  # 上位10手のみ
            else:
                max_moves = 15  # 上位15手まで
                
            ordered_next_moves = self._order_moves(board, next_moves[:max_moves])
            
            if is_maximizing:
                max_eval = float('-inf')
                for next_move in ordered_next_moves:
                    eval_score = self._alpha_beta_search(board, next_move, depth - 1, 
                                                       alpha, beta, False, start_time, time_limit)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    
                    # ベータカット
                    if beta <= alpha:
                        break
                        
                return max_eval
            else:
                min_eval = float('inf')
                for next_move in ordered_next_moves:
                    eval_score = self._alpha_beta_search(board, next_move, depth - 1, 
                                                       alpha, beta, True, start_time, time_limit)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    
                    # アルファカット
                    if beta <= alpha:
                        break
                        
                return min_eval
                
        finally:
            # 盤面を復元
            self._restore_simple_state(board, original_state)
            
    def _order_moves(self, board, moves):
        """手の順序付け（良い手を先に評価）"""
        def move_priority(move):
            priority = 0
            
            # 駒を取る手を優先
            if move['type'] == 'move':
                to_row, to_col = move['to']
                target = board.grid[to_row][to_col]
                if target and target.player != board.player_turn:
                    priority += self.evaluator.piece_values[target.name]
                    
            # 王手をかける手を優先
            if self._gives_check_quick(board, move):
                priority += 500
                
            # 中央への手を優先
            to_pos = move['to']
            center_distance = abs(to_pos[0] - 4) + abs(to_pos[1] - 4)
            priority += max(0, 8 - center_distance) * 10
            
            return priority
            
        return sorted(moves, key=move_priority, reverse=True)
        
    def _gives_check_quick(self, board, move):
        """簡易王手判定"""
        if move['type'] == 'move':
            to_row, to_col = move['to']
            piece = move['piece']
            
            # 相手の王の位置を探す
            enemy_king_pos = None
            for row in range(9):
                for col in range(9):
                    p = board.grid[row][col]
                    if p and p.name == "king" and p.player != piece.player:
                        enemy_king_pos = (row, col)
                        break
                        
            if enemy_king_pos:
                # 距離による簡易判定
                king_row, king_col = enemy_king_pos
                distance = abs(to_row - king_row) + abs(to_col - king_col)
                
                if piece.name in ["rook", "bishop"] and distance <= 4:
                    return True
                elif piece.name in ["gold", "silver"] and distance <= 2:
                    return True
                    
        return False
        
    def _is_endgame(self, board):
        """終盤かどうかの判定"""
        total_pieces = 0
        for row in range(9):
            for col in range(9):
                if board.grid[row][col]:
                    total_pieces += 1
                    
        return total_pieces <= 16  # 駒が16個以下で終盤
        
    def _minimax_search(self, board, move, depth, is_maximizing, start_time, time_limit):
        """ミニマックス探索（再帰）"""
        # 時間制限チェック
        if time.time() - start_time > time_limit:
            return self._quick_evaluate(board, move)
            
        # 手を実行
        original_state = self._save_simple_state(board)
        self._execute_move_simple(board, move)
        
        try:
            # 終端条件
            if depth == 0 or self._is_terminal_position(board):
                return self.evaluator.evaluate_position(board, original_state['original_player'])
                
            # 手番を交代
            board.player_turn = 3 - board.player_turn
            
            # 次の手の候補を取得
            next_moves = self._get_possible_moves_simple(board)
            
            if not next_moves:
                # 合法手がない場合（詰み）
                if is_maximizing:
                    return float('-inf')
                else:
                    return float('inf')
            
            if is_maximizing:
                max_eval = float('-inf')
                for next_move in next_moves[:8]:  # 計算量制限のため上位8手のみ
                    eval_score = self._minimax_search(board, next_move, depth - 1, False, start_time, time_limit)
                    max_eval = max(max_eval, eval_score)
                return max_eval
            else:
                min_eval = float('inf')
                for next_move in next_moves[:8]:  # 計算量制限のため上位8手のみ
                    eval_score = self._minimax_search(board, next_move, depth - 1, True, start_time, time_limit)
                    min_eval = min(min_eval, eval_score)
                return min_eval
                
        finally:
            # 盤面を復元
            self._restore_simple_state(board, original_state)
            
    def _quick_evaluate(self, board, move):
        """時間制限時の簡易評価"""
        return self._evaluate_move_basic(board, move)
        
    def _evaluate_move_basic(self, board, move):
        """基本的な手の評価"""
        score = 0
        
        # 駒を取る価値
        if move['type'] == 'move':
            to_row, to_col = move['to']
            target_piece = board.grid[to_row][to_col]
            if target_piece and target_piece.player != board.player_turn:
                score += self.evaluator.piece_values[target_piece.name]
                
        return score
        
    def _is_terminal_position(self, board):
        """終端局面かどうか"""
        return board.checkmate or board.game_over
        
    def _save_simple_state(self, board):
        """簡易状態保存"""
        grid_copy = []
        for row in board.grid:
            grid_copy.append(row[:])  # 浅いコピー
            
        return {
            'grid': grid_copy,
            'player_turn': board.player_turn,
            'original_player': board.player_turn
        }
        
    def _restore_simple_state(self, board, state):
        """簡易状態復元"""
        board.grid = state['grid']
        board.player_turn = state['player_turn']
        
    def _execute_move_simple(self, board, move):
        """簡易手実行（探索用）"""
        if move['type'] == 'move':
            from_row, from_col = move['from']
            to_row, to_col = move['to']
            
            piece = board.grid[from_row][from_col]
            board.grid[from_row][from_col] = None
            board.grid[to_row][to_col] = piece
            
        elif move['type'] == 'drop':
            piece_index = move['piece_index']
            to_row, to_col = move['to']
            
            if piece_index < len(board.captured_pieces[board.player_turn]):
                piece = board.captured_pieces[board.player_turn][piece_index]
                board.grid[to_row][to_col] = piece
                
    def _get_possible_moves_simple(self, board):
        """簡易合法手生成"""
        possible_moves = []
        
        # 盤上の駒の移動
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == board.player_turn:
                    try:
                        moves = piece.get_possible_moves(board, (row, col))
                        for move_row, move_col in moves:
                            possible_moves.append({
                                'type': 'move',
                                'from': (row, col),
                                'to': (move_row, move_col),
                                'piece': piece
                            })
                    except:
                        continue
        
        # 持ち駒の配置（簡略化）
        for i, piece in enumerate(board.captured_pieces[board.player_turn][:3]):  # 上位3つのみ
            try:
                drop_positions = board.get_valid_drop_positions(piece)
                for drop_row, drop_col in drop_positions[:5]:  # 上位5箇所のみ
                    possible_moves.append({
                        'type': 'drop',
                        'piece_index': i,
                        'to': (drop_row, drop_col),
                        'piece': piece
                    })
            except:
                continue
        
        return possible_moves


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
        
    def evaluate_position(self, board, player):
        """総合的な局面評価（序盤強化版）"""
        # ゲーム段階を判定
        game_phase = self._determine_game_phase(board)
        
        # 基本評価
        score = self._evaluate_material_and_position(board, player)
        
        # 段階別評価を追加
        if game_phase == "opening":
            score += self._evaluate_opening_phase(board, player)
        elif game_phase == "middlegame":
            score += self._evaluate_middlegame_phase(board, player)
        else:  # endgame
            score += self._evaluate_endgame_phase(board, player)
            
        return score
        
    def _determine_game_phase(self, board):
        """ゲームの段階を判定"""
        total_pieces = 0
        for row in range(9):
            for col in range(9):
                if board.grid[row][col]:
                    total_pieces += 1
                    
        if total_pieces > 30:
            return "opening"
        elif total_pieces > 20:
            return "middlegame"
        else:
            return "endgame"
            
    def _evaluate_material_and_position(self, board, player):
        """駒得と位置価値の基本評価"""
        score = 0
        
        # 盤上の駒を評価
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece:
                    piece_value = self.piece_values[piece.name]
                    
                    # 成り駒のボーナス
                    if piece.is_promoted and piece.name in self.promoted_bonus:
                        piece_value += self.promoted_bonus[piece.name]
                    
                    # 位置価値を追加
                    position_value = self.get_piece_square_value(piece, row, col, piece.player)
                    piece_value += position_value
                    
                    if piece.player == player:
                        score += piece_value
                    else:
                        score -= piece_value
        
        # 持ち駒を評価
        for piece in board.captured_pieces[player]:
            score += self.piece_values[piece.name] * 0.8
            
        for piece in board.captured_pieces[3 - player]:
            score -= self.piece_values[piece.name] * 0.8
            
        return score
        
    def _evaluate_opening_phase(self, board, player):
        """序盤特化評価"""
        score = 0
        
        # 駒組み評価（OpeningBookクラスを使用）
        # 注意: この時点ではOpeningBookのインスタンスがないので、簡易実装
        score += self._evaluate_piece_development_simple(board, player)
        
        # 中央制圧ボーナス
        score += self._evaluate_center_control(board, player)
        
        # 王の安全確保
        score += self._evaluate_king_safety_opening(board, player)
        
        return score * 0.3  # 序盤評価の重み
        
    def _evaluate_middlegame_phase(self, board, player):
        """中盤特化評価"""
        score = 0
        
        # 攻撃力評価
        score += self._evaluate_attack_potential(board, player)
        
        # 駒の連携評価
        score += self._evaluate_piece_coordination(board, player)
        
        return score * 0.2  # 中盤評価の重み
        
    def _evaluate_endgame_phase(self, board, player):
        """終盤特化評価"""
        score = 0
        
        # 王の活用度（終盤では王も攻撃に参加）
        score += self._evaluate_king_activity(board, player)
        
        # 持ち駒の活用度
        score += self._evaluate_captured_pieces_activity(board, player)
        
        return score * 0.2  # 終盤評価の重み
        
    def _evaluate_piece_development_simple(self, board, player):
        """簡易駒組み評価"""
        score = 0
        
        # 銀が前進しているかチェック
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == "silver" and piece.player == player:
                    if player == 1 and row <= 6:  # 先手の銀が前進
                        score += 20
                    elif player == 2 and row >= 2:  # 後手の銀が前進
                        score += 20
                        
        # 金が王の近くにいるかチェック
        king_pos = self._find_king_position(board, player)
        if king_pos:
            king_row, king_col = king_pos
            for row in range(9):
                for col in range(9):
                    piece = board.grid[row][col]
                    if piece and piece.name == "gold" and piece.player == player:
                        distance = abs(row - king_row) + abs(col - king_col)
                        if distance <= 2:
                            score += 15
                            
        return score
        
    def _evaluate_center_control(self, board, player):
        """中央制圧評価"""
        score = 0
        center_squares = [(4, 4), (4, 5), (5, 4), (5, 5)]
        
        for row, col in center_squares:
            piece = board.grid[row][col]
            if piece and piece.player == player:
                score += 25
            elif piece and piece.player != player:
                score -= 15
                
        return score
        
    def _evaluate_king_safety_opening(self, board, player):
        """序盤の王の安全度"""
        score = 0
        king_pos = self._find_king_position(board, player)
        
        if king_pos:
            king_row, king_col = king_pos
            
            # 王が初期位置近くにいるかチェック
            if player == 1 and king_row >= 7:  # 先手の王が下段にいる
                score += 30
            elif player == 2 and king_row <= 1:  # 後手の王が上段にいる
                score += 30
                
        return score
        
    def _evaluate_attack_potential(self, board, player):
        """攻撃力評価"""
        score = 0
        
        # 飛車・角の働きを評価
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == player:
                    if piece.name in ["rook", "bishop"]:
                        try:
                            moves = piece.get_possible_moves(board, (row, col))
                            score += len(moves) * 3  # 移動可能マス数で評価
                        except:
                            continue
                            
        return score
        
    def _evaluate_piece_coordination(self, board, player):
        """駒の連携評価"""
        score = 0
        
        # 隣接する味方駒の数をカウント
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.player == player:
                    adjacent_allies = 0
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            new_row, new_col = row + dr, col + dc
                            if 0 <= new_row < 9 and 0 <= new_col < 9:
                                adjacent = board.grid[new_row][new_col]
                                if adjacent and adjacent.player == player:
                                    adjacent_allies += 1
                    score += adjacent_allies * 5
                    
        return score
        
    def _evaluate_king_activity(self, board, player):
        """王の活用度（終盤用）"""
        score = 0
        king_pos = self._find_king_position(board, player)
        
        if king_pos:
            king_row, king_col = king_pos
            
            # 王が中央寄りにいるかチェック（終盤では有利）
            center_distance = abs(king_row - 4) + abs(king_col - 4)
            score += max(0, 8 - center_distance) * 10
            
        return score
        
    def _evaluate_captured_pieces_activity(self, board, player):
        """持ち駒の活用度"""
        score = 0
        
        # 持ち駒の種類による評価
        for piece in board.captured_pieces[player]:
            if piece.name in ["rook", "bishop"]:
                score += 50  # 大駒は終盤で威力を発揮
            elif piece.name == "gold":
                score += 30
            elif piece.name in ["silver", "knight"]:
                score += 20
            else:
                score += 10
                
        return score
        
    def _find_king_position(self, board, player):
        """王の位置を探す"""
        for row in range(9):
            for col in range(9):
                piece = board.grid[row][col]
                if piece and piece.name == "king" and piece.player == player:
                    return (row, col)
        return None


class ShogiAI:
    def __init__(self, board, game_mode="normal"):
        self.board = board
        self.game_mode = game_mode  # ゲームモードを保存
        self.evaluator = PositionEvaluator()
        self.searcher = MoveSearcher(self.evaluator)  # アルファベータ対応探索エンジン
        self.opening_book = OpeningBook()  # 序盤定跡エンジン
        self.tactics_engine = TacticsEngine(self.evaluator)  # 戦術認識エンジン
        self.endgame_engine = EndgameEngine(self.evaluator)  # 終盤特化エンジン
        self.move_count = 0  # 手数カウンター
        
    def make_move(self):
        """AIの手を決定して実行する"""
        start_time = time.time()
        max_time = 10.0  # 最大10秒
        
        # 全ての合法手を列挙
        possible_moves = self._get_all_possible_moves()
        
        if not possible_moves:
            return False  # 合法手がない（詰み）
            
        # 手数をカウント
        self.move_count += 1
        
        # 通常モードでのみ序盤定跡をチェック（強制実行）
        if self.game_mode == "normal" and self.move_count <= 12:
            opening_move = self.opening_book.get_opening_move(self.board, self.move_count)
            if opening_move:
                # 定跡手を強制実行（合法性は事前にチェック済み）
                print(f"定跡手を実行: {opening_move.get('move', '不明')} ({self.move_count}手目)")
                self._execute_move(opening_move)
                return True
        
        # 時間制限チェック
        elapsed_time = time.time() - start_time
        remaining_time = max_time - elapsed_time
        
        if remaining_time <= 0.5:  # 残り時間が0.5秒以下の場合は即座に手を選択
            print(f"時間切れ間近のため高速評価を使用")
            best_move = self._evaluate_moves_fast(possible_moves)
        else:
            # 定跡がない場合、またはendgameモードの場合は通常の評価
            print(f"残り時間: {remaining_time:.1f}秒で思考開始")
            best_move = self._evaluate_moves(possible_moves, remaining_time)
        
        # 選んだ手を実行
        self._execute_move(best_move)
        
        # 思考時間を表示
        total_time = time.time() - start_time
        print(f"思考時間: {total_time:.2f}秒")
        
        return True
        
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
        
    def _evaluate_moves(self, possible_moves, time_limit=10.0):
        """手を評価して最良の手を選択（ミニマックス探索版）"""
        # 王手をかけられている場合は従来の高速評価
        if self.board.in_check:
            return self._evaluate_moves_fast(possible_moves)
            
        # 通常時はミニマックス探索（時間制限付き）
        best_moves = self.searcher.search_best_move(self.board, possible_moves, time_limit)
        
        # 同じスコアの手からランダム選択（既存と同じ）
        return random.choice(best_moves)
        
    def _evaluate_moves_fast(self, possible_moves):
        """王手時の高速評価（従来の方法）"""
        best_moves = []
        best_score = float('-inf')
        
        for move in possible_moves:
            # 従来の評価方法を使用
            score = self._evaluate_move_advanced(move)
            
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
                
        return random.choice(best_moves)
        
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
                score += piece_value * 1.5  # 駒を取る価値を1.5倍に増加
                
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
            score -= 500  # 10000から500に減少
            
        # 自分の重要な駒を見捨てる手を減点
        if self._abandons_important_piece(move):
            score -= 300  # 8000から300に減少
            
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
            if moving_value > target_value + 500:  # 200点から500点に変更（より大きな差でのみ悪い交換と判定）
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
