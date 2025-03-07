import os
import time
import numpy as np
from dotenv import load_dotenv
from google.api_core import exceptions

class LoadBalancer:
    def __init__(self, n, ct):
        self.index = -1
        self.no_of_keys = n
        load_dotenv()
        self.keys = [os.getenv(f'GOOGLE_API_KEY_{x}') for x in range(1, n+1)]
        self.fail_keys = {}
        self.cooltime = ct
        self.usage_count = {key: 0 for key in self.keys}

    def Round_Robin(self):
        self.index = (self.index + 1) % self.no_of_keys
        key = self.keys[self.index]

        if key in self.fail_keys:
            if time.time() < self.fail_keys[key]:
                return self.FailureAware()
            else:
                del self.fail_keys[key]
                
        self.usage_count[key] = self.usage_count.get(key, 0) + 1
        return key

    def FailureAware(self):
        for _ in range(self.no_of_keys):
            self.index = (self.index+1) % self.no_of_keys
            key = self.keys[self.index]

            if key in self.fail_keys:
                if time.time() < self.fail_keys[key]:
                    continue
                else:
                    del self.fail_keys[key]
            
            self.usage_count[key] = self.usage_count.get(key, 0) + 1
            return key
        
        raise Exception("No keys available... All keys in cooldown...")
    
    def report_fail(self, key):
        self.fail_keys[key] = time.time() + self.cooltime
    
    def StdDev(self):
        try:
            avail_keys = [key for key in self.keys if key not in self.fail_keys or time.time() >= self.fail_keys[key]]

            if not avail_keys:
                return self.FailureAware()
                
            max_usage = max(self.usage_count.get(key, 0) for key in avail_keys)
            
            filtered_keys = [key for key in avail_keys if self.usage_count.get(key, 0) < max_usage]
            
            if not filtered_keys:
                filtered_keys = avail_keys
                
            use_counts = np.array([self.usage_count.get(key, 0) for key in filtered_keys])
            mean_use = np.mean(use_counts)
            std_dev = np.std(use_counts) + 1e-6
            
            prob = 1 / (1 + np.abs(use_counts - mean_use) / std_dev)
            prob /= prob.sum()
            
            sel_key = np.random.choice(filtered_keys, p=prob)
            self.usage_count[sel_key] = self.usage_count.get(sel_key, 0) + 1
            
            return sel_key
            
        except Exception as e:
            if isinstance(e, exceptions.ResourceExhausted) or "Resource has been exhausted" in str(e):
                if 'sel_key' in locals():
                    self.report_fail(sel_key)
                return self.FailureAware()
            else:
                raise e

    def get_key(self, method="std_dev"):
        """
        Get an API key using the specified method
        
        Args:
            method (str): The load balancing method to use:
                "std_dev" - Use standard deviation method (default)
                "round_robin" - Use round robin method
                "failure_aware" - Use failure-aware method
                
        Returns:
            str: API key
        """
        try:
            if method == "round_robin":
                return self.Round_Robin()
            elif method == "failure_aware":
                return self.FailureAware()
            else: 
                return self.StdDev()
        except exceptions.ResourceExhausted as e:
            if 'key' in locals():
                self.report_fail(key)
            return self.FailureAware()
        except Exception as e:
            if "Resource has been exhausted" in str(e):
                if 'key' in locals():
                    self.report_fail(key)
                return self.FailureAware()
            raise e