#!/bin/bash
# Build script for Lambda Layers
# This script builds the Lambda layers locally for testing before deployment

set -e  # Exit on error

echo "🔨 Building Lambda Layers..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Layer 1: Data Processing
echo -e "${YELLOW}Building Data Processing Layer...${NC}"
cd layers/data-processing
mkdir -p python
pip install -r requirements.txt -t python --platform manylinux2014_x86_64 --only-binary=:all: --upgrade
echo -e "${GREEN}✓ Data Processing Layer built${NC}"
cd ../..

# Layer 2: Google APIs
echo -e "${YELLOW}Building Google APIs Layer...${NC}"
cd layers/google-apis
mkdir -p python
pip install -r requirements.txt -t python --platform manylinux2014_x86_64 --only-binary=:all: --upgrade
echo -e "${GREEN}✓ Google APIs Layer built${NC}"
cd ../..

echo -e "${GREEN}✓ All layers built successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Test locally: cd infrastructure && sam build && sam local start-api"
echo "2. Deploy to AWS: cd infrastructure && sam deploy"
