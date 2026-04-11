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
    keywords = ['play', 'song', 'music', 'video', 'youtube', 'spotify', 'watch', 'pause', 'stop', 'next', 'previous']
    return any(keyword in command for keyword in keywords)

def _is_web_command(command: str) -> bool:
    keywords = ['open http', 'open www', 'search', 'website', 'url', 'visit', 'google']
    return any(keyword in command for keyword in keywords)

def _is_app_command(command: str) -> bool:
    keywords = ['open', 'launch', 'start', 'run']
    return any(keyword in command for keyword in keywords)

def _is_system_command(command: str) -> bool:
    keywords = ['shutdown', 'restart', 'sleep', 'lock']
    return any(keyword in command for keyword in keywords)

def _handle_media_command(command: str) -> str:
    # Handle direct pyautogui controls
    if command in ['pause music', 'play music', 'stop music', 'stop', 'pause', 'rok do', 'band kar do']:
        if pyautogui:
            pyautogui.press('playpause')
            return "⏯ Media toggled."
        return "Error: pyautogui not installed."
        
    if command in ['next song', 'next track', 'next']:
        if pyautogui:
            pyautogui.press('nexttrack')
            return "⏭ Next track."
        return "Error: pyautogui not installed."

    if command in ['previous song', 'prev track', 'previous']:
        if pyautogui:
            pyautogui.press('prevtrack')
            return "⏮ Previous track."
        return "Error: pyautogui not installed."

    # Handle YouTube playback
    if 'play' in command:
        song_part = command.split('play', 1)[1].strip()
        if pywhatkit:
            try:
                pywhatkit.playonyt(song_part)
                return f"Playing '{song_part}' on YouTube."
            except Exception as e:
                return f"YouTube playback error: {e}"
        else:
            encoded = urllib.parse.quote(song_part)
            webbrowser.open(f"https://music.youtube.com/search?q={encoded}")
            return f"Opened search for '{song_part}'. (Install pywhatkit for auto-play)"
            
    return "Media command processed."

def _handle_web_command(command: str) -> str:
    site_part = command.replace('open ', '').replace('search ', '').strip()
    if not site_part.startswith("http"):
        if "." in site_part and " " not in site_part:
            site_part = "https://" + site_part
        else:
            encoded = urllib.parse.quote(site_part)
            site_part = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(site_part)
    return f"Opened: {site_part}"

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
        'word': 'winword.exe',
        'excel': 'excel.exe',
        'powerpoint': 'powerpnt.exe'
    }
    
    executable = app_mappings.get(app_part, app_part)
    try:
        subprocess.Popen(executable, shell=True)
        return f"Launched application: {app_part}"
    except Exception as e:
        return f"Could not launch '{app_part}'. Make sure it's installed."

def _handle_system_command(command: str) -> str:
    if 'lock' in command:
        subprocess.Popen('rundll32.exe user32.dll,LockWorkStation', shell=True)
        return "Screen locked."
    return "Advanced system command blocked for safety."