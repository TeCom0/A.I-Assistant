import speech_recognition as sr
from pygame import mixer
import yt_dlp
import os
import tempfile
import re
import random
from characterai import pycai

# Initialize components
mixer.init()
recognizer = sr.Recognizer()

# Character.AI Setup (Updated for current API)
TOKEN = "Fe26.2*1*61b6dff3b81993d93548db1aa03af19a1dad401ec71d29d6ee4fa0d1931d058e*ZxG9GUwbWaQIDacdolnMvg*WIE6uipUWDnXaxfY8iL7rb4CaYc63ngu5nxLqCIDX2xs5Wz4UrFwcB3FTfbKYHFHQ846N0VIKPLzlo53ROCTWw**50e33f1504f5196cc5627a6fd1520e23f0250180760482b9edf9216234baab87*yAt1WxTqIW7g229e5ZZMZVhEuUKbMiVqokiHw1li6co~2"
CHARACTER_ID = "https://character.ai/chat/QL-kiI8v8Vf-ZrJn5qPCggZ_Da1gudacx1lGeJzpkbo"  # Just the ID part from URL

client = pycai(TOKEN)
try:
    # Updated API method to get character
    character_info = client.character_info(CHARACTER_ID)
    chat = client.chat.new_chat(character_info['external_id'])
except Exception as e:
    print(f"CharacterAI init error: {e}")
    chat = None

# FFmpeg configuration
FFMPEG_PATH = r"C:\Program Files\ffmpeg-2025-03-31-git-35c091f4b7-essentials_build\ffmpeg-2025-03-31-git-35c091f4b7-essentials_build\bin\ffmpeg.exe"

# Global variables
current_song = ""
song_history = []
is_paused = False

def play_song(song_name, announce=True):
    global current_song, is_paused
    try:
        if not os.path.exists(FFMPEG_PATH):
            if chat:
                chat.send_message("System alert: FFmpeg not found")
            return

        temp_dir = tempfile.mkdtemp()
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'ffmpeg_location': FFMPEG_PATH,
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
            filename = ydl.prepare_filename(info['entries'][0])
            mp3_file = os.path.splitext(filename)[0] + '.mp3'
            
            current_song = song_name
            song_history.append(song_name)
            is_paused = False
            
            if announce and chat:
                chat.send_message(f"Now playing: {song_name}")
            
            mixer.music.load(mp3_file)
            mixer.music.play()
            
            while mixer.music.get_busy():
                continue
                
        os.remove(mp3_file)
        os.rmdir(temp_dir)
        
    except Exception as e:
        if chat:
            chat.send_message(f"Sorry, I couldn't play {song_name}")

def pause_music():
    global is_paused
    if mixer.music.get_busy() and not is_paused:
        mixer.music.pause()
        is_paused = True
        if chat:
            chat.send_message("Music paused")
    elif is_paused:
        if chat:
            chat.send_message("Music is already paused")
    else:
        if chat:
            chat.send_message("No music is currently playing")

def resume_music():
    global is_paused
    if is_paused:
        mixer.music.unpause()
        is_paused = False
        if chat:
            chat.send_message("Music resumed")
    elif mixer.music.get_pos() > 0:  # If music was playing before
        if chat:
            chat.send_message("Music is already playing")
    else:
        if chat:
            chat.send_message("No music to resume")

def rewind_music(seconds):
    try:
        current_pos = mixer.music.get_pos() / 1000  # Convert to seconds
        new_pos = max(0, current_pos - seconds)
        mixer.music.set_pos(new_pos)
        if chat:
            chat.send_message(f"Rewound {seconds} seconds")
    except:
        if chat:
            chat.send_message("Couldn't rewind")

def play_similar():
    if current_song:
        similar_artists = {
            "eminem": ["D12", "50 Cent", "Dr. Dre", "Royce da 5'9", "Kendrick Lamar"],
            "the weeknd": ["Daft Punk", "Bruno Mars", "Post Malone", "Doja Cat"],
            "taylor swift": ["Olivia Rodrigo", "Ed Sheeran", "Selena Gomez", "Shawn Mendes"]
        }
        
        # Find matching artist
        artist = next((a for a in similar_artists if a in current_song.lower()), None)
        
        if artist and chat:
            similar_song = random.choice(similar_artists[artist])
            play_song(f"{similar_song} {current_song.split()[-1]}")  # Keep the same song title structure
        else:
            play_song(current_song + " remix")  # Fallback
    elif chat:
        chat.send_message("No song history to find similar music")

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening... (Speak now)")
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
            text = r.recognize_google(audio).lower()
            print(f"You said: {text}")
            return text
        except Exception as e:
            print(f"Listening error: {e}")
            return ""

def process_command(text):
    if not text:
        return
    
    if "exit" in text or "quit" in text:
        if chat:
            chat.send_message("Goodbye!")
        return "exit"
    
    if "pause" in text:
        pause_music()
    elif "play" in text and not "play something" in text:
        if is_paused:
            resume_music()
        else:
            song = text.replace("play", "").strip()
            if song:  # Only play if there's actually a song name
                play_song(song)
    elif "rewind" in text:
        try:
            seconds = int(re.search(r'rewind (\d+)', text).group(1))
            rewind_music(seconds)
        except:
            if chat:
                chat.send_message("How many seconds should I rewind?")
    elif "play something similar" in text:
        play_similar()
    elif chat:
        # Regular conversation
        response = chat.send_message(text)
        print(f"AI: {response.text}")

def main():
    if chat:
        chat.send_message("Music assistant ready! You can ask me to play songs, pause, or rewind.")
    
    while True:
        text = listen()
        if process_command(text) == "exit":
            break

if __name__ == "__main__":
    main()