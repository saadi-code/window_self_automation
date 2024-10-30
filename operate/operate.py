import sys
import os
import time
import asyncio
import platform
import http.client
import json
import io
from pydub import AudioSegment
from pydub.playback import play
from prompt_toolkit.shortcuts import message_dialog
from prompt_toolkit import prompt
from operate.exceptions import ModelNotRecognizedException
from operate.models.prompts import USER_QUESTION, get_system_prompt
from operate.config import Config
from operate.utils.style import (
    ANSI_GREEN,
    ANSI_RESET,
    ANSI_YELLOW,
    ANSI_RED,
    ANSI_BRIGHT_MAGENTA,
    ANSI_BLUE,
    style,
)
from operate.utils.operating_system import OperatingSystem
from operate.models.apis import get_next_action

# Load configuration
config = Config()
operating_system = OperatingSystem()

def speak_with_deepgram(text):
    """
    Generate speech from text using Deepgram's API.
    """
    url = "api.deepgram.com"
    request_body = json.dumps({"text": text})
    headers = {
        "Authorization": "Token 25a30643a96d443cd94f1d79bf987cd35ba30d3e",  # Replace with your Deepgram API key
        "Content-Type": "application/json"
    }

    # Establish HTTPS connection
    conn = http.client.HTTPSConnection(url)

    # Send request to Deepgram API
    conn.request("POST", "/v1/speak?model=aura-asteria-en", request_body, headers)

    # Get response
    response = conn.getresponse()

    # Read the audio data from the response
    audio_data = response.read()

    # Close the connection
    conn.close()

    # Load the audio data into an AudioSegment
    audio = AudioSegment.from_mp3(io.BytesIO(audio_data))

    # Play the audio
    play(audio)

def main(model, terminal_prompt=None, voice_mode=False, verbose_mode=False):
    """
    Main function for the Self-Operating Computer.

    Parameters:
    - model: The model used for generating responses.
    - terminal_prompt: A string representing the prompt provided in the terminal.
    - voice_mode: A boolean indicating whether to enable voice mode.

    Returns:
    None
    """
    mic = None
    config.verbose = verbose_mode
    config.validation(model, voice_mode)

    if voice_mode:
        try:
            from whisper_mic import WhisperMic
            mic = WhisperMic()  # Initialize WhisperMic
        except ImportError:
            print("Voice mode requires the 'whisper_mic' module. Please install it using 'pip install -r requirements-audio.txt'")
            sys.exit(1)

    if not terminal_prompt:
        message_dialog(
            title="Self-Operating Computer",
            text="An experimental framework to enable multimodal models to operate computers",
            style=style,
        ).run()
    else:
        print("Running direct prompt...")

    if platform.system() == "Windows":
        os.system("cls")
    else:
        print("\033c", end="")

    if terminal_prompt:  # Terminal prompt passed as argument
        objective = terminal_prompt
    elif voice_mode:
        print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RESET} Listening for your command... (speak now)")
        try:
            objective = mic.listen()
        except Exception as e:
            print(f"{ANSI_RED}Error in capturing voice input: {e}{ANSI_RESET}")
            return  # Exit if voice input fails
    else:
        print(f"[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]\n{USER_QUESTION}")
        print(f"{ANSI_YELLOW}[User]{ANSI_RESET}")
        objective = prompt(style=style)

    system_prompt = get_system_prompt(model, objective)
    system_message = {"role": "system", "content": system_prompt}
    messages = [system_message]

    loop_count = 0
    session_id = None

    while True:
        if config.verbose:
            print("[Self-Operating Computer] loop_count", loop_count)
        try:
            # Use asyncio to run the get_next_action call
            operations, session_id = asyncio.run(get_next_action(model, messages, objective, session_id))

            stop = operate(operations, model)
            if stop:
                break

            loop_count += 1
            if loop_count > 10:
                break
        except ModelNotRecognizedException as e:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] -> {e} {ANSI_RESET}")
            break
        except Exception as e:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] -> {e} {ANSI_RESET}")
            break

def operate(operations, model):
    """
    Perform the operations received from the model.
    """
    if config.verbose:
        print("[Self-Operating Computer][operate]")

    for operation in operations:
        if config.verbose:
            print("[Self-Operating Computer][operate] operation", operation)

        # Wait one second between operations
        time.sleep(1)

        operate_type = operation.get("operation").lower()
        operate_thought = operation.get("thought")
        operate_detail = ""

        if config.verbose:
            print("[Self-Operating Computer][operate] operate_type", operate_type)
            print(f"this is a operate {operate_type}")
        
        # Speak the operation thought
        if operate_thought:
            speak_with_deepgram(operate_thought)

        if operate_type == "press" or operate_type == "hotkey":
            keys = operation.get("keys")
            operate_detail = keys
            operating_system.press(keys)
        elif operate_type == "write":
            content = operation.get("content")
            operate_detail = content
            operating_system.write(content)
        elif operate_type == "click":
            x = operation.get("x")
            y = operation.get("y")
            click_detail = {"x": x, "y": y}
            operate_detail = click_detail
            operating_system.mouse(click_detail)
        elif operate_type == "done":
            summary = operation.get("summary")
            print(f"[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]")
            print(f"{ANSI_BLUE}Objective Complete: {ANSI_RESET}{summary}\n")
            return True  # End the loop once the objective is complete
        else:
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] unknown operation response :({ANSI_RESET}")
            print(f"{ANSI_GREEN}[Self-Operating Computer]{ANSI_RED}[Error] AI response {ANSI_RESET}{operation}")
            return True  # Stop on unknown operation

        print(f"[{ANSI_GREEN}Self-Operating Computer {ANSI_RESET}|{ANSI_BRIGHT_MAGENTA} {model}{ANSI_RESET}]")
        print(f"{operate_thought}")
        print(f"{ANSI_BLUE}Action: {ANSI_RESET}{operate_type} {operate_detail}\n")

    return False  # Continue the loop

if __name__ == "__main__":
    # Entry point for the script; you may pass model, terminal prompt, etc.
    model = "your_model_here"  # Replace with your model
    main(model)