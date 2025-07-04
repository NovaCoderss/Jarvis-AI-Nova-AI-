# Import required libraries
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print # Keep rich print for better console output
from groq import Groq
import subprocess
import screen_brightness_control as sbc
import requests
import keyboard
import asyncio
import os
import logging
import glob # For searching for executable files
import psutil # For checking running processes
import time

import screen_brightness_control # Import time for sleep

# Configure logging for Automation.py
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey") # Retrieve the Groq API key.

# Define CSS classes for parsing specific elements in HTML content.
classes = ["zCuQIf", "bKkCELc", "lv7C", "Zlcm", "gsrt vk bk Fzvwsb VwPmf", "pclqee", "tw-data-text tw-text-small tw-ia",
           "IZ6rdc", "oGU8kd LTXOO", "vlzfe4", "webanswers-webanswers_table__webanswers-table", "dOOlO lkb0A8b gsrt", "sKLode",
           "LWKFKe", "vOf4g", "qv3hpe", "kno-rdesc", "SPZzbb"]

# Define a user-agent for making web requests.
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize the Groq client with the API Key
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses for User Interactions.
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need-don't hesitate to ask.",
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
SystemChatBot = {"role": "system", "content": f"Hello, I am {os.environ.get('USERNAME', 'User')}, You're a content writer. You have to write content like letters, applications, etc."}

# Helper function to check if a process is running
def is_app_running(app_name_query: str) -> bool:
    """Checks if an application process is currently running, by name or executable path."""
    app_name_query_lower = app_name_query.lower()
    
    # Try common executable name variations
    possible_process_names = [app_name_query_lower, f"{app_name_query_lower}.exe"]
    if ' ' in app_name_query_lower:
        possible_process_names.append(app_name_query_lower.replace(' ', '').replace('_', ''))
        possible_process_names.append(f"{app_name_query_lower.replace(' ', '').replace('_', '')}.exe")
    
    # Specific popular app executable names that might differ from display name
    if "chrome" in app_name_query_lower: possible_process_names.append("chrome.exe")
    if "edge" in app_name_query_lower: possible_process_names.append("msedge.exe")
    if "firefox" in app_name_query_lower: possible_process_names.append("firefox.exe")
    if "notepad" in app_name_query_lower: possible_process_names.append("notepad.exe")
    if "calculator" in app_name_query_lower: possible_process_names.append("calc.exe")
    if "word" in app_name_query_lower: possible_process_names.append("winword.exe")
    if "excel" in app_name_query_lower: possible_process_names.append("excel.exe")


    for proc in psutil.process_iter(['name', 'exe']):
        try:
            # Check if any of the possible names match the process name or executable path
            proc_name = proc.info['name'].lower()
            proc_exe = proc.info['exe'].lower() if proc.info['exe'] else ''

            for name_variant in possible_process_names:
                if name_variant in proc_name or name_variant in proc_exe:
                    logger.debug(f"Process '{proc_name}' (PID: {proc.pid}) matches query '{app_name_query}'.")
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

# Function to perform a Google search.
def GoogleSearch(Topic):
    logger.info(f"Performing Google search for: {Topic}")
    try:
        search(Topic) # Use pywhatkit's search function to perform the search.
        return True # Indicate success.
    except Exception as e:
        logger.error(f"Error during Google search for '{Topic}': {e}")
        return False

