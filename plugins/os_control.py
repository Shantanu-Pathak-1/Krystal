"""OS Control plugin for Krystal's system superpowers."""

from __future__ import annotations

import os
import re
import subprocess
import urllib.parse
import webbrowser

try:
    import pywhatkit
except ImportError:
    pywhatkit = None

try:
    import pyautogui
except ImportError:
    pyautogui = None

NAME = "/os"
DESCRIPTION = "Controls the local operating system, launches local apps, and opens the user's default real browser."

def run(query, **kwargs):
    _ = kwargs
    command = query.strip().lower()
    
    if not command:
        return "Error: Please provide an OS command."
    
    try:
        if _is_media_command(command):
            return _handle_media_command(command)
        elif _is_web_command(command):
            return _handle_web_command(command)
        elif _is_app_command(command):
            return _handle_app_command(command)
        elif _is_system_command(command):
            return _handle_system_command(command)
        else:
            # Fallback app launch check
            return _handle_app_command(f"open {command}")
            
    except Exception as e:
        return f"OS control error: {e}"

def _is_media_command(command: str) -> bool:
    # Media commands that should use media keys or pywhatkit
    media_keywords = ['play', 'song', 'music', 'video', 'spotify', 'watch', 'pause', 'stop', 'next', 'previous']
    # Only treat as media if it's NOT a simple "open youtube" command
    if 'open youtube' in command or 'launch youtube' in command:
        return False  # This is a web command, not media playback
    return any(keyword in command for keyword in media_keywords)

def _is_web_command(command: str) -> bool:
    keywords = ['open http', 'open www', 'search', 'website', 'url', 'visit', 'google', 'open youtube', 'launch youtube', 'go to']
    return any(keyword in command for keyword in keywords)

def _is_app_command(command: str) -> bool:
    keywords = ['open', 'launch', 'start', 'run']
    return any(keyword in command for keyword in keywords)

def _is_system_command(command: str) -> bool:
    keywords = ['shutdown', 'restart', 'sleep', 'lock']
    return any(keyword in command for keyword in keywords)

def _handle_media_command(command: str) -> str:
    # Handle direct pyautogui controls for media keys
    pause_commands = ['pause music', 'play music', 'stop music', 'stop', 'pause', 'rok do', 'band kar do', 'pause karo', 'band karo']
    if any(cmd in command for cmd in pause_commands):
        if pyautogui:
            pyautogui.press('playpause')
            return "⏯ Media toggled."
        return "Error: pyautogui not installed."
        
    next_commands = ['next song', 'next track', 'next', 'agla gaana', 'next gana']
    if any(cmd in command for cmd in next_commands):
        if pyautogui:
            pyautogui.press('nexttrack')
            return "⏭ Next track."
        return "Error: pyautogui not installed."

    prev_commands = ['previous song', 'prev track', 'previous', 'pichla gaana', 'last song']
    if any(cmd in command for cmd in prev_commands):
        if pyautogui:
            pyautogui.press('prevtrack')
            return "⏮ Previous track."
        return "Error: pyautogui not installed."

    # Handle YouTube playback for "play <song>" commands
    if 'play' in command:
        song_part = command.split('play', 1)[1].strip()
        if song_part:
            if pywhatkit:
                try:
                    pywhatkit.playonyt(song_part)
                    return f"▶️ Playing '{song_part}' on YouTube."
                except Exception as e:
                    # Fallback to web search
                    encoded = urllib.parse.quote(song_part)
                    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
                    return f"🔍 Opened YouTube search for '{song_part}'."
            else:
                encoded = urllib.parse.quote(song_part)
                webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
                return f"🔍 Opened YouTube search for '{song_part}'."
    
    # If we get here with 'youtube' but no play command, open youtube.com
    if 'youtube' in command:
        webbrowser.open("https://www.youtube.com")
        return "🌐 Opened YouTube."
            
    return "❓ Media command not recognized."

def _handle_web_command(command: str) -> str:
    # Extract the target from commands like "open youtube", "open google", etc.
    site_part = command
    
    # Remove common prefixes
    for prefix in ['open ', 'launch ', 'go to ', 'search ', 'visit ', 'start ']:
        if site_part.startswith(prefix):
            site_part = site_part[len(prefix):].strip()
            break
    
    # Handle specific popular sites
    site_mappings = {
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'gmail': 'https://mail.google.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://twitter.com',
        'x': 'https://twitter.com',
        'instagram': 'https://www.instagram.com',
        'linkedin': 'https://www.linkedin.com',
        'github': 'https://github.com',
        'netflix': 'https://www.netflix.com',
        'amazon': 'https://www.amazon.com',
        'reddit': 'https://www.reddit.com',
        'spotify': 'https://open.spotify.com',
        'wikipedia': 'https://www.wikipedia.org',
    }
    
    # Check if it's a known site
    if site_part.lower() in site_mappings:
        url = site_mappings[site_part.lower()]
        webbrowser.open(url)
        return f"🌐 Opened {site_part.title()}."
    
    # Check for URL format
    if not site_part.startswith("http"):
        if "." in site_part and " " not in site_part:
            # Looks like a domain
            if not site_part.startswith("www."):
                site_part = "www." + site_part
            url = "https://" + site_part
        else:
            # Treat as search query
            encoded = urllib.parse.quote(site_part)
            url = f"https://www.google.com/search?q={encoded}"
    else:
        url = site_part
    
    webbrowser.open(url)
    return f"🌐 Opened: {url}"

def _handle_app_command(command: str) -> str:
    app_part = command.replace('open ', '').replace('launch ', '').strip()
    
    app_mappings = {
        'notepad': 'notepad.exe',
        'calculator': 'calc.exe',
        'calc': 'calc.exe',
        'paint': 'mspaint.exe',
        'cmd': 'cmd.exe',
        'terminal': 'cmd.exe',
        'explorer': 'explorer.exe',
        'task manager': 'taskmgr.exe',
        'chrome': 'chrome.exe',
        'edge': 'msedge.exe',
        'firefox': 'firefox.exe',
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe',
        'vscode': 'code.exe',
        'code': 'code.exe',
        'spotify': 'spotify.exe',
        'discord': 'discord.exe',
        'steam': 'steam.exe',
    }
    
    # Normalize the app name
    app_key = app_part.lower().replace('.exe', '')
    executable = app_mappings.get(app_key, app_part)
    
    try:
        # Try to launch the application
        if executable.endswith('.exe'):
            subprocess.Popen(executable, shell=True)
        else:
            # Try as a command (might be on PATH)
            subprocess.Popen(executable, shell=True)
        return f"🚀 Launched: {app_part.title()}"
    except Exception as e:
        # Fallback: try opening as if it's a file/program path
        try:
            os.startfile(executable)
            return f"🚀 Launched: {app_part.title()}"
        except:
            return f"❌ Could not launch '{app_part}'. Make sure it's installed."

def _handle_system_command(command: str) -> str:
    if 'lock' in command:
        subprocess.Popen('rundll32.exe user32.dll,LockWorkStation', shell=True)
        return "Screen locked."
    return "Advanced system command blocked for safety."