# Inbound Capacity Report — Automation Pipeline

A weekly Python automation that reads Air, OTR, and Ocean inbound tracking files, aggregates shipment data by site and week, fills the Capacity Report Excel template, and distributes the result via email every Monday.

> **Visual overview:** [project-overview.html](project-overview.html)

---

## Overview

Each Monday, three tracking files are prepared by the inbound team. This pipeline:

1. **Discovers** today's tracking files by matching the date in their filenames
2. **Aggregates** each source by site and ISO week using pandas
3. **Fills** the Capacity Report template with the aggregated values
4. **Distributes** the completed report as an email attachment
5. **Alerts** stakeholders if any tracking files are missing — listing all missing files in a single email

---

## Project Structure

```
Capacity_report/
├── main.py                        # Entry point
├── main_example.py                # Reference version of main.py (sanitized)
├── email_pipeline_example.py      # Reference implementation of email pipeline
├── project-overview.html          # Visual project overview (portfolio)
├── processors/
│   ├── air_processor.py           # AIR data aggregation (past 4wk avg)
│   ├── otr_processor.py           # OTR data aggregation (BL# dedup, past 4wk avg)
│   ├── vessel_processor.py        # Ocean data aggregation (forward 4wk)
│   ├── report_builder.py          # Writes aggregated data into Excel template
│   └── chart_builder.py           # Dashboard charts (portfolio reference)
├── email_pipeline/
│   ├── email_setup.py             # All settings (paths, SMTP, recipients)
│   └── sender.py                  # SMTP email sender
└── utils/
    ├── date_utils.py              # Date formatting utilities
    └── email_utils.py
```

---

## Data Sources

| Mode  | Source File               | Direction | Metric                      |
|-------|---------------------------|-----------|-----------------------------|
| AIR   | Air Inbound Tracking.xlsm | Past 4wk  | C/W sum · HAWB# count       |
| OTR   | OTR Inbound Tracking.xlsm | Past 4wk  | BL# count (deduped)         |
| Ocean | Vessel Inbound Tracking.xlsm | Future 4wk | Cntr.# count · HBL# count |

> If a file is not found, all missing files are reported together in a single failure alert before the process exits.

---

## Output

```
Desktop/
└── [Project Folder]/
    ├── AIR inbound/final/         *MM-DD-YY*Air Inbound Tracking*.xlsm
    ├── OTR inbound/final/         *MM-DD-YY*OTR Inbound Tracking*.xlsm
    ├── Ocean inbound/final/       *MM-DD-YY*Vessel Inbound Tracking*.xlsm
    └── Capacity/
        ├── Inbound Capacity Report.xlsx        (template)
        └── Inbound Capacity Report WK##.xlsx   (output)
```

---

## How It Works

### 1. File Discovery
Tracking files are located by glob pattern matching today's date (`MM-DD-YY`) in the filename. All three files are checked before any processing begins.

### 2. Aggregation
Each processor reads the `RawData` sheet and aggregates independently:
- **AIR** — C/W sum and HAWB# count per POD, current week + rolling avg2/3/4
- **OTR** — BL# count per State after deduplication, current week + rolling avg1/2/3/4
- **Ocean** — Cntr.# and HBL# count per Final Destination, current + next 3 weeks

### 3. Report Writing
The template is copied via `shutil.copy2`, preserving all formatting. Week headers and data cells are filled using a fixed `ROW_MAP` and column index mapping.

### 4. Distribution
The completed report is attached to a weekly email and sent to the configured recipients.

---

## Configuration

All settings are managed in `email_pipeline/email_setup.py`:

| Setting | Description |
|---------|-------------|
| `AIR_DIR` / `OTR_DIR` / `OCEAN_DIR` | Paths to tracking file folders |
| `CAPACITY_DIR` | Path to template and output folder |
| `SMTP_SERVER` / `SMTP_PORT` | SMTP server settings |
| `EMAIL_TO` / `EMAIL_CC` | Report email recipients |
| `EMAIL_TO_FAILURE` | Failure alert recipients |

Credentials (SMTP username and password) are stored in a `.env` file and loaded at runtime.

---

## Requirements

```
pandas
openpyxl
python-dotenv
```

---

## Running

```bash
python main.py
```

Intended to be triggered every Monday at 9AM via Windows Task Scheduler.
