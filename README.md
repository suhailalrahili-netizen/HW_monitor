# HW_monitor

A Linux tool that tells you when a program starts using your webcam or mic.

```
kernel module -> python parser & notifier -> python UI
```

## hw_monitor.c

This file is written in C and is built as a Linux kernel module. It plants two kprobes, one on `v4l2_ioctl` (camera) and one on `snd_pcm_ioctl` (microphone). Every ioctl sent to these devices passes through the probe. When the command is `VIDIOC_STREAMON` (camera) or `SNDRV_PCM_IOCTL_START` (microphone), it prints a line to the kernel log:

```
[HW_MONITOR] DEVICE=CAMERA, PID=1974, NAME=Discord, ACTION=RECORDING_STARTED
```

## project_mini_group.py

This file is a Python script that runs as a background daemon. It follows the kernel log live with `journalctl -k -f` and matches the lines above with a regex. It ignores system processes (`systemd`, `wireplumber`, ...) and repeated events from the same device within 5 seconds. Every event that passes is appended as one JSON line to `~/.hw_events.jsonl`, and a desktop notification is shown with the device, the app name and the action:

```json
{"timestamp": "2026-09-30 11:34:08", "device": "CAMERA", "pid": 1974, "process_name": "Discord", "action": "RECORDING_STARTED"}
```

## dashboard.py

This file is a Python desktop app built with CustomTkinter. It keeps reading `~/.hw_events.jsonl` and adds every new event to a scrolling table (timestamp, device, PID, process, action). Camera events are shown in red and microphone events in orange. The buttons at the top let you show a single column, and in the All view two checkboxes filter the rows by camera or microphone.

## The files only agree on two formats

1. The kernel log line printed by `hw_monitor.c` and parsed by `project_mini_group.py`:

```
   [HW_MONITOR] DEVICE=..., PID=..., NAME=..., ACTION=...
```

2. The JSON line written by `project_mini_group.py` and read by `dashboard.py`, with the keys `timestamp`, `device`, `pid`, `process_name` and `action`.

## Installation and Usage

### Prerequisites
Ensure you have the standard Linux build tools and kernel headers installed for the C module, along with the required Python libraries for the UI:
```bash
sudo apt install build-essential linux-headers-$(uname -r)
pip3 install customtkinter
```

### 1. Build and Load the Kernel Module (make sure your working directory is kernel_module)
Compile the C code into a kernel object and insert it into the kernel space:
```bash
make
sudo insmod hw_monitor.ko
```
*(Note: To stop monitoring and remove the module later, run `sudo rmmod hw_monitor`)*

### 2. Start the Background Parser
Run the daemon script with root privileges so it can read the live kernel logs. This process will detach from the terminal and run silently in the background:
```bash
sudo python3 project_mini_group.py
```

### 3. Launch the Dashboard
Start the CustomTkinter graphical interface to view the live logs. This command will consume the active terminal session until you close the application window:
```bash
python3 dashboard.py
```