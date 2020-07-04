echo "Installing development fixtures..."
DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$DIR")"
"$APP_DIR"/manage.py loaddata "$DIR"/fixtures/dev_initial.json