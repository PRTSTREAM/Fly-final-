import os
import re
import time
import cloudscraper

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
            
            # Retry mechanism taaki server block ya timeout na kare
            for attempt in range(3):
                try:
                    time.sleep(1)
                    page_res = scraper.get(page_url, timeout=30)
                    
                    if page_res.text:
                        html_content = page_res.text
                        
                        # 1. Poore HTML source code me sabse pehle Pixeldrain /u/ pattern dhoondo
                        match_pixel = re.search(r'/u/([a-zA-Z0-9_-]+)', html_content)
                        if match_pixel:
                            file_id = match_pixel.group(1)
                            final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                            print(f"-> Found Pixeldrain in HTML source: {final_direct_url}")
                            break
                        
                        # 2. Agar Pixeldrain nahi mila, tabhi poore HTML source code me Pub/R2 link dhoondo
                        all_links = re.findall(r'https?://[^\s<>"]+', html_content)
                        for link in all_links:
                            if ('pub-' in link or 'r2.dev' in link) and "filesdl.in" not in link and "zdownload" not in link:
                                final_direct_url = link
                                print(f"-> Found Pub Link in HTML source: {final_direct_url}")
                                break
                        
                        if final_direct_url:
                            break
                except Exception as e:
                    print(f"Attempt {attempt+1} error for {page_url}: {e}")
                    time.sleep(2)
            
            # Agar dono me se kuch bhi mil gaya toh add karo, warna skip karo
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel (Neither Pixeldrain nor Pub found in HTML source).")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist updated successfully!")

if __name__ == "__main__":
    process_playlist()
