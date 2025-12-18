#!/bin/bash
# Exit on error
set -o errexit

echo "--- Installing Python Dependencies ---"
cd server
pip install -r requirements.txt
cd ..

echo "--- Building Frontend ---"
cd client
npm install
npm run build
# Note: Ensure next.config.ts has output: 'export'
cd ..

echo "--- Setup Complete ---"
