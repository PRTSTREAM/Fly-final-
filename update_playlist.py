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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
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
                # Session ya headers ke sath request bhejo taaki block na kare
                session = requests.Session()
                page_res = session.get(page_url, headers=headers, allow_redirects=True, timeout=15)
                
                if page_res.status_code == 200:
                    html_content = page_res.text
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # 1. Check for Pixeldrain URL in the whole HTML / text / scripts
                    pixeldrain_match = re.search(r'pixeldrain\.dev/u/([a-zA-Z0-9_-]+)', html_content)
                    if pixeldrain_match:
                        file_id = pixeldrain_match.group(1)
                        final_direct_url = f"https://pixeldrain.dev/api/file/{file_id}?download"
                        print(f"-> Found Pixeldrain: {final_direct_url}")
                    else:
                        # 2. Filesdl ya HubCloud / Direct download buttons ke liye a tags aur onclick check karo
                        for a_tag in soup.find_all(['a', 'button'], href=True):
                            href = a_tag['href']
                            text = a_tag.get_text().lower()
                            if 'pub' in href or 'download' in href or 'dl' in href or 'pixeldrain' in href:
                                final_direct_url = href
                                break
                        
                        # Agar a tag mein nahi mila, toh script tags ya forms mein dhoondo
                        if not final_direct_url:
                            for script in soup.find_all('script'):
                                script_text = script.string or ''
                                match = re.search(r'https?://[^\s<>"]+?(?:pub|download|dl)[^\s<>"]*', script_text)
                                if match:
                                    final_direct_url = match.group(0)
                                    break
                        
                        # Agar fir bhi na mile toh filesdl ke page se redirected final url utha lo agar available ho
                        if not final_direct_url and 'filesdl.in' in page_url:
                            # Try fetching buttons with specific classes or text
                            for a in soup.find_all('a', href=True):
                                if 'http' in a['href'] and 'filesdl.in' not in a['href']:
                                    final_direct_url = a['href']
                                    break

                    if final_direct_url:
                        print(f"-> Extracted Link: {final_direct_url}")
                    else:
                        print(f"-> No direct link found in HTML.")
            except Exception as e:
                print(f"Error scraping {page_url}: {e}")
            
            if final_direct_url:
                if 'group-title=' in extinf_line:
                    updated_extinf = re.sub(r'group-title="[^"]*"]*', 'group-title="🎞️4k Movies🆕"', extinf_line)
                    if 'group-title=' not in updated_extinf: # fallback regex check
                        updated_extinf = re.sub(r'group-title="[^"]*">', 'group-title="🎞️4k Movies🆕">', extinf_line)
                else:
                    updated_extinf = extinf_line.replace('#EXTINF:', '#EXTINF:-1 group-title="🎞️4k Movies🆕",')
                
                new_m3u_lines.append(updated_extinf)
                new_m3u_lines.append(final_direct_url)
            else:
                print(f"-> Skipping channel.")
        
        i += 1
        
    with open(OUTPUT_M3U_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_m3u_lines) + '\n')
    print("Done!")

if __name__ == "__main__":
    process_playlist()
