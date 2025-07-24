import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, WINDOW_BG_COLOR, WINDOW_BORDER_COLOR
from utils import load_piece_images, setup_fonts, load_sounds
from board import Board
from ui.button import Button
from ui.windows import SpecialMoveWindow, PromotionWindow
from event_manager import EventManager, GameEvent
from ai import ShogiAI
from bgm_manager import BGMManager

def main():
    # 初期化
    pygame.init()
    pygame.mixer.init()  # 音声機能の初期化
    
    # イベントマネージャーの作成
    event_manager = EventManager()
    
    # 画面設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("エクストリーム将棋")
    
    # BGM管理の初期化
    bgm_manager = BGMManager()
    bgm_manager.load_bgm("YASHA")
    
    # リソースの読み込み
    piece_images = load_piece_images()
    font, button_font = setup_fonts()
    sounds = load_sounds()  # 辞書として受け取る
    
    # ゲームモード選択画面（音声再生も含む）
    game_mode = show_game_mode_selection(screen, font, button_font, sounds)
    
    # ゲームオブジェクトの作成
    board = Board(screen, font, piece_images, sounds, event_manager, bgm_manager)  # BGMManagerも渡す
    
    # 特殊技の使用状態をリセット
    from special_moves import reset_special_moves
    reset_special_moves()
    
    # 選択されたモードに応じて初期配置を設定
    if game_mode == "endgame":
        board.setup_random_endgame()
    # 通常モードの場合はデフォルトのsetup_boardが既に呼ばれている
    
    # 対局開始時にBGM再生
    bgm_manager.play_bgm(volume=0.3)  # 音量調整
    
    clock = pygame.time.Clock()
    
    # 「最初に戻る」ボタン
    restart_button = Button(
        SCREEN_WIDTH // 2 - 100, 
        SCREEN_HEIGHT - 60, 
        200, 40, 
        "最初に戻る", 
        lambda: None  # 実際のアクションはループ内で設定
    )
    
    # 「投了」ボタン
    resign_button = Button(
        SCREEN_WIDTH // 2 - 100, 
        SCREEN_HEIGHT - 60, 
        200, 40, 
        "投了", 
        lambda: None  # 実際のアクションはループ内で設定
    )
    
    # 「技を使う」ボタン
    special_move_button = Button(
        SCREEN_WIDTH - 120,
        90,
        100, 40,
        "技を使う",
        lambda: None  # 実際のアクションはループ内で設定
    )
    
    # 特殊技ウィンドウ
    special_move_window = SpecialMoveWindow(font, button_font)
    
    # 成り判定ウィンドウ
    promotion_window = PromotionWindow(font, button_font)
    
    # AIの初期化
    ai = ShogiAI(board)
    
    # AI手番タイマー
    ai_move_timer = 0  # AIの手番タイマー
    ai_delay = 60      # 60フレーム（約1秒）の遅延
    
    # 特殊技イベントのリスナーを登録
    def on_special_move_activated(data):
        message = data["message"]
        move_name = data.get("move_name", "")
        affected_positions = data.get("affected_positions", [])
        
        # メッセージエフェクトを追加（画面上部に表示）
        board.effect_display.add_message(message, position=(SCREEN_WIDTH // 2, 30), color=(255, 0, 0))
        
        # 影響を受けた駒をハイライト
        for row, col in affected_positions:
            x = (col * CELL_SIZE) + (SCREEN_WIDTH - CELL_SIZE * 9) // 2
            y = (row * CELL_SIZE) + (SCREEN_HEIGHT - CELL_SIZE * 9) // 2
            board.effect_display.add_highlight((x, y), CELL_SIZE, color=(255, 255, 0, 150), duration=1.5)
        
        # 特殊技に応じた音声再生
        if move_name == "メンコ" and not board.menko_sound_played:
            board.play_menko_sound()
            board.menko_sound_played = True
            board.current_special_move = "メンコ"
        elif move_name == "突風" and not board.toppu_sound_played:
            board.play_toppu_sound()
            board.toppu_sound_played = True
            board.current_special_move = "突風"
        elif move_name == "変化の杖" and not board.hengenotsue_sound_played:
            board.play_hengenotsue_sound()
            board.hengenotsue_sound_played = True
            board.current_special_move = "変化の杖"
        elif move_name == "転送装置" and not board.tensousouchi_sound_played:
            board.play_tensousouchi_sound()
            board.tensousouchi_sound_played = True
            board.current_special_move = "転送装置"
        elif move_name == "駒落ち" and not board.komaochi_sound_played:
            board.play_komaochi_sound()
            board.komaochi_sound_played = True
            board.current_special_move = "駒落ち"
    
    # イベントリスナーを登録
    event_manager.subscribe(GameEvent.SPECIAL_MOVE_ACTIVATED, on_special_move_activated)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # 特殊技エフェクト完了チェック
        board.check_special_effects_complete()
        
        # AIの手番処理（描画前に実行）
        if (board.player_turn == 1 and not board.game_over and 
            not board.promotion_pending and not special_move_window.active and
            board.can_change_turn()):  # エフェクト完了チェックを追加
            
            ai_move_timer += 1
            if ai_move_timer >= ai_delay:
                # AIの手を実行
                ai.make_move()
                ai_move_timer = 0  # タイマーリセット
        else:
            ai_move_timer = 0  # AI以外の手番ではタイマーリセット
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    # 成り判定ウィンドウが開いている場合
                    if promotion_window.active:
                        promotion_window.handle_event(event)
                        continue
                        
                    # 特殊技ウィンドウが開いている場合
                    if special_move_window.active:
                        special_move_window.handle_event(event)
                        continue
                        
                    # 「技を使う」ボタンのクリック処理（後手の時のみ）
                    if special_move_button.is_hovered and not board.game_over and board.player_turn == 2:
                        special_move_window.open(board, board.current_player)
                        continue
                    
                    # 「投了」ボタンのクリック処理
                    if not board.game_over and not board.special_move_active and not promotion_window.active and resign_button.handle_event(event):
                        # 現在のプレイヤーが投了
                        board.resign()
                        continue
                    
                    # ゲーム終了時のボタン処理
                    if board.game_over and restart_button.handle_event(event):
                        # BGM停止
                        bgm_manager.stop_bgm()
                        
                        # ゲームをリセット
                        board = Board(screen, font, piece_images, sounds, event_manager, bgm_manager)
                        # モード選択画面を再表示（音声再生も含む）
                        game_mode = show_game_mode_selection(screen, font, button_font, sounds)
                        # 選択されたモードに応じて初期配置を設定
                        if game_mode == "endgame":
                            board.setup_random_endgame()
                        # 特殊技の使用状態をリセット
                        from special_moves import reset_special_moves
                        reset_special_moves()
                        # AIも再初期化
                        ai = ShogiAI(board)
                        # AIタイマーもリセット
                        ai_move_timer = 0
                        
                        # 新しいゲームでBGM再開
                        bgm_manager.play_bgm(volume=0.3)
                        continue
                        
                    # 通常のゲームプレイ
                    pos = board.get_board_position(event.pos)
                    
                    # 特殊技の確認中の場合、「はい」「いいえ」ボタンのクリック処理
                    if board.special_move_confirm:
                        if board.confirm_yes_button.handle_event(event):
                            # 特殊技を適用
                            board.confirm_special_move()
                            continue
                        elif board.confirm_no_button.handle_event(event):
                            # 確認をキャンセル
                            board.cancel_confirm()
                            # メンコや突風の場合は特殊技選択ウィンドウを再度開く
                            if board.special_move_active is None:
                                special_move_window.open(board, board.current_player)
                            continue
                    
                    # 特殊技が選択されている場合、「技選択に戻る」ボタンのクリック処理
                    if board.special_move_active and not board.special_move_confirm and board.back_to_special_move_button.handle_event(event):
                        # 特殊技選択をキャンセルして技選択ウィンドウを再度開く
                        board.special_move_active = None
                        special_move_window.open(board, board.current_player)
                        continue
                    
                    # 後手の時のみユーザーの操作を受け付ける
                    if board.player_turn != 2:
                        continue
                    
                    board.select(pos, event.pos)  # マウス位置も渡す
            
        # 画面クリア
        screen.fill((255, 255, 255))
        
        # 盤と駒の描画
        show_restart = board.draw()
        
        # エフェクト表示の更新
        board.effect_display.update()
        
        # AI思考中の表示
        if (board.player_turn == 1 and not board.game_over and ai_move_timer > 0 and
            board.can_change_turn()):
            thinking_text = font.render("コンピュータが考え中...", True, (100, 100, 100))
            screen.blit(thinking_text, (10, 10))
        
        # 「技を使う」ボタンの更新と描画（ゲーム終了時または先手番は表示しない）
        if not board.game_over and not board.special_move_active and board.player_turn == 2:
            special_move_button.update(mouse_pos)
            special_move_button.draw(screen, button_font)
        
        # 特殊技選択中は「技選択に戻る」ボタンを更新
        if board.special_move_active and not board.special_move_confirm:
            board.back_to_special_move_button.update(mouse_pos)
            
        # 特殊技確認中は「はい」「いいえ」ボタンを更新
        if board.special_move_confirm:
            board.confirm_yes_button.update(mouse_pos)
            board.confirm_no_button.update(mouse_pos)
        
        # ゲーム状態に応じたボタン表示
        if show_restart:
            # ゲーム終了時は「最初に戻る」ボタンを表示
            restart_button.update(mouse_pos)
            restart_button.draw(screen, button_font)
        elif not board.special_move_active and not board.special_move_confirm and not promotion_window.active:
            # 後手番の時のみ「投了」ボタンを表示
            if board.player_turn == 2:
                resign_button.update(mouse_pos)
                resign_button.draw(screen, button_font)
        
        # 特殊技ウィンドウの描画
        special_move_window.update(mouse_pos)
        special_move_window.draw(screen)
        
        # 成り判定ウィンドウの表示
        if board.promotion_pending and not promotion_window.active:
            # コンピュータプレイヤーの場合は自動判定（既にAIで処理済み）
            if not board.is_computer_player(board.player_turn):
                # 人間プレイヤーの場合のみウィンドウを開く
                promotion_window.open(None, board.handle_promotion)
        
        # 成り判定ウィンドウの描画
        promotion_window.update(mouse_pos)
        promotion_window.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

def show_game_mode_selection(screen, font, button_font, sounds=None):
    """ゲームモード選択画面を表示し、選択されたモードを返す"""
    
    # 前回の音声を停止（重複再生防止）
    pygame.mixer.stop()
    
    # タイトル音声を再生
    if sounds and sounds.get('title'):
        try:
            sounds['title'].play()
            print("タイトル音声を再生しました")
        except pygame.error as e:
            print(f"タイトル音声の再生に失敗しました: {e}")
    
    # タイトル画像の読み込み
    from utils import load_title_image
    title_image = load_title_image()
    
    # ウィンドウの設定
    window_width = 600
    window_height = 160
    window_x = (SCREEN_WIDTH - window_width) // 2
    window_y = (SCREEN_HEIGHT - window_height) // 1.1
    
    # ボタンの作成
    normal_button = Button(
        window_x + 50,
        window_y + 80,
        140, 50,
        "通常対戦",
        None
    )
    
    endgame_button = Button(
        window_x + 400,
        window_y + 80,
        140, 50,
        "短期決戦",
        None
    )
    
    selected_mode = None
    
    # 選択画面のループ
    while selected_mode is None:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左クリック
                    if normal_button.is_hovered:
                        selected_mode = "normal"
                    elif endgame_button.is_hovered:
                        selected_mode = "endgame"
        
        # 画面クリア
        screen.fill((255, 255, 255))
        
        # タイトル画像の描画
        if title_image:
            screen.blit(title_image, (0, 0))
        
        # 選択ウィンドウの描画（半透明にして背景画像を見えるようにする）
        window_rect = pygame.Rect(window_x, window_y, window_width, window_height)
        window_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        window_surface.fill((240, 240, 240, 200))  # 半透明の背景
        screen.blit(window_surface, (window_x, window_y))
        pygame.draw.rect(screen, WINDOW_BORDER_COLOR, window_rect, 2)
        
        # タイトルの描画
        title_text = font.render("ゲームモードを選択してください", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, window_y + 40))
        screen.blit(title_text, title_rect)
        
        # ボタンの更新と描画
        normal_button.update(mouse_pos)
        normal_button.draw(screen, button_font)
        
        endgame_button.update(mouse_pos)
        endgame_button.draw(screen, button_font)
        
        pygame.display.flip()
    
    return selected_mode

if __name__ == "__main__":
    main()
