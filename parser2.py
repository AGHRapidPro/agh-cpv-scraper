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


class XLSProcessor:
    """Handles downloading, processing, and converting XLS files to JSON."""
    
    MONTHS_TO_NUMBERS = {
        'styczeń': 1,
        'luty': 2,
        'marzec': 3,
        'kwiecień': 4,
        'maj': 5,
        'czerwiec': 6,
        'lipiec': 7,
        'sierpień': 8,
        'wrzesień': 9,
        'październik': 10,
        'listopad': 11,
        'grudzień': 12
    }
    
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
    
    def __init__(self, output_directory):
        self.output_directory = output_directory
        self._ensure_output_directory_exists()
    
    def _ensure_output_directory_exists(self):
        """Create output directory if it doesn't exist."""
        try:
            os.makedirs(self.output_directory, exist_ok=True)
            print(f"Directory '{self.output_directory}' ready.")
        except PermissionError:
            print(f"Permission denied: Unable to create '{self.output_directory}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def _convert_month_name_to_number(self, month_name):
        """Convert Polish month name to its numerical representation."""
        return self.MONTHS_TO_NUMBERS.get(month_name.lower(), 1)

    def _safe_round_number(self, value):
        """Safely convert and round a value to 2 decimal places."""
        try:
            return str(round(float(value), 2))
        except (ValueError, TypeError):
            return '0'

    def _fix_broken_xls_file(self, dataframe, output_path):
        """Fix malformed XLS files by selecting only the first 5 columns with complete data."""
        relevant_columns = dataframe.iloc[:, :5]
        valid_rows = relevant_columns.apply(lambda row: row.count(), axis=1) == 5
        fixed_data = relevant_columns[valid_rows]
        fixed_data.to_excel(output_path, index=False)
        print(f'Fixed XLS file saved to {output_path}')

    def _parse_product_data(self, excel_path):
        """Extract and clean product data from Excel file."""
        dataframe = pd.read_excel(excel_path)
        
        # Rename columns for clarity
        dataframe.columns = ["id", "code", "name", "price_pln", "price_eur"]
        
        # Clean and filter data
        cleaned_data = dataframe[dataframe['name'].notnull()].copy()
        cleaned_data['price_pln'] = cleaned_data['price_pln'].fillna(0).apply(self._safe_round_number)
        cleaned_data['price_eur'] = cleaned_data['price_eur'].fillna(0).apply(self._safe_round_number)
        cleaned_data['code'] = cleaned_data['code'].fillna('')
        
        return cleaned_data.to_dict('records')

    def _group_products_by_category(self, product_list):
        """Organize products into categories based on pricing patterns."""
        categorized_products = []
        current_category = []
        
        for product in product_list:
            if (product['price_pln'] == '0.0' and 
                product['price_eur'] == '0.0' and 
                len(current_category) > 0):
                categorized_products.append({
                    "category": current_category[0]['name'],
                    "products": current_category
                })
                current_category = [product]
            else:
                current_category.append(product)
        
        return categorized_products

    def _save_as_json(self, data, output_path):
        """Save processed data to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False)
            print(f"JSON file saved successfully to {output_path}")
        except Exception as e:
            print(f"Error writing JSON file: {e}")

    def _download_file(self, url, save_path):
        """Download file from URL and save to specified path."""
        print(f'Downloading {url} to {save_path}')
        urllib.request.urlretrieve(url, save_path)
        print('Download complete')

    def _process_excel_file(self, excel_path, output_base_name):
        """Process Excel file through the entire pipeline."""
        try:
            dataframe = pd.read_excel(excel_path)
            
            # Handle broken files with extra columns
            if len(dataframe.columns) > 5:
                os.remove(excel_path)
                fixed_path = f"{output_base_name}.xlsx"
                self._fix_broken_xls_file(dataframe, fixed_path)
                excel_path = fixed_path
            
            # Process and save data
            product_data = self._parse_product_data(excel_path)
            categorized_data = self._group_products_by_category(product_data)
            self._save_as_json(categorized_data, f"{output_base_name}.json")
            
            # Clean up
            os.remove(excel_path)
            print(f"Temporary file {excel_path} removed")
        except Exception as e:
            print(f"Error processing {excel_path}: {e}")

    def _is_relevant_link(self, link_text):
        """Check if link text matches the pattern of procurement files."""
        pattern = (
            r'Dostawy i usługi .*plan zamówień publicznych \d{4} .*'
            r'(grudzień( \d{1}\.?0?)?|listopad( \d{1}\.?0?)?|'
            r'październik( \d{1}\.?0?)?|wrzesień( \d{1}\.?0?)?|'
            r'sierpień( \d{1}\.?0?)?|lipiec( \d{1}\.?0?)?|'
            r'czerwiec( \d{1}\.?0?)?|styczeń( \d{1}\.?0?)?|'
            r'luty( \d{1}\.?0?)?|marzec( \d{1}\.?0?)?|'
            r'kwiecień( \d{1}\.?0?)?|maj( \d{1}\.?0?)?)'
        )
        return re.search(pattern, link_text, re.IGNORECASE)

    def _generate_output_name(self, year, month, is_current=False):
        """Generate standardized output filename."""
        if is_current:
            return os.path.join(self.output_directory, 'latest')
        return os.path.join(self.output_directory, f"{year}-{month:02d}")

    def process_url(self, url):
        """Main method to process all files from a given URL."""
        try:
            response = requests.get(url, headers={'User-Agent': self.USER_AGENT})
            soup = BeautifulSoup(response.text, "html.parser")
            
            current_date = datetime.date.today()
            current_year = current_date.year
            current_month = current_date.month
            
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().strip()
                
                if not self._is_relevant_link(link_text):
                    continue
                
                # Extract year and month from filename
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
                
                # Build full URL
                url_parts = urlsplit(url)
                file_url = f"{url_parts.scheme}://{url_parts.netloc}{link['href']}"
                
                # Determine output filename
                is_current = (file_year == current_year and file_month == current_month)
                output_name = self._generate_output_name(file_year, file_month, is_current)
                xls_path = f"{output_name}.xls"
                
                # Download and process file
                self._download_file(file_url, xls_path)
                self._process_excel_file(xls_path, output_name)
                
        except Exception as e:
            print(f"Error processing URL {url}: {e}")


def main():
    """Entry point for command line execution."""
    parser = argparse.ArgumentParser(
        description="Download and convert public procurement XLS files to JSON"
    )
    parser.add_argument(
        '-u', '--url',
        default='https://www.dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych-agh/',
        help='URL to scrape for XLS files'
    )
    parser.add_argument(
        '-o', '--output',
        default='./cpv',
        help='Output directory for processed files'
    )
    
    args = parser.parse_args()
    processor = XLSProcessor(args.output)
    processor.process_url(args.url)


if __name__ == "__main__":
    main()
