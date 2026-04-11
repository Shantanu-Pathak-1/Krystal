"""Web browsing plugin: uses Playwright to read and extract webpage content."""

from playwright.sync_api import sync_playwright
import sys
import re
from pathlib import Path

NAME = "/browse"
DESCRIPTION = "Opens a headless browser to read a webpage and extract text content."


def run(query, **kwargs):
    """
    Browse to a URL and extract content.
    
    Args:
        query: The URL to browse to
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Extracted and summarized content from webpage
    """
    _ = kwargs
    
    # Extract URL from query
    url = query.strip()
    if not url:
        return "Error: Please provide a URL to browse. Usage: /browse <URL>"
    
    # Validate URL format
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to URL
            page.goto(url, wait_until='networkidle')
            
            # Extract text content
            content = page.evaluate("() => document.body.innerText")
            
            # Close browser
            browser.close()
            
            if not content or len(content.strip()) < 50:
                return f"Unable to extract meaningful content from {url}"
            
            # Get LLMProcessor for summarization
            root = Path(__file__).resolve().parent.parent
            engine_dir = root / "krystal-core-engine"
            if str(engine_dir) not in sys.path:
                sys.path.insert(0, str(engine_dir))
            
            from api_router import KeyManager
            from llm_processor import LLMProcessor
            
            env_file = root / ".env"
            keys = KeyManager(env_path=env_file if env_file.is_file() else None)
            llm = LLMProcessor(keys)
            
            # Prepare summarization prompt
            summarization_prompt = f"""
            Please summarize the key information from this webpage content. 
            Focus on the main points, important details, and any actionable information.
            Keep it concise but comprehensive.
            
            URL: {url}
            
            Content to summarize:
            {content[:8000]}  # Limit to first 8000 chars for context window
            """
            
            # Get summary from LLM
            summary = llm.generate_response(summarization_prompt)
            
            return f"Summary of {url}:\n\n{summary}"
            
    except Exception as e:
        return f"Error browsing to {url}: {str(e)}"
