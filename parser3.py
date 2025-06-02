#!/usr/bin/env python3

import os
import re
import json
import argparse
import datetime
from urllib.parse import urlsplit
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.request


class ProcurementTracker:
    """Tracks and processes procurement files based on remote href states."""
    
    MONTHS_TO_NUMBERS = {
        'styczeń': 1, 'luty': 2, 'marzec': 3, 'kwiecień': 4,
        'maj': 5, 'czerwiec': 6, 'lipiec': 7, 'sierpień': 8,
        'wrzesień': 9, 'październik': 10, 'listopad': 11, 'grudzień': 12
    }
    
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
    
    def __init__(self, output_directory):
        self.output_directory = output_directory
        self.state_file = os.path.join(output_directory, '.procurement_tracker.json')
        self._ensure_output_directory_exists()
        self.state = self._load_state()
    
    def _ensure_output_directory_exists(self):
        """Create output directory if needed."""
        os.makedirs(self.output_directory, exist_ok=True)

    def _load_state(self):
        """Load tracking state from file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {'tracked_files': {}}

    def _save_state(self):
        """Persist current tracking state."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _convert_month_name_to_number(self, month_name):
        """Convert Polish month name to number."""
        return self.MONTHS_TO_NUMBERS.get(month_name.lower(), 1)

    def _generate_file_id(self, year, month):
        """Create standardized file identifier."""
        return f"{year}-{month:02d}"

    def _process_excel_file(self, excel_path, output_base_name):
        """Convert Excel file to JSON and clean up."""
        try:
            # Read and fix Excel if needed
            df = pd.read_excel(excel_path)
            if len(df.columns) > 5:
                fixed_path = f"{output_base_name}.xlsx"
                df = df.iloc[:, :5]
                df = df[df.apply(lambda row: row.count(), axis=1) == 5]
                df.to_excel(fixed_path, index=False)
                os.remove(excel_path)
                excel_path = fixed_path

            # Process data
            df.columns = ["id", "code", "name", "price_pln", "price_eur"]
            products = df[df['name'].notnull()].copy()
            products['price_pln'] = products['price_pln'].fillna(0).apply(
                lambda x: str(round(float(x), 2)) if str(x).replace('.','').isdigit() else '0')
            products['price_eur'] = products['price_eur'].fillna(0).apply(
                lambda x: str(round(float(x), 2)) if str(x).replace('.','').isdigit() else '0')
            products['code'] = products['code'].fillna('')

            # Categorize products
            categories = []
            current_category = []
            for _, row in products.iterrows():
                if (row['price_pln'] == '0.0' and 
                    row['price_eur'] == '0.0' and 
                    len(current_category) > 0):
                    categories.append({
                        "category": current_category[0]['name'],
                        "products": current_category
                    })
                    current_category = [row.to_dict()]
                else:
                    current_category.append(row.to_dict())

            # Save JSON
            json_path = f"{output_base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False)

            # Clean up
            if os.path.exists(excel_path):
                os.remove(excel_path)

            return True
        except Exception as e:
            print(f"Error processing {excel_path}: {e}")
            return False

    def _download_if_needed(self, file_url, file_id, href):
        """Download and process file if it's new or changed."""
        current_state = self.state['tracked_files'].get(file_id, {})
        
        # Skip if href hasn't changed
        if current_state.get('href') == href:
            print(f"Skipping unchanged file: {file_id}")
            return False
        
        # Determine output paths
        is_current = file_id == self._generate_file_id(
            datetime.date.today().year,
            datetime.date.today().month
        )
        output_name = os.path.join(
            self.output_directory,
            'latest' if is_current else file_id
        )
        xls_path = f"{output_name}.xls"

        # Download and process
        print(f"Processing new/updated file: {file_id}")
        urllib.request.urlretrieve(file_url, xls_path)
        
        if self._process_excel_file(xls_path, output_name):
            # Update state
            self.state['tracked_files'][file_id] = {
                'href': href,
                'last_processed': datetime.datetime.now().isoformat(),
                'json_path': f"{output_name}.json"
            }
            return True
        return False

    def process_url(self, url):
        """Main processing method with href-based tracking."""
        try:
            response = requests.get(url, headers={'User-Agent': self.USER_AGENT})
            soup = BeautifulSoup(response.text, "html.parser")
            found_hrefs = set()

            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                
                # Check if link matches procurement file pattern
                if not re.search(
                    r'Dostawy i usługi .*plan zamówień publicznych \d{4} .*'
                    r'(grudzień|listopad|październik|wrzesień|sierpień|'
                    r'lipiec|czerwiec|styczeń|luty|marzec|kwiecień|maj)',
                    link_text, re.IGNORECASE
                ):
                    continue

                # Extract year and month
                year_match = re.search(r'20\d{2}', link_text)
                month_match = re.search(
                    'grudzień|listopad|październik|wrzesień|sierpień|'
                    'lipiec|czerwiec|styczeń|luty|marzec|kwiecień|maj',
                    link_text, re.IGNORECASE
                )
                if not year_match or not month_match:
                    continue

                file_year = int(year_match.group())
                file_month = self._convert_month_name_to_number(month_match.group())
                file_id = self._generate_file_id(file_year, file_month)
                href = link['href']
                found_hrefs.add(file_id)

                # Build full URL
                url_parts = urlsplit(url)
                file_url = f"{url_parts.scheme}://{url_parts.netloc}{href}"

                print(flie_url)

                # Process file if needed
                #self._download_if_needed(file_url, file_id, href)

            # Remove disappeared files from state (except current month)
            current_file_id = self._generate_file_id(
                datetime.date.today().year,
                datetime.date.today().month
            )
            for file_id in list(self.state['tracked_files'].keys()):
                if file_id not in found_hrefs and file_id != current_file_id:
                    print(f"File no longer available: {file_id}")
                    # Keep in state but mark as unavailable
                    self.state['tracked_files'][file_id]['available'] = False

            self._save_state()
            return True

        except Exception as e:
            print(f"Error processing {url}: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Track and process procurement files based on remote href states"
    )
    parser.add_argument(
        '-u', '--url',
        default='https://www.dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych-agh/',
        help='Source URL to monitor'
    )
    parser.add_argument(
        '-o', '--output',
        default='./cpv',
        help='Output directory for processed files'
    )
    
    args = parser.parse_args()
    tracker = ProcurementTracker(args.output)
    tracker.process_url(args.url)


if __name__ == "__main__":
    main()
