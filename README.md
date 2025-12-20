# MediTranslate:

**MediTranslate** is a private, offline-first medical translation tool designed to help patients understand complex medical documents.

It combines **local machine translation** (for privacy) with **cloud-based AI** (for simplification), allowing users to scan documents, translate them into their native language, and get simple, jargon-free explanations.

---

## Features:

* **Privacy First:** OCR and Translation run entirely **offline** on your device. No patient data leaves your computer during the basic translation process.
* **OCR:** Auto-detects text from scanned PDFs or images using Tesseract and OpenCV.
* **Hybrid AI:**
    * **Local:** Uses `MarianMT` (Transformers) for accurate, private translation.
    * **Cloud (Optional):** Uses Google Gemini to "explain like I'm 5" for difficult medical terms (requires API key).
* **Medical Glossary:** Built-in database of 70,000+ medical terms and ICD-10 codes.
* **Cross-Platform:** Works on Windows, macOS, and Linux.

When the user runs the app, it will do the following before runtime: 
1. check for models in the `resources/models` directory. If they are not found, it will download them.
2. load glossaries and read the JSON files. 
3. check API key in the `.env` file on root directory. If it is not found, it will prompt the user to manually enter it.

---

## Installation:

### Windows:

#### Step 1: Install Tesseract OCR:

1.  Download the installer from the [Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
2.  Run the installer.
3.  **CRITICAL:** During installation, you will see an option for language data. Ensure you check the boxes for languages you plan to scan (e.g., Spanish, Hindi).
4.  **CRITICAL:** Once installed, you must add Tesseract to your System PATH:
    * Press `Win` key, type **"Edit the system environment variables"**, and hit Enter.
    * Click the **"Environment Variables"** button.
    * Under **"System variables"** (bottom box), find the row named **"Path"** and double-click it.
    * Click **"New"** and paste this path: `C:\Program Files\Tesseract-OCR`
    * Click OK on all windows.

#### Step 2: Install uv:
1.  Open **PowerShell**.
2.  Paste this command and press Enter:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
3.  Close PowerShell and open it again to refresh.

#### Step 3: Install MediTranslate
1.  In the new PowerShell window, run:
    ```powershell
    uv tool install meditranslate
    ```
2.  Once finished, you can run the app by typing:
    ```powershell
    meditranslate
    ```
---

### macOS:

#### Step 1: Install Homebrew (if you haven't already):
1.  Open **Terminal**.
2.  Paste this and hit Enter (follow the prompts on screen):
    ```bash
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    ```

#### Step 2: Install Tesseract
1.  In the Terminal, run:
    ```bash
    brew install tesseract
    brew install tesseract-lang
    ```

#### Step 3: Install `uv` and MediTranslate
1.  Install `uv`:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Close your Terminal and open a new one.**
3.  Install the app:
    ```bash
    uv tool install meditranslate
    ```
4.  Run it:
    ```bash
    meditranslate
    ```

---

### Linux (Debian/Ubuntu):

#### Step 1: Install Dependencies:
1.  Open **Terminal**.
2.  Run the following commands:
    ```bash
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-all libgl1
    ```

#### Step 2: Install `uv`:
1.  Paste this command into your terminal and hit Enter:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Close your terminal window and open a new one**

#### Step 3: Install MediTranslate
1.  In the new terminal window, run:
    ```bash
    uv tool install meditranslate
    ```
2.  Once finished, you can run the app by typing:
    ```bash
    meditranslate
    ```

---

### Linux (Arch/Manjaro):

#### Step 1: Install Dependencies:
1.  Open **Terminal**.
2.  Run the following command (installs Tesseract, language data, and graphics libraries):
    ```bash
    sudo pacman -Syu tesseract tesseract-data-eng tesseract-data-spa tesseract-data-hin libglvnd
    ```

#### Step 2: Install `uv`:
1.  Arch Linux includes `uv` in the official repositories. Run this command:
    ```bash
    sudo pacman -S uv
    ```
2.  **Close your terminal window and open a new one**

#### Step 3: Install MediTranslate
1.  In the new terminal window, run:
    ```bash
    uv tool install meditranslate
    ```
2.  Once finished, you can run the app by typing:
    ```bash
    meditranslate
    ```

<!-- TODO: Add AI / glossary installation instructions -->