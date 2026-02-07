Perfect! Here’s a concise, **interview-friendly README** version — short, professional, and to the point:

---

# TJM Desktop Automation

## Overview

Automates typing posts from an API into Notepad on Windows. Dynamically detects the Notepad icon using **OCR**, types content, saves `.txt` files, and closes Notepad.

---

## Features

* Detects **Notepad icon** anywhere on the desktop
* Fetches posts from [JSONPlaceholder](https://jsonplaceholder.typicode.com/) or local fallback
* Types and saves posts automatically
* Press **ESC** to stop automation

---

## Setup

1. Install Python 3.12+ and [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
3. Set Tesseract path in `main.py`:

   ```python
   pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

---

## Usage

1. Place Notepad on the desktop.
2. Run:

   ```bash
   python src/main.py
   ```
3. Automation will process posts and save them to `Desktop/tjm-project/`.

---

## Notes

* Supports Windows OS only.
* Works with standard desktop icon sizes and resolution (1920x1080 recommended).
* Debug screenshots saved in `screenshots/`.

---

## Project Structure

```
tjm-desktop-automation/
├─ src/main.py
├─ screenshots/
├─ sample_posts.json
├─ README.md
└─ requirements.txt
```

---
