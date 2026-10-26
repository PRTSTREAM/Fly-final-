import re
import requests
from bs4 import BeautifulSoup

PLAYLIST_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"

# ब्राउज़र जैसा हेडर
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def bypass_and_extract_link(target_url):
    try:
        # अगर इनपुट URL ही पहले से pub या pixeldrain direct stream लिंक है तो सीधे लौटाएं
        if target_url.startswith("https://pub") or "pixeldrain.dev/api/file/" in target_url:
            return target_url

        session = requests.Session()
        response = session.get(target_url, headers=HEADERS, timeout=15, allow_redirects=True)
        
        print(f"Fetching: {target_url} -> Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Warning: Site blocked or failed with status {response.status_code}")
            return None

        html_text = response.text

        # ------------------ Logic 1: Pixeldrain / iwebp Store Extract ------------------
        # पहले BeautifulSoup से check करें
        soup = BeautifulSoup(html_text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if ('/u/' in href or 'pixeldrain' in href or 'iwebp.store' in href) and 'download' in href:
                match = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
                if match:
                    file_id = match.group(1)
                    return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # अगर BeautifulSoup में नहीं मिला, तो Raw HTML में Regex चलाएं
        pixel_match = re.search(r'https?://[^\s\'"]+/u/([a-zA-Z0-9_-]+)', html_text)
        if pixel_match:
            file_id = pixel_match.group(1)
            return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # ------------------ Logic 2: Direct https://pub URL Search ------------------
        # BeautifulSoup <a> href check
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://pub'):
                return href

        # पूरे HTML text में से https://pub वाला URL ढूँढें (Regex search)
        pub_match = re.search(r'https://pub[^\s\'"<>]+', html_text)
        if pub_match:
            return pub_match.group(0)

    except Exception as e:
        print(f"Error fetching {target_url}: {e}")
    
    return None

def process_playlist():
    print("Fetching existing playlist...")
    try:
        response = requests.get(PLAYLIST_URL, headers=HEADERS)
        if response.status_code != 200:
            print("Failed to fetch M3U playlist.")
            return
        playlist_content = response.text
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return

    lines = playlist_content.splitlines()
    new_lines = ["#EXTM3U"]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF"):
            extinf_header = line
            i += 1
            if i < len(lines):
                target_url = lines[i].strip()
                if target_url and not target_url.startswith("#"):
                    extracted_link = bypass_and_extract_link(target_url)
                    if extracted_link:
                        print(f"-> SUCCESS: {extracted_link}\n")
                        new_lines.append(extinf_header)
                        new_lines.append(extracted_link)
                    else:
                        print(f"-> SKIPPED: No link extracted from {target_url}\n")
        i += 1

    # Save output
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    
    print("Playlist update process completed!")

if __name__ == "__main__":
    process_playlist()
