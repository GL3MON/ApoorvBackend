# Apoorv Backend

## Setup

- Make sure you install **poetry**
- Create a conda environment with Python version 3.11
- Execute:
  ```bash
  poetry install
  ```
- Create a copy of `.env.template` and rename it to `.env` after populating it with necessary values.
- **Redis Setup:**
  - Install Redis by following the [installation guide](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/).
  - Update your `.env` file to include the Redis configuration variables:
    ```env
    REDIS_HOST=localhost
    REDIS_PORT=6379
    REDIS_DB=0
    ```
  - Make sure that your Redis instance is running and accessible before starting the application.


## Optional [not really needed]: Setting Up Redis Persistence

- To enable persistence, configure Redis with either RDB snapshotting or Append Only File (AOF) options:
  - **RDB Snapshots:**  
    Configure snapshot intervals in your `redis.conf` by adding `save 900 1` (for saving every 15 minutes if at least 1 key changed).
  - **AOF:**  
    Enable AOF by setting `appendonly yes` and fine-tune the `appendfsync` policy as needed.

## LoadBalancer

### How to Create an Object
To use the `LoadBalancer` class, first import it and initialize an object:

```python
from load_balancer import LoadBalancer

# Create a LoadBalancer object with 10 API keys and a cooldown time of 10 seconds
lb = LoadBalancer(n=10, ct=10)
```

### Purpose of Each Method

#### `__init__(self, n, ct)`
- Initializes the load balancer with `n` API keys.
- Loads API keys from environment variables.
- Initializes tracking for failed keys and their cooldown times.
- Keeps a usage count for each key.
- **Parameters:**
  - `n`: Number of API keys.
  - `ct`: Cooldown time (in seconds) for failed keys.

#### `Round_Robin(self)`
- Implements a round-robin load balancing strategy.
- Returns the next API key in sequence.

#### `FailureAware(self)` and `report_fail(self, key)`
- `FailureAware` selects an API key while avoiding failed keys.
- If a key has failed and is still in cooldown, it is skipped.
- Raises an exception if all keys are in cooldown.
- `report_fail` marks an API key as failed and sets its cooldown time.
- **Parameter:**
  - `key`: The failed API key.

#### `StdDev(self)`
- Selects an API key based on a probability distribution using standard deviation.
- Prioritizes keys that have been used less frequently.
- Does **not** check for failed keys.

### Usage of Each Method

#### Example 1: Using Round Robin Load Balancing
```python
key = lb.Round_Robin()
print("Selected Key:", key)
```

#### Example 2: Using Failure-Aware Selection and Reporting Failure
```python
try:
    key = lb.FailureAware()
    print("Selected Key:", key)
except Exception as e:
    print("Error:", e)

# Reporting a failed key
lb.report_fail("API_KEY_1")
```

#### Example 3: Using Standard Deviation-Based Selection
```python
key = lb.StdDev()
print("Selected Key:", key)
```
Further stress testing needs to be done in order to find out which algorithm can handle the traffic the best.

## .env File Format

The `.env` file should be structured as follows:

```
GOOGLE_API_KEY_<n> = <your_gemini_api_key>
```

Replace `<n>` with the key index (e.g., `1, 2, 3,...`) and `<your_gemini_api_key>` with your actual Gemini API key.

**Example:**
```
GOOGLE_API_KEY_1 = <your_gemini_api_key_1>
GOOGLE_API_KEY_2 = <your_gemini_api_key_2>
```

## How to Contribute

- **Don't commit code/changes directly to `main`.**
- Create a separate branch for your changes and then create a PR request to merge into `main`.
- Branch names shouldn't be random:
  - For a new feature, use `feature/{feature_name}`.
  - For a fix, use `fix/{fix_name}`.
- Every PR message must include a **title**, **description**, and **changes**.
