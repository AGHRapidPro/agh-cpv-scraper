# Procurement Tracker

This Python script automates the tracking and processing of xls files from [AGH DZP website](https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych), handling version detection and converting Excel data to structured JSON.

## Features

- **Automated tracking**: Monitors the source URL for new procurement files
- **Version detection**: Identifies newer file versions based on naming patterns
- **Data processing**: Converts Excel files to structured JSON with categorization
- **State management**: Maintains processing history between runs
- **Data cleaning**: Handles inconsistent Excel formats and missing values

## Usage - Docker

### Running:
```bash
docker run --rm -itd \
-v ./agh-cpv-scraper:/app/cpv \
--name agh-cpv-scraper \
aghrapidpro/agh-cpv-scraper:latest
```
### Building:
```bash
docker buildx build \
--build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
-t aghrapidpro/agh-cpv-scraper:1.0 \
-t aghrapidpro/agh-cpv-scraper:latest \
--push .
```

## Usage - local
```bash
python3 -m venv .
source bin/activate
pip install -r requirements.txt
./procurement_tracker.py
```
### Options
| Option | Description | Default |
|--------|-------------|---------|
| `-u`, `--url` | Source URL to monitor | [AGH University Procurement Plans](https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych) |
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
    "name": "Materiały wzorcowe produktow roślinnych",
    "category": "Produkty rolnictwa, hodowli, rybołówstwa, leśnictwa i podobne",
    "lp": 2.0,
    "code": "03000000-1",
    "price_pln": "500.00",
    "price_eur": "107.83"
  },
  {
    "name": "Drewno",
    "category": "Leśnictwo i pozyskiwanie drewna",
    "lp": 5.0,
    "code": "03410000-7",
    "price_pln": "81697.57",
    "price_eur": "17618.25"
  },
  {
    "name": "Paliwa stałe (węgiel i paliwa na bazie węgla, węgiel i torf, koks), ropa naftowa, produkty naftowe",
    "category": "Produkty naftowe, paliwo, energia elektryczna i inne źródła energii",
    "lp": 9.0,
    "code": "09110000-3",
    "price_pln": "8000.00",
    "price_eur": "1725.22"
  },
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
