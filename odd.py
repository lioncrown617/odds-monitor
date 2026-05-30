Last login: Sat May 30 12:27:20 on ttys003
lioncrown@lioncrowndeMacBook-Neo ~ % vi odd.py
lioncrown@lioncrowndeMacBook-Neo ~ % cd templates 
lioncrown@lioncrowndeMacBook-Neo templates % ls -tlr
total 1120
-rw-r--r--  1 lioncrown  staff  12287 17  5 18:12 index.old
-rw-r--r--  1 lioncrown  staff  18927 17  5 18:39 index.old1
-rw-r--r--  1 lioncrown  staff  20521 17  5 18:53 index.old2
-rw-r--r--  1 lioncrown  staff  23137 17  5 19:10 index.old3
-rw-r--r--@ 1 lioncrown  staff  25880 19  5 20:31 index.old4
-rw-r--r--@ 1 lioncrown  staff  27899 19  5 21:18 index.old5
-rw-r--r--  1 lioncrown  staff  28000 19  5 22:41 index.keep
-rw-r--r--  1 lioncrown  staff  26608 20  5 22:03 index.bak
-rw-r--r--  1 lioncrown  staff  13122 21  5 22:00 index.win
-rw-r--r--  1 lioncrown  staff  10266 21  5 23:37 index.html.keep
-rw-r--r--  1 lioncrown  staff  13122 22  5 21:40 index.html.noadrci
-rw-r--r--  1 lioncrown  staff  17315 22  5 21:55 index.20260523
-rw-r--r--  1 lioncrown  staff  20250 24  5 12:04 index.202605241.html
-rw-r--r--  1 lioncrown  staff  20480 24  5 12:16 index.html.202505242
-rw-r--r--  1 lioncrown  staff  21799 24  5 12:39 index.html.202505243
-rw-r--r--  1 lioncrown  staff  21911 24  5 12:46 index.html.202505244
-rw-r--r--  1 lioncrown  staff  21354 24  5 13:20 index.html.2025245
-rw-r--r--  1 lioncrown  staff  20771 24  5 13:51 index.html.202504256
-rw-r--r--  1 lioncrown  staff  20091 24  5 14:22 index.html.ok
-rw-r--r--  1 lioncrown  staff  21891 24  5 17:44 index.html.freeze
-rw-r--r--  1 lioncrown  staff  21784 24  5 18:43 index.night2
-rw-r--r--  1 lioncrown  staff  15584 24  5 23:09 index.html.night
-rw-r--r--  1 lioncrown  staff  15474 24  5 23:51 index.html.veryok
-rw-r--r--@ 1 lioncrown  staff  23213 30  5 15:33 index.html.veryok2
-rw-r--r--  1 lioncrown  staff  19548 30  5 22:10 index.html.veryok3
-rw-r--r--  1 lioncrown  staff  20796 30  5 22:36 index.html
lioncrown@lioncrowndeMacBook-Neo templates % mv index.html index.html.veryok4
lioncrown@lioncrowndeMacBook-Neo templates % vi index.html
lioncrown@lioncrowndeMacBook-Neo templates % cd ..
lioncrown@lioncrowndeMacBook-Neo ~ % vi odd.py
lioncrown@lioncrowndeMacBook-Neo ~ % vi odd.py
lioncrown@lioncrowndeMacBook-Neo ~ % top
lioncrown@lioncrowndeMacBook-Neo ~ % vi tmp

[No write since last change]

Press ENTER or type command to continue
import os   
import json 
import time
import threading
from datetime import datetime
from collections import defaultdict, deque
from zoneinfo import ZoneInfo 

HKT = ZoneInfo("Asia/Hong_Kong")

# Replace every occurrence of:
    
# With:
now = datetime.now(HKT).strftime('%H:%M:%S')

import requests
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

NODE_API = os.environ.get("NODE_API", "http://localhost:3000/odds")

def _deque5():
    return deque(maxlen=5)

def _deque60():
    return deque(maxlen=60)
search hit BOTTOM, continuing at TOP                                                                           
