Last login: Sat May 30 12:27:20 on ttys003
lioncrown@lioncrowndeMacBook-Neo ~ % vi odd.py


























import os
import json
import time
import threading
from datetime import datetime
from collections import defaultdict, deque

import requests
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__)

NODE_API = os.environ.get("NODE_API", "http://localhost:3000/odds")

def _deque5():
    return deque(maxlen=5)

def _deque60():
    return deque(maxlen=60)

def _inf():
    return float("inf")

state = {
    "running": False,
    "data": [],
    "base_data": {},
"odd.py" 931L, 31460B
