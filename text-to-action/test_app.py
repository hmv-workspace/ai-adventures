import subprocess
import sys
import time

# List of user inputs to test
TEST_INPUTS = [
    "print hello world",
    "what's the time?",
    "what is the day today?",
    "show the current date and time",
    "list files in the current directory",
    "print hello world for 10 times with a delay of 2 second",
    "read the contents of a text-to-action/VISION_AND_ROADMAP.md",
    "fetch the current weather in London",
    "get the latest news headlines",
    "generate a random number between 1 and 100",
    "calculate the factorial of 5",
    "show the current working directory",
    "play summer of '69 by Bryan Adams",
    "buy woman's fossil watch",
    "display a multiplication table for 7"
]

APP_PATH = "app.py"


def run_test(input_text):
    """Run the app and send input_text, return output."""
    process = subprocess.Popen(
        [sys.executable, APP_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    output_lines = []
    try:
        # Read output until the prompt appears
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_lines.append(line)
            if "What would you like to do?" in line:
                break
        # Send the test input
        process.stdin.write(input_text + "\n")
        process.stdin.flush()
        # Read output until the prompt appears again (after execution)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_lines.append(line)
            if "What would you like to do?" in line or "bye" in input_text:
                break
        # Send 'bye' to exit
        process.stdin.write("bye\n")
        process.stdin.flush()
        # Read remaining output
        out, err = process.communicate(timeout=10)
        output_lines.append(out)
        return ''.join(output_lines), err
    except Exception as e:
        process.kill()
        return '', str(e)

def main():
    print("Running TextToAction app tests...\n")
    for idx, test_input in enumerate(TEST_INPUTS, 1):
        print(f"Test {idx}: {test_input}")
        output, error = run_test(test_input)
        if error:
            print(f"  ERROR: {error}")
        elif ("ImportError" in output or "Execution error" in output or "Maximum retries reached" in output):
            print(f"  FAIL: Execution error detected.")
            print(f"  Output: {output}")
            print(f"  Error: {error}")
        else:
            print(f"  PASS")
        print("-" * 40)

if __name__ == "__main__":
    main()
