# need to pip install requests_futures
# e.g.
#    python3 -m venv path/to/venv
#    source path/to/venv/bin/activate
#    python3 -m pip install flask requests_futures

from abc import ABC, abstractmethod
import argparse
from collections import namedtuple
from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
import time

UserResult = namedtuple('UserResult', ['username', 'latency'])

class LoadGeneratorBase(ABC):
    def __init__(self):
        super().__init__()
        self.args = None
        self.program_start = time.time()
        self.URLS = []


    # project implements this method.  Called in separate threads for each user
    @abstractmethod
    def get_user_info(self, user: str):
        pass

    def get_urls(self):
        URLS = []
        if self.args.urlsfile is not None:
                for line in self.args.urlsfile.readlines():
                    line = line.strip()
                    if len(line) > 5 and not line.startswith("#"):
                        URLS.append(line.strip()) 
        else:
            for i in range(self.args.localservers):
                URLS.append(f"http://localhost:{5555+i}/getuserinfo")
        return URLS

    def parse_args(self, impl_args: Callable[[argparse.ArgumentParser], None]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(add_help=True)
        # test case parameters
        parser.add_argument("--users", type=int, default=100)
        parser.add_argument("--parallelUsers", type=int, default=100)

        # standard local server config
        parser.add_argument("--localservers", help="n where running n servers on ports 5555, 5556, ...",
                            type=int, default=1)
        # optional read config from file
        parser.add_argument("--urlsfile", help="name of file of URLs to use, one per line.  Overrides localservers",
                            type=argparse.FileType('r'), default=None)
        impl_args(parser)
        self.args = parser.parse_args()
        print (f"loadgenerator with {vars(self.args)}")

        return self.args


    def get_user_info_timed(self, user: str) -> UserResult:
        user_start = time.time()
        complete = False
        while not complete:
            try:
                self.get_user_info(user)
                complete = True
            except Exception as e:
                print (f"user failed, try again: {e}")
        user_latency = time.time() - user_start
        return UserResult(username=user, latency=user_latency)

    # do not change this function
    # This launches users into the system, it is your job to make them happy!
    def generate_load(self):
        usercount = self.args.users
        parallel_users = self.args.parallelUsers
        with ThreadPoolExecutor(max_workers = parallel_users) as user_executor:
            futures = [user_executor.submit(self.get_user_info_timed, f"user{user}") for user in range(usercount)]
            for future in as_completed(futures):
                result = future.result()
                print (f"{result.username} fetch {result.latency:.3f} total {time.time()-self.program_start:.3f}")