# Function to generate content using AI and save it to a file.
def Content(Topic):
    # Nested function to open a file in Notepad.
    def OpenNotepad(File):
        default_text_editor = "notepad.exe" # Default text editor.
        try:
            subprocess.Popen([default_text_editor, File]) # Open the file in Notepad.
            logger.info(f"Opened file: {File} in Notepad.")
        except FileNotFoundError:
            logger.error(f"Notepad.exe not found or file path is incorrect for: {File}")
        except Exception as e:
            logger.error(f"Error opening {File} in Notepad: {e}")

    # Nested function to generate content using the AI chatbot.
    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"}) # Add the user's prompt to messages.

        # Call Groq client to create completion
        try:
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768", # Specify the AI model.
                messages=[SystemChatBot] + messages, # Include system instructions and chat history.
                max_tokens=2048, # Limit the maximum tokens in the response.
                temperature=0.7, # Adjust response randomness.
                top_p=1, # Use nucleus sampling for response diversity.
                stream=True, # Enable streaming response.
                stop=None # Allow the model to determine stopping conditions.
            )
        except Exception as e:
            logger.error(f"Error calling Groq API for ContentWriterAI: {e}")
            return "Error: Could not generate content from AI."

        Answer = "" # Initialize an empty string for the response.

        # Process streamed response chunks.
        try:
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    Answer += chunk.choices[0].delta.content

            Answer = Answer.replace("</s>", "") # Remove unwanted tokens from the response.
            messages.append({"role": "assistant", "content": Answer}) # Add the AI's response to messages.
            return Answer
        except Exception as e:
            logger.error(f"Error processing AI response chunks: {e}")
            return "Error: Problem processing AI generated content."


    Topic = str(Topic).replace("Content ", "").strip() # Remove "Content " from the topic and strip whitespace.
    if not Topic:
        logger.warning("Content command received without a specific topic.")
        return False

    logger.info(f"Generating content for topic: {Topic}")
    generated_content = ContentWriterAI(Topic)

    if "Error:" in generated_content: # Check if AI generation itself returned an error
        logger.error(f"Failed to generate content: {generated_content}")
        return False

    # Save the generated content to a text file.
    file_name = rf"Data\{Topic.lower().replace(' ', '')}.txt"
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(generated_content)
        logger.info(f"Content saved to: {file_name}")
        OpenNotepad(file_name) # Open the file in Notepad.
        return True # Indicate success.
    except IOError as e:
        logger.error(f"Error saving content to file {file_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in Content function: {e}")
        return False

# Function to search for a topic on YouTube.
def YouTubeSearch(Topic):
    logger.info(f"Performing YouTube search for: {Topic}")
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}" # Corrected YouTube search URL
    try:
        webopen(Url4Search) # Open the search URL in a web browser.
        return True
    except Exception as e:
        logger.error(f"Error opening YouTube search for '{Topic}': {e}")
        return False

# Function to play a video on YouTube.
def PlayYouTube(Query):
    logger.info(f"Attempting to play YouTube video for query: {Query}")
    try:
        playonyt(Query) # Use pywhatkit's playonyt function to play the video.
        return True # Indicate success.
    except Exception as e:
        logger.error(f"Error playing YouTube video for '{Query}': {e}. Ensure pywhatkit is installed and query is valid.")
        return False

