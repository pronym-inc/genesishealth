echo "Setting up virtual environment..."
DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$DIR")"
VENV_DIR=$APP_DIR/venv
python3.8 -m venv "$VENV_DIR"
