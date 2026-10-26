import os
import re
import time
import cloudscraper
from bs4 import BeautifulSoup

INPUT_M3U_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"
OUTPUT_M3U_FILE = "playlist.m3u"

def process_playlist():
    print("Fetching original playlist...")
    
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'android',
            'desktop': False
        }
    )
    
    response = scraper.get(INPUT_M3U_URL)
    if response.status_code != 200:
        print("Failed to fetch playlist!")
        return
    
    lines = response.text.splitlines()
    new_m3u_lines = ["#EXTM3U"]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("#EXTINF:"):
            extinf_line = line
            
            # Image resolution fix (60-65-2x -> 280-380-3x)
            if "60-65-2x" in extinf_line:
                extinf_line = extinf_line.replace("60-65-2x", "280-380-3x")
            
            if i + 1 < len(lines) and not lines[i+1].startswith("#"):
                page_url = lines[i+1].strip()
                i += 1
            else:
                i += 1
                continue
            
            print(f"Checking URL: {page_url}")
            final_direct_url = None
            raw_html = ""
            
            # 6-Step Multi-Logic Execution Flow
            for attempt in range(3):
                try:
                    time.sleep(1)
                    page_res = scraper.get(page_url, timeout=30)
                    
                    if page_res.text:
                        raw_html = page_res.text
                        break
                except Exception as e:
                    # Logic 6: Agar http/https ki problem ya connection fail ho, toh URL scheme switch karke try karo
                    if attempt == 1 and page_url.startswith("http://"):
                        page_url = page_url.replace("http://", "https://")
                    elif attempt == 1 and page_url.startswith("https://"):
                        page_url = page_url.replace("https://", "http://")
                    time.sleep(2)
            
            if raw_html:
                # Unicode aur slashes ko clean karna taaki parsing clean ho
                html = raw_html.replace("\\u003C", "<").replace("\\u003E", ">").replace("\\\"", "\"").replace("\\u0026", "&")
                soup = BeautifulSoup(html, 'html.parser')
                
                # -------------------------------------------------------------
                # LOGIC 1: Sabse pehle /u/... (Pixeldrain) dhoondo chahe koi bhi domain ho
                # -------------------------------------------------------------
                match_pixel = re.search(r'https?://[^\s<>\"']+/u/([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
                if match_pixel:
                    file_id = match_pixel.group(1)
                    final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                    print(f"-> [Logic 1] Found Pixeldrain via Full URL: {final_direct_url}")
                else:
                    match_short_pixel = re.search(r'/u/([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
                    if match_short_pixel:
                        file_id = match_short_pixel.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> [Logic 1] Found Pixeldrain via Short Path: {final_direct_url}")
                
                # -------------------------------------------------------------
                # LOGIC 2: "Fast Cloud" button dhoondo aur uska href link uthao
                # -------------------------------------------------------------
                if not final_direct_url:
                    for a_tag in soup.find_all('a', href=True):
                        text = a_tag.get_text(strip=True).lower()
                        if "fast cloud" in text or "fast cloud" in a_tag.get('class', [''])[0].lower():
                            href = a_tag['href']
                            if href.startswith("http") and "filesdl.in" not in href and "zdownload" not in href:
                                final_direct_url = href
                                print(f"-> [Logic 2] Found via Fast Cloud Button: {final_direct_url}")
                                break
                
                # -------------------------------------------------------------
                # LOGIC 3: Poore HTML mein 'https://pub' se shuru hone wala link dhoondo
                # -------------------------------------------------------------
                if not final_direct_url:
                    matches_pub = re.findall(r'https?://[^\s<>\"']*pub-[^\s<>\"']+', html, re.IGNORECASE)
                    for link in matches_pub:
                        if "filesdl.in" not in link and "zdownload" not in link:
                            final_direct_url = link
                            print(f"-> [Logic 3] Found via 'https://pub' pattern: {final_direct_url}")
                            break
                
                # -------------------------------------------------------------
                # LOGIC 4: Sabhi <a> tags (`<a href=...`) ko scan karo jisme pub ho
                # -------------------------------------------------------------
                if not final_direct_url:
                    for a_tag in soup.find_all('a', href=True):
                        href = a_tag['href']
                        if 'pub-' in href and "filesdl.in" not in href and "zdownload" not in href:
                            final_direct_url = href
                            print(f"-> [Logic 4] Found in <a> tag href: {final_direct_url}")
                            break
                
                # -------------------------------------------------------------
                # LOGIC 5: Kisi bhi link mein 'r2.dev' ho toh use utha lo
                # -------------------------------------------------------------
                if not final_direct_url:
                    matches_r2 = re.findall(r'https?://[^\s<>\"']+\.r2\.dev[^\s<>\"']+', html, re.IGNORECASE)
                    for link in matches_r2:
                        if "filesdl.in" not in link and "zdownload" not in link:
                            final_direct_url = link
                            print(f"-> [Logic 5] Found via r2.dev check: {final_direct_url}")
                            break
            
            # -------------------------------------------------------------
            # LOGIC 6: Agar upar ke saare 5 tareeqe fail ho jayein, toh channel skip
            # -------------------------------------------------------------
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> [Logic 6] All 5 checks failed. Skipping channel: {page_url}")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist updated successfully with 6-Step Logic!")

if __name__ == "__main__":
    process_playlist()
