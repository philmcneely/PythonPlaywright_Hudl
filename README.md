
# Playwright Python Test Setup & Usage

This guide explains how to set up and run Playwright-based Python tests with Allure reporting on **macOS**, **Windows**, and **Linux**.

---

## Prerequisites

**All Platforms:**
- [Python 3.11+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [Node.js](https://nodejs.org/) (for Playwright browser installation)
- [Allure Commandline](https://docs.qameta.io/allure/#_installing_a_commandline)
- [`python-dotenv`](https://pypi.org/project/python-dotenv/) (for loading `.env` files)

**Windows Only:**
- [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**macOS Only:**
- [Homebrew](https://brew.sh/) (recommended for installing Allure and Node.js)

---

## 1. Clone the Repository

```sh
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

---

## 2. Create Environment Files

Create the environment file(s) you need in the project root:

- `.env.dev` for development
- `.env.test` for test
- `.env.prod` for production

Each file should contain the environment variables your tests require, for example:

```
BASE_URL=https://your-base-url
API_LOGIN_URL=https://your-api-url
USER_EMAIL=pm@example.com
USER_PASSWORD=yourpassword
# ...and so on for all required variables
```
Alternately, these files should be available in your secrets server and may need to be customized for your tests.

---

## 3. Set Up a Python Virtual Environment

**macOS/Linux:**

```sh
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scriptsctivate
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

---

## 4. Install Python Dependencies

```sh
pip install --upgrade pip
pip install -r requirements_with_versions.txt
```

Make sure your `requirements_with_versions.txt` includes `python-dotenv`:

```
python-dotenv
```

---

## 5. Install Playwright Browsers

```sh
python -m playwright install --with-deps
```

---

## 6. Install Allure Commandline

**macOS (with Homebrew):**

```sh
brew install allure
```

**Linux:**

```sh
sudo apt-get install default-jre
wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz
tar -xzf allure-2.27.0.tgz
sudo mv allure-2.27.0 /opt/allure
sudo ln -s /opt/allure/bin/allure /usr/bin/allure
```

**Windows:**

- Download the [Allure zip](https://github.com/allure-framework/allure2/releases) and extract it.
- Add the `bin` folder to your `PATH` environment variable.
- Open a new terminal and run `allure --version` to verify.

---

## 7. Load Environment Variables Automatically

Add this to your `conftest.py` or at the top of your test entrypoint:

```python
import os
from dotenv import load_dotenv

# Choose the environment file you want to load
env_file = os.getenv("ENV_FILE", ".env.dev")
load_dotenv(dotenv_path=env_file)
```

You can set the `ENV_FILE` environment variable to switch between `.env.dev`, `.env.test`, or `.env.prod`.

**Example:**

```sh
ENV_FILE=.env.test pytest ...
```

---

## 8. Run the Tests

Run your tests with pytest. For example, to run smoke tests with Allure reporting, reruns and in parallel:

```sh
pytest --alluredir=allure-results --capture=tee-sys --reruns 2 --reruns-delay 5 -m smoke -n auto
```

- Adjust the `-m smoke` marker or other pytest options as needed.

You can also pass env vars on the commandline, for example if you want headed tests or a different browser.

```sh
BROWSER=firefox HEADLESS=false pytest --alluredir=allure-results --capture=tee-sys --reruns 2 --reruns-delay 5 -m smoke -n auto
```

Adjust as needed.

---

## 9. Generate the Allure Report

```sh
allure generate allure-results -o allure-report --clean --single-file
```

---

## 10. View the Allure Report

**macOS:**

```sh
open allure-report/index.html
```

**Linux:**

```sh
xdg-open allure-report/index.html
```

**Windows:**

Open `allure-report\index.html` in your browser.

---

## 11. Github Actions

Everything is already configured to run a smoke test, then if that passes it will run the full 'login' test suite. All secrets are configured on the repo level, so if you add any, you will need to update the config.

---


## 11. AI Self healing

Install Ollama Python library

```sh
pip install ollama
```

# Ollama Model Setup for AI Healing

**Check Available Models**

```sh
ollama list
```

**Pull a Suitable Model**

### For vision + text analysis (recommended for screenshot analysis):

```sh
ollama pull llava:7b
# or
ollama pull llava:13b
```

### For text-only analysis (faster, smaller):

```sh
ollama pull llama3.1:8b
# or
ollama pull llama3.2:3b
```

**Update Your Environment Variable**

Set the model you actually have:

```sh
export OLLAMA_MODEL=llava:7b
# or whatever model you pulled
```

**Test Ollama is Working**

```sh
ollama run llava:7b "Hello, can you analyze test failures?"
```
---

## Troubleshooting

- **Missing .env file:**  
  Make sure you have created the correct `.env.<env>` file with all required variables.
- **Virtual environment activation issues:**  
  Double-check the activation command for your OS and shell.
- **Allure not found:**  
  Ensure Allure is installed and available in your `PATH`.
- **Windows build errors:**  
  Install the Visual C++ Build Tools as described above.

---

## Directory Structure

- `.env.dev`, `.env.test`, `.env.prod` — Environment variable files
- `requirements_with_versions.txt` — Python dependencies
- `allure-report/` — Generated Allure HTML report
- `allure-results/` — Allure raw results
- `screenshots/` — Test screenshots

---

**Happy testing! 🚀**
