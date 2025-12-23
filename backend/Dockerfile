# Use AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Set working directory to Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces image size
# --upgrade ensures latest compatible versions
RUN pip install --no-cache-dir -r requirements.txt --upgrade

# Copy application code
# This includes: main.py, lambda_handler.py, src/, etc.
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to Lambda handler
# Format: module_name.function_name
# This points to the 'handler' function in lambda_handler.py
CMD ["lambda_handler.handler"]
