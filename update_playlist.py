import re
from bs4 import BeautifulSoup
from curl_cffi import requests  # Cloudflare / 403 Bypass के लिए

PLAYLIST_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"
GROUP_TITLE_NAME = "🎬 NEW 4K"

def add_or_update_group_title(extinf_line, group_name):
    # अगर लाइन #EXTINF से शुरू नहीं होती, तो वैसे ही लौटा दें
    if not extinf_line.startswith("#EXTINF"):
        return extinf_line
        
    # कॉमा (,) से एट्रीब्यूट्स और चैनल/मूवी के नाम को अलग करें
    if ',' in extinf_line:
        attrs_part, name_part = extinf_line.split(',', 1)
    else:
        attrs_part = extinf_line
        name_part = ""
        
    # चेक करें कि क्या पहले से group-title मौजूद है
    if 'group-title=' in attrs_part:
        # अगर है तो उसे नए वाले से बदल दें
        attrs_part = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', attrs_part)
        attrs_part = re.sub(r"group-title='[^']*'", f'group-title="{group_name}"', attrs_part)
    else:
        # अगर नहीं है तो जोड़ दें
        attrs_part = f'{attrs_part} group-title="{group_name}"'
        
    return f"{attrs_part},{name_part}" if name_part else attrs_part

def bypass_and_extract_link(target_url):
    try:
        if target_url.startswith("https://pub") or "pixeldrain.dev/api/file/" in target_url:
            return target_url

        print(f"Fetching via Chrome TLS Impersonation: {target_url}")
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

        pixel_match = re.search(r'https?://[^\s\'"]+/u/([a-zA-Z0-9_-]+)', html_text)
        if pixel_match:
            file_id = pixel_match.group(1)
            return f"https://pixeldrain.dev/api/file/{file_id}?download"

        # ------------------ Logic 2: Direct https://pub URL Search ------------------
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://pub'):
                return href

        pub_match = re.search(r'https://pub[^\s\'"<>]+', html_text)
        if pub_match:
            return pub_match.group(0)

    except Exception as e:
        print(f"Error fetching {target_url}: {e}")
    
    return None

def process_playlist():
    print("Fetching existing playlist...")
    try:
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
            # Group Title जोड़ें या अपडेट करें
            extinf_header = add_or_update_group_title(line, GROUP_TITLE_NAME)
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
    with open("playlist.m3u", "w",
