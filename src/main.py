import cv2
import numpy as np
import pyautogui
import pytesseract
import time
from pathlib import Path
import requests
import json
from requests.adapters import HTTPAdapter, Retry
import keyboard
import threading

# -----------------------------
# GLOBAL SAFETY FLAGS
# -----------------------------
pyautogui.FAILSAFE = True  # move mouse to top-left to abort
STOP_REQUESTED = False

# -----------------------------
# Setup folders
# -----------------------------
screenshots_dir = Path("screenshots")
screenshots_dir.mkdir(exist_ok=True)

project_dir = Path.home() / "Desktop" / "tjm-project"
project_dir.mkdir(exist_ok=True)

# Set Tesseract executable path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------
# ESC key listener
# -----------------------------
def listen_for_escape():
    global STOP_REQUESTED
    keyboard.wait("esc")
    STOP_REQUESTED = True
    print("ESC pressed. Automation stopped by user.")
listener_thread = threading.Thread(target=listen_for_escape, daemon=True)
listener_thread.start()

# -----------------------------
# Helper functions
# -----------------------------
def move_mouse_away():
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height // 2, duration=0.3)
    
def show_desktop():
    pyautogui.hotkey("win", "d")
    time.sleep(0.5)

def take_screenshot():
    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshot_path = screenshots_dir / "desktop.png"
    screenshot.save(screenshot_path)
    return img, screenshot_path

def find_notepad_icon(img, debug=True):
    h_img, w_img = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)

    _contours = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = _contours[0] if len(_contours) == 2 else _contours[1]

    candidates = []
    # Icon size heuristics based on screen size to handle scaling.
    min_dim = max(32, int(min(w_img, h_img) * 0.02))
    max_dim = max(96, int(min(w_img, h_img) * 0.10))
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if min_dim <= w <= max_dim and min_dim <= h <= max_dim:
            aspect_ratio = w / float(h)
            if 0.8 < aspect_ratio < 1.2:
                candidates.append((x, y, w, h))

    for (x, y, w, h) in candidates:
        # Expand label search region to include wider and lower text.
        pad_x = int(w * 0.5)
        label_y1 = y + h
        label_y2 = min(y + h + int(h * 1.2) + 20, h_img)
        label_x1 = max(0, x - pad_x)
        label_x2 = min(x + w + pad_x, w_img)

        label_region = img[label_y1:label_y2, label_x1:label_x2]
        if label_region.size == 0:
            continue

        gray_label = cv2.cvtColor(label_region, cv2.COLOR_BGR2GRAY)
        # Improve OCR reliability: scale up and try normal + inverted.
        scaled = cv2.resize(
            gray_label, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC
        )
        _, thresh = cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        inv = cv2.bitwise_not(thresh)

        label_text = pytesseract.image_to_string(thresh).strip().lower()
        if "notepad" not in label_text:
            label_text = pytesseract.image_to_string(inv).strip().lower()

        if "notepad" in label_text:
            center_x = x + w // 2
            center_y = y + h // 2

            if debug:
                debug_img = img.copy()
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.rectangle(
                    debug_img, (label_x1, label_y1), (label_x2, label_y2), (255, 0, 0), 1
                )
                debug_path = screenshots_dir / "notepad_detected.png"
                cv2.imwrite(str(debug_path), debug_img)

            return center_x, center_y

    return None, None

def click_icon(x, y):
    pyautogui.moveTo(x, y, duration=0.4)
    pyautogui.doubleClick()
    time.sleep(1.2)
    move_mouse_away()
# -----------------------------
# API Fetch (with fallback)
# -----------------------------
def fetch_posts():
    posts = []
    try:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1)
        session.mount("https://", HTTPAdapter(max_retries=retries))

        response = session.get(
            "https://jsonplaceholder.typicode.com/posts", timeout=10
        )
        response.raise_for_status()
        posts = response.json()[:10]

    except Exception as e:
        print(f"Failed to fetch posts from API: {e}")
        fallback_file = Path("sample_posts.json")
        if fallback_file.exists():
            print("Using local fallback posts")
            with open(fallback_file, "r", encoding="utf-8") as f:
                posts = json.load(f)[:10]
        else:
            print("No posts available. Exiting.")
            exit()

    return posts

# -----------------------------
# Notepad automation helpers
# -----------------------------
def type_post_in_notepad(post):
    text = f"Title: {post['title']}\n\n{post['body']}"
    pyautogui.write(text, interval=0.01)
    time.sleep(0.5)

def save_notepad_file(post_id):
    pyautogui.hotkey("ctrl", "s")
    time.sleep(0.5)

    base_name = f"post_{post_id}.txt"
    filename = project_dir / base_name

    if filename.exists():
        counter = 1
        while True:
            candidate = project_dir / f"post_{post_id}_{counter}.txt"
            if not candidate.exists():
                filename = candidate
                print(
                    f"File already exists for post {post_id}. Saving as: {filename.name}"
                )
                break
            counter += 1

    pyautogui.write(str(filename), interval=0.01)
    pyautogui.press("enter")
    time.sleep(0.5)

def close_notepad():
    pyautogui.hotkey("alt", "f4")
    time.sleep(0.5)

# -----------------------------
# MAIN WORKFLOW
# -----------------------------
img, screenshot_path = take_screenshot()
print(f"Desktop screenshot saved at: {screenshot_path}")

posts = fetch_posts()

for post in posts:
    if STOP_REQUESTED:
        break

    for attempt in range(3):
        if STOP_REQUESTED:
            break

        img, _ = take_screenshot()
        x, y = find_notepad_icon(img)

        if x is not None and y is not None:
            click_icon(x, y)
            break
        else:
            print(f"Notepad not found. Retrying ({attempt + 1}/3)...")
            time.sleep(1)
    else:
        print("Failed to find Notepad after 3 attempts. Skipping post.")
        continue

    if STOP_REQUESTED:
        break

    type_post_in_notepad(post)
    save_notepad_file(post["id"])
    close_notepad()
print("Automation finished.")
