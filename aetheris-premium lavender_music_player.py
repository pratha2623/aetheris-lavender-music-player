# ---------------------------------------------------------
# Aetheris - Lavender Premium Music Player
# ---------------------------------------------------------

import os
import math
import time
import random
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from pygame import mixer
import mutagen

# Initialize application configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  # Accent colors will be overridden customly

# Playback State Constants
STATE_STOPPED = 0
STATE_PLAYING = 1
STATE_PAUSED = 2

class AetherisMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Aetheris - Premium Lavender Player")
        self.root.geometry("880x600")
        self.root.minsize(850, 560)
        
        # Color Palette Definitions
        self.COLOR_BG = "#0A090F"          # Deep cosmic black-violet
        self.COLOR_SIDEBAR = "#13111C"     # Sleek sidebar black-purple
        self.COLOR_CARD = "#1C182A"        # High contrast card background
        self.COLOR_ACCENT = "#B18CFE"      # Vibrant Lavender
        self.COLOR_ACCENT_HOVER = "#C8AEFF" # Glowing light Lavender
        self.COLOR_TEXT = "#F5F2FA"        # Bright lavender-white
        self.COLOR_MUTED = "#9F98B2"       # Muted gray-purple
        self.COLOR_DANGER = "#FF6B6B"      # Error/Danger Red
        self.COLOR_WARNING = "#FFD166"     # Warning Yellow

        # Apply root background
        self.root.configure(fg_color=self.COLOR_BG)
        
        # Initialize pygame mixer
        mixer.init()
        
        # Music Player Variables
        self.playlist = []                 # List of absolute filepaths
        self.playlist_metadata = []        # List of metadata dictionaries
        self.current_song_index = -1
        self.state = STATE_STOPPED
        self.shuffle_mode = False
        self.repeat_mode = "none"          # none, all, one
        self.volume = 0.7                  # Default volume 70%
        self.is_muted = False
        self.volume_before_mute = 0.7
        
        # Playback Timing Variables
        self.song_duration = 0.0
        self.current_time = 0.0
        self.last_update_time = 0.0
        self.is_dragging = False
        
        # Animation Variables
        self.stylus_angle = -0.2           # Pivot angle for stylus arm
        self.vinyl_rotation_angle = 0.0    # Rotation angle for vinyl record
        self.play_history = []             # History stack for back navigation
        self.shuffle_queue = []            # Pop list for shuffle queue
        
        # Build UI Layout
        self.setup_ui()
        
        # Start core periodic loops
        self.update_loop()
        self.animate_visualizer()
        self.animate_vinyl()
        
    def setup_ui(self):
        # Configure Grid Layout
        self.root.grid_columnconfigure(0, weight=0, minsize=300) # Sidebar
        self.root.grid_columnconfigure(1, weight=1)              # Now Playing
        self.root.grid_rowconfigure(0, weight=1)
        
        # ---------------------------------------------------------
        # LEFT SIDEBAR: Playlist & Queue
        # ---------------------------------------------------------
        self.sidebar_frame = ctk.CTkFrame(
            self.root, 
            fg_color=self.COLOR_SIDEBAR, 
            corner_radius=0,
            border_width=1,
            border_color="#1E1B28"
        )
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(2, weight=1) # Scroll frame expands
        
        # Title/Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="💜 A E T H E R I S",
            font=("Poppins", 20, "bold"),
            text_color=self.COLOR_ACCENT
        )
        self.logo_label.grid(row=0, column=0, pady=(25, 15), padx=20, sticky="w")
        
        # Search Box
        self.search_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.search_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Search tracks...",
            font=("Poppins", 11),
            fg_color="#1A1824",
            border_color="#2A243D",
            text_color=self.COLOR_TEXT,
            placeholder_text_color=self.COLOR_MUTED,
            height=35
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.on_search_keypress)
        
        # Playlist Queue Scrollable Frame
        self.playlist_scroll_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame,
            fg_color="transparent",
            scrollbar_button_color="#2A243D",
            scrollbar_button_hover_color=self.COLOR_ACCENT
        )
        self.playlist_scroll_frame.grid(row=2, column=0, padx=10, pady=0, sticky="nsew")
        
        # Sidebar Action Buttons
        self.sidebar_actions = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_actions.grid(row=3, column=0, padx=15, pady=20, sticky="ew")
        self.sidebar_actions.grid_columnconfigure((0, 1), weight=1)
        
        # Button styling helper
        action_btn_style = {
            "font": ("Poppins", 11, "bold"),
            "fg_color": "#1C182A",
            "text_color": self.COLOR_TEXT,
            "border_color": "#2A243D",
            "border_width": 1,
            "hover_color": "#2A243D",
            "height": 38
        }
        
        self.add_files_btn = ctk.CTkButton(
            self.sidebar_actions, 
            text="➕ Files", 
            command=self.add_files, 
            **action_btn_style
        )
        self.add_files_btn.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        self.add_dir_btn = ctk.CTkButton(
            self.sidebar_actions, 
            text="📁 Folder", 
            command=self.add_folder, 
            **action_btn_style
        )
        self.add_dir_btn.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🗑️ Clear Queue",
            font=("Poppins", 11, "bold"),
            fg_color="transparent",
            text_color=self.COLOR_DANGER,
            hover_color="#301414",
            height=32,
            command=self.clear_playlist
        )
        self.clear_btn.grid(row=4, column=0, padx=15, pady=(0, 20), sticky="ew")
        
        # ---------------------------------------------------------
        # RIGHT PANEL: Now Playing & Controls
        # ---------------------------------------------------------
        self.main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1) # Main section
        self.main_frame.grid_rowconfigure(1, weight=0) # Controls footer
        
        # Main Info Frame
        self.info_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_panel.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        self.info_panel.grid_columnconfigure(0, weight=1)
        self.info_panel.grid_rowconfigure(1, weight=1) # Center album art
        
        # Header text
        self.status_header = ctk.CTkLabel(
            self.info_panel,
            text="N O W   P L A Y I N G",
            font=("Poppins", 10, "bold"),
            text_color=self.COLOR_MUTED
        )
        self.status_header.grid(row=0, column=0, pady=(5, 10))
        
        # Center Vinyl Display Frame
        self.vinyl_frame = ctk.CTkFrame(
            self.info_panel,
            fg_color=self.COLOR_CARD,
            corner_radius=20,
            border_width=1,
            border_color="#2A243D"
        )
        self.vinyl_frame.grid(row=1, column=0, pady=10, padx=40, sticky="nsew")
        self.vinyl_frame.grid_rowconfigure(0, weight=1)
        self.vinyl_frame.grid_columnconfigure(0, weight=1)
        
        # Vinyl Record Canvas
        self.canvas = tk.Canvas(
            self.vinyl_frame,
            width=210,
            height=210,
            bg=self.COLOR_CARD,
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(row=0, column=0, pady=20)
        
        # Song Info & Visualizer Container
        self.song_meta_container = ctk.CTkFrame(self.info_panel, fg_color="transparent")
        self.song_meta_container.grid(row=2, column=0, pady=15, sticky="ew")
        self.song_meta_container.grid_columnconfigure(0, weight=1)
        
        self.song_title_lbl = ctk.CTkLabel(
            self.song_meta_container,
            text="No track selected",
            font=("Poppins", 18, "bold"),
            text_color=self.COLOR_TEXT,
            anchor="center"
        )
        self.song_title_lbl.grid(row=0, column=0, sticky="ew")
        
        self.song_artist_lbl = ctk.CTkLabel(
            self.song_meta_container,
            text="Import music to begin",
            font=("Poppins", 12),
            text_color=self.COLOR_MUTED,
            anchor="center"
        )
        self.song_artist_lbl.grid(row=1, column=0, sticky="ew", pady=(2, 10))
        
        # Equalizer Visualizer Frame (placed below labels)
        self.visualizer_frame = ctk.CTkFrame(self.song_meta_container, fg_color="transparent", height=40)
        self.visualizer_frame.grid(row=2, column=0, pady=5)
        self.visualizer_frame.grid_propagate(False)
        
        self.visualizer_bars = []
        for i in range(16):
            bar = ctk.CTkFrame(
                self.visualizer_frame,
                width=6,
                height=5,
                fg_color=self.COLOR_ACCENT,
                corner_radius=3
            )
            bar.pack(side="left", padx=2, fill="y", anchor="s")
            self.visualizer_bars.append(bar)
            
        # ---------------------------------------------------------
        # BOTTOM CONTROLS FOOTER
        # ---------------------------------------------------------
        self.controls_panel = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.COLOR_CARD,
            corner_radius=0,
            border_width=1,
            border_color="#2A243D"
        )
        self.controls_panel.grid(row=1, column=0, sticky="ew")
        self.controls_panel.grid_columnconfigure(0, weight=1)
        
        # 1. Progress Bar / Slider Row
        self.progress_frame = ctk.CTkFrame(self.controls_panel, fg_color="transparent")
        self.progress_frame.grid(row=0, column=0, padx=25, pady=(15, 5), sticky="ew")
        self.progress_frame.grid_columnconfigure(1, weight=1)
        
        self.time_elapsed_label = ctk.CTkLabel(
            self.progress_frame,
            text="00:00",
            font=("Consolas", 11),
            text_color=self.COLOR_MUTED,
            width=40
        )
        self.time_elapsed_label.grid(row=0, column=0, padx=(0, 10))
        
        self.progress_slider = ctk.CTkSlider(
            self.progress_frame,
            from_=0,
            to=100,
            height=12,
            fg_color="#13111C",
            progress_color=self.COLOR_ACCENT,
            button_color=self.COLOR_ACCENT,
            button_hover_color=self.COLOR_ACCENT_HOVER,
            command=self.on_slider_drag
        )
        self.progress_slider.grid(row=0, column=1, sticky="ew")
        self.progress_slider.set(0)
        self.progress_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        
        self.time_total_label = ctk.CTkLabel(
            self.progress_frame,
            text="00:00",
            font=("Consolas", 11),
            text_color=self.COLOR_MUTED,
            width=40
        )
        self.time_total_label.grid(row=0, column=2, padx=(10, 0))
        
        # 2. Main Playback Controls Bar
        self.button_dock = ctk.CTkFrame(self.controls_panel, fg_color="transparent")
        self.button_dock.grid(row=1, column=0, padx=25, pady=(5, 10), sticky="ew")
        self.button_dock.grid_columnconfigure((0, 4), weight=1) # Side padding columns
        
        # Central Control Buttons Subframe
        self.center_controls = ctk.CTkFrame(self.button_dock, fg_color="transparent")
        self.center_controls.grid(row=0, column=2)
        
        # Control button styling configs
        small_btn_cfg = {
            "width": 34,
            "height": 34,
            "corner_radius": 17,
            "fg_color": "transparent",
            "text_color": self.COLOR_MUTED,
            "hover_color": "#2A243D",
            "font": ("Poppins", 15)
        }
        
        self.shuffle_btn = ctk.CTkButton(
            self.center_controls, 
            text="🔀", 
            command=self.toggle_shuffle, 
            **small_btn_cfg
        )
        self.shuffle_btn.grid(row=0, column=0, padx=8)
        
        self.prev_btn = ctk.CTkButton(
            self.center_controls, 
            text="⏮", 
            command=self.prev_song, 
            **small_btn_cfg
        )
        self.prev_btn.grid(row=0, column=1, padx=8)
        
        # Main Play Button (Larger & Prominent)
        self.play_btn = ctk.CTkButton(
            self.center_controls,
            text="▶",
            font=("Poppins", 18),
            width=48,
            height=48,
            corner_radius=24,
            fg_color=self.COLOR_ACCENT,
            text_color=self.COLOR_BG,
            hover_color=self.COLOR_ACCENT_HOVER,
            command=self.toggle_play_pause
        )
        self.play_btn.grid(row=0, column=2, padx=12)
        
        self.next_btn = ctk.CTkButton(
            self.center_controls, 
            text="⏭", 
            command=self.next_song, 
            **small_btn_cfg
        )
        self.next_btn.grid(row=0, column=3, padx=8)
        
        self.repeat_btn = ctk.CTkButton(
            self.center_controls, 
            text="🔁", 
            command=self.cycle_repeat, 
            **small_btn_cfg
        )
        self.repeat_btn.grid(row=0, column=4, padx=8)
        
        # Volume Section (Docked to the Right)
        self.volume_dock = ctk.CTkFrame(self.button_dock, fg_color="transparent")
        self.volume_dock.grid(row=0, column=3, sticky="e")
        
        self.volume_btn = ctk.CTkButton(
            self.volume_dock,
            text="🔊",
            font=("Poppins", 12),
            width=28,
            height=28,
            fg_color="transparent",
            text_color=self.COLOR_TEXT,
            hover_color="#2A243D",
            command=self.toggle_mute
        )
        self.volume_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.volume_slider = ctk.CTkSlider(
            self.volume_dock,
            from_=0,
            to=100,
            width=90,
            height=10,
            fg_color="#13111C",
            progress_color=self.COLOR_ACCENT,
            button_color=self.COLOR_ACCENT,
            button_hover_color=self.COLOR_ACCENT_HOVER,
            command=self.on_volume_change
        )
        self.volume_slider.grid(row=0, column=1)
        self.volume_slider.set(self.volume * 100)
        
        # Status Label Bar
        self.status_label = ctk.CTkLabel(
            self.controls_panel,
            text="Aetheris Premium 💜",
            font=("Poppins", 10, "italic"),
            text_color=self.COLOR_MUTED
        )
        self.status_label.grid(row=2, column=0, pady=(5, 12))

    # ---------------------------------------------------------
    # PLAYBACK & METADATA LOGIC
    # ---------------------------------------------------------
    
    def extract_metadata(self, filepath):
        """Reads ID3/audio metadata tags, utilizing fallbacks for errors."""
        title = os.path.splitext(os.path.basename(filepath))[0]
        artist = "Unknown Artist"
        duration = 0.0
        
        # Clean title strings that look like "01 - Title" or "01. Title"
        # by removing starting digits/dashes
        temp_title = title
        for i, char in enumerate(temp_title):
            if char.isdigit() or char in (' ', '-', '.', '_'):
                continue
            else:
                if i > 0:
                    temp_title = temp_title[i:]
                break
        
        try:
            audio = mutagen.File(filepath)
            if audio is not None:
                duration = audio.info.length
                
                # Check MP3 tags
                if filepath.lower().endswith('.mp3'):
                    try:
                        from mutagen.easyid3 import EasyID3
                        easy_audio = EasyID3(filepath)
                        if 'title' in easy_audio:
                            title = easy_audio['title'][0]
                        if 'artist' in easy_audio:
                            artist = easy_audio['artist'][0]
                    except Exception:
                        # Fallback to key index reading
                        if 'TIT2' in audio:
                            title = str(audio['TIT2'])
                        if 'TPE1' in audio:
                            artist = str(audio['TPE1'])
                # Check Ogg / FLAC tags
                elif hasattr(audio, 'tags') and audio.tags:
                    if 'title' in audio.tags:
                        title = audio.tags['title'][0]
                    if 'artist' in audio.tags:
                        artist = audio.tags['artist'][0]
        except Exception as e:
            print(f"Error parsing metadata for {filepath}: {e}")
            
        # Fallback for duration if mutagen failed to calculate length
        if duration <= 0.0:
            try:
                sound = mixer.Sound(filepath)
                duration = sound.get_length()
            except Exception:
                duration = 180.0  # Fallback guess 3 mins
                
        return {
            "path": filepath,
            "title": title,
            "artist": artist,
            "duration": duration,
            "formatted_duration": self.format_time(duration)
        }
        
    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def add_files(self):
        filepaths = filedialog.askopenfilenames(
            title="Select Music Files",
            filetypes=(("Audio Files", "*.mp3 *.wav *.ogg *.flac"), ("All Files", "*.*"))
        )
        if filepaths:
            for path in filepaths:
                self.add_song_by_path(path)
            self.update_playlist_ui(self.search_entry.get())
            if self.current_song_index == -1:
                self.select_song(0)

    def add_folder(self):
        dirpath = filedialog.askdirectory(title="Select Music Folder")
        if dirpath:
            supported_exts = ('.mp3', '.wav', '.ogg', '.flac')
            added_count = 0
            for root_dir, _, files in os.walk(dirpath):
                for file in files:
                    if file.lower().endswith(supported_exts):
                        filepath = os.path.join(root_dir, file)
                        self.add_song_by_path(filepath)
                        added_count += 1
            if added_count > 0:
                self.update_playlist_ui(self.search_entry.get())
                if self.current_song_index == -1:
                    self.select_song(0)

    def add_song_by_path(self, filepath):
        normalized_path = os.path.abspath(filepath)
        if normalized_path not in self.playlist:
            self.playlist.append(normalized_path)
            metadata = self.extract_metadata(normalized_path)
            self.playlist_metadata.append(metadata)

    def clear_playlist(self):
        self.stop_song()
        self.playlist.clear()
        self.playlist_metadata.clear()
        self.current_song_index = -1
        self.play_history.clear()
        self.shuffle_queue.clear()
        
        self.song_title_lbl.configure(text="No track selected")
        self.song_artist_lbl.configure(text="Import music to begin")
        self.time_total_label.configure(text="00:00")
        self.time_elapsed_label.configure(text="00:00")
        self.progress_slider.set(0)
        self.status_label.configure(text="Queue Cleared 🗑️", text_color=self.COLOR_MUTED)
        
        self.update_playlist_ui()

    def remove_song(self, index):
        if index == self.current_song_index:
            self.stop_song()
            self.current_song_index = -1
            
        self.playlist.pop(index)
        self.playlist_metadata.pop(index)
        
        if self.current_song_index > index:
            self.current_song_index -= 1
            
        # Clean history items pointing above index
        self.play_history = [i - 1 if i > index else i for i in self.play_history if i != index]
        self.shuffle_queue = [i - 1 if i > index else i for i in self.shuffle_queue if i != index]
        
        self.update_playlist_ui(self.search_entry.get())
        if self.playlist and self.current_song_index == -1:
            self.select_song(0)

    # ---------------------------------------------------------
    # PLAYBACK CONTROL WORKFLOWS
    # ---------------------------------------------------------

    def select_song(self, index):
        if index < 0 or index >= len(self.playlist):
            return
        self.current_song_index = index
        meta = self.playlist_metadata[index]
        
        self.song_title_lbl.configure(text=meta["title"])
        self.song_artist_lbl.configure(text=meta["artist"])
        self.time_total_label.configure(text=meta["formatted_duration"])
        self.time_elapsed_label.configure(text="00:00")
        self.progress_slider.set(0)
        self.song_duration = meta["duration"]
        self.current_time = 0.0
        
        self.update_playlist_ui(self.search_entry.get())

    def play_selected_song(self, index):
        if index < 0 or index >= len(self.playlist):
            return
            
        if self.current_song_index != -1 and self.current_song_index != index:
            self.play_history.append(self.current_song_index)
            
        self.current_song_index = index
        filepath = self.playlist[index]
        meta = self.playlist_metadata[index]
        
        self.song_title_lbl.configure(text=meta["title"])
        self.song_artist_lbl.configure(text=meta["artist"])
        self.time_total_label.configure(text=meta["formatted_duration"])
        self.time_elapsed_label.configure(text="00:00")
        self.progress_slider.set(0)
        
        self.song_duration = meta["duration"]
        self.current_time = 0.0
        self.last_update_time = time.time()
        
        try:
            mixer.music.load(filepath)
            # Apply volume setting
            mixer.music.set_volume(0.0 if self.is_muted else self.volume)
            mixer.music.play()
            self.state = STATE_PLAYING
            self.play_btn.configure(text="⏸")
            self.status_label.configure(text="Playing Now 💜", text_color=self.COLOR_ACCENT)
        except Exception as e:
            self.status_label.configure(text="Error playing file! ⚠️", text_color=self.COLOR_DANGER)
            print(f"Playback error: {e}")
            
        self.update_playlist_ui(self.search_entry.get())

    def toggle_play_pause(self):
        if not self.playlist:
            self.status_label.configure(text="Queue is empty! 🎵", text_color=self.COLOR_WARNING)
            return
            
        if self.state == STATE_STOPPED:
            idx = self.current_song_index if self.current_song_index != -1 else 0
            self.play_selected_song(idx)
        elif self.state == STATE_PLAYING:
            mixer.music.pause()
            self.state = STATE_PAUSED
            self.play_btn.configure(text="▶")
            self.status_label.configure(text="Paused ⏸", text_color=self.COLOR_MUTED)
        elif self.state == STATE_PAUSED:
            mixer.music.unpause()
            self.state = STATE_PLAYING
            self.last_update_time = time.time()
            self.play_btn.configure(text="⏸")
            self.status_label.configure(text="Playing Now 💜", text_color=self.COLOR_ACCENT)

    def stop_song(self):
        mixer.music.stop()
        self.state = STATE_STOPPED
        self.current_time = 0.0
        self.progress_slider.set(0)
        self.time_elapsed_label.configure(text="00:00")
        self.play_btn.configure(text="▶")
        self.status_label.configure(text="Stopped ⏹", text_color=self.COLOR_DANGER)

    def get_next_song_index(self):
        if not self.playlist:
            return -1
            
        if self.repeat_mode == "one":
            return self.current_song_index if self.current_song_index != -1 else 0
            
        if self.shuffle_mode:
            # Rebuild shuffle stack if playlist length changed or empty
            if not self.shuffle_queue or len(self.shuffle_queue) != len(self.playlist):
                self.shuffle_queue = list(range(len(self.playlist)))
                if self.current_song_index in self.shuffle_queue:
                    self.shuffle_queue.remove(self.current_song_index)
                random.shuffle(self.shuffle_queue)
                
            if self.shuffle_queue:
                return self.shuffle_queue.pop(0)
            else:
                return 0
        else:
            if self.current_song_index == -1:
                return 0
            next_idx = self.current_song_index + 1
            if next_idx >= len(self.playlist):
                return 0 if self.repeat_mode == "all" else -1
            return next_idx

    def get_prev_song_index(self):
        if not self.playlist:
            return -1
            
        if self.play_history:
            return self.play_history.pop()
            
        if self.shuffle_mode:
            return random.randint(0, len(self.playlist) - 1)
        else:
            if self.current_song_index <= 0:
                return len(self.playlist) - 1 if self.repeat_mode == "all" else 0
            return self.current_song_index - 1

    def next_song(self):
        if not self.playlist:
            return
        next_idx = self.get_next_song_index()
        if next_idx != -1:
            self.play_selected_song(next_idx)
        else:
            # Loop around if next is forced
            self.play_selected_song(0)

    def prev_song(self):
        if not self.playlist:
            return
        prev_idx = self.get_prev_song_index()
        if prev_idx != -1:
            self.play_selected_song(prev_idx)

    # ---------------------------------------------------------
    # VOLUME & SEEK CONTROLS
    # ---------------------------------------------------------

    def on_volume_change(self, val):
        self.volume = val / 100.0
        if self.is_muted and val > 0:
            self.is_muted = False
            self.volume_btn.configure(text="🔊")
        mixer.music.set_volume(self.volume)

    def toggle_mute(self):
        if self.is_muted:
            self.is_muted = False
            mixer.music.set_volume(self.volume)
            self.volume_btn.configure(text="🔊")
            self.volume_slider.set(self.volume * 100)
            self.status_label.configure(text="Volume Restored 🔊", text_color=self.COLOR_ACCENT)
        else:
            self.is_muted = True
            self.volume_before_mute = self.volume
            mixer.music.set_volume(0.0)
            self.volume_btn.configure(text="🔇")
            self.volume_slider.set(0)
            self.status_label.configure(text="Muted 🔇", text_color=self.COLOR_MUTED)

    def on_slider_drag(self, val):
        self.is_dragging = True
        elapsed_seconds = (val / 100.0) * self.song_duration
        self.time_elapsed_label.configure(text=self.format_time(elapsed_seconds))

    def on_slider_release(self, event):
        if not self.playlist or self.current_song_index == -1:
            self.progress_slider.set(0)
            self.is_dragging = False
            return
            
        seek_time = (self.progress_slider.get() / 100.0) * self.song_duration
        self.current_time = seek_time
        self.last_update_time = time.time()
        
        try:
            # Seek using starting point argument
            mixer.music.play(start=seek_time)
            if self.state == STATE_PAUSED:
                # Keep paused after seek
                mixer.music.pause()
            else:
                self.state = STATE_PLAYING
                self.play_btn.configure(text="⏸")
        except Exception as e:
            print(f"Error seeking: {e}")
            # Fallback re-play
            mixer.music.play()
            
        self.is_dragging = False

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_btn.configure(text_color=self.COLOR_ACCENT, fg_color="#2A243D")
            self.status_label.configure(text="Shuffle Queue Active 🔀", text_color=self.COLOR_ACCENT)
        else:
            self.shuffle_btn.configure(text_color=self.COLOR_MUTED, fg_color="transparent")
            self.status_label.configure(text="Shuffle Queue Inactive ➡️", text_color=self.COLOR_MUTED)

    def cycle_repeat(self):
        if self.repeat_mode == "none":
            self.repeat_mode = "all"
            self.repeat_btn.configure(text="🔁", text_color=self.COLOR_ACCENT, fg_color="#2A243D")
            self.status_label.configure(text="Repeating Playlist 🔁", text_color=self.COLOR_ACCENT)
        elif self.repeat_mode == "all":
            self.repeat_mode = "one"
            self.repeat_btn.configure(text="🔂", text_color=self.COLOR_ACCENT, fg_color="#2A243D")
            self.status_label.configure(text="Repeating Track One 🔂", text_color=self.COLOR_ACCENT)
        else:
            self.repeat_mode = "none"
            self.repeat_btn.configure(text="🔁", text_color=self.COLOR_MUTED, fg_color="transparent")
            self.status_label.configure(text="Loop Modes Off ➡️", text_color=self.COLOR_MUTED)

    # ---------------------------------------------------------
    # DYNAMIC SEARCH & UI DRAWING
    # ---------------------------------------------------------

    def on_search_keypress(self, event):
        self.update_playlist_ui(self.search_entry.get())

    def update_playlist_ui(self, filter_text=""):
        # Clear existing elements
        for widget in self.playlist_scroll_frame.winfo_children():
            widget.destroy()
            
        filter_text = filter_text.lower().strip()
        
        for idx, meta in enumerate(self.playlist_metadata):
            title = meta["title"]
            artist = meta["artist"]
            
            # Filter matches
            if filter_text and filter_text not in title.lower() and filter_text not in artist.lower():
                continue
                
            is_active = (idx == self.current_song_index)
            
            # Row container
            row = ctk.CTkFrame(
                self.playlist_scroll_frame,
                fg_color="#1E1B28" if is_active else "transparent",
                corner_radius=8,
                height=48
            )
            row.pack(fill="x", pady=3, padx=2)
            row.pack_propagate(False)
            
            # Double click binding context
            row.bind("<Double-Button-1>", lambda e, i=idx: self.play_selected_song(i))
            
            # Hover effect helper functions
            def bind_hover(target_row, idx_val):
                target_row.bind("<Enter>", lambda e: self.on_row_enter(e, target_row, idx_val))
                target_row.bind("<Leave>", lambda e: self.on_row_leave(e, target_row, idx_val))
                
            bind_hover(row, idx)
            
            # Track Index Number
            idx_lbl = ctk.CTkLabel(
                row,
                text=f"{idx+1:02d}",
                font=("Poppins", 10, "bold"),
                text_color=self.COLOR_ACCENT if is_active else self.COLOR_MUTED,
                width=30
            )
            idx_lbl.pack(side="left", padx=(10, 5))
            
            # Track Text Metadata Frame
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5)
            
            song_title = ctk.CTkLabel(
                info_frame,
                text=title,
                font=("Poppins", 11, "bold" if is_active else "normal"),
                text_color=self.COLOR_TEXT if is_active else "#EDE6FA",
                anchor="w"
            )
            song_title.pack(fill="x", side="top", pady=(4, 0))
            
            song_artist = ctk.CTkLabel(
                info_frame,
                text=artist,
                font=("Poppins", 9),
                text_color=self.COLOR_ACCENT if is_active else self.COLOR_MUTED,
                anchor="w"
            )
            song_artist.pack(fill="x", side="top")
            
            # Remove Button
            del_btn = ctk.CTkButton(
                row,
                text="×",
                font=("Poppins", 14),
                width=24,
                height=24,
                fg_color="transparent",
                text_color=self.COLOR_MUTED,
                hover_color=self.COLOR_DANGER,
                command=lambda i=idx: self.remove_song(i)
            )
            del_btn.pack(side="right", padx=(5, 10))
            
            # Bind child items for easy double-clicking
            for child in (idx_lbl, info_frame, song_title, song_artist):
                child.bind("<Double-Button-1>", lambda e, i=idx: self.play_selected_song(i))
                
    def on_row_enter(self, event, row_frame, idx):
        if idx != self.current_song_index:
            row_frame.configure(fg_color="#181522")

    def on_row_leave(self, event, row_frame, idx):
        if idx != self.current_song_index:
            row_frame.configure(fg_color="transparent")

    # ---------------------------------------------------------
    # CORE TIMER UPDATES & ANIMATION SCHEDULERS
    # ---------------------------------------------------------

    def update_loop(self):
        """Standard timer updater for calculating elapsed track time."""
        if self.state == STATE_PLAYING:
            if not mixer.music.get_busy():
                # Natural track ending reached
                self.on_song_end()
            else:
                # Increment time delta
                dt = time.time() - self.last_update_time
                self.current_time += dt
                self.last_update_time = time.time()
                
                # Cap progress
                if self.current_time > self.song_duration:
                    self.current_time = self.song_duration
                    
                # Update visual labels
                if not self.is_dragging:
                    self.time_elapsed_label.configure(text=self.format_time(self.current_time))
                    if self.song_duration > 0:
                        pct = (self.current_time / self.song_duration) * 100
                        self.progress_slider.set(pct)
                        
        self.root.after(100, self.update_loop)

    def on_song_end(self):
        next_idx = self.get_next_song_index()
        if next_idx != -1:
            self.play_selected_song(next_idx)
        else:
            self.stop_song()

    def animate_visualizer(self):
        """Animates graphic visualizer heights based on playback state."""
        if self.state == STATE_PLAYING:
            for bar in self.visualizer_bars:
                # Generate dynamic bounce heights
                h = random.randint(8, 38)
                bar.configure(height=h)
        else:
            # Settle bars smoothly down when paused/stopped
            for bar in self.visualizer_bars:
                curr_h = bar.cget("height")
                if curr_h > 5:
                    bar.configure(height=max(5, curr_h - 4))
                    
        self.root.after(80, self.animate_visualizer)

    def animate_vinyl(self):
        """Handles vinyl graphic rendering and stylus arm movement."""
        # Update stylus angle based on playing state
        if self.state == STATE_PLAYING:
            self.stylus_angle = min(0.25, self.stylus_angle + 0.03)
            # Increment rotation angle
            self.vinyl_rotation_angle = (self.vinyl_rotation_angle + 0.08) % (2 * math.pi)
        elif self.state == STATE_PAUSED:
            self.stylus_angle = min(0.25, self.stylus_angle + 0.03)  # Stylus stays on record
        else:
            # Liftoff stylus when stopped
            self.stylus_angle = max(-0.25, self.stylus_angle - 0.03)
            
        self.draw_vinyl()
        self.root.after(40, self.animate_vinyl)

    def draw_vinyl(self):
        """Draws the fully geometric rendering of a vinyl record & stylus."""
        self.canvas.delete("all")
        
        cx, cy = 105, 105  # Canvas Center
        r_outer = 85
        
        # 1. Draw Vinyl Outer Shadow Rim
        self.canvas.create_oval(
            cx - r_outer - 2, cy - r_outer - 2, 
            cx + r_outer + 2, cy + r_outer + 2, 
            fill="#09080C", outline="#1F1B2B", width=2
        )
        
        # 2. Draw Vinyl Core Body
        self.canvas.create_oval(
            cx - r_outer, cy - r_outer, 
            cx + r_outer, cy + r_outer, 
            fill="#121016", outline="#2F293F", width=1
        )
        
        # 3. Draw Grooves (Concentric Circles)
        for r in [75, 68, 60, 52, 45, 38]:
            self.canvas.create_oval(
                cx - r, cy - r, 
                cx + r, cy + r, 
                outline="#1C1A23", width=1
            )
            
        # 4. Draw Center Record Label (Lavender Disk)
        r_label = 26
        self.canvas.create_oval(
            cx - r_label, cy - r_label, 
            cx + r_label, cy + r_label, 
            fill=self.COLOR_ACCENT, outline=""
        )
        
        # 5. Draw Spinning Marker Dot on Label (shows rotation)
        marker_r = 17
        mx = cx + marker_r * math.cos(self.vinyl_rotation_angle)
        my = cy + marker_r * math.sin(self.vinyl_rotation_angle)
        self.canvas.create_oval(
            mx - 2.5, my - 2.5, 
            mx + 2.5, my + 2.5, 
            fill=self.COLOR_BG, outline=""
        )
        
        # 6. Center Hole
        self.canvas.create_oval(
            cx - 4, cy - 4, 
            cx + 4, cy + 4, 
            fill=self.COLOR_CARD, outline=""
        )
        
        # 7. Draw Stylus Arm
        # Pivot point (Top Right)
        px, py = 180, 25
        theta = self.stylus_angle
        
        # Arm geometry (Pivot -> Elbow -> Needle Cartridge)
        # Relative vectors at 0-angle: elbow is (-20, 65), cartridge is (-65, 95)
        ex = px + (-20 * math.cos(theta) - 65 * math.sin(theta))
        ey = py + (-20 * math.sin(theta) + 65 * math.cos(theta))
        cx_cart = px + (-60 * math.cos(theta) - 100 * math.sin(theta))
        cy_cart = py + (-60 * math.sin(theta) + 100 * math.cos(theta))
        
        # Pivot Base representation
        self.canvas.create_oval(
            px - 12, py - 12, 
            px + 12, py + 12, 
            fill="#231F30", outline="#3D3556", width=2
        )
        
        # Pivot Core
        self.canvas.create_oval(
            px - 5, py - 5, 
            px + 5, py + 5, 
            fill=self.COLOR_ACCENT, outline=""
        )
        
        # Tone Arm Lines
        self.canvas.create_line(
            px, py, ex, ey, 
            fill="#AFA9C0", width=4, capstyle="round"
        )
        self.canvas.create_line(
            ex, ey, cx_cart, cy_cart, 
            fill="#C9C4D5", width=3, capstyle="round"
        )
        
        # Cartridge Head
        self.canvas.create_rectangle(
            cx_cart - 4, cy_cart - 4, 
            cx_cart + 4, cy_cart + 4, 
            fill=self.COLOR_ACCENT, outline=self.COLOR_TEXT, width=1
        )

# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    root = ctk.CTk()
    app = AetherisMusicPlayer(root)
    root.mainloop()