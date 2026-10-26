import re
import requests
from bs4 import BeautifulSoup

# आपकी M3U प्लेलिस्ट का रॉ लिंक
PLAYLIST_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

def bypass_and_extract_link(page_url):
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # लॉजिक 1: Pixeldrain / iwebp store / download links check & replace
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/u/' in href and ('download' in href or 'pixeldrain' in href or 'iwebp.store' in href):
                match = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
                if match:
                    file_id = match.group(1)
                    return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # लॉजिक 2: https://pub से शुरू होने वाले डायरेक्ट लिंक्स
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://pub'):
                return href

    except Exception as e:
        print(f"Error fetching {page_url}: {e}")
    
    return None

def process_playlist():
    print("Fetching existing playlist...")
    try:
        response = requests.get(PLAYLIST_URL, headers=HEADERS)
        if response.status_code != 200:
            print("Failed to fetch playlist.")
            return
        playlist_content = response.text
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return

    lines = playlist_content.splitlines()
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # अगर यह एक्सटइन्फो (#EXTINF) है, तो इसे और इसके नीचे वाले URL को प्रोसेस करेंगे
        if line.startswith("#EXTINF"):
            new_lines.append(line)
            i += 1
            if i < len(lines):
                target_url = lines[i].strip()
                print(f"Processing: {target_url}")
                
                # बोट बायपास और लिंक एक्सट्रैक्ट करना
                extracted_link = bypass_and_extract_link(target_url)
                
                if extracted_link:
                    print(f"-> Success: {extracted_link}")
                    new_lines.append(extracted_link)
                else:
                    print(f"-> Skipped (No valid link found)")
                    # अगर दोनों लॉजिक फेल हो जाएं, तो EXTINF और इस लाइन को हटा दें (यानी चैनल स्किप)
                    new_lines.pop() 
        else:
            if line and not line.startswith("#"):
                # अगर कोई अन्य डायरेक्ट लिंक है
                extracted_link = bypass_and_extract_link(line)
                if extracted_link:
                    new_lines.append(extracted_link)
            elif line.startswith("#"):
                new_lines.append(line)
        i += 1

    # अपडेटेड M3U फाइल सेव करें
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
    
    print("Playlist updated successfully!")

if __name__ == "__main__":
    process_playlist()
