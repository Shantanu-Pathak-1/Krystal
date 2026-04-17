"""Social Hub plugin for Krystal to connect to multiple platforms."""

from __future__ import annotations

NAME = "/social"
DESCRIPTION = "Send messages to Telegram, WhatsApp, Instagram, or LinkedIn."

# Security: Only interact with pre-approved contacts
# Add your WhatsApp contacts (with country code, e.g., +919876543210)
# Add your Instagram usernames (with @, e.g., @username)
# Add your Telegram chat IDs (numbers, e.g., 123456789)
# Add your LinkedIn profile URLs
ALLOWED_CONTACTS = ["+918982955775", "@_dark.soul__1"]


def run(query, **kwargs):
    """
    Send messages to social media platforms with security firewall.

    Args:
        query: The command to execute (format: "/social <platform> <target> <message>")
                or IntentClassifier format: "-t <platform> -m <message> -p <target>"
        **kwargs: Additional arguments (ignored)

    Returns:
        Success message
    """
    _ = kwargs

    print(f"\033[96m[Social Hub Debug: Query = '{query}']\033[0m")

    if not query.strip():
        return "Error: Please provide platform, target, and message. Usage: /social <platform> <target> <message>"

    try:
        # Check if it's IntentClassifier format (-t, -m, -p flags)
        if "-t" in query and "-m" in query and "-p" in query:
            # Parse IntentClassifier format: -t platform -m message -p target
            import re
            platform_match = re.search(r'-t\s+(\w+)', query)
            message_match = re.search(r'-m\s+"([^"]+)"', query)
            target_match = re.search(r'-p\s+"([^"]+)"', query)

            if not platform_match or not message_match or not target_match:
                # Try without quotes
                message_match = re.search(r'-m\s+(\S+)', query)
                target_match = re.search(r'-p\s+(\S+)', query)

            if not platform_match or not message_match or not target_match:
                return "Error: Invalid IntentClassifier format"

            platform = platform_match.group(1).lower().strip()
            message = message_match.group(1).strip()
            target = target_match.group(1).strip()

            print(f"\033[96m[Social Hub Debug (IntentClassifier): platform={platform}, target={target}, message={message}]\033[0m")
        elif "send" in query.lower() and "to" in query.lower() and "on" in query.lower():
            # Parse natural language: "send hello to +918982955775 on whatsapp"
            import re
            # Extract platform (after "on")
            platform_match = re.search(r'on\s+(\w+)', query.lower())
            # Extract target (phone number between "to" and "on")
            target_match = re.search(r'to\s+([+\d]+)', query)
            # Extract message (between "send" and "to")
            message_match = re.search(r'send\s+(.+?)\s+to', query, re.IGNORECASE)

            if not platform_match or not target_match:
                return "Error: Could not parse natural language. Use format: send <message> to <target> on <platform>"

            platform = platform_match.group(1).lower().strip()
            target = target_match.group(1).strip()
            message = message_match.group(1).strip() if message_match else "Hello"

            print(f"\033[96m[Social Hub Debug (Natural Language): platform={platform}, target={target}, message={message}]\033[0m")
        else:
            # Parse direct command format: /social <platform> <target> <message>
            parts = query.strip().split()
            print(f"\033[96m[Social Hub Debug: Parts = {parts}]\033[0m")

            if len(parts) < 3:
                return "Error: Invalid format. Usage: /social <platform> <target> <message>"

            platform = parts[1].lower().strip()
            target = parts[2].strip()
            message = " ".join(parts[3:]) if len(parts) > 3 else "Hello"

            print(f"\033[96m[Social Hub Debug: platform={platform}, target={target}, message={message}]\033[0m")

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
    """Send message via Telegram using bot (simpler, just needs bot token)."""
    try:
        from telegram import Bot
        from telegram.error import TelegramError
        import os

        # Get bot token from environment variable
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

        if not bot_token:
            return "Telegram error: TELEGRAM_BOT_TOKEN not set. Run setup_telegram() for instructions."

        print(f"\033[96m[Social Hub: Sending '{message}' to {user_id} via Telegram Bot]\033[0m")

        # Initialize bot
        bot = Bot(token=bot_token)

        # Send message
        bot.send_message(chat_id=user_id, text=message)

        return f"Message sent to Telegram user {user_id}"

    except ImportError:
        return "Telegram error: python-telegram-bot not installed. Run: pip install python-telegram-bot"
    except TelegramError as e:
        return f"Telegram API error: {e}"
    except Exception as e:
        return f"Telegram error: {e}"


