import re
import xlrd

class XlsParser:
    @staticmethod
    def is_valid_cpv(cpv):
        return bool(re.fullmatch(r'\d{8}-\d', str(cpv).strip()))
    
    @staticmethod
    def clean_price(value):
        if isinstance(value, (int, float)):
            return str(float(value))
        
        if not value:
            return None
            
        s = str(value).strip()
        s = re.sub(r'[^\d.,-]', '', s)
        s = s.replace(',', '.')
        
        try:
            return str(float(s))
        except ValueError:
            return None

    def parse(self, filename):
        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_index(0)
        products = []
        current_category = None
        
        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)
            if len(row) < 5:
                continue
                
            lp_val, cpv_val, name_val, pln_val, eur_val = row[:5]
            
            # Clean prices for both category and product checks
            pln_clean = self.clean_price(pln_val)
            eur_clean = self.clean_price(eur_val)
            
            # Category detection - both prices must be zero or empty
            if (pln_clean in (None, '0.0') and 
                eur_clean in (None, '0.0') and
                self.is_valid_cpv(cpv_val) and
                name_val):
                current_category = {
                    'name': name_val,
                    'code': str(cpv_val).strip()
                }
                continue
            
            # Skip products without category context
            if not current_category:
                continue
                
            # Skip products without name or invalid line number
            if not name_val:
                continue
            try:
                lp_float = float(lp_val)
            except (TypeError, ValueError):
                continue
                
            # Skip products with no valid prices
            if pln_clean is None and eur_clean is None:
                continue
                
            # Use product's CPV if valid, otherwise category's CPV
            product_code = (str(cpv_val).strip() if self.is_valid_cpv(cpv_val) 
                            else current_category['code']
            ) 
            products.append({
                "category": current_category['name'],
                "lp": lp_float,
                "code": product_code,
                "name": name_val,
                "price_pln": pln_clean or "",
                "price_eur": eur_clean or ""
            })
            
        return products

import sys
import os
import json
#from parser import XlsParser

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <file.xls>")
        return

    input_path = sys.argv[1]
    output_path = os.path.splitext(input_path)[0] + '.json'
    
    parser = XlsParser()
    products = parser.parse(input_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"Converted {len(products)} products to {output_path}")

if __name__ == "__main__":
    main()


