"""
AWS Lambda handler for FastAPI application using Mangum adapter.

This module wraps the FastAPI application with Mangum to make it compatible
with AWS Lambda's event-driven execution model.

The Mangum adapter transforms API Gateway events into ASGI requests that
FastAPI can process, and converts FastAPI responses back to API Gateway format.
"""
import sys
import os
import logging
from pathlib import Path

# Configure logging FIRST (before other imports)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Remove default handlers to avoid duplicate logs
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

# Add CloudWatch-compatible handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("🚀 [Lambda] Initializing Lambda handler...")

# Add src/ directory to Python path to support non-prefixed imports
# This allows imports like "from adapter..." to work in Lambda environment
LAMBDA_TASK_ROOT = os.environ.get('LAMBDA_TASK_ROOT', os.path.dirname(__file__))
src_path = str(Path(LAMBDA_TASK_ROOT) / 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logger.info(f"✅ [Lambda] Added {src_path} to Python path")

# Import Mangum and FastAPI app
try:
    from mangum import Mangum
    logger.info("✅ [Lambda] Mangum imported successfully")
except ImportError as e:
    logger.error(f"❌ [Lambda] Failed to import Mangum: {e}")
    raise

try:
    from main import app
    logger.info("✅ [Lambda] FastAPI app imported successfully")
except ImportError as e:
    logger.error(f"❌ [Lambda] Failed to import FastAPI app: {e}")
    raise

# Create Lambda handler with Mangum
# lifespan="off" disables FastAPI startup/shutdown events which don't work in Lambda
# Lambda is stateless and doesn't support long-running background tasks
try:
    handler = Mangum(app, lifespan="off")
    logger.info("✅ [Lambda] Lambda handler initialized successfully with Mangum")
except Exception as e:
    logger.error(f"❌ [Lambda] Failed to create Mangum handler: {e}")
    raise

logger.info("🎉 [Lambda] Handler ready to process events")
