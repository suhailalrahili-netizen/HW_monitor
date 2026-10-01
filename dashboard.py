import json
import threading
import time
import customtkinter as ctk
import os.path


ctk.set_appearance_mode("Dark")

class MonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Hardware Monitor")
        self.geometry("750x400")

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, fill="x", padx=15)

        for i in range(6):
             self.button_frame.columnconfigure(i, weight=1)

        ctk.CTkButton(self.button_frame, text="All", command=lambda: self.set_filter("ALL")).grid(row=0, column=0, padx=2, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Timestamp", command=lambda: self.set_filter("TIMESTAMP")).grid(row=0, column=1, padx=2, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Device", command=lambda: self.set_filter("DEVICE")).grid(row=0, column=2, padx=2, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="PID", command=lambda: self.set_filter("PID")).grid(row=0, column=3, padx=2, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Process", command=lambda: self.set_filter("PROCESS_NAME")).grid(row=0, column=4, padx=2, pady=5, sticky="ew")
        ctk.CTkButton(self.button_frame, text="Action", command=lambda: self.set_filter("ACTION")).grid(row=0, column=5, padx=2, pady=5, sticky="ew")


        self.camera = ctk.BooleanVar(value = False)
        self.microphone = ctk.BooleanVar(value = False)


        self.cb_frame = ctk.CTkFrame(self.button_frame, fg_color = "transparent")
        self.cb_frame.grid(row = 1, column = 0, columnspan = 6, padx = 6, sticky = "w")

        self.camera_cb = ctk.CTkCheckBox(self.cb_frame, text = "camera", variable= self.camera, command = self.refresh_table)
        self.camera_cb.pack(side = "left", padx = (0,15), pady = 5)

        self.mic_cb = ctk.CTkCheckBox(self.cb_frame, text = "microphone", variable= self.microphone, command = self.refresh_table)
        self.mic_cb.pack(side = "left", pady = 5)


        self.scroll_frame = ctk.CTkScrollableFrame(self, width=900, height=450)
        self.scroll_frame.pack(pady=20, fill="both", expand=True)

        self.all_events = []
        self.current_filter = "ALL"
        self.row_count = 0

        self.refresh_table()

        threading.Thread(target=self.watch_file, daemon=True).start()

    def set_filter(self, filter_type):
        self.current_filter = filter_type

        if filter_type == "ALL":
             self.cb_frame.grid()
        else:
             self.cb_frame.grid_remove()

        self.refresh_table()


    def matches(self, data):

         if self.current_filter != "ALL":
              return True
         cam = self.camera.get()
         mic = self.microphone.get()
         if not cam and not mic:
              return True
         device = str(data.get("device", "")).upper()
         return (cam and "CAM" in device) or (mic and "MIC" in device)

    def add_event(self, data):
         self.all_events.append(data)
         if self.matches(data):
              self.render_row(data)


    def refresh_table(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if self.current_filter == "ALL":
            headers = ["timestamp", "device", "pid", "process_name", "action"]
        elif self.current_filter == "TIMESTAMP":
                headers = ["timestamp"]
        elif self.current_filter == "DEVICE":
                headers = ["device"]
        elif self.current_filter == "PID":
                headers = ["pid"]
        elif self.current_filter == "PROCESS_NAME":
                headers = ["process_name"]
        elif self.current_filter == "ACTION":
                headers = ["action"]

        for col_index, text in enumerate(headers):
            label = ctk.CTkLabel(self.scroll_frame, text=text, font=("Arial", 12, "bold"))
            label.grid(row=0, column=col_index, padx=15, pady=5)

        self.row_count = 0
        for data in list(self.all_events):
             if self.matches(data):
                self.render_row(data)


    def render_row(self, data):
         self.row_count += 1

         if self.current_filter == "ALL":
            ctk.CTkLabel(self.scroll_frame, text=data["timestamp"]).grid(row=self.row_count, column=0, padx=15, pady=5)
            dev_color = "red" if "CAM" in str(data["device"]).upper() else "orange"
            ctk.CTkLabel(self.scroll_frame, text=data["device"], text_color=dev_color).grid(row=self.row_count, column=1, padx=15, pady=5)
            ctk.CTkLabel(self.scroll_frame, text=str(data["pid"])).grid(row=self.row_count, column=2, padx=15, pady=5)
            ctk.CTkLabel(self.scroll_frame, text=data["process_name"]).grid(row=self.row_count, column=3, padx=15, pady=5)
            ctk.CTkLabel(self.scroll_frame, text=data["action"]).grid(row=self.row_count, column=4, padx=15, pady=5)

         elif self.current_filter == "TIMESTAMP":
            ctk.CTkLabel(self.scroll_frame, text=data["timestamp"]).grid(row=self.row_count, column=0, padx=15, pady=5)

         elif self.current_filter == "DEVICE":
            ctk.CTkLabel(self.scroll_frame, text=data["device"]).grid(row=self.row_count, column=0, padx=15, pady=5)

         elif self.current_filter == "PID":
            ctk.CTkLabel(self.scroll_frame, text=str(data["pid"])).grid(row=self.row_count, column=0, padx=15, pady=5)

         elif self.current_filter == "PROCESS_NAME":
            ctk.CTkLabel(self.scroll_frame, text=data["process_name"]).grid(row=self.row_count, column=0, padx=15, pady=5)
         elif self.current_filter == "ACTION":
            ctk.CTkLabel(self.scroll_frame, text=data["action"]).grid(row=self.row_count, column=0, padx=15, pady=5)


    def watch_file(self):
        file_path = os.path.expanduser("~/.hw_events.jsonl")
        
        if not os.path.exists(file_path):
            open(file_path, "w").close()

        with open(file_path, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue

                line_str = line.strip()
                if not line_str:
                    continue

                try:
                    data = json.loads(line_str)
                    # self.all_events.append(data)
                    self.after(0, self.add_event, data)
                except Exception as e:
                    print(f"Error parsing line: {e}")

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()