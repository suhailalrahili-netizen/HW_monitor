# Hardware Monitor Dashboard
 
A small desktop dashboard that shows camera and microphone usage events in real time, built with Python and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).
 
The dashboard only **reads** events. A separate process writes them to a file, and the dashboard displays them as they arrive.
 
## Features
 
- Live table that updates as new events are written to the file
- Column views: show only Timestamp, Device, PID, Process, or Action
- Camera / Microphone checkboxes (in the **All** view) to show only camera events, only microphone events, or both
- Camera events are shown in red, other devices in orange
- Dark mode UI
## Requirements
 
- Python 
- customtkinter
```bash
pip install customtkinter
```
 
## Run
 
```bash
python3 dashboard.py
```
 
## Event file
 
The dashboard watches this file:
 
```
~/.hw_events.jsonl
```
 
It is created automatically if it does not exist. Each line is one JSON event:
 
```json
{"timestamp": "2026-10-01 15:26:33", "device": "CAMERA", "pid": 13531, "process_name": "brave", "action": "RECORDING_STARTED"}
```
 
| Field          | Description                                   |
| -------------- | --------------------------------------------- |
| `timestamp`    | When the event happened                       |
| `device`       | Device name, e.g. `CAMERA` or `MICROPHONE`    |
| `pid`          | Process ID                                    |
| `process_name` | Name of the process using the device          |
| `action`       | What the process did                          |
 
To test without a monitor, append a line yourself:
 
```bash
echo '{"timestamp":"12:00:01","device":"CAMERA","pid":1234,"process_name":"test","action":"RECORDING_STARTED"}' >> ~/.hw_events.jsonl
```
 
## How to use
 
| Control                 | What it does                                          |
| ----------------------- | ----------------------------------------------------- |
| **All**                 | Shows every column and every event                    |
| **Timestamp / Device / PID / Process / Action** | Shows only that column |
| **camera** checkbox     | In **All** view, shows only camera events             |
| **microphone** checkbox | In **All** view, shows only microphone events         |
 
If neither checkbox is selected, all events are shown. If both are selected, camera and microphone events are shown.
 
## Notes
 
- The device filter matches by name: any device containing `CAM` counts as a camera, and any containing `MIC` counts as a microphone.
- Events are kept in memory only, so they are cleared when the dashboard is closed, but the event file stays.
 
