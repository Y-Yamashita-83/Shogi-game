import os
import pygame
from constants import CELL_SIZE

def load_piece_images():
    """駒の画像を読み込む"""
    images = {}
    image_dir = os.path.join(os.path.dirname(__file__), "assets", "images", "koma")
    
    # 駒の種類と対応するファイル名のマッピング
    piece_files = {
        "pawn": {"normal": "pawn", "promoted": "prom_pawn"},
        "lance": {"normal": "lance", "promoted": "prom_lance"},
        "knight": {"normal": "knight", "promoted": "prom_knight"},
        "silver": {"normal": "silver", "promoted": "prom_silver"},
        "gold": {"normal": "gold", "promoted": "gold"},
        "king": {"normal": "king", "promoted": "king"},
        "bishop": {"normal": "bishop", "promoted": "horse"},
        "rook": {"normal": "rook", "promoted": "dragon"}
    }
    
    # 各駒の画像を読み込む
    for piece_name, variants in piece_files.items():
        for state, file_suffix in variants.items():
            # 先手（白）の駒
            white_file = os.path.join(image_dir, f"white_{file_suffix}.png")
            if os.path.exists(white_file):
                images[(piece_name, 1, state == "promoted")] = pygame.image.load(white_file)
            
            # 後手（黒）の駒
            black_file = os.path.join(image_dir, f"black_{file_suffix}.png")
            if os.path.exists(black_file):
                images[(piece_name, 2, state == "promoted")] = pygame.image.load(black_file)
    
    return images

# フォント設定
def setup_fonts():
    try:
        # 日本語フォントを試みる
        font = pygame.font.SysFont("msgothic", 30)
        button_font = pygame.font.SysFont("msgothic", 24)
        # テスト描画して日本語が表示できるか確認
        test_surface = font.render("王", True, (0, 0, 0))
        return font, button_font
    except:
        # 失敗した場合はデフォルトフォントを使用
        font = pygame.font.SysFont(None, 30)
        button_font = pygame.font.SysFont(None, 24)
        return font, button_font

# 効果音の読み込み
def load_sounds():
    try:
        sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "tap.mp3")
        move_sound = pygame.mixer.Sound(sound_path)
        return move_sound
    except:
        print("効果音の読み込みに失敗しました")
        return None