# Function to open an application or a relevant webpage.
def OpenApp(app_name: str):
    app_name = app_name.strip() # Remove any leading/trailing whitespace
    if not app_name:
        logger.warning("OpenApp received an empty application name.")
        return False

    logger.info(f"Attempting to open application: '{app_name}'")

    # --- Step 1: Check if already running ---
    if is_app_running(app_name):
        logger.info(f"'{app_name}' appears to be already running. Skipping open attempt.")
        return True # Consider it a success if it's already open

    # --- Attempt 1: Use AppOpener (most common method) ---
    logger.debug(f"Attempt 1: Trying to open '{app_name}' with AppOpener.")
    try:
        appopen(app_name, match_closest=True, output=True, throw_error=True)
        time.sleep(2) # Give app a moment to launch
        if is_app_running(app_name):
            logger.info(f"Successfully opened '{app_name}' using AppOpener.")
            return True
        else:
            logger.warning(f"AppOpener command sent for '{app_name}', but process not detected after 2 seconds. Trying fallback.")
    except Exception as e:
        logger.warning(f"Attempt 1 (AppOpener) failed for '{app_name}': {e}. Trying fallback methods.")

    # --- Attempt 2: Web Search Fallback ---
    logger.debug(f"Attempt 2: Trying web search fallback for '{app_name}'.")
    def extract_links(html_content):
        if html_content is None:
            logger.debug("HTML content is None in extract_links.")
            return []
        soup = BeautifulSoup(html_content, 'html.parser')
        external_links = []
        for link_tag in soup.find_all('a', href=True):
            href = link_tag.get('href')
            if href and href.startswith("http") and not href.startswith("https://www.google.com"):
                if "/url?q=" in href:
                    actual_url = href.split("/url?q=")[1].split("&sa=")[0]
                    external_links.append(actual_url)
                elif not any(x in href for x in ["accounts.google.com", "policies.google.com", "support.google.com"]):
                    external_links.append(href)
        if not external_links:
            logger.debug("No relevant external links found in Google search results for fallback.")
        return external_links

    def search_google(query_term):
        url = f"https://www.google.com/search?q={query_term}"
        headers = {"User-Agent": useragent}
        try:
            response = requests.get(url, headers=headers, timeout=15) # Increased timeout
            response.raise_for_status()
            logger.debug(f"Successfully fetched Google search results for '{query_term}'.")
            return response.text
        except requests.exceptions.RequestException as req_e:
            logger.error(f"Failed to retrieve search results from Google for '{query_term}'. Error: {req_e}")
            return None

    html_content = search_google(app_name)
    if html_content:
        found_links = extract_links(html_content)
        if found_links:
            first_link = found_links[0]
            logger.info(f"Attempt 2: Opening '{first_link}' via web browser fallback for '{app_name}'.")
            try:
                webopen(first_link)
                time.sleep(3) # Give browser more time to open and load
                # Check if the browser process is now running. This is a heuristic.
                # You might need to refine 'browser_exe_name' for your default browser.
                browser_exe_name = "chrome.exe" # Common default: Chrome
                if "edge" in first_link or "microsoft.com" in first_link:
                    browser_exe_name = "msedge.exe"
                elif "firefox" in first_link:
                    browser_exe_name = "firefox.exe"

                if is_app_running(browser_exe_name):
                     logger.info(f"Browser ({browser_exe_name}) opened for '{app_name}' via web fallback.")
                     return True
                else:
                    logger.warning(f"Browser ({browser_exe_name}) did not seem to open for '{app_name}' via web fallback after 3 seconds.")
            except Exception as web_e:
                logger.error(f"Attempt 2 (Web Browser) failed for '{app_name}' with link '{first_link}': {web_e}")
        else:
            logger.warning(f"Attempt 2: No valid web links found for '{app_name}' after Google search. Cannot open.")
    else:
        logger.error(f"Attempt 2: Google search for '{app_name}' failed to return any HTML content. Cannot open via web.")

    # --- Attempt 3: Direct Executable Launch (Experimental/Last Resort) ---
    logger.debug(f"Attempt 3: Trying direct executable launch for '{app_name}'.")
    possible_exe_locations = [
        os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
        os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'WindowsApps'), # For UWP apps - difficult
        os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
        os.path.join(os.environ.get('LOCALAPPDATA', os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local'))),
        os.path.join(os.environ.get('APPDATA', os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming'))),
        "C:\\Windows\\System32",
        "C:\\Windows",
        "C:\\", # Sometimes portable apps are here
    ]

    # Generate common executable name variations
    app_exe_names = [
        f"{app_name}.exe",
        f"{app_name.replace(' ', '').lower()}.exe", # e.g., "Visual Studio Code" -> "visualstudiocode.exe"
        f"{app_name.replace(' ', '_').lower()}.exe", # e.g., "VLC Media Player" -> "vlc_media_player.exe"
        app_name.lower().replace(' ', '') + '.exe', # Another common variation
        app_name.lower().replace(' ', '-').replace('_', '-') + '.exe', # Yet another
    ]
    # Add common specific browser names
    if "chrome" in app_name.lower(): app_exe_names.append("chrome.exe")
    if "edge" in app_name.lower(): app_exe_names.append("msedge.exe")
    if "firefox" in app_name.lower(): app_exe_names.append("firefox.exe")
    if "notepad" in app_name.lower(): app_exe_names.append("notepad.exe")
    if "calculator" in app_name.lower(): app_exe_names.append("calc.exe")
    if "vlc" in app_name.lower(): app_exe_names.append("vlc.exe")
    if "word" in app_name.lower(): app_exe_names.append("winword.exe") # For MS Word
    if "excel" in app_name.lower(): app_exe_names.append("excel.exe") # For MS Excel
    if "powerpoint" in app_name.lower(): app_exe_names.append("powerpnt.exe") # For MS PowerPoint
    if "outlook" in app_name.lower(): app_exe_names.append("outlook.exe") # For MS Outlook
    if "file explorer" in app_name.lower() or "files" in app_name.lower(): app_exe_names.append("explorer.exe")


    found_exe_path = None
    for loc in possible_exe_locations:
        for exe_name_variant in app_exe_names:
            # Check direct path first
            full_path_guess = os.path.join(loc, exe_name_variant)
            if os.path.exists(full_path_guess):
                found_exe_path = full_path_guess
                logger.debug(f"Found direct match: {found_exe_path}")
                break
            # Then check within common subdirectories like 'Application', 'bin', 'Program', etc.
            # This can be slow, so it's a deeper search.
            for root, dirs, files in os.walk(loc):
                if exe_name_variant in files:
                    found_exe_path = os.path.join(root, exe_name_variant)
                    logger.debug(f"Found {exe_name_variant} in sub-directory: {root}")
                    break
                # Limit depth to avoid extremely long searches
                if root.count(os.sep) - loc.count(os.sep) > 3: # Max 3 levels deep
                    dirs[:] = [] # Don't go deeper
            if found_exe_path: break
        if found_exe_path: break
            
    if found_exe_path:
        logger.info(f"Attempt 3: Found executable at '{found_exe_path}'. Trying to launch directly.")
        try:
            subprocess.Popen([found_exe_path])
            time.sleep(3) # Give more time for direct launch
            if is_app_running(os.path.basename(found_exe_path)):
                logger.info(f"Successfully launched '{app_name}' via direct executable path.")
                return True
            else:
                logger.warning(f"Direct executable launch for '{app_name}' command sent, but process not detected.")
        except FileNotFoundError:
            logger.error(f"Attempt 3: Executable not found at '{found_exe_path}' (should not happen if os.path.exists was true).")
        except Exception as sub_e:
            logger.error(f"Attempt 3: Error launching '{app_name}' via subprocess: {sub_e}")
    else:
        logger.warning(f"Attempt 3: Could not find a common executable path for '{app_name}'.")

    logger.error(f"All attempts to open '{app_name}' failed. Please check the exact application name or its executable path.")
    return False # Indicate complete failure after all attempts.

# Function to close an application.
def CloseApp(app_name: str):
    app_name = app_name.strip() # Remove any leading/trailing whitespace
    if not app_name:
        logger.warning("CloseApp received an empty application name.")
        return False

    app_lower = app_name.lower()

    if "chrome" in app_lower:
        logger.info(f"Skipping direct close for '{app_name}'. Please close Chrome manually if needed.")
        return True # Indicate that we've "handled" the close request by skipping it.
    else:
        logger.info(f"Attempting to close application: '{app_name}'.")
        try:
            close(app_name, match_closest=True, output=True, throw_error=True)
            logger.info(f"Successfully closed '{app_name}'.")
            return True # Indicate success.
        except Exception as e:
            logger.error(f"Error closing app '{app_name}': {e}. It might not be running or AppOpener could not find it.")
            return False # Indicate failure.

# Function to execute system-level commands.
def System(command: str):
    command = command.strip().lower() # Normalize command for easier matching
    logger.info(f"Executing system command: '{command}'")

    if command == "mute":
        keyboard.press_and_release("volume mute")
        logger.info("System muted.")
    elif command == "unmute":
        keyboard.press_and_release("volume mute")
        logger.info("System unmuted.")
    
    elif command == "volume up":
        keyboard.press_and_release("volume up")
        logger.info("Volume increased.")    
    elif command == "volume down":
        keyboard.press_and_release("volume down")
        logger.info("Volume decreased.")
    elif command == "brightness up":
       current = sbc.get_brightness()[0]  # Get current brightness
       sbc.set_brightness(min(current + 10, 100))  # Increase by 10% (max 100)
    elif command == "brightness down":
        current = sbc.get_brightness()[0]  # Get current brightness
        sbc.set_brightness(max(current - 10, 0))  # Decrease by 10% (min 0)
    elif command == "paste": # NEW: Handle paste command
        keyboard.press_and_release("ctrl+v")
        logger.info("Paste command executed.")
    else:
        logger.warning(f"Unknown system command: '{command}'")
        return False
    return True

# Asynchronous function to translate and execute user commands.
async def TranslateAndExecute(commands: list[str]):
    funcs = []
    logger.info(f"Translating and executing commands: {commands}")
    for command in commands:
        command_lower = command.lower().strip() # Convert command to lowercase and strip whitespace

        if command_lower.startswith("open "):
            app_name = command.removeprefix("open ").strip()
            if "open it" in command_lower or "open file" in command_lower or not app_name:
                logger.warning(f"Ignoring generic or ambiguous open command: '{command}'")
            else:
                funcs.append(asyncio.to_thread(OpenApp, app_name))
        elif command_lower.startswith("close "):
            app_name = command.removeprefix("close ").strip()
            if not app_name:
                logger.warning(f"Close command '{command}' is missing an application name.")
            else:
                funcs.append(asyncio.to_thread(CloseApp, app_name))
        elif command_lower.startswith("play "):
            query = command.removeprefix("play ").strip()
            if not query:
                logger.warning(f"Play command '{command}' is missing a query.")
            else:
                funcs.append(asyncio.to_thread(PlayYouTube, query))
        elif command_lower.startswith("content "):
            topic = command.removeprefix("content ").strip()
            if not topic:
                logger.warning(f"Content command '{command}' is missing a topic.")
            else:
                funcs.append(asyncio.to_thread(Content, topic))
        elif command_lower.startswith("google search "):
            topic = command.removeprefix("google search ").strip()
            if not topic:
                logger.warning(f"Google search command '{command}' is missing a topic.")
            else:
                funcs.append(asyncio.to_thread(GoogleSearch, topic))
        elif command_lower.startswith("youtube search "):
            topic = command.removeprefix("youtube search ").strip()
            if not topic:
                logger.warning(f"YouTube search command '{command}' is missing a topic.")
            else:
                funcs.append(asyncio.to_thread(YouTubeSearch, topic))
        elif command_lower.startswith("system "):
            sys_command = command.removeprefix("system ").strip()
            if not sys_command:
                logger.warning(f"System command '{command}' is missing a specific action.")
            else:
                funcs.append(asyncio.to_thread(System, sys_command))
        elif command_lower.startswith("general ") or command_lower.startswith("realtime "):
            logger.info(f"Handling general/realtime command: {command}")
            pass # Placeholder for general/realtime commands, not implemented yet
        else:
            logger.warning(f"No specific function found for command: '{command}'")

    if funcs:
        results = await asyncio.gather(*funcs)
        for result in results:
            if isinstance(result, bool):
                logger.debug(f"Function execution result: {result}")
            else:
                logger.debug(f"Function execution result (non-boolean): {result}")
            yield result
    else:
        logger.info("No valid functions to execute for the given commands.")
        yield False

# Asynchronous function to automate command execution.
async def Automation(commands: list[str]):
    logger.info(f"Starting Automation for commands: {commands}")
    success = True
    async for result in TranslateAndExecute(commands):
        if result is False:
            success = False
    logger.info(f"Automation finished. Overall success: {success}")
    return success

# This block demonstrates how the Automation module would be used programmatically.
# It does NOT take direct keyboard input like 'input()'.
# Your main voice assistant script would call 'await Automation([your_voice_command_text])'.
if __name__ == "__main__":
    logger.setLevel(logging.DEBUG) # Set logging to DEBUG for detailed output in testing.
