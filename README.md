# Procurement Tracker

This Python script automates the tracking and processing of xls files from [AGH DZP website](https://www.dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych-agh/), handling version detection and converting Excel data to structured JSON.

## Features

- **Automated tracking**: Monitors the source URL for new procurement files
- **Version detection**: Identifies newer file versions based on naming patterns
- **Data processing**: Converts Excel files to structured JSON with categorization
- **State management**: Maintains processing history between runs
- **Data cleaning**: Handles inconsistent Excel formats and missing values

## Usage

```bash
python3 -m venv .
source bin/activate
pip install -r requirements.txt
./procurement_tracker.py
```

### Options
| Option | Description | Default |
|--------|-------------|---------|
| `-u`, `--url` | Source URL to monitor | [AGH University Procurement Plans](https://www.dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych-agh/) |
| `-o`, `--output` | Output directory for processed files | `./cpv` |

## Workflow

1. **Scrape** the source URL for procurement files
2. **Detect** file versions based on naming patterns
3. **Download** only newer versions of files
4. **Process** Excel files:
   - Clean and standardize data
   - Categorize products
   - Convert to JSON format
5. **Maintain state** between runs in `.procurement_tracker.json`

## Output Structure

Processed files are saved in the output directory with the following naming convention:

```
cpv/
├── latest.json        # Current month's data
├── 2024-05.json       # Historical data (YYYY-MM)
├── 2024-04.json
└── .procurement_tracker.json  # Processing state
```

### JSON Format Example
```json
[
  {
    "category": "Computer Equipment",
    "list": [
      {"lp": 1, "code": "PC-001", "name": "Laptop", "price_pln": "4500.00", "price_eur": "1000.00"},
      {"lp": 2, "code": "PC-002", "name": "Monitor", "price_pln": "1200.00", "price_eur": "270.00"}
    ]
  },
  {
    "category": "Office Supplies",
    "list": [
      {"lp": 3, "code": "OS-001", "name": "Printer", "price_pln": "800.00", "price_eur": "180.00"}
    ]
  }
]
```

## State Management

The script maintains a state file (`.procurement_tracker.json`) that tracks:

- Processed file versions
- Last processing timestamp
- Output JSON file paths
- Availability status of historical files

## Contribution

Contributions are welcome! Please open an issue or submit a pull request for any:
- Bug fixes
- Feature enhancements
- Documentation improvements

## Notes

- Designed specifically for AGH University's DZP website structure
- Handles Polish month names and date formats
- Processes files with inconsistent Excel formats
- Automatically cleans temporary files after processing
