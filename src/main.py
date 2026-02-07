import cv2
import numpy as np
import pyautogui
import pytesseract
import time
from pathlib import Path
import requests
import json
from requests.adapters import HTTPAdapter, Retry
import os

# -----------------------------
# Setup folders
# -----------------------------
screenshots_dir = Path("screenshots")
screenshots_dir.mkdir(exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -----------------------------
# Helper functions
# -----------------------------
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
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 40 < w < 120 and 40 < h < 120:
            aspect_ratio = w / float(h)
            if 0.8 < aspect_ratio < 1.2:
                candidates.append((x, y, w, h))

    if not candidates:
        return None, None

    for (x, y, w, h) in candidates:
        label_y1 = y + h
        label_y2 = min(y + h + 40, h_img)
        label_x1 = x
        label_x2 = min(x + w + 10, w_img)

        label_region = img[label_y1:label_y2, label_x1:label_x2]
        if label_region.size == 0:
            continue

        gray_label = cv2.cvtColor(label_region, cv2.COLOR_BGR2GRAY)
        _, label_thresh = cv2.threshold(gray_label, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        label_text = pytesseract.image_to_string(label_thresh).strip()

        if "notepad" in label_text.lower():
            center_x = x + w // 2
            center_y = y + h // 2

            if debug:
                debug_img = img.copy()
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                debug_path = screenshots_dir / "notepad_detected.png"
                cv2.imwrite(str(debug_path), debug_img)

            return center_x, center_y

    return None, None

def click_icon(center_x, center_y):
    pyautogui.moveTo(center_x, center_y, duration=0.5)
    pyautogui.doubleClick()
    time.sleep(1.5)

project_dir = Path.home() / "Desktop" / "tjm-project"
project_dir.mkdir(exist_ok=True)

def fetch_posts():
    posts = []
    try:
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1)
        session.mount('https://', HTTPAdapter(max_retries=retries))
        response = session.get("https://jsonplaceholder.typicode.com/posts", timeout=10)
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

def type_post_in_notepad(post):
    text = f"Title: {post['title']}\n\n{post['body']}"
    pyautogui.write(text, interval=0.01)
    time.sleep(0.5)

def save_notepad_file(post_id):
    pyautogui.hotkey('ctrl', 's')
    time.sleep(0.5)
    filename = project_dir / f"post_{post_id}.txt"
    pyautogui.write(str(filename), interval=0.01)
    pyautogui.press('enter')
    time.sleep(0.5)

def close_notepad():
    pyautogui.hotkey('alt', 'f4')
    time.sleep(0.5)

# -----------------------------
# Main workflow
# -----------------------------
img, screenshot_path = take_screenshot()
print(f"Desktop screenshot saved at: {screenshot_path}")

center_x, center_y = find_notepad_icon(img)
if center_x is not None and center_y is not None:
    click_icon(center_x, center_y)
    print(f"Notepad icon clicked at: ({center_x}, {center_y})")
else:
    print("Notepad icon not found. Make sure it's visible and labeled correctly.")

posts = fetch_posts()

for post in posts:
    for attempt in range(3):
        img, _ = take_screenshot()
        x, y = find_notepad_icon(img)
        if x is not None and y is not None:
            click_icon(x, y)
            break
        else:
            print(f"Notepad not found. Retrying ({attempt+1}/3)...")
            time.sleep(1)
    else:
        print("Failed to find Notepad after 3 attempts. Skipping post.")
        continue

    type_post_in_notepad(post)
    save_notepad_file(post['id'])
    close_notepad()

print("All posts processed successfully.")
