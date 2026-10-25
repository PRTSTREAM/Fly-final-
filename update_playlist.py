import os
import re
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
            
            # 1. Image URL replacement (60-65-2x -> 280-380-3x)
            if "60-65-2x" in extinf_line:
                extinf_line = extinf_line.replace("60-65-2x", "280-380-3x")
                print("-> Updated image resolution in EXTINF")
            
            # Agli line page URL honi chahiye
            if i + 1 < len(lines) and not lines[i+1].startswith("#"):
                page_url = lines[i+1].strip()
                i += 1
            else:
                i += 1
                continue
            
            print(f"Checking URL: {page_url}")
            final_direct_url = None
            
            try:
                page_res = scraper.get(page_url, timeout=15)
                
                if page_res.status_code == 200:
                    html_content = page_res.text
                    
                    # 2. Sabse pehle Pixeldrain /u/ pattern check karo
                    pixeldrain_match = re.search(r'/u/([a-zA-Z0-9_-]+)', html_content)
                    if pixeldrain_match:
                        file_id = pixeldrain_match.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> Found Pixeldrain (/u/ pattern): {final_direct_url}")
                    else:
                        # 3. Agar Pixeldrain na mile, toh 'pub' ya koi bhi download/dl link dhoondo taaki miss na ho
                        match_pub = re.search(r'https?://[^\s<>"]+?(?:pub|download|dl)[^\s<>"]*', html_content)
                        if match_pub:
                            final_direct_url = match_pub.group(0)
                            print(f"-> Found Direct/Pub Link: {final_direct_url}")
                        else:
                            # BeautifulSoup se a tags check karo
                            soup = BeautifulSoup(html_content, 'html.parser')
                            for a_tag in soup.find_all('a', href=True):
                                href = a_tag['href']
                                if '/u/' in href:
                                    match_id = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
                                    if match_id:
                                        file_id = match_id.group(1)
                                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                                        print(f"-> Found Pixeldrain in Tag: {final_direct_url}")
                                        break
                                elif 'pub' in href or 'download' in href or 'dl' in href:
                                    final_direct_url = href
                                    print(f"-> Found Link in Tag: {final_direct_url}")
                                    break
            except Exception as e:
                print(f"Error opening {page_url}: {e}")
            
            # Agar valid link mila tabhi add karo aur group-title set karo, warna skip karo
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel (No valid link found).")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist successfully updated with image fix and link matching!")

if __name__ == "__main__":
    process_playlist()
