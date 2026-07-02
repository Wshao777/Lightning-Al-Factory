#!/bin/bash
set -e

echo "Setting up environment for Commercial-Al-Smart..."

# Install dependencies
pip install -r public/api/requirements.txt

# Create .env template in private_core
cat <<EOF > private_core/secrets.env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
MAX_POOL_SIZE=20
EOF

echo "Setup complete."
