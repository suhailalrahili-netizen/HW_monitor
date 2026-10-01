# Kernel Module

A kernel module that detects when the camera or microphone is actively recording.

## How It Works
This module uses **Kprobes** to hook directly into the Linux kernel's functions. It intercepts `ioctl` system calls right before they execute, reading the raw CPU registers to determine exactly what hardware command is being sent.

- **Camera Hook:** Attaches to `v4l2_ioctl`. Checks if the `RSI` register contains `VIDIOC_STREAMON`.
- **Microphone Hook:** Attaches to `snd_pcm_ioctl`. Checks if the `RSI` register contains `SNDRV_PCM_IOCTL_START` and verifies the ALSA substream is flagged for `CAPTURE` (ignores speakers).

## Log Output
The module writes directly to the kernel ring buffer. You can view the logs using `dmesg -w`. 

Example output: \
`[HW_MONITOR] DEVICE=CAMERA, PID=5394, NAME=Discord, ACTION=RECORDING_STARTED` \
`[HW_MONITOR] DEVICE=MIC, PID=1306, NAME=pipewire, ACTION=RECORDING_STARTED`

*Note: The module logs the Thread Group Leader (tgid) to show the main application PID and name, rather than individual sub thread IDs.*

## Building and Running
1. Compile the module:
   ```bash
   make
   ```
2. Insert the module into the kernel:
   ```bash
   sudo insmod hw_monitor.ko
   ```
3. Remove the module:
   ```bash
   sudo rmmod hw_monitor
   ```

## Architecture Notes
- Due to modern Linux multimedia stacks, video/audio requests routed through PipeWire will show `pipewire` (PID 1306) as the requesting process. Direct hardware requests from other processes will show the native application name.