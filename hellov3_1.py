# -*- coding: utf-8 -*-
"""
Voice-controlled assistant with Arduino integration.
Optimized and refactored for stability and clarity.

Original author: anith
Refactored: 2026-02-25
"""

import os
import re
import sys
import glob
import random
import signal
import serial
import tempfile
import pyttsx3
import pygame
import PyPDF2
import requests
import datetime as dt
import speech_recognition as sr

# ==========================================
# CONFIGURATION
# ==========================================

VA_NAME = "atom"
ARDUINO_PORT = "COM6"
ARDUINO_BAUD = 9600

DUCKDUCKGO_URL = "https://api.duckduckgo.com/"
WEATHER_API_KEY = "ac8d888b5eebbe9e131e7daf96e3dfbc"
WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"

SPEECH_RATE = 150
VOICE_INDEX = 1

MIC_INDEX = None

MUSIC_FOLDERS = [
    os.path.expanduser("~\\Downloads"),
    os.path.expanduser("~\\Music"),
    os.path.expanduser("~\\OneDrive\\Downloads"),
    os.path.expanduser("~\\Desktop"),
]

MUSIC_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma", ".aac")

TEMP_MUSIC_DIR = os.path.join(tempfile.gettempdir(), "atom_music")
os.makedirs(TEMP_MUSIC_DIR, exist_ok=True)

ARDUINO_COMMANDS = {
    "shake_hand": b"9",
    "walk":       b"8",
    "back":       b"7",
    "left":       b"6",
    "right":      b"5",
    "led_on":     b"0",
    "led_off":    b"1",
}

SEARCH_KEYWORDS = (
    "search for", "google", "who is", "which is", "what is", "tell me about",
)


