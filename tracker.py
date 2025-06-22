#!/usr/bin/env python3

import argparse
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
        os.makedirs(output_directory, exist_ok=True)
        self.state = self.load_state()
    
    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'downloaded': {}}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def extract_version(self, text):
        match = re.search(r'(?:ver|wersja|version)[\s._]*(\d+)', text, re.IGNORECASE)
        return int(match.group(1)) if match else 1

    def process_links(self, base_url):
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if not href.endswith('.xls'):
                continue
            
            full_url = urljoin(base_url, link['href'])
            text = link.text.lower() + full_url.lower()
            
            for month_polish, month_num in MONTHS_POLISH.items():
                if month_polish in text:
                    version = self.extract_version(text)
                    year_match = re.search(r'\d{4}', full_url)
                    if not year_match:
                        continue
                    
                    year = int(year_match.group(0))
                    file_id = f"{year}-{month_num:02d}"
                    
                    current = self.state['downloaded'].get(file_id, {'version': 0})
                    if version > current['version']:
                        self.download_file(full_url, file_id, version)
                    break

    def download_file(self, url, file_id, version):
        output_path = os.path.join(self.output_directory, f"{file_id}.xls")
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        self.state['downloaded'][file_id] = {
            'url': url,
            'version': version,
            'downloaded_at': datetime.now().isoformat()
        }
        print(f"Downloaded {url} as {file_id}.xls (v{version})")

def main():
    parser = argparse.ArgumentParser(
        description="Track and download procurement files with version detection"
    )
    parser.add_argument(
        '-u', '--url',
        default='https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych',
        help='Source URL to scrape'
    )
    parser.add_argument(
        '-o', '--output',
        default='./cpv',
        help='Output directory for downloaded files'
    )
    args = parser.parse_args()
    
    tracker = ProcurementTracker(args.output)
    tracker.process_links(args.url)
    tracker.save_state()

if __name__ == "__main__":
    main()
