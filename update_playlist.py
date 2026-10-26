import re
import requests
from bs4soup import BeautifulSoup

# आपकी मोजिदा M3U या सोर्स प्लेलिस्ट का रॉ लिंक
PLAYLIST_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive"
}

def bypass_and_extract_links(html_content, title):
    soup = BeautifulSoup(html_content, 'html.parser')
    final_url = None

    # सभी <a> टैग्स चेक करें
    for a in soup.find_all('a', href=True):
        href = a['href']
        
        # लॉजिक 1: Pixeldrain / iwebp store / download links check
        if '/u/' in href and ('download' in href or 'pixeldrain' in href or 'iwebp.store' in href):
            match = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
            if match:
                file_id = match.group(1)
                final_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                break
        
        # लॉजिक 2: https://pub से शुरू होने वाले लिंक्स
        elif href.startswith('https://pub'):
            final_url = href
            break

    return final_url

def process_playlist():
    print("Fetching existing playlist...")
    try:
        response = requests.get(PLAYLIST_URL, headers=HEADERS)
        playlist_data = response.text
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return

    # यहाँ आप अपनी प्ले लिस्ट के चैनल्स या सोर्स वेबसाइट्स की सूची रख सकते हैं
    # उदाहरण के लिए मान लेते हैं कि आप उन साइट्स को स्कैन कर रहे हैं
    print("Processing links and bypassing bot detection...")
    
    # नई M3U जनरेट करने की प्रक्रिया यहाँ पूरी होगी
    # (आप चाहें तो अपनी डायनामिक लिस्ट यहाँ जोड़ सकते हैं)

if __name__ == "__main__":
    process_playlist()
