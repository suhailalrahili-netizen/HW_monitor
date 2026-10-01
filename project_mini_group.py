import pwd
import subprocess
import re 
import json 
import os 
import sys
import time
from datetime import datetime

SUDO_USER = os.environ.get("SUDO_USER") or "suhail"
try:
    USER_UID = pwd.getpwnam(SUDO_USER).pw_uid
except Exception:
    USER_UID = 1000

LOG_PATTERN = re.compile(
    r"\[HW_MONITOR\]\s+DEVICE=(?P<device>[^,]+),\s*PID=(?P<pid>\d+),"
    r"\s*NAME=(?P<process>[^,]+),\s*ACTION=(?P<action>\S+)"
)

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e}\n")
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e}\n")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()

    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, sys.stdin.fileno())

IGNORED_PROCESSES = ["VideoDevicePoll", "kernel", "systemd", "wireplumber"]

LAST_EVENT_TIMES = {}
COOLDOWN_SECONDS = 5  

def should_notify(device, process_name):
    if process_name in IGNORED_PROCESSES:
        return False
    
    current_time = time.time()
    
    if device in LAST_EVENT_TIMES:
        if current_time - LAST_EVENT_TIMES[device] < COOLDOWN_SECONDS:
            return False  
            
    LAST_EVENT_TIMES[device] = current_time
    return True

def send_desktop_notification(device, process_name, action):
    popup_title = "Hardware Event Detected"
    popup_message = f"Device: {device}\nProcess: {process_name}\nAction: {action}"
    
    xauth = f"/home/{SUDO_USER}/.Xauthority"
    dbus_bus = f"unix:path=/run/user/{USER_UID}/bus"
    
    cmd = [
        "sudo", "-u", SUDO_USER,
        "env",
        "DISPLAY=:0",
        f"DBUS_SESSION_BUS_ADDRESS={dbus_bus}",
        f"XAUTHORITY={xauth}",
        "notify-send", "-u", "critical", popup_title, popup_message
    ]
    
    subprocess.run(cmd, capture_output=True, text=True)

def main():
    daemonize()

    process = subprocess.Popen(
        ["journalctl", "-k", "-f", "--output=cat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            match = LOG_PATTERN.search(line)
            if not match:
                continue
            
            data = match.groupdict()
            device = data["device"].strip()
            pid = int(data["pid"])
            process_name = data["process"].strip()
            
            if not should_notify(device, process_name):
                continue

            action = data["action"].strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            event_data = {
                "timestamp": timestamp,
                "device": device,
                "pid": pid,
                "process_name": process_name,
                "action": action,
            }
            
            try:
                log_file = f"/home/{SUDO_USER}/.hw_events.jsonl"
                with open(log_file, "a") as f:
                    f.write(json.dumps(event_data) + "\n")
            except Exception as e:
                import traceback
                try:
                    with open("/var/log/hw_script_errors.log", "a") as err_file:
                        err_file.write(f"[{timestamp}] File write failed: {str(e)}\n")
                        err_file.write(traceback.format_exc() + "\n")
                except:
                    pass

            send_desktop_notification(device, process_name, action)

    except KeyboardInterrupt:
        pass  
    finally:
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()