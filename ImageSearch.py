import json
import os
import requests
import time
import cv2
import numpy as np

CARDS_JSON = "cards_data.json"
OUTPUT_FOLDER = "card_images"
SERPER_API_KEY = "a576c9de12ed9f97f3a1d502b87e8f5c4403f9d3"  # Get from https://serper.dev (2,500 free queries on signup)

def load_cards():
    with open(CARDS_JSON) as f:
        return json.load(f)

def search_google_images(query):
    """Uses Serper.dev Google Images API to find a matching card image."""
    url = "https://google.serper.dev/images"
    payload = json.dumps({
        "q": query,
        "num": 5,          # Get a few options
        "gl": "us",        # Country
        "hl": "en"         # Language
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        resp = requests.post(url, headers=headers, data=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        images = data.get("images", [])
        if images:
            # Prefer high-quality images; take the first good one
            for img in images:
                if img.get("imageUrl"):
                    return img.get("imageUrl")  # Full/resized image URL
            return images[0].get("imageUrl")
    except Exception as e:
        print(f"Serper API error: {e}")
    return None

def crop_card_by_contour(img):
    """Detects the card's rectangular boundary and crops to it, leaving the card fully intact."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    kernel = np.ones((5, 5), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    # Small margin so we don't clip the card's edge/border
    margin = 5
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(img.shape[1] - x, w + margin * 2)
    h = min(img.shape[0] - y, h + margin * 2)

    return img[y:y+h, x:x+w]

def download_and_process(url, save_path):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return False

        nparr = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False

        cropped = crop_card_by_contour(img)
        if cropped is None:
            print("No card contour detected, saving original uncropped image instead.")
            cropped = img

        cv2.imwrite(save_path, cropped)
        return True
    except Exception as e:
        print(f"Failed to process {url}: {e}")
    return False

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    cards = load_cards()

    for card in cards:
        card_id = card.get("id")
        if not card_id:
            continue

        save_path = os.path.join(OUTPUT_FOLDER, f"{card_id}.jpg")

        # Skip if an image already exists
        if os.path.exists(save_path):
            print(f"Skipping {card_id}, image already exists")
            continue

        # Build search query (tuned for sports cards)
        variant = card.get("Variant") if card.get("Variant") not in (None, "-") else ""
        query = f"{card['Player']} {card['Set']} {variant} #{card.get('Card Number', '')} trading card ungraded".strip()
        print(f"Searching Google Images: {query}")

        img_url = search_google_images(query)
        if img_url and download_and_process(img_url, save_path):
            print(f"Saved {save_path}")
        else:
            print(f"No suitable image found for {card_id}")

        time.sleep(1)  # Be respectful of rate limits (Serper is fast)

if __name__ == "__main__":
    main()