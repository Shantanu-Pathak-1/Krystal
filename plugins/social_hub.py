"""Social Hub plugin for Krystal to connect to multiple platforms."""

from __future__ import annotations

NAME = "/social"
DESCRIPTION = "Send messages to Telegram, WhatsApp, Instagram, or LinkedIn."

# Security: Only interact with pre-approved contacts
ALLOWED_CONTACTS = ["+910000000000", "your_best_friend_insta_id"]


def run(query, **kwargs):
    """
    Send messages to social media platforms with security firewall.
    
    Args:
        query: The command to execute (format: "/social <platform> <target> <message>")
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Success message
    """
    _ = kwargs
    
    if not query.strip():
        return "Error: Please provide platform, target, and message. Usage: /social <platform> <target> <message>"
    
    try:
        # Parse command
        parts = query.strip().split(None, 2)
        if len(parts) < 3:
            return "Error: Invalid format. Usage: /social <platform> <target> <message>"
        
        platform = parts[1].lower().strip()
        target = parts[2].strip()
        message = " ".join(parts[3:]) if len(parts) > 3 else ""
        
        if not platform or not target:
            return "Error: Platform and target are required"
        
        # Security: Check if target is in allowed contacts
        if target not in ALLOWED_CONTACTS:
            print(f"\033[91m[Security Block: Attempted to contact unauthorized user {target}]\033[0m")
            return f"Security Error: Cannot contact '{target}'. Not in allowed contacts list."
        
        # Route to appropriate platform
        if platform == "telegram":
            return _send_telegram(target, message)
        elif platform == "whatsapp":
            return _send_whatsapp(target, message)
        elif platform == "instagram":
            return _send_instagram(target, message)
        elif platform == "linkedin":
            return _send_linkedin(target, message)
        else:
            return f"Error: Unsupported platform '{platform}'. Supported: telegram, whatsapp, instagram, linkedin"
            
    except Exception as e:
        return f"Social Hub error: {type(e).__name__}: {e}"


def _send_telegram(user_id: str, message: str) -> str:
    """Send message via Telegram."""
    try:
        # Placeholder - would need python-telegram-bot library
        print(f"\033[96m[Social Hub: Sending '{message}' to {user_id} via Telegram]\033[0m")
        return f"Message sent to Telegram user {user_id}"
    except Exception as e:
        return f"Telegram error: {e}"


def _send_whatsapp(phone_number: str, message: str) -> str:
    """Send message via WhatsApp."""
    try:
        # Placeholder - would need pywhatkit library
        print(f"\033[96m[Social Hub: Sending '{message}' to {phone_number} via WhatsApp]\033[0m")
        return f"Message sent to WhatsApp {phone_number}"
    except Exception as e:
        return f"WhatsApp error: {e}"


def _send_instagram(username: str, message: str) -> str:
    """Send message via Instagram."""
    try:
        # Placeholder - would need instagrapi library
        print(f"\033[96m[Social Hub: Sending '{message}' to @{username} via Instagram]\033[0m")
        return f"Message sent to Instagram @{username}"
    except Exception as e:
        return f"Instagram error: {e}"


def _send_linkedin(profile_url: str, message: str) -> str:
    """Send message via LinkedIn."""
    try:
        # Placeholder - would need linkedin-api library
        print(f"\033[96m[Social Hub: Sending '{message}' to {profile_url} via LinkedIn]\033[0m")
        return f"Message sent to LinkedIn profile {profile_url}"
    except Exception as e:
        return f"LinkedIn error: {e}"
