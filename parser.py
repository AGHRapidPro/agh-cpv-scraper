import os
import xlrd
import json

class XLSConverter:
    def __init__(self, file_path):
        self.file_path = file_path

    def convert(self, output_file_path=None):
        if output_file_path is None:
            base = os.path.splitext(self.file_path)[0]
            output_file_path = base + '.json'

        workbook = xlrd.open_workbook(self.file_path)
        sheet = workbook.sheet_by_index(0)

        items = []
        current_category = None
        current_cpv = None
        in_empty_category = False

        for row_idx in range(1, sheet.nrows):
            row = sheet.row(row_idx)

            # Extract values with proper type handling
            lp_val = self._get_cell_value(row, 0)
            cpv_val = self._get_cell_value(row, 1)
            name_val = self._get_cell_value(row, 2)
            pln_val = self._get_cell_value(row, 3)
            eur_val = self._get_cell_value(row, 4)

            # Skip completely empty rows
            if not any([lp_val, cpv_val, name_val, pln_val, eur_val]):
                continue

            # Detect empty category markers (no name and no CPV)
            if not name_val and not cpv_val:
                in_empty_category = True
                continue

            # Reset empty category flag when we find valid name/CPV
            if name_val or cpv_val:
                in_empty_category = False

            # Skip rows within empty categories
            if in_empty_category:
                continue

            # Handle category rows (have name but may or may not have CPV)
            if name_val and self._is_price_empty(pln_val, eur_val):
                # Only set category if it has either name or CPV
                current_category = name_val
                current_cpv = cpv_val if cpv_val else None
                continue

            # Handle item rows (must have name and at least one price)
            if name_val and not self._is_price_empty(pln_val, eur_val):
                # Skip if no valid CPV available (neither item nor category has CPV)
                if not cpv_val and not current_cpv:
                    continue

                # Use item's CPV if available, otherwise use category's CPV
                code = cpv_val if cpv_val else current_cpv

                # Skip if no valid category
                if not current_category:
                    continue

                # Convert and validate LP
                try:
                    lp_float = float(lp_val)
                except (ValueError, TypeError):
                    continue

                # Format prices to 2 decimal places
                pln_str = self._format_price(pln_val)
                eur_str = self._format_price(eur_val)

                items.append({
                    "category": current_category,
                    "lp": lp_float,
                    "code": code,
                    "name": name_val,
                    "price_pln": pln_str,
                    "price_eur": eur_str
                })

        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        return output_file_path

    def _get_cell_value(self, row, index):
        """Extract cell value with proper type handling"""
        if index >= len(row):
            return ""

        cell = row[index]
        if cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
            return ""

        # Convert numbers to floats, leave strings as-is
        if cell.ctype == xlrd.XL_CELL_NUMBER:
            return float(cell.value)

        return str(cell.value).strip()

    def _is_price_empty(self, pln, eur):
        """Check if both prices are empty/zero"""
        pln_empty = pln in (0, 0.0, "", None)
        eur_empty = eur in (0, 0.0, "", None)
        return pln_empty and eur_empty

    def _format_price(self, value):
        """Format price as string rounded to 2 decimals or empty string"""
        if value in (0, 0.0, "", None):
            return ""

        try:
            # Handle both string and numeric values
            num_value = float(value)
            return f"{num_value:.2f}"
        except (ValueError, TypeError):
            return ""
