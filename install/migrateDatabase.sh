echo "Migrating database..."
DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$DIR")"
"$APP_DIR"/manage.py migrate