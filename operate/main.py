# """
# Self-Operating Computer
# """
# import argparse
# from operate.utils.style import ANSI_BRIGHT_MAGENTA
# from operate.operate import main


# def main_entry():
#     parser = argparse.ArgumentParser(
#         description="Run the self-operating-computer with a specified model."
#     )
#     parser.add_argument(
#         "-m",
#         "--model",
#         help="Specify the model to use",
#         required=False,
#         default="gpt-4-with-ocr",
#     )

#     # Add a voice flag
#     parser.add_argument(
#         "--voice",
#         help="Use voice input mode",
#         action="store_true",
#     )
    
#     # Add a flag for verbose mode
#     parser.add_argument(
#         "--verbose",
#         help="Run operate in verbose mode",
#         action="store_true",
#     )
    
#     # Allow for direct input of prompt
#     parser.add_argument(
#         "--prompt",
#         help="Directly input the objective prompt",
#         type=str,
#         required=False,
#     )

#     try:
#         args = parser.parse_args()
#         main(
#             args.model,
#             terminal_prompt=args.prompt,
#             voice_mode=args.voice,
#             verbose_mode=args.verbose
#         )
#     except KeyboardInterrupt:
#         print(f"\n{ANSI_BRIGHT_MAGENTA}Exiting...")


# if __name__ == "__main__":
#     main_entry()

import time
import argparse
import speech_recognition as sr
from operate.utils.style import ANSI_BRIGHT_MAGENTA
from operate.exceptions import ModelNotRecognizedException
from operate.operate import main as operate_main

# Global variable to control the shutdown
operation_running = True

def listen_for_commands(recognizer, source, model, voice_mode, verbose_mode):
    """
    Continuously listen for commands until the user says 'shutdown' or an external shutdown is triggered.
    """
    commands = []  # To store user commands
    print("Listening for your commands (say 'shutdown' to stop):")

    while operation_running:  # Check if operation is still running
        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")

            if "shutdown" in command:
                print("Shutting down...")
                return "shutdown", None  # Signal shutdown

            # If a command is recognized, add it to the list
            if command:  
                commands.append(command)
                print(f"Command added: {command}")
                print("Waiting for 4 seconds before accepting more commands...")
                time.sleep(4)  # Wait for 4 seconds

                if commands:
                    terminal_prompt = " ".join(commands)  # Join all collected commands
                    print(f"Executing commands: {terminal_prompt}")
                    operate_main(
                        model=model,
                        terminal_prompt=terminal_prompt,
                        voice_mode=voice_mode,
                        verbose_mode=verbose_mode
                    )
                    commands.clear()  # Clear commands after execution
                    
                    # Ask for further assistance after completing an action
                    further_assistance(recognizer, source)

        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return "error", None

def further_assistance(recognizer, source):
    """Prompt the user for further assistance after an action is complete."""
    print("How can I assist you further?")
    try:
        audio = recognizer.listen(source)
        command = recognizer.recognize_google(audio).lower()
        print(f"Further assistance command: {command}")

        if "shutdown" in command:
            print("Shutting down...")
            return "shutdown", None  # Signal shutdown
        else:
            print("Continuing to listen for further commands...")
            time.sleep(2)  # Wait briefly before listening again
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")

def main_entry(model, voice_mode, verbose_mode):
    global operation_running  # Declare the global variable to control shutdown
    print(f"Debug: Received model argument: {model}")  # Debug print
    recognized_models = ["gpt-4-with-ocr", "llava"]  # Ensure this includes all valid models
    if model not in recognized_models:
        print(f"Debug: Unrecognized model: {model}")  # Debug print
        raise ModelNotRecognizedException(f"Model not recognized: {model}. Please use one of {recognized_models}")
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        listen_for_commands(recognizer, source, model, voice_mode, verbose_mode)

# Function to stop the operation
def stop_operation():
    global operation_running
    operation_running = False  # Set to False to stop the loop

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the self-operating-computer with a specified model.")
    parser.add_argument("-m", "--model", help="Specify the model to use", required=False, default="gpt-4-with-ocr")
    parser.add_argument("--voice", help="Use voice input mode", action="store_true")
    parser.add_argument("--verbose", help="Run operate in verbose mode", action="store_true")
    args = parser.parse_args()

    main_entry(args.model, args.voice, args.verbose)
