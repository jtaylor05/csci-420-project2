#!/usr/bin/python
# needs pip install flask
import argparse
from flask import Flask, request
import hashlib
import logging
import os
from random import random 
import sys
import threading
import time

app = Flask(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

args = None

# lock used to simulate running on a CPU
worklock = threading.Lock()

# flag to indicate doing real work
WORK_ROUNDS=150000

# lock and int to count number of current requests
parallellock = threading.Lock()
parallel = int(0)

@app.route('/hello')
def hello():
    return f"Hello from instance: {os.environ.get('HOSTNAME')}\n", 200

@app.route('/health')
def health():
    return 'loadserver is healthy\n', 200

@app.route('/getuserinfo')
def compute():
    user = request.args.get('user')
    start_time = time.time()
    work = 0
    global parallel
    current_work = 0
    with parallellock:
        current_work = parallel
        if current_work >= args.maxload:
            # server cost of overload is high
            with worklock:
                logging.log
                logging.info("overloaded")
                time.sleep(args.overloadCostS)
            return f"user {user} 420", 420
        parallel+=1

    try:    # make sure load is decremented 
        if not args.real:
            work = int(args.basework + ( args.loadfactor * current_work)) # ms ticks
            # get work of lock time, in 1ms increments
            for i in range(work):
                with worklock:
                    # NOTE never do this in real code
                    time.sleep(0.001)
        else:
            work = WORK_ROUNDS
            hashlib.pbkdf2_hmac('sha256',b'THIS IS WORK',b'SALTY', work)
    finally:        
        with parallellock:
            parallel-=1
        
    return f"user {user} work {work} wallclock {time.time()-start_time}\n", 200

@app.route('/')
def root():
    msg = f"Hello from instance /: {os.environ.get('HOSTNAME')}  load: {parallel}\n"
    return msg
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--loadfactor", help="additional cost as more work in parallel", type=float, default=0)
    parser.add_argument("--basework", help="work in ms per request", type=int, default=10)
    parser.add_argument("--overloadCostS", help="time in S wasted when server is overloaded", type=float, default=0.10)
    parser.add_argument("--maxload", help="maximum number of requests before overload", type=int, default=10)
    args = parser.parse_args()
    realwork = args.real
    app.config['PORT'] = args.port
    app.run(host='0.0.0.0', threaded=True, port=args.port)
