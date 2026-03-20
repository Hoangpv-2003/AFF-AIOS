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
        encoding='utf-8',
        bufsize=1
    )

    prompt = "Tìm kiếm doanh thu VinFast năm 2025 và gửi báo cáo đó cho tuanm7530@gmail.com"
    print(f"--- SENDING: {prompt} ---")
    process.stdin.write(prompt + "\n")
    process.stdin.flush()
    
    # Wait for completion (generous timeout)
    time.sleep(300)
    
    process.stdin.write("exit\n")
    process.stdin.flush()
    
    stdout, stderr = process.communicate()
    
    with open("one_shot_results.log", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n" + stdout)
        f.write("\n\nSTDERR:\n" + stderr)
    
    print("Test finished. Results in one_shot_results.log")

if __name__ == "__main__":
    run_test()
