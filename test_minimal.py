import subprocess
import os

def run_test():
    cmd = ["./.venv/Scripts/python.exe", "tools/cli_agent.py", "--real"]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        bufsize=1
    )

    prompt = "Tìm kiếm doanh thu VinFast năm 2025 và gửi báo cáo đó cho tuanm7530@gmail.com\nexit\n"
    
    # Mirror output
    import threading
    def mirror(pipe, label):
        with open(f"final_{label}.log", "w", encoding="utf-8") as f:
            for line in pipe:
                print(f"[{label}] {line.strip()}")
                f.write(line)
                f.flush()

    threading.Thread(target=mirror, args=(process.stdout, "stdout"), daemon=True).start()
    threading.Thread(target=mirror, args=(process.stderr, "stderr"), daemon=True).start()

    process.stdin.write(prompt)
    process.stdin.flush()
    
    process.wait(timeout=600)
    print("Test finished.")

if __name__ == "__main__":
    run_test()
