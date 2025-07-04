from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDWM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
from time import sleep
import subprocess
import threading
import json
import os
import sys
import cv2

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f'~{Username} : Hello {Assistantname}, How are you?\n{Assistantname} : Welcome {Username}. I am doing well. How may I help you?~'
subprocesses = []
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

def ShowDefaultChatIfNoChats():
    try:
        with open(r"Data\Chatlog.json", "r", encoding='utf-8') as file:
            if len(file.read()) < 5:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as db_file:
                    db_file.write(DefaultMessage)
    except Exception as e:
        print(f"[ERROR] in ShowDefaultChatIfNoChats: {e}")

with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
    file.write(DefaultMessage)

def ReadChatLogJson():
    try:
        with open(r'Data\ChatLog.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"[ERROR] reading ChatLog.json: {e}")
        return []

def ChatLoginRegistration():
    try:
        json_data = ReadChatLogJson()
        formatted_chatLog = ""
        for entry in json_data:
            if entry["role"] == "user":
                formatted_chatLog += f"User: {entry['content']}\n"
            elif entry["role"] == "assistant":
                formatted_chatLog += f"Assistant: {entry['content']}\n"
        formatted_chatLog = formatted_chatLog.replace("User", Username + " ")
        formatted_chatLog = formatted_chatLog.replace("Assistant", Assistantname + " ")
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatLog))
    except Exception as e:
        print(f"[ERROR] in ChatLoginRegistration: {e}")

def ShowChatsOnGUI():
    try:
        with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as File:
            Data = File.read()
            if len(str(Data)) > 0:
                with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as out_file:
                    out_file.write(Data)
    except Exception as e:
        print(f"[ERROR] in ShowChatsOnGUI: {e}")

def InitializeRecursion():
    try:
        SetMicrophoneStatus("False")
        ShowTextToScreen("")
        ShowDefaultChatIfNoChats()
        ChatLoginRegistration()
        ShowChatsOnGUI()
    except Exception as e:
        print(f"[ERROR] in InitializeRecursion: {e}")

