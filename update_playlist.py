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
                    
                    # 1. Sabse pehle Pixeldrain /u/ pattern check karo (chahe kisi bhi domain par ho)
                    # Jaise: /u/8W1jwq5t?download ya /u/tSoaVSru
                    pixeldrain_match = re.search(r'/u/([a-zA-Z0-9_-]+)', html_content)
                    if pixeldrain_match:
                        file_id = pixeldrain_match.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> Found Pixeldrain (/u/ pattern): {final_direct_url}")
                    else:
                        # 2. Agar Pixeldrain nahi mila, toh 'pub' wala link dhoondo
                        match_pub = re.search(r'https?://[^\s<>"]+?pub[^\s<>"]*', html_content)
                        if match_pub:
                            final_direct_url = match_pub.group(0)
                            print(f"-> Found Pub Link: {final_direct_url}")
                        else:
                            # BeautifulSoup se a tags me bhi check kar lo
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
                                elif 'pub' in href:
                                    final_direct_url = href
                                    print(f"-> Found Pub Link in Tag: {final_direct_url}")
                                    break
            except Exception as e:
                print(f"Error opening {page_url}: {e}")
            
            # Agar Pixeldrain ya Pub link mil gaya, tabhi add karo. Nahi toh skip karo!
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel (No Pixeldrain /u/ or Pub link found).")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist successfully updated with proper /u/ and pub filtering!")

if __name__ == "__main__":
    process_playlist()