def _safe_eval(expr: str):
    import ast, operator
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg,
    }
    def _eval_node(node):
        if isinstance(node, ast.Expression): return _eval_node(node.body)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)): return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](_eval_node(node.left), _eval_node(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](_eval_node(node.operand))
        else: raise ValueError(f"Unsupported expression: {ast.dump(node)}")
    return _eval_node(ast.parse(expr, mode="eval"))


class VoiceAssistant:
    def __init__(self):
        self.listener = sr.Recognizer()
        self.listener.energy_threshold = 100
        self.listener.dynamic_energy_threshold = True
        self.listener.pause_threshold = 1.0
        try:
            mic = self._get_microphone()
            with mic as source:
                self.listener.adjust_for_ambient_noise(source, duration=2)
        except Exception as e:
            print(f"[WARN] Microphone calibration failed: {e}")
        self.arduino = None
        try:
            self.arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD)
        except Exception as e:
            print(f"[WARN] Arduino not available: {e}")
        self.ytdlp_available = False
        try:
            import yt_dlp
            self.ytdlp_available = True
        except ImportError:
            pass
        self.running = True
        self.music_playing = False
        self.current_temp_file = None

    @staticmethod
    def _get_microphone():
        if MIC_INDEX is not None: return sr.Microphone(device_index=MIC_INDEX)
        return sr.Microphone()

    def speak(self, text: str):
        print(f"[{VA_NAME}] {text}")
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", SPEECH_RATE)
            voices = engine.getProperty("voices")
            if VOICE_INDEX < len(voices): engine.setProperty("voice", voices[VOICE_INDEX].id)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"[ERROR] Speech failed: {e}")

    def send_arduino(self, command_key: str):
        if self.arduino and command_key in ARDUINO_COMMANDS:
            try: self.arduino.write(ARDUINO_COMMANDS[command_key])
            except serial.SerialException as e: print(f"[ERROR] Arduino write failed: {e}")

    def listen(self) -> str:
        try:
            mic = self._get_microphone()
            with mic as source:
                self.send_arduino("led_on")
                voice = self.listener.listen(source, timeout=8, phrase_time_limit=15)
                command = self.listener.recognize_google(voice).lower()
                return command
        except (sr.WaitTimeoutError, sr.UnknownValueError): return ""
        except Exception as e:
            print(f"[ERROR] Listening failed: {e}"); return ""
        finally: self.send_arduino("led_off")

    def handle_command(self, cmd: str):
        if not cmd: return
        if cmd in ("stop", "quit", "exit"):
            self.stop_music(); self.speak("Goodbye!"); self.running = False
        elif "stop music" in cmd: self.stop_music()
        elif "pause" in cmd: self.pause_music()
        elif "resume" in cmd: self.resume_music()
        elif "weather in" in cmd:
            city = cmd.split("weather in", 1)[1].strip()
            self.speak(self.get_weather(city))
        elif "play" in cmd: self.handle_play_command(cmd)
        elif "time" in cmd: self.speak(f"The time is {dt.datetime.now().strftime('%I:%M %p')}")
        elif any(kw in cmd for kw in SEARCH_KEYWORDS):
            self.speak(self.search_duckduckgo(cmd))
        elif "shake hand" in cmd: self.send_arduino("shake_hand"); self.speak("Shaking hand.")
        elif "walk" in cmd: self.send_arduino("walk"); self.speak("Walking.")
        elif "left" in cmd: self.send_arduino("left"); self.speak("Turning left.")
        elif "right" in cmd: self.send_arduino("right"); self.speak("Turning right.")
        elif "back" in cmd: self.send_arduino("back"); self.speak("Moving back.")
        else: self.speak("Sorry, I didn't understand that.")

    def get_weather(self, city):
        try:
            r = requests.get(WEATHER_URL, params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"}, timeout=10)
            d = r.json()
            if d.get("cod") == 200:
                return f"Weather in {d['name']}: {d['weather'][0]['description']}, {d['main']['temp']}°C"
            return "Couldn't fetch weather."
        except: return "Weather fetch failed."

    def search_duckduckgo(self, query):
        try:
            r = requests.get(DUCKDUCKGO_URL, params={"q": query, "format": "json", "no_html": "1"}, timeout=10)
            d = r.json()
            if d.get("AbstractText"): return d["AbstractText"][:200]
            return "No results found."
        except: return "Search failed."

    def find_local_songs(self):
        songs = []
        for folder in MUSIC_FOLDERS:
            if os.path.isdir(folder):
                for ext in MUSIC_EXTENSIONS:
                    songs.extend(glob.glob(os.path.join(folder, f"*{ext}")))
        return songs

    def play_mp3(self, file_path):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.music_playing = True
            self.speak(f"Now playing {os.path.splitext(os.path.basename(file_path))[0]}")
        except Exception as e: self.speak("Couldn't play that file.")

    def stop_music(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop(); pygame.mixer.quit()
                self.music_playing = False; self.speak("Music stopped.")
            else: self.speak("No music playing.")
        except: self.speak("No music playing.")

    def pause_music(self):
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause(); self.speak("Paused.")
        except: pass

    def resume_music(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.unpause(); self.speak("Resuming.")
        except: pass

    def handle_play_command(self, cmd):
        song_query = cmd
        for prefix in ["play me", "play song", "play music", "play a song", "play some music", "play"]:
            if cmd.startswith(prefix):
                song_query = cmd.replace(prefix, "", 1).strip(); break
        if song_query:
            matched = [s for s in self.find_local_songs() if song_query.lower() in os.path.basename(s).lower()]
            if matched: self.play_mp3(random.choice(matched)); return
        all_songs = self.find_local_songs()
        if all_songs: self.play_mp3(random.choice(all_songs))
        else: self.speak("No local music found.")

    def shutdown(self):
        if self.arduino:
            try: self.arduino.close()
            except: pass
        try:
            if pygame.mixer.get_init(): pygame.mixer.quit()
        except: pass

    def run(self):
        self.speak(f"Hello! I am {VA_NAME}. How can I help you?")
        while self.running:
            command = self.listen()
            self.handle_command(command)
        self.shutdown()


if __name__ == "__main__":
    assistant = VoiceAssistant()
    def _signal_handler(sig, frame):
        assistant.running = False
    signal.signal(signal.SIGINT, _signal_handler)
    assistant.run()
