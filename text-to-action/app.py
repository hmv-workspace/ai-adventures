# -*- coding: utf-8 -*-
"""
Text to Action: This is script that takes user's text input,
tries to understand the requirement, generates required code
and execute it in possible ways.
"""

import os
import re
import time
import threading
import requests
import sys
from ollama import chat, ChatResponse

__VERSION__ = "0.0.2"
print(f"""
Welcome to TextToAction v{__VERSION__}!

This application turns your natural language instructions into executable task using AI. It can:
- Fetch real-world data from the internet using public APIs (e.g., weather, news, etc.)
- Read and write files, list directories, and perform basic file operations
- Render images or play music (if the required libraries are available)
- Run code in a restricted sandbox for safety

Type your request in plain English and TextToAction will generate and execute the code for you.

Example tasks:
  1. print hello world
  2. what's the time?
  3. publish a 'hello world' message to 'mqtt/python' topic on 'broker.hivemq.com'
  4. save text to a file
  5. list files in the current directory
  6. play a .wav file (if supported)

Type 'bye' to quit.
""")

OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'qwen2.5-coder:7b')

def extract_code_blocks(text):
    pattern = r""

    # Define the regular expression pattern to match the code blocks
    if "```python" in text:
        pattern = r"```python\s+(.*?)\s+```"
    elif "```" in text:
        pattern = r"```\s+(.*?)\s+```"
    if pattern:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            code_blocks = ''
            for c in matches:
                code_blocks += c
            return code_blocks.strip()
    # Fallback: return the whole text if no code block found
    return text.strip()

def generate_code(prompt):
    """Generate code for the given prompt using Ollama chat API"""
    try:
        response: ChatResponse = chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ]
        )
        return extract_code_blocks(response.message.content.strip())
    except Exception as error:
        print(f"Ollama package error: {error}")
        return ''

def spinner_animation(stop_event, message="Reviewing your request..."):
    spinner = ['|', '/', '-', '\\']
    idx = 0
    # sys.stdout.write(message + ' ')
    sys.stdout.flush()
    while not stop_event.is_set():
        sys.stdout.write(spinner[idx % len(spinner)])
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\b')
        idx += 1
    sys.stdout.write('\b' + ' ' * len(spinner[idx % len(spinner)]) + '\b')  # Clear spinner
    sys.stdout.write('\n')
    sys.stdout.flush()

def find_task(user_input):
    """Prepare prompt from user instructions"""
    prompt = (
        "You need to come up with a Python script that can be executed right away to fulfill the following user input: \""
        + user_input +
        "\". If the task requires real-world data (like weather, news, etc.), use the 'requests' library to fetch it from a public API. "
        "If the information can be obtained locally (like the current time or date), use Python's standard libraries (like datetime) instead of an API. "
        "If the task requires file, image, or music access, use the built-in 'open', 'os', or pre-imported libraries directly (no import statement needed). "
        "Do not use hardcoded or made-up values. Make sure to return only the python code without any additional text or explanation."
    )

    # Animation spinner setup
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner_animation, args=(stop_event,))
    spinner_thread.start()
    try:
        generated_code = generate_code(prompt)
    finally:
        stop_event.set()
        spinner_thread.join()
    return generated_code

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    allowed = {'datetime', 'time', 'threading', 'requests'}
    if name in allowed:
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError(f"Import of '{name}' is not allowed in sandbox.")

def perform_task(instructions):
    """Perform given task in a restricted (sandboxed) environment"""
    code = ""
    max_retries = 3
    attempt = 0
    # Define a restricted set of built-ins
    safe_builtins = {
        'print': print,
        'range': range,
        'len': len,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'enumerate': enumerate,
        'zip': zip,
        'min': min,
        'max': max,
        'sum': sum,
        'abs': abs,
        'time': time,
        'threading': threading,
        'requests': requests,
        'open': open,  # Allow file access (use with caution)
        '__import__': safe_import,
    }
    sandbox_globals = {
        '__builtins__': safe_builtins,
        'time': time,
        'threading': threading,
        'requests': requests,
        'os': os,  # Allow os operations (use with caution)
    }
    while attempt < max_retries:
        try:
            code = find_task(instructions)
        except Exception as error:
            print(f"{type(error).__name__} was raised: {error}")

        try:
            compiled_code = compile(code, "<string>", "exec")
            exec(compiled_code, sandbox_globals)
            break
        except Exception as error:
            print(f"Execution error: {type(error).__name__}: {error}")
            attempt += 1
            if attempt < max_retries:
                print(f"Retrying... ({attempt}/{max_retries})")
            else:
                print("Maximum retries reached. Task failed.")

while True:
    try:
        user_input = input("\nWhat would you like to do?\n> ")
        if user_input == 'bye':
            break

        perform_task(user_input)

    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"{type(error).__name__} was raised: {error}")
