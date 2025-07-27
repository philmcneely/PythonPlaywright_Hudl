# usage examples
# ./run_tests.sh                   # defaults to dev
# ./run_tests.sh test              # use .env.test
# ./run_tests.sh prod --rebuild    # force new .venv and use .env.prod


#!/bin/bash
#HEADLESS=false pytest --html=test-results/report.html --self-contained-html --capture=tee-sys --reruns 2 --reruns-delay 5
# pytest -n auto --html=test-results/report.html --self-contained-html --capture=tee-sys --reruns 2 --reruns-delay 5


set -e

ENV="dev"
REBUILD=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    dev|test|prod)
      ENV=$1
      shift
      ;;
    --rebuild)
      REBUILD=true
      shift
      ;;
    *)
      echo "❌ Unknown option: $1"
      echo "Usage: ./run_tests.sh [dev|test|prod] [--rebuild]"
      exit 1
      ;;
  esac
done

echo "🔧 Running tests using environment: $ENV"
ENV_FILE=".env.$ENV"

# Check for the .env file
if [ ! -f "$ENV_FILE" ]; then
  echo "❌ Missing environment file: $ENV_FILE"
  echo "Please create it or generate one using:"
  echo "  python config/config_loader.py > $ENV_FILE"
  exit 1
fi

export TEST_ENV=$ENV

# Setup virtual environment
if [ "$REBUILD" = true ]; then
  echo "♻️ Rebuilding virtual environment..."
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install --with-deps

# Prepare output directories
mkdir -p allure-report
mkdir -p allure-results
mkdir -p screenshots
echo "Pausing for 5 seconds..."
sleep 5

# Run tests
SKIP_SCREENSHOTS=0 HEADLESS=false pytest --alluredir=allure-results --capture=tee-sys --reruns 2 --reruns-delay 5 -m smoke -n 4 

# Generate Allure report
echo "📊 Generating Allure report..."
allure generate allure-results -o allure-report --clean --single-file

# Open Allure report (macOS/Linux only)
ALLURE_REPORT_PATH="allure-report/index.html"
if [ -f "$ALLURE_REPORT_PATH" ]; then
  echo "✅ Allure report generated successfully!"
  if command -v open &>/dev/null; then
    open "$ALLURE_REPORT_PATH"
  elif command -v xdg-open &>/dev/null; then
    xdg-open "$ALLURE_REPORT_PATH"
  else
    echo "ℹ️ Allure report saved at $ALLURE_REPORT_PATH"
  fi
else
  echo "❌ Allure report not found: $ALLURE_REPORT_PATH"
fi
