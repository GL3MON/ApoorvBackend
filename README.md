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

## How to Contribute

- **Don't commit code/changes directly to `main`.**
- Create a separate branch for your changes and then create a PR request to merge into `main`.
- Branch names shouldn't be random:
  - For a new feature, use `feature/{feature_name}`.
  - For a fix, use `fix/{fix_name}`.
- Every PR message must include a **title**, **description**, and **changes**.
