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
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 2. Sabse pehle Pixeldrain /u/ pattern check karo (text ya tags me)
                    pixeldrain_match = re.search(r'/u/([a-zA-Z0-9_-]+)', html_content)
                    if pixeldrain_match:
                        file_id = pixeldrain_match.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> Found Pixeldrain: {final_direct_url}")
                    else:
                        # 3. Agar Pixeldrain na mile, toh sabhi <a> tags ko check karo ki kisika href 'pub' ya '.r2.dev' se start hota hai
                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            # Agar href mein /u/ hai toh pixeldrain bana lo
                            if '/u/' in href:
                                match_id = re.search(r'/u/([a-zA-Z0-9_-]+)', href)
                                if match_id:
                                    file_id = match_id.group(1)
                                    final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                                    print(f"-> Found Pixeldrain in Tag: {final_direct_url}")
                                    break
                            # Agar pub ya r2.dev hai aur filesdl/zdownload nahi hai, toh yeh hamara target link hai!
                            elif ('pub' in href or 'r2.dev' in href) and "filesdl.in" not in href and "zdownload" not in href:
                                final_direct_url = href
                                print(f"-> Found Pub/R2 Link in Tag: {final_direct_url}")
                                break
                        
                        # Agar tags mein nahi mila, toh regex se poore HTML me dhoondo
                        if not final_direct_url:
                            matches = re.findall(r'https?://[^\s<>"]+', html_content)
                            for url in matches:
                                if ('pub-' in url or 'r2.dev' in url) and "filesdl.in" not in url and "zdownload" not in url:
                                    final_direct_url = url
                                    print(f"-> Found Pub/R2 Link via Regex: {final_direct_url}")
                                    break
            except Exception as e:
                print(f"Error opening {page_url}: {e}")
            
            # Agar valid link mil gaya toh add karo, warna skip karo
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"', 'group-title="🎞️4k Movies🆕"', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel (No Pixeldrain or Pub link found).")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Playlist successfully updated!")

if __name__ == "__main__":
    process_playlist()
