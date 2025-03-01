from loguru import logger
import sys

logger.add("logs/application.log", rotation="500 MB", backtrace=True, diagnose=False)
logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")