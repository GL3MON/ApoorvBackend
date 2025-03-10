import os
import json
import time
import psycopg2
from psycopg2.extras import execute_values
import threading
from dotenv import load_dotenv

from apoorvbackend.src.logger import logger
from apoorvbackend.src.redis.redis_handlers import RedisChatHandler

load_dotenv()

class PostgresBackupService:
    def __init__(self, interval_minutes=5):
        self.connection_string = os.getenv("DATABASE_URL")
        
        self.interval_seconds = interval_minutes * 60
        self.redis_handler = RedisChatHandler()
        self.running = False
        self.thread = None
        
        self._init_db()
    
    def _get_connection(self):
        """Create and return a connection to the PostgreSQL database using the connection string."""
        return psycopg2.connect(self.connection_string)
    
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        level VARCHAR(50) NOT NULL,
                        actor VARCHAR(50) NOT NULL,
                        chat_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
                    CREATE INDEX IF NOT EXISTS idx_chat_history_level_actor ON chat_history(level, actor);
                    """)
            logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing PostgreSQL database: {str(e)}")
    
    def _backup_all_redis_data(self):
        """Scan Redis for all chat keys and back them up to PostgreSQL."""
        try:
            # Get all keys matching the chat pattern
            all_keys = []
            cursor = "0"
            while cursor != 0:
                cursor, keys = self.redis_handler.client.scan(cursor=cursor, match="chat:*", count=100)
                all_keys.extend([key.decode('utf-8') for key in keys])
            
            if not all_keys:
                logger.info("No chat data found in Redis to backup")
                return
            
            rows_to_insert = []
            for key in all_keys:
                try:
                    # Parse the key to extract user_id, level, and actor
                    parts = key.split(":")
                    if len(parts) != 4:
                        logger.warning(f"Invalid key format: {key}")
                        continue
                    
                    _, user_id, level, actor = parts
                    
                    # Get the data
                    data = self.redis_handler.client.get(key)
                    if not data:
                        continue
                    
                    chat_data = json.loads(data)
                    
                    # Add to batch for processing
                    rows_to_insert.append((user_id, level, actor, json.dumps(chat_data)))
                
                except Exception as e:
                    logger.error(f"Error processing key {key}: {str(e)}")
            
            # Perform all database operations in a single connection
            if rows_to_insert:
                with self._get_connection() as conn:
                    with conn.cursor() as cursor:
                        # For each row, try to update if exists, otherwise insert
                        for user_id, level, actor, chat_data_json in rows_to_insert:
                            cursor.execute(
                                """
                                INSERT INTO chat_history (user_id, level, actor, chat_data)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (user_id, level, actor) 
                                DO UPDATE SET chat_data = EXCLUDED.chat_data, updated_at = CURRENT_TIMESTAMP
                                """,
                                (user_id, level, actor, chat_data_json)
                            )
            
            logger.info(f"Successfully backed up {len(all_keys)} chat histories to PostgreSQL")
        
        except Exception as e:
            logger.error(f"Error backing up Redis data to PostgreSQL: {str(e)}")
    
    def _scheduler_loop(self):
        """The main scheduler loop that runs in a separate thread."""
        while self.running:
            try:
                logger.info("Starting scheduled backup of Redis data to PostgreSQL")
                self._backup_all_redis_data()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
            
            # Sleep for the specified interval
            time_to_sleep = self.interval_seconds
            while time_to_sleep > 0 and self.running:
                time.sleep(min(1, time_to_sleep))
                time_to_sleep -= 1
    
    def start(self):
        """Start the backup scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        logger.info(f"PostgreSQL backup scheduler started with {self.interval_seconds / 60} minute interval")
    
    def stop(self):
        """Stop the backup scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("PostgreSQL backup scheduler stopped")
    
    def backup_now(self):
        """Manually trigger a backup."""
        logger.info("Manual backup of Redis data to PostgreSQL triggered")
        self._backup_all_redis_data()