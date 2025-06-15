import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE
from utils import load_piece_images, setup_fonts, load_sounds
from board import Board
from ui.button import Button
from ui.windows import SpecialMoveWindow, PromotionWindow
from event_manager import EventManager, GameEvent

def main():
    # 初期化
    pygame.init()
    pygame.mixer.init()  # 音声機能の初期化
    
    # イベントマネージャーの作成
    event_manager = EventManager()
    
    # 画面設定
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("将棋ゲーム")
    
    # リソースの読み込み
    piece_images = load_piece_images()
    font, button_font = setup_fonts()
    move_sound = load_sounds()
    
    # ゲームオブジェクトの作成
    board = Board(screen, font, piece_images, move_sound, event_manager)
    clock = pygame.time.Clock()
    
    # 「最初に戻る」ボタン
    restart_button = Button(
        SCREEN_WIDTH // 2 - 100, 
        SCREEN_HEIGHT - 60, 
        200, 40, 
        "最初に戻る", 
        lambda: None  # 実際のアクションはループ内で設定
    )
    
    # 「技を使う」ボタン
    special_move_button = Button(
        SCREEN_WIDTH - 120,
        20,
        100, 40,
        "技を使う",
        lambda: None  # 実際のアクションはループ内で設定
    )
    
    # 特殊技ウィンドウ
    special_move_window = SpecialMoveWindow(font, button_font)
    
    # 成り判定ウィンドウ
    promotion_window = PromotionWindow(font, button_font)
    
    # 特殊技イベントのリスナーを登録
    def on_special_move_activated(data):
        message = data["message"]
        affected_positions = data.get("affected_positions", [])
        
        # メッセージエフェクトを追加（画面上部に表示）
        board.effect_display.add_message(message, position=(SCREEN_WIDTH // 2, 30), color=(255, 0, 0))
        
        # 影響を受けた駒をハイライト
        for row, col in affected_positions:
            x = (col * CELL_SIZE) + (SCREEN_WIDTH - CELL_SIZE * 9) // 2
            y = (row * CELL_SIZE) + (SCREEN_HEIGHT - CELL_SIZE * 9) // 2
            board.effect_display.add_highlight((x, y), CELL_SIZE, color=(255, 255, 0, 150), duration=1.5)
    
    # イベントリスナーを登録
    event_manager.subscribe(GameEvent.SPECIAL_MOVE_ACTIVATED, on_special_move_activated)
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
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
                        
                    # 「技を使う」ボタンのクリック処理
                    if special_move_button.is_hovered and not board.game_over:
                        special_move_window.open(board, board.current_player)
                        continue
                    
                    # ゲーム終了時のボタン処理
                    if board.game_over and restart_button.handle_event(event):
                        # ゲームをリセット
                        board = Board(screen, font, piece_images, move_sound)
                        # 特殊技の使用状態をリセット
                        from special_moves import reset_special_moves
                        reset_special_moves()
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
                    
                    board.select(pos, event.pos)  # マウス位置も渡す
            
        # 画面クリア
        screen.fill((255, 255, 255))
        
        # 盤と駒の描画
        show_restart = board.draw()
        
        # 「技を使う」ボタンの更新と描画（ゲーム終了時は表示しない）
        if not board.game_over and not board.special_move_active:
            special_move_button.update(mouse_pos)
            special_move_button.draw(screen, button_font)
        
        # 特殊技選択中は「技選択に戻る」ボタンを更新
        if board.special_move_active and not board.special_move_confirm:
            board.back_to_special_move_button.update(mouse_pos)
            
        # 特殊技確認中は「はい」「いいえ」ボタンを更新
        if board.special_move_confirm:
            board.confirm_yes_button.update(mouse_pos)
            board.confirm_no_button.update(mouse_pos)
        
        # ゲーム終了時にリスタートボタンを表示
        if show_restart:
            restart_button.update(mouse_pos)
            restart_button.draw(screen, button_font)
        
        # 特殊技ウィンドウの描画
        special_move_window.update(mouse_pos)
        special_move_window.draw(screen)
        
        # 成り判定ウィンドウの表示
        if board.promotion_pending and not promotion_window.active:
            # 成り判定ウィンドウを開く
            promotion_window.open(None, board.handle_promotion)
        
        # 成り判定ウィンドウの描画
        promotion_window.update(mouse_pos)
        promotion_window.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
