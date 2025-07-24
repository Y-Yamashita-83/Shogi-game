import pygame
from constants import BOARD_COLOR, GRID_COLOR, VALID_MOVE_COLOR, BOARD_SIZE, CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, SELECTED_COLOR
from pieces import Piece
from ui.effect_display import EffectDisplay

class Board:
    def __init__(self, screen, font, piece_images, sounds, event_manager=None, bgm_manager=None):
        self.screen = screen
        self.font = font
        self.piece_images = piece_images
        self.sounds = sounds if sounds else {}
        self.move_sound = self.sounds.get('move')
        self.oute_sound = self.sounds.get('oute')
        self.toryo_sound = self.sounds.get('toryo')
        self.menko_sound = self.sounds.get('menko')  # メンコ音声を追加
        self.toppu_sound = self.sounds.get('toppu')  # 突風音声を追加
        self.hengenotsue_sound = self.sounds.get('hengenotsue')  # 変化の杖音声を追加
        self.tensousouchi_sound = self.sounds.get('tensousouchi')  # 転送装置音声を追加
        self.komaochi_sound = self.sounds.get('komaochi')  # 駒落ち音声を追加
        self.oute_sound_played = False  # 王手音声再生フラグ
        self.toryo_sound_played = False  # 投了音声再生フラグ
        self.menko_sound_played = False  # メンコ音声再生フラグ
        self.toppu_sound_played = False  # 突風音声再生フラグ
        self.hengenotsue_sound_played = False  # 変化の杖音声再生フラグ
        self.tensousouchi_sound_played = False  # 転送装置音声再生フラグ
        self.komaochi_sound_played = False  # 駒落ち音声再生フラグ
        self.current_special_move = None  # 現在実行中の特殊技名
        self.bgm_manager = bgm_manager  # BGM管理の参照を追加
        self.grid = [[None for _ in range(9)] for _ in range(9)]
        self.selected_piece = None
        self.selected_pos = None
        self.player_turn = 1  # 1: 先手, 2: 後手
        self.current_player = 1  # 現在のプレイヤー（特殊技用）
        self.captured_pieces = {1: [], 2: []}  # 持ち駒
        self.valid_moves = []  # 選択した駒の移動可能なマス
        self.in_check = False  # 王手状態かどうか
        self.checkmate = False  # 詰み状態かどうか
        self.game_over = False  # ゲーム終了状態
        self.event_manager = event_manager
        self.effect_display = EffectDisplay(screen, font)
        self.winner = None     # 勝者（1: 先手, 2: 後手）
        self.promotion_pending = False  # 成り判定中かどうか
        self.pending_move = None  # 成り判定中の移動情報
        self.special_move_active = None  # 現在選択中の特殊技
        self.turn_count = 1  # 現在のターン数
        self.move_count = 0  # 手数カウンター（2手で1ターン）
        
        # 特殊技関連
        self.special_move_confirm = False  # 特殊技の確認中かどうか
        self.special_move_target = None    # 特殊技の対象の駒の位置
        self.special_effect_pending = False  # 特殊技エフェクト待機中
        
        # 特殊技確認用ボタン
        from ui.button import Button
        self.confirm_yes_button = Button(
            SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 20, 100, 40, "はい", self.confirm_special_move
        )
        self.confirm_no_button = Button(
            SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 20, 100, 40, "いいえ", self.cancel_confirm
        )
        
        # ゲーム終了シーケンス用
        self.game_end_timer = 0
        self.game_end_bgm_delay = 1500  # 1.5秒（ミリ秒）
        self.game_end_bgm_started = False
        
        # 背景画像の読み込み
        from utils import load_battle_background
        self.battle_background = load_battle_background()
        
        self.setup_board()

    def check_special_effects_complete(self):
        """特殊技エフェクトが完了したかチェック"""
        if self.special_effect_pending:
            if not self.effect_display.is_effects_active():
                # エフェクト完了、手番交代を許可
                self.special_effect_pending = False
                
                # 特殊技音声フラグをリセット
                if self.current_special_move == "メンコ":
                    self.menko_sound_played = False
                    self.current_special_move = None
                elif self.current_special_move == "突風":
                    self.toppu_sound_played = False
                    self.current_special_move = None
                elif self.current_special_move == "変化の杖":
                    self.hengenotsue_sound_played = False
                    self.current_special_move = None
                elif self.current_special_move == "転送装置":
                    self.tensousouchi_sound_played = False
                    self.current_special_move = None
                elif self.current_special_move == "駒落ち":
                    self.komaochi_sound_played = False
                    self.current_special_move = None
                
                self.end_turn()
                
    def draw_game_over_message(self):
        """ゲーム終了メッセージの表示と音声再生"""
        if self.game_over:
            # BGM停止（一度だけ）
            if self.bgm_manager and not self.toryo_sound_played:
                self.bgm_manager.stop_bgm()
                
            # 投了音声を再生（一度だけ）
            if not self.toryo_sound_played:
                self.play_toryo_sound()
                self.toryo_sound_played = True
                
            # 勝者メッセージの表示
            if self.winner:
                winner_name = "先手番" if self.winner == 1 else "後手番"
                if self.checkmate:
                    game_over_text = f"詰み！！{winner_name}の勝ち！！"
                else:
                    game_over_text = f"{winner_name}の勝ち！！"
            else:
                game_over_text = "ゲーム終了"
                
            text = self.font.render(game_over_text, True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            self.screen.blit(text, text_rect)
            
            return True  # 「最初に戻る」ボタンを表示するためのフラグ
        else:
            # ゲーム終了でない場合はフラグをリセット
            self.toryo_sound_played = False
            return False
    
    def draw_check_message(self):
        """王手メッセージの表示と音声再生"""
        if self.in_check and not self.game_over and not self.special_move_active:
            # 「王手！！」の文字を表示
            check_text = "王手！！"
            text = self.font.render(check_text, True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 30))
            self.screen.blit(text, text_rect)
            
            # 王手音声を再生（一度だけ）
            if not self.oute_sound_played:
                self.play_oute_sound()
                self.oute_sound_played = True
        else:
            # 王手状態でない場合はフラグをリセット
            self.oute_sound_played = False
    
    def play_komaochi_sound(self):
        """駒落ち音声を再生"""
        if self.komaochi_sound:
            try:
                self.komaochi_sound.play()
                print("駒落ち音声を再生しました")
            except pygame.error as e:
                print(f"駒落ち音声の再生に失敗しました: {e}")
        else:
            print("駒落ち音声が読み込まれていません")
    
    def play_tensousouchi_sound(self):
        """転送装置音声を再生"""
        if self.tensousouchi_sound:
            try:
                self.tensousouchi_sound.play()
                print("転送装置音声を再生しました")
            except pygame.error as e:
                print(f"転送装置音声の再生に失敗しました: {e}")
        else:
            print("転送装置音声が読み込まれていません")
    
    def play_hengenotsue_sound(self):
        """変化の杖音声を再生"""
        if self.hengenotsue_sound:
            try:
                self.hengenotsue_sound.play()
                print("変化の杖音声を再生しました")
            except pygame.error as e:
                print(f"変化の杖音声の再生に失敗しました: {e}")
        else:
            print("変化の杖音声が読み込まれていません")
    
    def play_toppu_sound(self):
        """突風音声を再生"""
        if self.toppu_sound:
            try:
                self.toppu_sound.play()
                print("突風音声を再生しました")
            except pygame.error as e:
                print(f"突風音声の再生に失敗しました: {e}")
        else:
            print("突風音声が読み込まれていません")
    
    def play_menko_sound(self):
        """メンコ音声を再生"""
        if self.menko_sound:
            try:
                self.menko_sound.play()
                print("メンコ音声を再生しました")
            except pygame.error as e:
                print(f"メンコ音声の再生に失敗しました: {e}")
        else:
            print("メンコ音声が読み込まれていません")
    
    def play_toryo_sound(self):
        """投了音声を再生"""
        if self.toryo_sound:
            try:
                self.toryo_sound.play()
                print("投了音声を再生しました")
            except pygame.error as e:
                print(f"投了音声の再生に失敗しました: {e}")
        else:
            print("投了音声が読み込まれていません")
    
    def play_oute_sound(self):
        """王手音声を再生"""
        if self.oute_sound:
            try:
                self.oute_sound.play()
                print("王手音声を再生しました")
            except pygame.error as e:
                print(f"王手音声の再生に失敗しました: {e}")
        else:
            print("王手音声が読み込まれていません")
    
    def _play_game_end_bgm(self):
        """勝負終了時のBGMを再生"""
        import os
        end_bgm_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "bgm", "tasogare-hanabi.mp3")
        if os.path.exists(end_bgm_path):
            try:
                pygame.mixer.music.load(end_bgm_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)  # ループ再生
                print("勝負終了BGMを再生しました")
            except pygame.error as e:
                print(f"勝負終了BGMの再生に失敗しました: {e}")
        else:
            print(f"勝負終了BGMファイルが見つかりません: {end_bgm_path}")
    
    def _stop_game_end_bgm(self):
        """勝負終了BGMを停止"""
        pygame.mixer.music.stop()
        print("勝負終了BGMを停止しました")
    
    def _start_game_end_sequence(self):
        """ゲーム終了シーケンスを開始（音声 → BGM）"""
        # 「まいりました」音声を再生
        if self.toryo_sound:
            self.toryo_sound.play()
            print("ゲーム終了音声を再生しました")
        
        # タイマーを開始
        self.game_end_timer = pygame.time.get_ticks()
        self.game_end_bgm_started = False
    
    def update_game_end_sequence(self):
        """ゲーム終了シーケンスの更新"""
        if self.game_over and not self.game_end_bgm_started:
            current_time = pygame.time.get_ticks()
            # 1.5秒経過後にBGMを開始
            if current_time - self.game_end_timer > self.game_end_bgm_delay:
                self._play_game_end_bgm()
                self.game_end_bgm_started = True
    
    def can_change_turn(self):
        """手番交代が可能かどうか"""
        return not self.special_effect_pending
    
    def is_computer_player(self, player):
        """指定したプレイヤーがコンピュータかどうかを判定"""
        # 先手（player=1）がコンピュータ
        return player == 1
    
    def setup_board(self):
        # 駒の初期配置
        # 歩兵
        for i in range(9):
            self.grid[2][i] = Piece("pawn", "歩", player=1)
            self.grid[6][i] = Piece("pawn", "歩", player=2)
        
        # 香車
        self.grid[0][0] = Piece("lance", "香", player=1)
        self.grid[0][8] = Piece("lance", "香", player=1)
        self.grid[8][0] = Piece("lance", "香", player=2)
        self.grid[8][8] = Piece("lance", "香", player=2)
        
        # 桂馬
        self.grid[0][1] = Piece("knight", "桂", player=1)
        self.grid[0][7] = Piece("knight", "桂", player=1)
        self.grid[8][1] = Piece("knight", "桂", player=2)
        self.grid[8][7] = Piece("knight", "桂", player=2)
        
        # 銀将
        self.grid[0][2] = Piece("silver", "銀", player=1)
        self.grid[0][6] = Piece("silver", "銀", player=1)
        self.grid[8][2] = Piece("silver", "銀", player=2)
        self.grid[8][6] = Piece("silver", "銀", player=2)
        
        # 金将
        self.grid[0][3] = Piece("gold", "金", player=1)
        self.grid[0][5] = Piece("gold", "金", player=1)
        self.grid[8][3] = Piece("gold", "金", player=2)
        self.grid[8][5] = Piece("gold", "金", player=2)
        
        # 王将・玉将
        self.grid[0][4] = Piece("king", "王", player=1)
        self.grid[8][4] = Piece("king", "玉", player=2)
        
        # 飛車
        self.grid[1][1] = Piece("rook", "飛", player=1)
        self.grid[7][7] = Piece("rook", "飛", player=2)
        
        # 角行
        self.grid[1][7] = Piece("bishop", "角", player=1)
        self.grid[7][1] = Piece("bishop", "角", player=2)
        
    def setup_random_endgame(self):
        """ランダムな終盤状態を生成する"""
        import random
        
        # 盤面をクリア
        self.grid = [[None for _ in range(9)] for _ in range(9)]
        
        # 両者の王/玉は必ず配置
        self.grid[0][4] = Piece("king", "王", player=1)  # 先手の王
        self.grid[8][4] = Piece("king", "玉", player=2)  # 後手の玉
        
        # 残りの駒をランダムに配置（少数）
        remaining_pieces = [
            ("gold", "金"), ("silver", "銀"), ("rook", "飛"), 
            ("bishop", "角"), ("pawn", "歩"), ("lance", "香"),
            ("knight", "桂")
        ]
        
        # 成り駒も含める
        promoted_pieces = [
            ("rook", "飛", True), ("bishop", "角", True),
            ("silver", "銀", True), ("pawn", "歩", True),
            ("lance", "香", True), ("knight", "桂", True)
        ]
        
        # 先手の駒を3-5個ランダムに配置
        num_pieces = random.randint(3, 5)
        for _ in range(num_pieces):
            # 通常の駒か成り駒かをランダムに決定
            if random.random() < 0.3:  # 30%の確率で成り駒
                piece_type, kanji, promoted = random.choice(promoted_pieces)
                row = random.randint(0, 8)  # 成り駒は盤上のどこにでも配置可能
            else:
                piece_type, kanji = random.choice(remaining_pieces)
                promoted = False
                row = random.randint(0, 3)  # 通常の駒は自陣側に配置
                
            col = random.randint(0, 8)
            # 既に駒がある場合や王/玉の位置は避ける
            if self.grid[row][col] is None and not (row == 0 and col == 4) and not (row == 8 and col == 4):
                self.grid[row][col] = Piece(piece_type, kanji, is_promoted=promoted, player=1)
        
        # 後手の駒を2-4個ランダムに配置
        num_pieces = random.randint(2, 4)
        for _ in range(num_pieces):
            # 通常の駒か成り駒かをランダムに決定
            if random.random() < 0.3:  # 30%の確率で成り駒
                piece_type, kanji, promoted = random.choice(promoted_pieces)
                row = random.randint(0, 8)  # 成り駒は盤上のどこにでも配置可能
            else:
                piece_type, kanji = random.choice(remaining_pieces)
                promoted = False
                row = random.randint(5, 8)  # 通常の駒は自陣側に配置
                
            col = random.randint(0, 8)
            # 既に駒がある場合や王/玉の位置は避ける
            if self.grid[row][col] is None and not (row == 0 and col == 4) and not (row == 8 and col == 4):
                self.grid[row][col] = Piece(piece_type, kanji, is_promoted=promoted, player=2)
        
        # 持ち駒もランダムに設定
        self.captured_pieces = {1: [], 2: []}
        for player in [1, 2]:
            num_captured = random.randint(1, 3)
            for _ in range(num_captured):
                piece_type, kanji = random.choice(remaining_pieces)
                self.captured_pieces[player].append(Piece(piece_type, kanji, player=player))
        
        # 王手状態のチェックと修正
        for player in [1, 2]:
            # 王手状態かチェック
            if self.is_in_check(player):
                # 王手をかけている駒を特定
                attacking_pieces = self.find_attacking_pieces(player)
                
                for piece_pos in attacking_pieces:
                    # 駒を取り除く
                    row, col = piece_pos
                    piece = self.grid[row][col]
                    self.grid[row][col] = None
                    
                    # 持ち駒に追加
                    opponent = 3 - player
                    self.captured_pieces[opponent].append(piece)
                    
                    # 再度王手チェック
                    if not self.is_in_check(player):
                        break  # 王手が解消されたら終了

    def draw(self):
        # 背景画像を描画（最初に描画して他の要素の下に配置）
        if self.battle_background:
            self.screen.blit(self.battle_background, (0, 0))
        else:
            # 背景画像がない場合はデフォルトの背景色
            self.screen.fill((240, 217, 181))  # 薄い茶色
        
        # 盤の描画
        board_rect = pygame.Rect((SCREEN_WIDTH - BOARD_SIZE) // 2, (SCREEN_HEIGHT - BOARD_SIZE) // 2, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, BOARD_COLOR, board_rect)
        
        # マス目の描画
        for i in range(10):
            # 横線
            pygame.draw.line(self.screen, GRID_COLOR, 
                            (board_rect.left, board_rect.top + i * CELL_SIZE),
                            (board_rect.right, board_rect.top + i * CELL_SIZE), 2)
            # 縦線
            pygame.draw.line(self.screen, GRID_COLOR, 
                            (board_rect.left + i * CELL_SIZE, board_rect.top),
                            (board_rect.left + i * CELL_SIZE, board_rect.bottom), 2)
        
        # 移動可能なマスのハイライト
        for row, col in self.valid_moves:
            x = board_rect.left + col * CELL_SIZE
            y = board_rect.top + row * CELL_SIZE
            highlight = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            highlight.fill(VALID_MOVE_COLOR)
            self.screen.blit(highlight, (x, y))
        
        # 駒の描画
        for row in range(9):
            for col in range(9):
                x = board_rect.left + col * CELL_SIZE
                y = board_rect.top + row * CELL_SIZE
                
                if self.grid[row][col]:
                    self.grid[row][col].draw(self.screen, x, y, self.piece_images, self.font, SELECTED_COLOR)
                    
        # 持ち駒の描画
        self.draw_captured_pieces()
        
        # 手番表示
        turn_text = "先手番↓" if self.player_turn == 1 else "後手番↑"
        text = self.font.render(turn_text, True, (255, 255, 255))
        if self.player_turn == 1:
            self.screen.blit(text, (20, 90))
        else:
            self.screen.blit(text, (20, SCREEN_HEIGHT - 90))

        # # ターン数表示
        # turn_count_text = f"ターン: {self.turn_count}"
        # text = self.font.render(turn_count_text, True, (0, 0, 0))
        # self.screen.blit(text, (SCREEN_WIDTH - 150, 150))
        
        # 特殊技確認中の場合、確認メッセージと「はい」「いいえ」ボタンを表示
        if self.special_move_confirm:
            # 半透明の背景
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # 半透明の黒
            self.screen.blit(overlay, (0, 0))
            
            # 確認メッセージの背景
            message_bg = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 70, 500, 150)
            pygame.draw.rect(self.screen, (240, 240, 240), message_bg)
            pygame.draw.rect(self.screen, (0, 0, 0), message_bg, 2)
            
            # 確認メッセージ
            message_text = f"「{self.special_move_active.name}」を使用しますか？"
            text = self.font.render(message_text, True, (0, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(text, text_rect)
            
            # 「はい」「いいえ」ボタン
            self.confirm_yes_button.draw(self.screen, self.font)
            self.confirm_no_button.draw(self.screen, self.font)
        
        # ゲーム終了メッセージの表示と音声再生
        show_restart = self.draw_game_over_message()
        if show_restart:
            return True
        
        # 王手メッセージの表示と音声再生
        self.draw_check_message()
        
        # エフェクトの更新と描画
        if self.effect_display:
            self.effect_display.update()
            self.effect_display.draw()
            
        return False
        
    def draw_captured_pieces(self):
        # 先手の持ち駒（画面左側、左上から）
        for i, piece in enumerate(self.captured_pieces[1]):
            row = i // 2  # 2駒ごとに行を変える
            col = i % 2   # 列は0か1
            x = 20 + col * (CELL_SIZE + 5)
            y = 150 + row * (CELL_SIZE + 5)
            piece.draw(self.screen, x, y, self.piece_images, self.font, SELECTED_COLOR)
        
        # 後手の持ち駒（画面右側、右下から）
        for i, piece in enumerate(self.captured_pieces[2]):
            row = i // 2  # 2駒ごとに行を変える
            col = i % 2   # 列は0か1
            # 右側に配置し、右下から上に向かって配置
            x = SCREEN_WIDTH - 20 - CELL_SIZE - col * (CELL_SIZE + 5)
            y = SCREEN_HEIGHT - 50 - CELL_SIZE - row * (CELL_SIZE + 5)
            piece.draw(self.screen, x, y, self.piece_images, self.font, SELECTED_COLOR)
    def get_board_position(self, mouse_pos):
        board_rect = pygame.Rect((SCREEN_WIDTH - BOARD_SIZE) // 2, (SCREEN_HEIGHT - BOARD_SIZE) // 2, BOARD_SIZE, BOARD_SIZE)
        
        if not board_rect.collidepoint(mouse_pos):
            return None
        
        x = (mouse_pos[0] - board_rect.left) // CELL_SIZE
        y = (mouse_pos[1] - board_rect.top) // CELL_SIZE
        
        if 0 <= x < 9 and 0 <= y < 9:
            return (y, x)
        return None
        
    def get_captured_piece_at_position(self, mouse_pos):
        # 先手の持ち駒（画面左側、左上から）
        for i, piece in enumerate(self.captured_pieces[1]):
            row = i // 2  # 2駒ごとに行を変える
            col = i % 2   # 列は0か1
            x = 20 + col * (CELL_SIZE + 5)
            y = 150 + row * (CELL_SIZE + 5)
            piece_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            
            if piece_rect.collidepoint(mouse_pos):
                return (1, i)  # プレイヤー1の持ち駒のインデックスiを返す
        
        # 後手の持ち駒（画面右側、右下から）
        for i, piece in enumerate(self.captured_pieces[2]):
            row = i // 2  # 2駒ごとに行を変える
            col = i % 2   # 列は0か1
            # 右側に配置し、右下から上に向かって配置
            x = SCREEN_WIDTH - 20 - CELL_SIZE - col * (CELL_SIZE + 5)
            y = SCREEN_HEIGHT - 50 - CELL_SIZE - row * (CELL_SIZE + 5)
            piece_rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            
            if piece_rect.collidepoint(mouse_pos):
                return (2, i)  # プレイヤー2の持ち駒のインデックスiを返す
                
        return None
    def select(self, pos, mouse_pos=None):
        # 成り判定中または詰み・ゲーム終了の場合は操作を受け付けない
        if self.promotion_pending or self.checkmate or self.game_over:
            return
            
        # 特殊技の確認中の場合は何もしない（ボタンのクリック処理はmain.pyで行う）
        if self.special_move_confirm:
            return
            
        # 特殊技が選択されている場合
        if self.special_move_active and pos:
            row, col = pos
            piece = self.grid[row][col]
            
            # 対象の駒を選択した場合、確認画面に移行
            if piece and piece.player == self.player_turn:
                # 特殊技の種類に応じた対象駒のチェック
                if self.special_move_active.name == "歩強化" and piece.name != "pawn":
                    print("この技は歩にのみ使用できます")
                    return
                
                self.special_move_target = pos
                self.special_move_confirm = True
                return
            return
            
        # 持ち駒を選択した場合
        if mouse_pos:
            captured_pos = self.get_captured_piece_at_position(mouse_pos)
            if captured_pos:
                player, index = captured_pos
                
                # 自分の持ち駒のみ選択可能
                if player == self.player_turn and index < len(self.captured_pieces[player]):
                    # 既に選択されている駒があれば選択解除
                    if self.selected_piece:
                        self.selected_piece.selected = False
                        
                    # 持ち駒を選択
                    piece = self.captured_pieces[player][index]
                    piece.selected = True
                    self.selected_piece = piece
                    self.selected_pos = None  # 盤上の位置はNone
                    
                    # 持ち駒を打てる場所を計算
                    self.valid_moves = self.get_valid_drop_positions(piece)
                    return
        
        # 盤上の操作
        if not pos:
            return
        
        row, col = pos
        piece = self.grid[row][col]
        
        # 既に駒が選択されている場合
        if self.selected_piece:
            # 持ち駒が選択されていて、盤上の空きマスをクリックした場合
            if self.selected_pos is None and pos in self.valid_moves:
                # 持ち駒を盤上に配置
                self.drop_piece(self.selected_piece, pos)
                self.selected_piece.selected = False
                self.selected_piece = None
                self.valid_moves = []
                return
                
            # 同じプレイヤーの駒を選択した場合は選択を変更
            if piece and piece.player == self.player_turn:
                self.selected_piece.selected = False
                piece.selected = True
                self.selected_piece = piece
                self.selected_pos = pos
                self.valid_moves = piece.get_possible_moves(self, pos)
            # 移動先を選択した場合
            else:
                # 移動可能なマスかチェック
                if pos in self.valid_moves:
                    self.move_piece(self.selected_pos, pos)
                    self.selected_piece.selected = False
                    self.selected_piece = None
                    self.selected_pos = None
                    self.valid_moves = []
        # 新しく駒を選択する場合
        elif piece and piece.player == self.player_turn:
            piece.selected = True
            self.selected_piece = piece
            self.selected_pos = pos
            self.valid_moves = piece.get_possible_moves(self, pos)
    def get_valid_drop_positions(self, piece):
        """持ち駒を打てる場所のリストを返す"""
        valid_positions = []
        
        for row in range(9):
            for col in range(9):
                # 空きマスのみに打てる
                if self.grid[row][col] is None:
                    # 歩と香車は1段目（後手は9段目）に打てない
                    if piece.name == "pawn" or piece.name == "lance":
                        if (piece.player == 2 and row == 0) or (piece.player == 1 and row == 8):
                            continue
                    
                    # 桂馬は1、2段目（後手は8、9段目）に打てない
                    if piece.name == "knight":
                        if (piece.player == 2 and row <= 1) or (piece.player == 1 and row >= 7):
                            continue
                    
                    # 二歩のチェック（同じ筋に自分の歩がないか）
                    if piece.name == "pawn":
                        has_pawn_in_same_column = False
                        for r in range(9):
                            if self.grid[r][col] and self.grid[r][col].name == "pawn" and self.grid[r][col].player == piece.player:
                                has_pawn_in_same_column = True
                                break
                        if has_pawn_in_same_column:
                            continue
                    
                    valid_positions.append((row, col))
        
        return valid_positions
        
    def drop_piece(self, piece, pos):
        """持ち駒を盤上に打つ"""
        row, col = pos
        
        # 持ち駒リストから削除
        player = piece.player
        self.captured_pieces[player].remove(piece)
        
        # 盤上に配置
        self.grid[row][col] = piece
        
        # 効果音を鳴らす
        if self.move_sound:
            self.move_sound.play()
        
        # 王手と詰みの判定
        opponent = 3 - player
        self.in_check = self.is_in_check(opponent)
        if self.in_check:
            self.checkmate = self.is_checkmate(opponent)
            if self.checkmate:
                self.game_over = True
                self.winner = player
                
                # ゲーム用BGMを停止
                if self.bgm_manager:
                    self.bgm_manager.stop_bgm()
                
                # ゲーム終了シーケンスを開始
                self._start_game_end_sequence()
                
        # end_turnメソッドを使用して効果の持続時間も更新する
        self.end_turn()
    def is_valid_move(self, from_pos, to_pos):
        return to_pos in self.valid_moves

    def move_piece(self, from_pos, to_pos):
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # 相手の駒を取る場合
        if self.grid[to_row][to_col]:
            captured_piece = self.grid[to_row][to_col]
            
            # 王または玉を取った場合はゲーム終了
            if captured_piece.name == "king":
                self.grid[to_row][to_col] = self.grid[from_row][from_col]
                self.grid[from_row][from_col] = None
                
                # 効果音を鳴らす
                if self.move_sound:
                    self.move_sound.play()
                    
                self.game_over = True
                self.winner = self.player_turn
                
                # ゲーム用BGMを停止
                if self.bgm_manager:
                    self.bgm_manager.stop_bgm()
                
                # ゲーム終了シーケンスを開始
                self._start_game_end_sequence()
                return
            else:
                # 通常の駒を取る場合
                captured_piece.player = self.player_turn  # 駒の向きを変える
                captured_piece.is_promoted = False  # 成りを解除
                captured_piece.reset_effects()  # 特殊効果をリセット
                self.captured_pieces[self.player_turn].append(captured_piece)
        
        # 駒を移動
        self.grid[to_row][to_col] = self.grid[from_row][from_col]
        self.grid[from_row][from_col] = None
        
        # 効果音を鳴らす
        if self.move_sound:
            self.move_sound.play()
        
        piece = self.grid[to_row][to_col]
        
        # 成りの判定（敵陣3段目に入ったら成れる）
        if not piece.is_promoted and piece.name != "king" and piece.name != "gold":
            # 先手の場合は下側3段（6,7,8）、後手の場合は上側3段（0,1,2）が敵陣
            promotion_zone = [6, 7, 8] if piece.player == 1 else [0, 1, 2]
            if to_row in promotion_zone or from_row in promotion_zone:
                # 成れる駒の場合
                if piece.name in ["pawn", "lance", "knight", "silver", "bishop", "rook"]:
                    # 成り判定中フラグを立てる
                    self.promotion_pending = True
                    self.pending_move = (from_pos, to_pos)
                    return
        
        # 成り判定がない場合は通常の処理を続行
        self.finish_move()
    def finish_move(self):
        """駒の移動を完了し、手番を交代する"""
        # 王手と詰みの判定（ゲームが終了していない場合のみ）
        if not self.game_over:
            opponent = 3 - self.player_turn
            self.in_check = self.is_in_check(opponent)
            if self.in_check:
                self.checkmate = self.is_checkmate(opponent)
                if self.checkmate:
                    self.game_over = True
                    self.winner = self.player_turn
                    
                    # ゲーム用BGMを停止
                    if self.bgm_manager:
                        self.bgm_manager.stop_bgm()
                    
                    # ゲーム終了シーケンスを開始
                    self._start_game_end_sequence()
        
        # 手番を交代
        if not self.promotion_pending:
            # end_turnメソッドを使用して効果の持続時間も更新する
            self.end_turn()
            
    def handle_promotion(self, promote):
        """成り判定の結果を処理する"""
        if not self.promotion_pending or not self.pending_move:
            return
            
        from_pos, to_pos = self.pending_move
        to_row, to_col = to_pos
        piece = self.grid[to_row][to_col]
        
        if promote and piece:
            piece.is_promoted = True
            # 成った場合、特殊効果をリセット
            piece.reset_effects()
            print(f"{piece.kanji}が成り、特殊効果がリセットされました")
            
        self.promotion_pending = False
        self.pending_move = None
        
        # 移動を完了（end_turnメソッドを使用）
        self.end_turn()

    def find_king_position(self, player):
        """指定したプレイヤーの王の位置を返す"""
        for row in range(9):
            for col in range(9):
                piece = self.grid[row][col]
                if piece and piece.name == "king" and piece.player == player:
                    return (row, col)
        return None
        
    def is_position_under_attack(self, pos, attacking_player):
        """指定した位置が指定したプレイヤーの駒から攻撃されているかチェック"""
        row, col = pos
        
        # 盤上の全ての駒をチェック
        for r in range(9):
            for c in range(9):
                piece = self.grid[r][c]
                if piece and piece.player == attacking_player:
                    # その駒の移動可能な位置を取得
                    moves = piece.get_possible_moves(self, (r, c))
                    if pos in moves:
                        return True
        
        return False
        
    def find_attacking_pieces(self, player):
        """プレイヤーの王/玉に王手をかけている相手の駒の位置を返す"""
        attacking_pieces = []
        
        # 王/玉の位置を特定
        king_pos = self.find_king_position(player)
        if not king_pos:
            return []
            
        king_row, king_col = king_pos
        opponent = 3 - player  # 相手プレイヤー
        
        # 盤面上の全ての相手の駒をチェック
        for row in range(9):
            for col in range(9):
                piece = self.grid[row][col]
                if piece and piece.player == opponent:
                    # この駒が王/玉に到達可能かチェック
                    moves = piece.get_possible_moves(self, (row, col))
                    if (king_row, king_col) in moves:
                        attacking_pieces.append((row, col))
                        
        return attacking_pieces
        
    def is_in_check(self, player):
        """指定したプレイヤーが王手状態かどうかをチェック"""
        # 王の位置を取得
        king_pos = self.find_king_position(player)
        if not king_pos:
            return False
            
        # 相手のプレイヤー
        opponent = 3 - player
        
        # 王が相手の駒から攻撃されているかチェック
        return self.is_position_under_attack(king_pos, opponent)
        
    def is_checkmate(self, player):
        """指定したプレイヤーが詰み状態かどうかをチェック"""
        # 王手状態でなければ詰みではない
        if not self.is_in_check(player):
            return False
            
        # 王の位置を取得
        king_pos = self.find_king_position(player)
        if not king_pos:
            return False
            
        king_row, king_col = king_pos
        king = self.grid[king_row][king_col]
        
        # 王が移動できるかチェック
        king_moves = king.get_possible_moves(self, king_pos)
        for move in king_moves:
            # 一時的に王を移動させてみる
            temp_grid = [row[:] for row in self.grid]
            self.grid[move[0]][move[1]] = king
            self.grid[king_row][king_col] = None
            
            # 移動先が攻撃されていないかチェック
            is_safe = not self.is_position_under_attack(move, 3 - player)
            
            # 盤面を元に戻す
            self.grid = temp_grid
            
            if is_safe:
                return False  # 安全な移動先があるので詰みではない
        
        # 他の駒が王手を防げるかチェック
        for r in range(9):
            for c in range(9):
                piece = self.grid[r][c]
                if piece and piece.player == player and piece.name != "king":
                    moves = piece.get_possible_moves(self, (r, c))
                    for move in moves:
                        # 一時的に駒を移動させてみる
                        temp_grid = [row[:] for row in self.grid]
                        captured = self.grid[move[0]][move[1]]
                        self.grid[move[0]][move[1]] = piece
                        self.grid[r][c] = None
                        
                        # 王手が解消されるかチェック
                        still_in_check = self.is_in_check(player)
                        
                        # 盤面を元に戻す
                        self.grid = temp_grid
                        
                        if not still_in_check:
                            return False  # 王手を防げる手があるので詰みではない
        
        # 持ち駒を打って王手を防げるかチェック
        for piece in self.captured_pieces[player]:
            valid_drops = self.get_valid_drop_positions(piece)
            for drop_pos in valid_drops:
                # 一時的に持ち駒を打ってみる
                temp_grid = [row[:] for row in self.grid]
                self.grid[drop_pos[0]][drop_pos[1]] = piece
                
                # 王手が解消されるかチェック
                still_in_check = self.is_in_check(player)
                
                # 盤面を元に戻す
                self.grid = temp_grid
                
                if not still_in_check:
                    return False  # 持ち駒を打って王手を防げるので詰みではない
        
        # 全ての手を試しても王手を防げないので詰み
        return True
    def apply_special_move(self, special_move, target_pos=None):
        """特殊技を適用する"""
        result = special_move.execute(self, self.player_turn, target_pos)
        if result:
            # 特殊技の使用に成功
            from special_moves import mark_as_used
            mark_as_used(self.special_move_active.name)
            self.special_move_active = None
            
            # エフェクト待機状態に設定（手番交代を遅延）
            self.special_effect_pending = True
            
            return True
        return False

    def end_turn(self):
        """ターンを終了し、必要に応じて特殊効果の持続時間を減らす"""
        # プレイヤーターンの切り替え
        self.player_turn = 3 - self.player_turn  # 1→2, 2→1
        self.current_player = self.player_turn
        
        # 王手音声フラグをリセット（新しい手番で王手になった場合に再生するため）
        self.oute_sound_played = False
        
        # 特殊技音声フラグをリセット
        self.menko_sound_played = False
        self.toppu_sound_played = False
        self.hengenotsue_sound_played = False
        self.tensousouchi_sound_played = False
        self.komaochi_sound_played = False
        self.current_special_move = None
        
        # 手数カウンターを増やす
        self.move_count += 1
        
        # 2手（先手と後手の両方が行動）で1ターン経過
        if self.move_count % 2 == 0:
            print(f"ターン{self.turn_count}が終了しました")
            
            # ターン数を増やす
            self.turn_count += 1
            
        # 王手判定
        self.check_for_check()
        
        # 詰み判定
        if self.in_check:
            self.check_for_checkmate()
    def check_for_check(self):
        """現在のプレイヤーが王手状態かどうかをチェック"""
        self.in_check = self.is_in_check(self.player_turn)
        
    def check_for_checkmate(self):
        """現在のプレイヤーが詰み状態かどうかをチェック"""
        if self.in_check:
            self.checkmate = self.is_checkmate(self.player_turn)
            if self.checkmate:
                self.game_over = True
                self.winner = 3 - self.player_turn  # 相手の勝ち
                
                # ゲーム用BGMを停止
                if self.bgm_manager:
                    self.bgm_manager.stop_bgm()
                
                # ゲーム終了シーケンスを開始
                self._start_game_end_sequence()
    def cancel_special_move(self):
        """特殊技の選択をキャンセルして技選択画面に戻る"""
        self.special_move_active = None
        # 特殊技ウィンドウを再度開く処理は main.py で行う
        print("技選択をキャンセルしました")
        
    def resign(self):
        """現在のプレイヤーが投了する"""
        # 現在のプレイヤーの相手を勝者とする
        self.winner = 3 - self.player_turn
        self.game_over = True
        
        # ゲーム用BGMを停止
        if self.bgm_manager:
            self.bgm_manager.stop_bgm()
        
        # ゲーム終了シーケンスを開始
        self._start_game_end_sequence()
        
        # 勝者のメッセージは通常のdrawメソッドで表示される
    def confirm_special_move(self):
        """特殊技の適用を確定する"""
        if self.special_move_active:
            result = self.apply_special_move(self.special_move_active)    
            # 確認状態をリセット
            self.special_move_confirm = False
            self.special_move_target = None
            return result
        return False
        
    def cancel_confirm(self):
        """特殊技の確認をキャンセルする"""
        self.special_move_confirm = False
        self.special_move_target = None
        
        # メンコ、突風、変化の杖、転送装置、駒落ちの場合は特殊技選択もキャンセルする
        if self.special_move_active and (self.special_move_active.name == "メンコ" or self.special_move_active.name == "突風" or self.special_move_active.name == "変化の杖" or self.special_move_active.name == "転送装置" or self.special_move_active.name == "駒落ち"):
            self.special_move_active = None
