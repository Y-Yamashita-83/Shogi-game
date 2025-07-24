import pygame
import os

class BGMManager:
    def __init__(self):
        self.bgm_playing = False
        self.bgm_file = None
        
    def load_bgm(self, bgm_name):
        """BGMファイルを読み込む"""
        bgm_path = os.path.join(os.path.dirname(__file__), "assets", "sound", "bgm", f"{bgm_name}.mp3")
        if os.path.exists(bgm_path):
            self.bgm_file = bgm_path
            print(f"BGMを読み込みました: {bgm_path}")
            return True
        else:
            print(f"BGMファイルが見つかりません: {bgm_path}")
            return False
            
    def play_bgm(self, volume=0.5):
        """BGMを再生開始（ループ）"""
        if self.bgm_file and not self.bgm_playing:
            try:
                pygame.mixer.music.load(self.bgm_file)
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(-1)  # -1 = 無限ループ
                self.bgm_playing = True
                print("BGMの再生を開始しました")
            except pygame.error as e:
                print(f"BGMの再生に失敗しました: {e}")
                
    def stop_bgm(self):
        """BGMを停止"""
        if self.bgm_playing:
            pygame.mixer.music.stop()
            self.bgm_playing = False
            print("BGMを停止しました")
            
    def pause_bgm(self):
        """BGMを一時停止"""
        if self.bgm_playing:
            pygame.mixer.music.pause()
            
    def resume_bgm(self):
        """BGMを再開"""
        if self.bgm_playing:
            pygame.mixer.music.unpause()
            
    def is_playing(self):
        """BGMが再生中かどうか"""
        return self.bgm_playing and pygame.mixer.music.get_busy()
