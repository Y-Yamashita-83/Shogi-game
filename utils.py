import os
import pygame
from constants import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT

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

def load_title_image():
    """タイトル画像を読み込む"""
    try:
        image_path = os.path.join(os.path.dirname(__file__), "assets", "images", "title", "title.png")
        if os.path.exists(image_path):
            title_image = pygame.image.load(image_path)
            # 画面サイズに合わせてリサイズ
            title_image = pygame.transform.scale(title_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
            return title_image
        else:
            print(f"タイトル画像が見つかりません: {image_path}")
            return None
    except Exception as e:
        print(f"タイトル画像の読み込みに失敗しました: {e}")
        return None

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
    """音声ファイルを読み込む"""
    sounds = {}
    
    try:
        # 駒の移動音
        move_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "tap.mp3")
        if os.path.exists(move_sound_path):
            sounds['move'] = pygame.mixer.Sound(move_sound_path)
        else:
            sounds['move'] = None
            
        # 王手音声
        oute_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "oute_takumi.mp3")
        if os.path.exists(oute_sound_path):
            sounds['oute'] = pygame.mixer.Sound(oute_sound_path)
            print(f"王手音声を読み込みました: {oute_sound_path}")
        else:
            sounds['oute'] = None
            print(f"王手音声ファイルが見つかりません: {oute_sound_path}")
            
        # 投了音声
        toryo_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "toryo_takumi.mp3")
        if os.path.exists(toryo_sound_path):
            sounds['toryo'] = pygame.mixer.Sound(toryo_sound_path)
            print(f"投了音声を読み込みました: {toryo_sound_path}")
        else:
            sounds['toryo'] = None
            print(f"投了音声ファイルが見つかりません: {toryo_sound_path}")
            
        # メンコ音声
        menko_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "menko_takumi.mp3")
        if os.path.exists(menko_sound_path):
            sounds['menko'] = pygame.mixer.Sound(menko_sound_path)
            print(f"メンコ音声を読み込みました: {menko_sound_path}")
        else:
            sounds['menko'] = None
            print(f"メンコ音声ファイルが見つかりません: {menko_sound_path}")
            
        # 突風音声
        toppu_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "toppu_takumi.mp3")
        if os.path.exists(toppu_sound_path):
            sounds['toppu'] = pygame.mixer.Sound(toppu_sound_path)
            print(f"突風音声を読み込みました: {toppu_sound_path}")
        else:
            sounds['toppu'] = None
            print(f"突風音声ファイルが見つかりません: {toppu_sound_path}")
            
        # 変化の杖音声
        hengenotsue_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "hengenotsue_takumi.mp3")
        if os.path.exists(hengenotsue_sound_path):
            sounds['hengenotsue'] = pygame.mixer.Sound(hengenotsue_sound_path)
            print(f"変化の杖音声を読み込みました: {hengenotsue_sound_path}")
        else:
            sounds['hengenotsue'] = None
            print(f"変化の杖音声ファイルが見つかりません: {hengenotsue_sound_path}")
            
        # 転送装置音声
        tensousouchi_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "tensousouchi_takumi.mp3")
        if os.path.exists(tensousouchi_sound_path):
            sounds['tensousouchi'] = pygame.mixer.Sound(tensousouchi_sound_path)
            print(f"転送装置音声を読み込みました: {tensousouchi_sound_path}")
        else:
            sounds['tensousouchi'] = None
            print(f"転送装置音声ファイルが見つかりません: {tensousouchi_sound_path}")
            
        # 駒落ち音声
        komaochi_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "komaochi_takumi.mp3")
        if os.path.exists(komaochi_sound_path):
            sounds['komaochi'] = pygame.mixer.Sound(komaochi_sound_path)
            print(f"駒落ち音声を読み込みました: {komaochi_sound_path}")
        else:
            sounds['komaochi'] = None
            print(f"駒落ち音声ファイルが見つかりません: {komaochi_sound_path}")
            
        # タイトル音声
        title_sound_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "voice", "title_takumi.mp3")
        if os.path.exists(title_sound_path):
            sounds['title'] = pygame.mixer.Sound(title_sound_path)
            print(f"タイトル音声を読み込みました: {title_sound_path}")
        else:
            sounds['title'] = None
            print(f"タイトル音声ファイルが見つかりません: {title_sound_path}")
            
    except pygame.error as e:
        print(f"音声ファイルの読み込みに失敗しました: {e}")
        sounds['move'] = None
        sounds['oute'] = None
        sounds['toryo'] = None
        sounds['menko'] = None
        sounds['toppu'] = None
        sounds['hengenotsue'] = None
        sounds['tensousouchi'] = None
        sounds['komaochi'] = None
        sounds['title'] = None
        
    return sounds
