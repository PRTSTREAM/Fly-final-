import re
from bs4 import BeautifulSoup
from curl_cffi import requests  # असली क्रोम ब्राउज़र का फिंगरप्रिंट मिमिक करने के लिए

PLAYLIST_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"

def bypass_and_extract_link(target_url):
    try:
        # अगर लिंक पहले से डायरेक्ट स्ट्रीम या पब यूआरएल है
        if target_url.startswith("https://pub") or "pixeldrain.dev/api/file/" in target_url:
            return target_url

        print(f"Fetching via Chrome TLS Impersonation: {target_url}")
        
        # curl_cffi से रिक्वेस्ट भेजें जो 403/Cloudflare को बायपास कर देगा
        response = requests.get(target_url, impersonate="chrome", timeout=20)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Warning: Failed with status {response.status_code}")
            return None

        html_text = response.text

        # ------------------ Logic 1: Pixeldrain / iwebp Store Extract ------------------
        soup = BeautifulSoup(html_text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if ('/u/' in href or 'pixeldrain' in href or 'iwebp.store' in href) and 'download' in href:
                match = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
                if match:
                    file_id = match.group(1)
                    return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # Raw HTML Regex for Pixeldrain
        pixel_match = re.search(r'https?://[^\s\'"]+/u/([a-zA-Z0-9_-]+)', html_text)
        if pixel_match:
            file_id = pixel_match.group(1)
            return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # ------------------ Logic 2: Direct https://pub URL Search ------------------
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://pub'):
                return href

        # Raw HTML Regex for pub links
        pub_match = re.search(r'https://pub[^\s\'"<>]+', html_text)
        if pub_match:
            return pub_match.group(0)

    except Exception as e:
        print(f"Error fetching {target_url}: {e}")
    
    return None

def process_playlist():
    print("Fetching existing playlist...")
    try:
        # प्लेलिस्ट डाउनलोड करने के लिए सामान्य रिक्वेस्ट या curl_cffi का उपयोग
        res = requests.get(PLAYLIST_URL, impersonate="chrome")
        if res.status_code != 200:
            print("Failed to fetch M3U playlist.")
            return
        playlist_content = res.text
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
    
    print("Playlist update process completed successfully!")

if __name__ == "__main__":
    process_playlist()
