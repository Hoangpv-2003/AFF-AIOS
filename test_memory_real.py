import subprocess
import time

def run_test():
    cmd = ["./.venv/Scripts/python.exe", "tools/cli_agent.py", "--real"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding='utf-8'
    )

    def send_input(text):
        print(f"--- SENDING: {text} ---")
        process.stdin.write(text + "\n")
        process.stdin.flush()

    # Step 1: Initial query
    send_input("Tìm kiếm doanh thu VinFast năm 2025")
    
    # Wait and read output
    # Note: We need a better way to wait for completion than just time.sleep
    # For now, we'll wait and then send turn 2.
    time.sleep(120) 
    
    # Step 2: Follow-up using memory
    send_input("Gửi báo cáo đó cho tuanm7530@gmail.com")
    
    time.sleep(180)
    
    send_input("exit")
    
    stdout, stderr = process.communicate()
    
    with open("test_results.log", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n" + stdout)
        f.write("\n\nSTDERR:\n" + stderr)
    
    print("Test finished. Results in test_results.log")

if __name__ == "__main__":
    run_test()
