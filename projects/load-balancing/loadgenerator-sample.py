# need to pip install requests_futures
# e.g.
#    python3 -m venv path/to/venv
#    source path/to/venv/bin/activate
#    python3 -m pip install flask requests_futures
import argparse
from collections import namedtuple
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
import random
from requests_futures.sessions import FuturesSession
import time

from loadgeneratorbase import LoadGeneratorBase


class LoadGeneratorSample(LoadGeneratorBase):
    # load balancing algorithm parameters: 
    # play with these and add/change more
    def my_args(self, parser: argparse.ArgumentParser):
        parser.add_argument("--parallelRequests", type=int, default=200)
        parser.add_argument("--timeout_s", type=float, default=60)
        parser.add_argument("--backoff_s", type=float, default=0.010)

    def __init__(self):
        super().__init__()
        self.args = super().parse_args( self.my_args )
        self.URLS = self.get_urls()
        # any init needed by get_user_info goes here
        self.session = FuturesSession(executor=ThreadPoolExecutor(max_workers=self.args.parallelRequests))


    def get_user_info(self, user: str):
        result = None
        while result is None or result.status_code != 200:
            # this might not be a great idea
            url = random.choice(self.URLS)
            # returns a https://docs.python.org/dev/library/concurrent.futures.html#future-objects
            request_future = self.session.get(url, params={'user':user})
            try:
                result = request_future.result(timeout = self.args.timeout_s)
                if result.status_code != 200:
                    # sleeping is OK because this is spawned in its own thread
                    time.sleep(self.args.backoff_s)
            except TimeoutError:
                request_future.cancel()

if __name__ == "__main__":
    generator = LoadGeneratorSample()
    generator.generate_load()
