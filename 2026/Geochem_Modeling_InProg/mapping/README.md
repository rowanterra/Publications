# Mapping

This folder contains the code and data required to reproduce the mapping figures from the manuscript. All figures show coal field distributions and sampling site locations across Pennsylvania.

---

## Figures produced

| # | Filename | Description |
|---|----------|-------------|
| 1 | `01_coal_grades_only.png` | Pennsylvania coal fields colored by rank |
| 2 | `02_all_sites.png` | All site categories overlaid on coal fields |
| 3 | `03_literature_only.png` | Literature sites only |
| 4 | `04_datashed_only.png` | DataShed sites only |
| 5 | `05_back_validation_only.png` | Back-validation sites only |

Output figures are written to an `outputs/` subfolder that is created automatically on first run.

---

## Folder structure

```
mapping/
├── mapping.py                                                   # main script
├── mapping_notebook.ipynb                                       # original notebook (reference)
├── All_Sites.xlsx                                               # site coordinates (sheets: Literature, Datashed, Backvalidation)
├── Pennsylvania_County_Boundaries.geojson                       # county boundaries
├── Coal_Fields_in_Pennsylvania_High-Volatile_Bituminous.geojson
├── Coal_Fields_in_Pennsylvania_Medium-Volatile_Bituminous.geojson
├── Coal_Fields_in_Pennsylvania_Low-Volatile_Bituminous.geojson
├── Coal_Fields_in_Pennsylvania_Semi-Anthracite.geojson
├── Coal_Fields_in_Pennsylvania_Anthracite.geojson
├── mining-svgrepo-com.svg                                       # optional custom marker
└── outputs/                                                     # generated figures (created on run)
```

---

## Requirements

Python 3.8+ is recommended. Install dependencies with:

```bash
pip install pandas geopandas matplotlib openpyxl
```

For the optional SVG back-validation marker, also install:

```bash
pip install svgpath2mpl
```

If `svgpath2mpl` is not installed or the `.svg` file is not present, the script falls back to a built-in arrow marker automatically — no action needed.

---

## How to run

Place this folder on your machine with all required files present (see folder structure above), then run:

```bash
python mapping.py
```

The script will print the resolved paths and site counts to the terminal, then write the five figures to `outputs/`. It can be run from any working directory as long as the script and data files are in the same folder.

---

## Site categories

| Category | Color | Source |
|----------|-------|--------|
| Literature sites | Black | `Literature` sheet in `All_Sites.xlsx` |
| DataShed sites | Green | `Datashed` sheet in `All_Sites.xlsx` |
| Back-validation sites | Orange | `Backvalidation` sheet in `All_Sites.xlsx` |

Each site table must contain at minimum a `Site`, `Lat`, and `Long` column.

---

## Coal rank colors

| Rank | Color |
|------|-------|
| High-Volatile Bituminous | `#c7dbf0` |
| Medium-Volatile Bituminous | `#8ab6e6` |
| Low-Volatile Bituminous | `#4f85c5` |
| Semi-Anthracite | `#d7c3ef` |
| Anthracite | `#6d4fa8` |