def _send_whatsapp(phone_number: str, message: str) -> str:
    """Send message via WhatsApp using pywhatkit (free, personal use)."""
    try:
        import pywhatkit
        import time

        # Format phone number (remove +, spaces, dashes)
        formatted_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')

        # Validate phone number (should be 10-15 digits)
        if not formatted_number.isdigit() or len(formatted_number) < 10:
            return f"Error: Invalid phone number '{phone_number}'. Use format: +919876543210"

        print(f"\033[96m[Social Hub: Sending '{message}' to {phone_number} via WhatsApp]\033[0m")

        # Send message (opens WhatsApp Web with QR code if not authenticated)
        pywhatkit.sendwhatmsg_instantly(
            phone_no=formatted_number,
            message=message,
            tab_close=True,
            close_time=3
        )

        return f"Message sent to WhatsApp {phone_number}. (Scan QR code if prompted in browser)"
    except ImportError:
        return "WhatsApp error: pywhatkit not installed. Run: pip install pywhatkit"
    except Exception as e:
        return f"WhatsApp error: {e}"


def setup_whatsapp_qr():
    """Open WhatsApp Web for QR code scanning (one-time setup)."""
    try:
        import pywhatkit
        import webbrowser

        print("\033[96m[Social Hub: Opening WhatsApp Web for QR code scan]\033[0m")
        print("1. Scan the QR code with your WhatsApp mobile app")
        print("2. After scanning, WhatsApp Web will be authenticated")
        print("3. You can now send messages via Krystal")

        webbrowser.open("https://web.whatsapp.com")
        return "WhatsApp Web opened. Scan QR code with your phone to authenticate."
    except ImportError:
        return "WhatsApp error: pywhatkit not installed. Run: pip install pywhatkit"
    except Exception as e:
        return f"WhatsApp setup error: {e}"


