#!/bin/bash
# Exit on error
set -o errexit

echo "--- Installing Python Dependencies ---"
cd server
pip install --upgrade pip
pip install -r requirements.txt
cd ..

echo "--- Creating Data Directories ---"
mkdir -p server/data/outputs
mkdir -p server/data/temp

echo "--- Building Frontend ---"
cd client
npm install
npm run build
# Note: Ensure next.config.ts has output: 'export'
cd ..

echo "--- Setup Complete ---"