def MainExecution():
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""
    
    try:
        SetAssistantStatus("Listening ...")
        Query = SpeechRecognition()
        ShowTextToScreen(f"{Username} : {Query}")
        SetAssistantStatus("Thinking ...")
        
        try:
            Decision = FirstLayerDWM(Query)
        except Exception as e:
            print(f"[ERROR] in FirstLayerDWM: {e}")
            Decision = ["general I encountered an error processing your request"]
        
        print(f"\nDecision : {Decision}\n")
        
        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])
        
        Merged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )
        
        # Image generation handling
        for query in Decision:
            if query.startswith("generate"):
                ImageGenerationQuery = query[len("generate"):].strip()
                if ImageGenerationQuery:
                    ImageExecution = True
                    break
        
        # Automation tasks
        for queries in Decision:
            if not TaskExecution and any(queries.startswith(func) for func in Functions):
                try:
                    run(Automation(list(Decision)))
                    TaskExecution = True
                except Exception as e:
                    print(f"[ERROR] in Automation: {e}")
                    ShowTextToScreen(f"{Assistantname} : Sorry, I couldn't complete that task.")
        
        # Image generation execution
        if ImageExecution:
            SetAssistantStatus("Generating Image...")
            ShowTextToScreen(f"{Assistantname} : Generating image of '{ImageGenerationQuery}'")
            
            try:
                # Check for required modules first
                try:
                    import PIL
                except ImportError:
                    ShowTextToScreen(f"{Assistantname} : Installing required image libraries...")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "pillow"], check=True)
                        import PIL  # Try importing again after installation
                    except subprocess.CalledProcessError:
                        ShowTextToScreen(f"{Assistantname} : Failed to install required libraries. Please install pillow manually.")
                        return

                os.makedirs(os.path.dirname(r"Frontend\Files\ImageGeneration.data"), exist_ok=True)
                
                with open(r"Frontend\Files\ImageGeneration.data", "w") as file:
                    file.write(f"{ImageGenerationQuery},True")
                
                try:
                    # Use the same python executable to ensure same environment
                    p1 = subprocess.Popen(
                        [sys.executable, r'Backend\ImageGeneration.py'],
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE, 
                        shell=False,
                        text=True
                    )
                    subprocesses.append(p1)
                    
                    # Wait and check result
                    sleep(2)  # Give more time for image generation
                    if p1.poll() is not None:
                        stderr = p1.stderr.read()
                        if stderr:
                            print(f"[ERROR] ImageGeneration failed: {stderr}")
                            if "ModuleNotFoundError" in stderr:
                                ShowTextToScreen(f"{Assistantname} : Required libraries missing. Please install pillow package.")
                            else:
                                ShowTextToScreen(f"{Assistantname} : Image generation failed. See logs for details.")
                    
                except Exception as e:
                    print(f"[ERROR] starting ImageGeneration: {e}")
                    ShowTextToScreen(f"{Assistantname} : Couldn't start image generation.")
                    
            except Exception as e:
                print(f"[ERROR] preparing image generation: {e}")
                ShowTextToScreen(f"{Assistantname} : Sorry, I encountered an error.")

        # Response handling
        if G and R or R:
            SetAssistantStatus("Searching ...")
            try:
                Answer = RealtimeSearchEngine(QueryModifier(Merged_query))
                ShowTextToScreen(f"{Assistantname} : {Answer}")
                SetAssistantStatus("Answering ...")
                TextToSpeech(Answer)
            except Exception as e:
                print(f"[ERROR] in RealtimeSearchEngine: {e}")
                ShowTextToScreen(f"{Assistantname} : I couldn't complete the search. Please check your internet connection.")
            return True
        else:
            for Queries in Decision:
                if "general" in Queries:
                    SetAssistantStatus("Thinking...")
                    try:
                        QueryFinal = Queries.replace("general ", "")
                        Answer = ChatBot(QueryModifier(QueryFinal))
                        ShowTextToScreen(f"{Assistantname} : {Answer}")
                        SetAssistantStatus("Answering ... ")
                        TextToSpeech(Answer)
                    except Exception as e:
                        print(f"[ERROR] in ChatBot: {e}")
                        ShowTextToScreen(f"{Assistantname} : I'm having trouble processing that request.")
                    return True
                elif "realtime" in Queries:
                    SetAssistantStatus("Searching ... ")
                    try:
                        QueryFinal = Queries.replace("realtime ", "")
                        Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
                        ShowTextToScreen(f"{Assistantname} : {Answer}")
                        SetAssistantStatus("Answering ... ")
                        TextToSpeech(Answer)
                    except Exception as e:
                        print(f"[ERROR] in RealtimeSearchEngine: {e}")
                        ShowTextToScreen(f"{Assistantname} : Search failed. Please check your connection.")
                    return True
                elif "exit" in Queries:
                    QueryFinal = "Okay, Bye!"
                    Answer = ChatBot(QueryModifier(QueryFinal))
                    ShowTextToScreen(f"{Assistantname} : {Answer}")
                    return True
    
    except Exception as e:
        print(f"[CRITICAL ERROR] in MainExecution: {e}")
        ShowTextToScreen(f"{Assistantname} : I encountered a serious error. Please try again.")
        return False

def FirstThread():
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()
            if CurrentStatus == "True":
                MainExecution()
            else:
                AIStatus = GetAssistantStatus()
                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available ...")
        except Exception as e:
            print(f"[THREAD ERROR] in FirstThread: {e}")
            sleep(1)

def SecondThread():
    try:
        GraphicalUserInterface()
    except Exception as e:
        print(f"[GUI ERROR] in SecondThread: {e}")

def cleanup_subprocesses():
    for process in subprocesses:
        try:
            process.terminate()
        except:
            pass

if __name__ == "__main__":
    try:
        InitializeRecursion()
        thread2 = threading.Thread(target=FirstThread, daemon=True)
        thread2.start()
        SecondThread()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"[MAIN ERROR] {e}")
    finally:
        cleanup_subprocesses()