def _send_instagram(username: str, message: str) -> str:
    """Send message via Instagram using selenium automation (full automation)."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        import os

        # Get credentials from environment variables
        insta_user = os.getenv('INSTAGRAM_USERNAME')
        insta_pass = os.getenv('INSTAGRAM_PASSWORD')

        if not insta_user or not insta_pass:
            return "Instagram error: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD not set in .env"

        print(f"\033[96m[Social Hub: Sending '{message}' to @{username} via Instagram]\033[0m")

        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Go to Instagram login
            driver.get("https://www.instagram.com/accounts/login/")
            time.sleep(3)

            # Enter credentials
            username_input = driver.find_element(By.NAME, "username")
            password_input = driver.find_element(By.NAME, "password")
            username_input.send_keys(insta_user)
            password_input.send_keys(insta_pass)
            password_input.submit()
            time.sleep(5)

            # Handle 2FA if needed (would need manual intervention)
            # For now, assume no 2FA or already logged in

            # Go to profile
            profile_url = f"https://www.instagram.com/{username.replace('@', '')}/"
            driver.get(profile_url)
            time.sleep(3)

            # Click message button
            try:
                message_button = driver.find_element(By.XPATH, "//div[text()='Message']")
                message_button.click()
                time.sleep(2)

                # Type message
                message_box = driver.find_element(By.TAG_NAME, "textarea")
                message_box.send_keys(message)
                time.sleep(1)

                # Send message (Enter key)
                message_box.send_keys("\n")
                time.sleep(2)

                return f"Message sent to Instagram @{username}"
            except Exception as e:
                return f"Instagram message failed: {e}. User might not be following you."

        finally:
            driver.quit()

    except ImportError:
        return "Instagram error: selenium not installed. Run: pip install selenium"
    except Exception as e:
        return f"Instagram error: {e}"


def _send_linkedin(profile_url: str, message: str) -> str:
    """Send message via LinkedIn using selenium automation (free web-based)."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        import time
        import os

        # Get credentials from environment variables
        linkedin_user = os.getenv('LINKEDIN_USERNAME')
        linkedin_pass = os.getenv('LINKEDIN_PASSWORD')

        if not linkedin_user or not linkedin_pass:
            return "LinkedIn error: LINKEDIN_USERNAME and LINKEDIN_PASSWORD not set in .env"

        print(f"\033[96m[Social Hub: Sending '{message}' to {profile_url} via LinkedIn]\033[0m")

        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Go to LinkedIn login
            driver.get("https://www.linkedin.com/login")
            time.sleep(2)

            # Enter credentials
            driver.find_element(By.ID, "username").send_keys(linkedin_user)
            driver.find_element(By.ID, "password").send_keys(linkedin_pass)
            driver.find_element(By.ID, "password").submit()
            time.sleep(3)

            # Go to profile
            driver.get(profile_url)
            time.sleep(2)

            # Click message button
            try:
                message_button = driver.find_element(By.CSS_SELECTOR, "[data-control-name='message']")
                message_button.click()
                time.sleep(2)

                # Type message
                message_box = driver.find_element(By.CSS_SELECTOR, "[contenteditable='true']")
                message_box.send_keys(message)
                time.sleep(1)

                # Send message
                send_button = driver.find_element(By.CSS_SELECTOR, "[data-control-name='send']")
                send_button.click()
                time.sleep(2)

                return f"Message sent to LinkedIn profile {profile_url}"
            except Exception as e:
                return f"LinkedIn message failed: {e}. Profile might not be in your network."

        finally:
            driver.quit()

    except ImportError:
        return "LinkedIn error: selenium not installed. Run: pip install selenium"
    except Exception as e:
        return f"LinkedIn error: {e}"


def setup_telegram():
    """Setup Telegram bot using BotFather (simpler than API credentials)."""
    print("\033[96m[Telegram Bot Setup Instructions]\033[0m")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot to create a new bot")
    print("3. Follow the instructions to name your bot")
    print("4. Copy the bot token (looks like: 123456789:ABCdefGHIjklMNOpqrSTUvwxYZ)")
    print("5. Add this to your .env file: TELEGRAM_BOT_TOKEN=your_token_here")
    print("6. Restart the backend to load the new environment variable")
    print("\nAfter setup, send a message to your bot on Telegram to start a chat")
    print("Then use: /social telegram <your_chat_id> <message>")
    print("\nTo get your chat_id, send /start to your bot and check the message ID")
    return "Telegram bot setup instructions displayed. Follow the steps above."


def setup_instagram():
    """Setup Instagram using selenium automation (full automation)."""
    print("\033[96m[Instagram Setup Instructions]\033[0m")
    print("1. Add to .env file:")
    print("   INSTAGRAM_USERNAME=your_username")
    print("   INSTAGRAM_PASSWORD=your_password")
    print("2. For security, disable 2FA or use a separate account")
    print("3. Selenium will automate the entire process (login, navigate, send)")
    print("\nNote: Instagram may block automated accounts. Use carefully.")
    return "Instagram setup instructions displayed. Add credentials to .env file."


def setup_linkedin():
    """Setup LinkedIn login credentials."""
    print("\033[96m[LinkedIn Setup Instructions]\033[0m")
    print("1. Add to .env file:")
    print("   LINKEDIN_USERNAME=your_email_or_phone")
    print("   LINKEDIN_PASSWORD=your_password")
    print("2. For security, enable 2FA on your LinkedIn account")
    print("3. Chrome browser will be used for automation (headless mode)")
    print("\nNote: LinkedIn has strict anti-automation. Use carefully.")
    print("Profile must be in your network to send messages.")
    return "LinkedIn setup instructions displayed. Add credentials to .env file."
