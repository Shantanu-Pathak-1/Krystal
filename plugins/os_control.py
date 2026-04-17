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
    command = query.strip()
    
    if not command:
        return "Error: Please provide an OS command."
    
    try:
        # Execute exact command passed by LLM - no keyword matching
        # The LLM should format commands as: "/os play <song>" or "/os open <app>"
        return _execute_command(command)
    except Exception as e:
        return f"OS control error: {e}"

def _execute_command(command: str) -> str:
    # Parse the command - LLM should have already decided the action
    parts = command.split(maxsplit=1)
    action = parts[0].lower() if parts else ""
    args = parts[1].strip() if len(parts) > 1 else ""
    
    if action == 'play' and args:
        return _play_media(args)
    elif action == 'pause':
        return _pause_media()
    elif action == 'next':
        return _next_track()
    elif action == 'previous':
        return _previous_track()
    elif action == 'open' and args:
        return _open_target(args)
    elif action == 'search' and args:
        return _search_web(args)
    elif action == 'lock':
        return _lock_screen()
    else:
        return f"❓ Unknown command: {action}. Please specify an action like 'play', 'open', 'search', etc."

def _play_media(query: str) -> str:
    """Play media on YouTube - requires exact song name from LLM"""
    if not query:
        return "❓ Please specify what to play. Example: 'play Bohemian Rhapsody'"
    
    if pywhatkit:
        try:
            pywhatkit.playonyt(query)
            return f"▶️ Playing '{query}' on YouTube."
        except Exception as e:
            # Fallback to web search
            encoded = urllib.parse.quote(query)
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
            return f"🔍 Opened YouTube search for '{query}'."
    else:
        encoded = urllib.parse.quote(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        return f"🔍 Opened YouTube search for '{query}'."

def _pause_media() -> str:
    """Toggle media playback"""
    if pyautogui:
        pyautogui.press('playpause')
        return "⏯ Media toggled."
    return "Error: pyautogui not installed."

def _next_track() -> str:
    """Skip to next track"""
    if pyautogui:
        pyautogui.press('nexttrack')
        return "⏭ Next track."
    return "Error: pyautogui not installed."

def _previous_track() -> str:
    """Go to previous track"""
    if pyautogui:
        pyautogui.press('prevtrack')
        return "⏮ Previous track."
    return "Error: pyautogui not installed."

def _open_target(target: str) -> str:
    """Open a website or application - requires exact target from LLM"""
    # Handle abbreviation mappings
    abbreviation_mappings = {
        'yt': 'youtube.com',
        'ig': 'instagram.com',
        'chatgpt': 'chatgpt.com',
        'gh': 'github.com',
        'fb': 'facebook.com',
        'x': 'twitter.com',
        'tw': 'twitter.com',
        'li': 'linkedin.com',
        'rd': 'reddit.com',
        'sp': 'spotify.com',
        'nf': 'netflix.com',
        'amz': 'amazon.com',
        'wiki': 'wikipedia.org',
    }
    
    # Handle specific popular sites (full names)
    site_mappings = {
        'youtube': 'https://www.youtube.com',
        'google': 'https://www.google.com',
        'gmail': 'https://mail.google.com',
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://twitter.com',
        'instagram': 'https://www.instagram.com',
        'linkedin': 'https://www.linkedin.com',
        'github': 'https://github.com',
        'netflix': 'https://www.netflix.com',
        'amazon': 'https://www.amazon.com',
        'reddit': 'https://www.reddit.com',
        'spotify': 'https://open.spotify.com',
        'wikipedia': 'https://www.wikipedia.org',
        'chatgpt': 'https://chatgpt.com',
    }
    
    # Check if it's a known abbreviation first
    target_lower = target.lower()
    if target_lower in abbreviation_mappings:
        domain = abbreviation_mappings[target_lower]
        url = f"https://www.{domain}" if not domain.startswith('http') else domain
        webbrowser.open(url)
        return f"🌐 Opened {domain}."
    
    # Check if it's a known site (full name)
    if target_lower in site_mappings:
        url = site_mappings[target_lower]
        webbrowser.open(url)
        return f"🌐 Opened {target.title()}."
    
    # Check for URL format
    if target.startswith("http"):
        url = target
    elif "." in target and " " not in target:
        # Looks like a domain
        if not target.startswith("www."):
            target = "www." + target
        url = "https://" + target
    else:
        # Treat as search query
        encoded = urllib.parse.quote(target)
        url = f"https://www.google.com/search?q={encoded}"
    
    webbrowser.open(url)
    return f"🌐 Opened: {url}"

def _search_web(query: str) -> str:
    """Search the web - requires exact query from LLM"""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"🔍 Searched for: {query}"

def _lock_screen() -> str:
    """Lock the computer screen"""
    subprocess.Popen('rundll32.exe user32.dll,LockWorkStation', shell=True)
    return "Screen locked."