"""
AWS Lambda handler for FastAPI application using Mangum adapter.

This module wraps the FastAPI application with Mangum to make it compatible
with AWS Lambda's event-driven execution model.

The Mangum adapter transforms API Gateway events into ASGI requests that
FastAPI can process, and converts FastAPI responses back to API Gateway format.
"""
import sys
import os
from pathlib import Path

# Add src/ directory to Python path to support non-prefixed imports
# This allows imports like "from adapter..." to work in Lambda environment
LAMBDA_TASK_ROOT = os.environ.get('LAMBDA_TASK_ROOT', os.path.dirname(__file__))
src_path = str(Path(LAMBDA_TASK_ROOT) / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    print(f"INFO [Lambda]: Added {src_path} to Python path")

from mangum import Mangum
from main import app
import logging

# Configure logging for Lambda
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log Lambda initialization
logger.info("INFO [Lambda]: Initializing Lambda handler with Mangum")

# Create Lambda handler with Mangum
# lifespan="off" disables FastAPI startup/shutdown events which don't work in Lambda
# Lambda is stateless and doesn't support long-running background tasks
handler = Mangum(app, lifespan="off")

logger.info("INFO [Lambda]: Lambda handler initialized successfully")
