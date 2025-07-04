import pygame # Import pygame library for handling audio playback
import random # Import random for generating random choices
import asyncio # Import asyncio for asynchronous operations
import edge_tts # Import edge_tts for text-to-speech functionality
import os # Import os for file path handling
from dotenv import dotenv_values # Import dotenv for reading environment variables from a .env file
import time # Import time for potential delays

# Load environment variables from a .env file.
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")

# Asynchronous function to convert text to an audio file
async def TextToAudioFile(text: str) -> None:
    file_path = r"Data\speech.mp3"

    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"[DEBUG] Old {file_path} removed.")

    print(f"[DEBUG] Generating speech for: '{text[:50]}...' using voice: {AssistantVoice}")

    # Corrected 'HZ' to 'Hz' and adjusted rate to a more moderate value.
    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+5%')
    # If this still causes issues, try without pitch/rate:
    # communicate = edge_tts.Communicate(text, AssistantVoice)

    await communicate.save(file_path)
    print(f"[DEBUG] Speech saved to {file_path}. File size: {os.path.getsize(file_path)} bytes")

# Function to manage Text-to-Speech (TTS) functionality
def TTS(Text: str, func=lambda r=None: True):
    # Ensure mixer is always quit before starting a new playback cycle.
    if pygame.mixer.get_init():
        print("[DEBUG] Pygame mixer was already initialized. Quitting before re-init.")
        pygame.mixer.quit()
        time.sleep(0.1) # Give a small moment for resources to release

    try:
        asyncio.run(TextToAudioFile(Text))

        mixer_initialized = False
        mixer_info = None # Initialize mixer_info to None

        try:
            # --- MODIFIED: Try with common optimized settings (without buffer explicitly) ---
            # Some older Pygame versions or specific audio drivers might not like 'buffer' explicitly.
            # Pygame will use a default buffer size if not provided.
            pygame.mixer.init(frequency=44100, size=-16, channels=1) # Removed buffer=1024
            mixer_info = pygame.mixer.get_init()

            # Robust check for mixer_info: it should be a tuple with at least 3 elements
            if mixer_info is not None and isinstance(mixer_info, tuple) and len(mixer_info) >= 3:
                # Dynamically print buffer if it's available (length >= 4)
                buffer_info = f", Buffer={mixer_info[3]}" if len(mixer_info) >= 4 else ""
                print(f"[DEBUG] Pygame mixer initialized: Freq={mixer_info[0]}, Size={mixer_info[1]}, Channels={mixer_info[2]}{buffer_info}")
                mixer_initialized = True
            else:
                print(f"[ERROR] Pygame mixer.init() returned invalid info ({mixer_info}) after specific settings. Initialization might have failed silently or returned unexpected format.")

        except pygame.error as e:
            print(f"[ERROR] Failed to initialize Pygame mixer with specific settings (44100, -16, 1): {e}")
            print("[INFO] Attempting to initialize with default settings as a fallback...")
            try:
                pygame.mixer.init() # Try with absolute default settings
                mixer_info = pygame.mixer.get_init()
                # --- MODIFIED: Robust check for mixer_info (for fallback) ---
                if mixer_info is not None and isinstance(mixer_info, tuple) and len(mixer_info) >= 3:
                    buffer_info = f", Buffer={mixer_info[3]}" if len(mixer_info) >= 4 else ""
                    print(f"[DEBUG] Pygame mixer initialized with defaults: Freq={mixer_info[0]}, Size={mixer_info[1]}, Channels={mixer_info[2]}{buffer_info}")
                    mixer_initialized = True
                else:
                    print(f"[ERROR] Pygame mixer.init() returned invalid info ({mixer_info}) after default settings. Default initialization might have failed silently or returned unexpected format.")
            except pygame.error as e:
                print(f"[CRITICAL ERROR] Pygame mixer failed to initialize even with default settings: {e}")
                print("[CRITICAL] Audio playback will not work. Please check your Pygame installation and audio drivers.")
                return False

        if not mixer_initialized:
            print("[CRITICAL] Pygame mixer is still not initialized after all attempts. Exiting TTS attempt.")
            return False

        file_path = r"Data\speech.mp3"
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print(f"[ERROR] {file_path} either does not exist or is empty. Cannot play audio.")
            return False

        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print(f"[DEBUG] Playing audio from {file_path}...")

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            if func() == False:
                print("[DEBUG] External function signaled to stop playback.")
                break

        print("[DEBUG] Audio playback finished or stopped.")
        return True

    except Exception as e:
        print(f"[ERROR] An unexpected error occurred during TTS (outside mixer init): {e}")
        return False

    finally:
        if pygame.mixer.get_init():
            print("[DEBUG] Quitting Pygame mixer in finally block.")
            try:
                func(False)
                pygame.mixer.stop()
                pygame.mixer.quit()
            except Exception as e:
                print(f"[ERROR] Error during mixer cleanup in finally block: {e}")
        else:
            print("[DEBUG] Pygame mixer was not initialized, no cleanup needed.")

def TextToSpeech(Text: str, func=lambda r=None: True):
    Data = str(Text).split('.')

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information.",
        "There's more text on the chat screen for you, sir.",
        "Sir, take a look at the chat screen for additional text.",
        "You'll find more to read on the chat screen, sir.",
        "Sir, check the chat screen for the rest of the text.",
        "The chat screen has the rest of the text, sir.",
        "There's more to see on the chat screen, sir, please look.",
        "Sir, the chat screen holds the continuation of the text.",
        "You'll find the complete answer on the chat screen, kindly check it out sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, look at the chat screen for the complete answer."
    ]

    if len(Data) > 4 and len(Text) >= 250:
        print("[INFO] Long text detected. Playing summary and directing to chat.")
        TTS(".".join(Text.split(".")[0:2]) + "." + random.choice(responses), func)
    else:
        print("[INFO] Playing full text.")
        TTS(Text, func)

if __name__ == "__main__":
    print("Starting TTS demonstration. Type 'exit' to quit.")
    while True:
        user_input = input("Enter the text: ")
        if user_input.lower() == 'exit':
            break
        TextToSpeech(user_input)

    print("TTS demonstration ended.")