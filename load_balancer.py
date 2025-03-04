import os
import time
from dotenv import load_dotenv
import numpy as np

class LoadBalancer:
    def __init__(self,n,ct):
        self.index = -1
        self.no_of_keys = n
        load_dotenv()
        self.keys = [os.getenv(f'GOOGLE_API_KEY_{x}') for x in range(1,n+1)]
        self.fail_keys = {}
        self.cooltime = ct
        self.usage_count = {key: 0 for key in self.keys}

    def Round_Robin(self):
        return self.keys[(self.index+1)%self.no_of_keys]

    def FailureAware(self):
        for _ in range(self.no_of_keys):
            self.index = (self.index+1) % self.no_of_keys
            key = self.keys[self.index]

            if key in self.fail_keys:
                if time.time() < self.fail_keys[key]:
                    continue
                else:
                    del self.fail_keys[key]
            return key
        
        raise Exception("No keys available... All keys in cooldown...")
    
    def report_fail(self,key):
        self.fail_keys[key] = time.time() + self.cooltime
    
    def StdDev(self):
        avail_keys = self.keys
        
        use_counts = np.array([self.usage_count[key] for key in avail_keys])
        mean_use = np.mean(use_counts)
        std_dev = np.std(use_counts) + 1e-6

        prob = 1 / (1 + np.abs(use_counts - mean_use) / std_dev)
        prob /= prob.sum()

        sel_key = np.random.choice(avail_keys,p=prob)
        self.usage_count[sel_key] += 1

        return sel_key
    