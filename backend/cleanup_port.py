import os
import subprocess

def cleanup_port(port: int = 8000):
    try:
        out = subprocess.getoutput("netstat -ano")
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    print(f"[INFO] Freeing port {port} (stopping PID {pid})...")
                    os.system(f"taskkill /PID {pid} /F >nul 2>&1")
    except Exception as e:
        print(f"[WARN] Port check error: {e}")

if __name__ == "__main__":
    cleanup_port(8000)
