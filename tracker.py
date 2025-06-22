import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

MONTHS_POLISH = {
    'styczeń': 1, 'luty': 2, 'marzec': 3, 'kwiecień': 4,
    'maj': 5, 'czerwiec': 6, 'lipiec': 7, 'sierpień': 8,
    'wrzesień': 9, 'październik': 10, 'listopad': 11, 'grudzień': 12
}
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'

class ProcurementTracker:
    def __init__(self, output_directory):
        self.output_directory = output_directory
        self.state_file = os.path.join(output_directory, '.procurement_tracker.json')
        self.any_upgrade = False
        os.makedirs(output_directory, exist_ok=True)
        self.state = self.load_state()
        self.verify_existing_files()
    
    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'downloaded': {}}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def verify_existing_files(self):
        for file_id, data in list(self.state['downloaded'].items()):
            file_path = os.path.join(self.output_directory, f"{file_id}.xls")
            if not os.path.exists(file_path):
                print(f"Missing file detected: {file_id}.xls. Redownloading...")
                self.download_file(data['url'], file_id, data['version'])

    def extract_version(self, text):
        match = re.search(r'(?:ver|wersja|version)[\s._]*(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 1

    def process_links(self, base_url):
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        found_links = False
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if not href.endswith('.xls'):
                continue
            
            full_url = urljoin(base_url, link['href'])
            text = (link.text + full_url).lower()
            
            for polish_month, month_num in MONTHS_POLISH.items():
                if polish_month in text:
                    year_match = re.search(r'20\d{2}', full_url)
                    if not year_match:
                        continue
                    
                    year = int(year_match.group(0))
                    file_id = f"{year}-{month_num:02d}"
                    version = self.extract_version(text)
                    found_links = True
                    
                    current = self.state['downloaded'].get(file_id, {'version': 0})
                    if version > current.get('version', 0):
                        self.any_upgrade = True
                        self.download_file(full_url, file_id, version)
                    break
        
        if not found_links:
            print("No valid links found on the page.")
        elif not self.any_upgrade:
            print("All files are up-to-date.")

    def download_file(self, url, file_id, version):
        output_path = os.path.join(self.output_directory, f"{file_id}.xls")
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        self.state.setdefault('downloaded', {})[file_id] = {
            'url': url,
            'version': version,
            'downloaded_at': datetime.now().isoformat()
        }
        print(f"Downloaded: {file_id}.xls (v{version})")
