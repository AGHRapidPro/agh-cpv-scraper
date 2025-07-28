# 🛒 Procurement Tracker

This 🐍 Python script automates the tracking and processing of `.xls` files from the [AGH DZP website](https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych), handling version detection and converting Excel data into structured JSON 📊.

---

## ✨ Features

* 🔍 **Automated tracking**: Monitors the source URL for new procurement files
* 🆕 **Version detection**: Identifies newer file versions based on naming patterns
* 🧹 **Data processing**: Converts Excel files to structured JSON with categorization
* 🧠 **State management**: Maintains processing history between runs
* 🧽 **Data cleaning**: Handles inconsistent Excel formats and missing values

---

## 🐳 Usage – Docker

### ▶️ Running:

```bash
docker run --rm -itd \
-v ./agh-cpv-scraper:/app/cpv \
--name agh-cpv-scraper \
aghrapidpro/agh-cpv-scraper:latest
```

### 🛠️ Building:

```bash
docker buildx build \
--build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
-t aghrapidpro/agh-cpv-scraper:1.0 \
-t aghrapidpro/agh-cpv-scraper:latest \
--push .
```

---

## 💻 Usage – Local

```bash
python3 -m venv .
source bin/activate
pip install -r requirements.txt
./procurement_tracker.py
```

### ⚙️ Options

| 🏷️ Option       | 📝 Description                       | 🧩 Default                                                                                              |
| ---------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `-u`, `--url`    | Source URL to monitor                | [AGH University Procurement Plans](https://dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych) |
| `-o`, `--output` | Output directory for processed files | `./cpv`                                                                                                 |

---

## 🔁 Workflow

1. 🧭 **Scrape** the source URL for procurement files
2. 🧩 **Detect** file versions based on naming patterns
3. 📥 **Download** only newer versions of files
4. 🔄 **Process** Excel files:

   * 🧽 Clean and standardize data
   * 🗂️ Categorize products
   * 💾 Convert to JSON format
5. 🧠 **Maintain state** between runs in `.procurement_tracker.json`

---

## 📁 Output Structure

Processed files are saved in the output directory with the following naming convention:

```
./cpv/
├── .procurement_tracker.json   # Processing state file
├── 2025-01.json
├── 2025-02.json
├── 2025-03.json
├── 2025-04.json
├── 2025-05.json    # Historical data (YYYY-MM)
├── 2025-06.json
└── latest.json -> 2025-06.json # Current month's data
```

---

### 🧾 JSON Format Example

```json
[
  {
    "name": "Laptops",
    "category": "Computers & Accessories",
    "lp": 1.0,
    "code": "30213100-6",
    "price_pln": "3500.00",
    "price_eur": "754.23"
  },
  {
    "name": "Monitors",
    "category": "Computers & Accessories",
    "lp": 2.0,
    "code": "32324100-3",
    "price_pln": "1100.00",
    "price_eur": "236.98"
  },
  {
    "name": "2D printers",
    "category": "Printers & Scanners",
    "lp": 3.0,
    "code": "30124500-0",
    "price_pln": "899.99",
    "price_eur": "193.85"
  },
  {
    "name": "Routers",
    "category": "Networking Equipment",
    "lp": 4.0,
    "code": "32412110-0",
    "price_pln": "499.00",
    "price_eur": "107.45"
  },
  {
    "name": "Switches",
    "category": "Networking Equipment",
    "lp": 5.0,
    "code": "48000000-8",
    "price_pln": "445.99",
    "price_eur": "107.63"
  }
]

```

---

## 🧠 State Management

The script maintains a state file (`.procurement_tracker.json`) that tracks:

* 📄 Processed file versions
* 🕒 Last processing timestamp
* 📂 Output JSON file paths
* ❓ Availability status of historical files

---

## 🤝 Contribution

Contributions are welcome!
Please open an issue or submit a pull request for:

* 🐞 Bug fixes
* 🌟 Feature enhancements
* 📝 Documentation improvements

---

## 📝 Notes

* 🎯 Designed specifically for AGH University's DZP website structure
* 🗓️ Handles Polish month names and date formats
* 📊 Processes files with inconsistent Excel formats
* 🧹 Automatically cleans temporary files after processing

