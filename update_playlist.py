import os
import re
import requests
from bs4 import BeautifulSoup

INPUT_M3U_URL = "https://raw.githubusercontent.com/PRTSTREAM/Filmyfy/refs/heads/main/playlist.m3u"
OUTPUT_M3U_FILE = "playlist.m3u"

def process_playlist():
    print("Fetching original playlist...")
    response = requests.get(INPUT_M3U_URL)
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
            # Agli line URL honi chahiye
            if i + 1 < len(lines) and not lines[i+1].startswith("#"):
                page_url = lines[i+1].strip()
                i += 1
            else:
                i += 1
                continue
            
            print(f"Checking URL: {page_url}")
            final_direct_url = None
            
            try:
                # Page ka HTML code fetch karo
                page_res = requests.get(page_url, timeout=10)
                if page_res.status_code == 200:
                    html_content = page_res.text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 1. Check for Pixeldrain URL
                    pixeldrain_match = re.search(r'pixeldrain\.dev/u/([a-zA-Z0-9_-]+)', html_content)
                    if pixeldrain_match:
                        file_id = pixeldrain_match.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> Found Pixeldrain, converted to API: {final_direct_url}")
                    else:
                        # 2. Check for alternative download link (jaise 'pub' wala url ya a tag links)
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            if 'pub' in href or 'download' in href.lower() or 'dl' in href.lower():
                                final_direct_url = href
                                print(f"-> Found fallback direct link: {final_direct_url}")
                                break
            except Exception as e:
                print(f"Error scraping {page_url}: {e}")
            
            # Agar valid direct link mil gaya, toh playlist mein add karo
            if final_direct_url:
                # Group title ko update karke '🎞️4k Movies🆕' kar do
                # Agar group-title pehle se hai toh regex se replace karo, nahi toh add karo
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"]*', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel (No Pixeldrain or valid download link found).")
        
        i += 1
        
    # Updated M3U file save karo
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist processing completed and saved to", OUTPUT_M3U_FILE)

if __name__ == "__main__":
    process_playlist()
