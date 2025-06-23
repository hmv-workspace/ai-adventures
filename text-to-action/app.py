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
from ollama import chat, ChatResponse

__VERSION__ = "1.0.0"
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

    generated_code = generate_code(prompt)
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
        print("\nGenerated code to be executed in sandbox:\n" + "-"*40)
        print(code)
        print("-"*40)
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

#
# We need to accept user's input and get it execute by preparing the required code. For example:
#
# 1.   print hello world
# 2.   subscribe to 'mqtt/python' topic on 'broker.hivemq.com' and keep waiting for message to come. Once message arrived print it.
# 3.   publish a 'hello world' message to 'mqtt/python' topic on 'broker.hivemq.com'
#

while True:
    try:
        user_input = input("\nWhat would you like to do?\n> ")
        if user_input == 'bye':
            break

        # TODO:
        # At this time assumption is user is giving a specific input of executing a task
        # with dynamic programming approach. Going forward, first we want to know what is
        # query (seeking info, request for task execution, etc.) and
        # based on that we want to perform tasks.

        perform_task(user_input)

    except KeyboardInterrupt:
        pass
    except Exception as error:
        print(f"{type(error).__name__} was raised: {error}")
