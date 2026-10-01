# Hardware Monitor Daemon

`project_mimi_group.py` is a Linux background daemon that watches the kernel log
for camera and microphone access events. For each accepted event it saves a JSON
record and shows a desktop notification.

## How it works

1. Detaches from the terminal and runs in the background.
2. Streams kernel messages in real time with `journalctl -k -f`.
3. Parses lines in this format:

```
   [HW_MONITOR] DEVICE=CAMERA, PID=1974, NAME=Discord, ACTION=OPEN
```
4. Ignores system processes and repeated events.
5. Appends each accepted event to `/home/<user>/.hw_events.jsonl`:

```json
   {"timestamp": "2026-09-30 11:34:50", "device": "CAMERA", "pid": 1974, "process_name": "Discord", "action": "OPEN"}
```
6. Shows a desktop notification with the device, process name and action.

## Code Components

### 1. User and privilege context
```python
SUDO_USER = os.environ.get("SUDO_USER") or "suhail"
USER_UID = pwd.getpwnam(SUDO_USER).pw_uid   # falls back to 1000 on error
```
The daemon runs as root (started with `sudo`), but the desktop session belongs to
the normal user. `SUDO_USER` is the name of the user who ran `sudo`, and
`pwd.getpwnam` returns that user's numeric UID, which is needed to locate the
user's D-Bus session bus.

### 2. Log parser (`LOG_PATTERN`)
A regular expression with named groups extracts four fields:

| Group | Meaning |
|---|---|
| `device` | `CAMERA` or `MIC` |
| `pid` | Process ID of the application |
| `process` | Process name (read up to the next comma, so names with spaces work) |
| `action` | Action reported in the log line (e.g. `OPEN`) |

`search()` is used instead of `match()`, so any prefix before the tag is ignored.
Lines that do not match are skipped.

### 3. Daemonization (`daemonize`)
| Step | Reason |
|---|---|
| First `fork()`, parent exits | Returns the shell prompt; the child is not a process-group leader (required for `setsid`) |
| `chdir("/")` | Does not block unmounting the starting directory |
| `setsid()` | New session, detached from the controlling terminal |
| `umask(0)` | Files are created with the permissions requested by `open()` |
| Second `fork()`, parent exits | A session leader could re-acquire a terminal; the grandchild cannot |
| `dup2` on stdin | stdin is redirected to `/dev/null` |

### 4. Filtering and throttling (`should_notify`)
- **Ignore list:** events whose process name is in `IGNORED_PROCESSES`
  (`VideoDevicePoll`, `kernel`, `systemd`, `pipewire`, `wireplumber`) are dropped.
- **Cooldown:** after an accepted event, any further event for the same device
  within `COOLDOWN_SECONDS` (5 seconds) is dropped. The last event time per device
  is stored in the `LAST_EVENT_TIMES` dictionary.

### 5. Event storage
Accepted events are appended to `/home/<SUDO_USER>/.hw_events.jsonl` in JSON
Lines format (one JSON object per line), so other programs can read the file
line by line. The file is stored in the desktop user's home directory, so it
survives reboots. A write failure is ignored so the daemon keeps running.

### 6. Desktop notification (`send_desktop_notification`)
`notify-send` talks to the desktop's notification service over the user's D-Bus
session bus. Because the daemon runs as root, a plain `notify-send` does not
reach the user's desktop. The function runs the command as the original user and
passes the required environment:

```python
["sudo", "-u", SUDO_USER, "env",
 "DISPLAY=:0",
 "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus",
 "XAUTHORITY=/home/<user>/.Xauthority",
 "notify-send", "-u", "critical", title, message]
```

## Main Execution Flow

1. `daemonize()` detaches the script from the terminal.
2. `journalctl -k -f --output=cat` is started as a child process
   (`-k` kernel messages, `-f` follow new messages, `--output=cat` message text only).
3. For each line read from the child's output:
   1. Strip whitespace and skip empty lines.
   2. Apply `LOG_PATTERN` and skip lines that do not match.
   3. Run `should_notify` and skip ignored or throttled events.
   4. Build the event dictionary with a local timestamp.
   5. Append it to `/home/<SUDO_USER>/.hw_events.jsonl`.
   6. Send the desktop notification.
4. On `KeyboardInterrupt`, the `finally` block terminates the `journalctl` child.

## Usage

```bash
# Start the daemon (from the desktop user's account)
sudo python3 project_mimi_group.py

# Simulate an event (without the kernel module)
echo "[HW_MONITOR] DEVICE=CAMERA, PID=1974, NAME=Discord, ACTION=OPEN" | sudo tee /dev/kmsg

# Check the result
cat ~/.hw_events.jsonl

# Stop the daemon
sudo pkill -f project_mimi_group
```

## Requirements
- Linux with systemd (`journalctl`) and a desktop environment with `notify-send`
- Started with `sudo` from the desktop user's account
- Python 3 (standard library only)