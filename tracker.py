import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from parser import XLSConverter

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
                state = json.load(f)
                # Backward compatibility: add json_path if missing
                for file_id, data in state['downloaded'].items():
                    if 'json_path' not in data:
                        data['json_path'] = os.path.join(
                            self.output_directory,
                            f"{file_id}.json"
                        )
                return state
        return {'downloaded': {}}

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def verify_existing_files(self):
        for file_id, data in list(self.state['downloaded'].items()):
            json_path = data['json_path']
            if not os.path.exists(json_path):
                print(f"Missing JSON file: {json_path}. Redownloading...")
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
        xls_path = os.path.join(self.output_directory, f"{file_id}.xls")
        json_path = os.path.join(self.output_directory, f"{file_id}.json")

        try:
            # Download XLS file
            response = requests.get(url, headers={'User-Agent': USER_AGENT})
            response.raise_for_status()

            with open(xls_path, 'wb') as f:
                f.write(response.content)

            # Convert to JSON and remove XLS
            converter = XLSConverter(xls_path)
            converter.convert(json_path)
            os.remove(xls_path)

            # Update state
            self.state.setdefault('downloaded', {})[file_id] = {
                'url': url,
                'version': version,
                'downloaded_at': datetime.now().isoformat(),
                'json_path': json_path
            }
            print(f"Processed: {file_id}.json (v{version}) from: {url}")

        except Exception as e:
            # Cleanup on error
            if os.path.exists(xls_path):
                os.remove(xls_path)
            if os.path.exists(json_path):
                os.remove(json_path)
            print(f"Error processing {url}: {str(e)}")
