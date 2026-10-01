# HW_monitor

# Camera and Microphone Access Monitor

A small Linux tool that tells you when a program starts using your webcam or mic.

```
hw_monitor.c -> project_mimi_group.py -> /tmp/hw_events.jsonl -> dashboard.py
```

## hw_monitor.c

This file is written in C and is built as a Linux kernel module. It plants two kprobes, one on `v4l2_ioctl` (camera) and one on `snd_pcm_ioctl` (microphone). Every ioctl sent to these devices passes through the probe. When the command is `VIDIOC_STREAMON` (camera) or `SNDRV_PCM_IOCTL_START` (microphone), it prints a line to the kernel log:

```
[HW_MONITOR] DEVICE=CAMERA, PID=1974, NAME=Discord, ACTION=RECORDING_STARTED
```

## project_mimi_group.py

This file is a Python script that runs as a background daemon. It follows the kernel log live with `journalctl -k -f` and matches the lines above with a regex. It ignores system processes (`systemd`, `pipewire`, `wireplumber`, ...) and repeated events from the same device within 5 seconds. Every event that passes is appended as one JSON line to `/tmp/hw_events.jsonl`, and a desktop notification is shown with the device, the app name and the action:

```json
{"timestamp": "2026-09-30 11:34:08", "device": "CAMERA", "pid": 1974, "process_name": "Discord", "action": "RECORDING_STARTED"}
```

## dashboard.py

This file is a Python desktop app built with CustomTkinter. It keeps reading `/tmp/hw_events.jsonl` in a background thread and adds every new event to a scrolling table (timestamp, device, PID, process, action). Camera events are shown in red and microphone events in orange. The buttons at the top let you show a single column, and in the All view two checkboxes filter the rows by camera or microphone.

## The files only agree on two formats

1. The kernel log line printed by `hw_monitor.c` and parsed by `project_mimi_group.py`:

```
   [HW_MONITOR] DEVICE=..., PID=..., NAME=..., ACTION=...
```

2. The JSON line written by `project_mimi_group.py` and read by `dashboard.py`, with the keys `timestamp`, `device`, `pid`, `process_name` and `action`.
