#!/usr/bin/env bash
set -e

PY_VERSION=3.13.7
PY_TARBALL=Python-$PY_VERSION.tgz
PY_SRC_DIR=Python-$PY_VERSION
VENV_DIR=.venv

echo "=== Step 1: Update system and install build tools ==="
sudo apt update
sudo apt install -y build-essential wget curl \
    libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev libffi-dev liblzma-dev tk-dev uuid-dev

echo "=== Step 2: Download Python $PY_VERSION source ==="
cd /usr/src
if [ ! -f $PY_TARBALL ]; then
    sudo wget https://www.python.org/ftp/python/$PY_VERSION/$PY_TARBALL
fi

echo "=== Step 3: Extract source ==="
sudo tar -xf $PY_TARBALL
cd $PY_SRC_DIR

echo "=== Step 4: Configure build ==="
sudo ./configure --enable-optimizations --with-ensurepip=install

echo "=== Step 5: Build and install ==="
sudo make -j$(nproc)
sudo make altinstall

echo "=== Step 6: Verify installation ==="
python3.13 --version
pip3.13 --version

echo "=== Step 7: Setup virtual environment ==="
python3.13 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

echo "=== Step 8: Upgrade pip tools ==="
pip install --upgrade pip setuptools wheel

if [ -f requirements.txt ]; then
    echo "=== Step 9: Install requirements.txt ==="
    pip install -r requirements.txt
else
    echo "requirements.txt not found — skipping package install."
fi

echo "✅ Python $PY_VERSION installed and virtualenv ready at $VENV_DIR"
