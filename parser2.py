import os
import re
import openpyxl
import xlrd

class XlsParser:
    @staticmethod
    def clean_price(price_value):
        if price_value is None:
            return None
        if isinstance(price_value, (int, float)):
            return str(float(price_value))
        s = str(price_value)
        s_no_space = s.replace(' ', '')
        s_clean = re.sub(r'[^\d.-]', '', s_no_space)
        if not s_clean or s_clean == '.' or s_clean == '-':
            return None
        try:
            num = float(s_clean)
            return str(num)
        except ValueError:
            return None

    def parse(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.xlsx':
            return self._parse_xlsx(filename)
        elif ext == '.xls':
            return self._parse_xls(filename)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _parse_xlsx(self, filename):
        wb = openpyxl.load_workbook(filename, data_only=True)
        sheet = wb.active
        rows = sheet.iter_rows(min_row=2, values_only=True)
        return self._process_rows(rows)

    def _parse_xls(self, filename):
        book = xlrd.open_workbook(filename)
        sheet = book.sheet_by_index(0)
        rows = []
        for row_idx in range(1, sheet.nrows):
            rows.append(sheet.row_values(row_idx))
        return self._process_rows(rows)

    def _process_rows(self, rows):
        current_category_name = None
        current_category_code = None
        products = []
        
        for row in rows:
            if len(row) < 5:
                continue
            lp_val, cpv_val, name_val, pln_val, eur_val = row[:5]
            
            is_category_row = False
            if cpv_val:
                cpv_str = str(cpv_val).strip()
                if re.fullmatch(r'\d{8}-\d', cpv_str):
                    if (pln_val in [None, '', '-'] or 
                        eur_val in [None, '', '-']):
                        is_category_row = True
                        current_category_name = name_val
                        current_category_code = cpv_str
            
            if is_category_row:
                continue
            
            if (lp_val is None or 
                name_val is None or 
                (pln_val is None and eur_val is None)):
                continue
            
            pln_clean = self.clean_price(pln_val)
            eur_clean = self.clean_price(eur_val)
            if pln_clean is None and eur_clean is None:
                continue
            
            if not current_category_name:
                continue
            
            try:
                lp_float = float(lp_val)
            except (TypeError, ValueError):
                continue
            
            code = current_category_code
            if cpv_val:
                cpv_str = str(cpv_val).strip()
                if re.fullmatch(r'\d{8}-\d', cpv_str):
                    code = cpv_str
            
            product = {
                "category": current_category_name,
                "lp": lp_float,
                "code": code,
                "name": name_val,
                "price_pln": pln_clean if pln_clean is not None else "",
                "price_eur": eur_clean if eur_clean is not None else ""
            }
            products.append(product)
        
        return products

import sys
import os
import json
#from parser import XlsParser

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.isfile(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    
    if not (file_path.endswith('.xls') or file_path.endswith('.xlsx')):
        print("Error: Input file must be an .xls or .xlsx file")
        sys.exit(1)
    
    parser = XlsParser()
    try:
        products = parser.parse(file_path)
    except Exception as e:
        print(f"Error parsing file: {e}")
        sys.exit(1)
    
    output_path = os.path.splitext(file_path)[0] + '.json'
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Successfully wrote output to {output_path}")
    except Exception as e:
        print(f"Error writing JSON file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


