#!/usr/bin/env python
# coding: utf-8

# # Mapping figures
# 
# This notebook reproduces the mapping figures used in the manuscript.
# 
# It assumes all required files are located in one folder that is downloaded from the repository.
# Place this notebook in that same folder, then run the notebook from top to bottom.
# 
# Outputs are written to an `outputs/` subfolder.
# 
# Figures produced:
# 1. Coal grades only
# 2. All sites
# 3. Literature sites only
# 4. DataShed sites only
# 5. Back-validation sites only

# ## 1. Libraries
# Run this cell first. It imports all libraries used in this notebook.

# In[3]:


from pathlib import Path
import warnings

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

try:
    from svgpath2mpl import parse_path
    import xml.dom.minidom as minidom
    SVG_SUPPORT = True
except Exception:
    SVG_SUPPORT = False


# ## 2. Folder layout and required files
# 
# This notebook uses a single folder that contains all required inputs.
# 
# Expected files in the same folder as this notebook:
# 
# - `Coal_Fields_in_Pennsylvania_High-Volatile_Bituminous.geojson`
# - `Coal_Fields_in_Pennsylvania_Medium-Volatile_Bituminous.geojson`
# - `Coal_Fields_in_Pennsylvania_Low-Volatile_Bituminous.geojson`
# - `Coal_Fields_in_Pennsylvania_Semi-Anthracite.geojson`
# - `Coal_Fields_in_Pennsylvania_Anthracite.geojson`
# - `Pennsylvania_County_Boundaries.geojson`
# - `Mapping_Sites.xlsx` (must contain sheets: `Datashed`, `Backvalidation`)
# - `Research_Paper_Sites_TEST.csv`
# - Optional: `backval_marker.svg` (custom marker for back-validation sites)
# 
# If your repository uses different filenames, edit the paths in the next cell.

# In[4]:


# Single folder containing ALL inputs
BASE_DIR = Path.cwd()

# Output folder for figures
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Inputs (edit filenames here if needed)
COAL_FILES = {
    "High-Volatile Bituminous":  BASE_DIR / "Coal_Fields_in_Pennsylvania_High-Volatile_Bituminous.geojson",
    "Medium-Volatile Bituminous": BASE_DIR / "Coal_Fields_in_Pennsylvania_Medium-Volatile_Bituminous.geojson",
    "Low-Volatile Bituminous":   BASE_DIR / "Coal_Fields_in_Pennsylvania_Low-Volatile_Bituminous.geojson",
    "Semi-Anthracite":           BASE_DIR / "Coal_Fields_in_Pennsylvania_Semi-Anthracite.geojson",
    "Anthracite":                BASE_DIR / "Coal_Fields_in_Pennsylvania_Anthracite.geojson",
}

COUNTIES_FILE = BASE_DIR / "Pennsylvania_County_Boundaries.geojson"

# Single Excel file containing all three site tables
ALL_SITES_XLSX = BASE_DIR / "All_Sites_Test.xlsx"  # sheets: Datashed, Backvalidation, Literature

BACKVAL_SVG = BASE_DIR / "mining-svgrepo-com.svg"  # optional

def require_file(p: Path):
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p.resolve()}")

# Validate required files
for p in list(COAL_FILES.values()) + [COUNTIES_FILE, ALL_SITES_XLSX]:
    require_file(p)

print("BASE_DIR:", BASE_DIR.resolve())
print("Outputs:", OUTPUTS_DIR.resolve())


# ## 3. Load spatial layers and site tables

# In[ ]:


# Load coal polygons and tag with rank
coal_gdfs = []
for rank, path in COAL_FILES.items():
    gdf = gpd.read_file(path)
    gdf["Rank"] = rank
    coal_gdfs.append(gdf)

coal = gpd.GeoDataFrame(pd.concat(coal_gdfs, ignore_index=True))
# Load counties
counties = gpd.read_file(COUNTIES_FILE)

#Make sure everything is in a common CRS
TARGET_CRS = "EPSG:4326"
if coal.crs is None:
    coal = coal.set_crs(TARGET_CRS)
else:
    coal = coal.to_crs(TARGET_CRS)

if counties.crs is None:
    counties = counties.set_crs(TARGET_CRS)
else:
    counties = counties.to_crs(TARGET_CRS)

# Load all three site tables from a single Excel file
datashed_df = pd.read_excel(ALL_SITES_XLSX, sheet_name="Datashed").drop_duplicates(subset="Site")
datashed_gdf = gpd.GeoDataFrame(
    datashed_df,
    geometry=gpd.points_from_xy(datashed_df["Long"], datashed_df["Lat"]),
    crs="EPSG:4326"
).to_crs(TARGET_CRS)

backval_df = pd.read_excel(ALL_SITES_XLSX, sheet_name="Backvalidation").drop_duplicates(subset="Site")
backval_gdf = gpd.GeoDataFrame(
    backval_df,
    geometry=gpd.points_from_xy(backval_df["Long"], backval_df["Lat"]),
    crs="EPSG:4326"
).to_crs(TARGET_CRS)

paper_df = pd.read_excel(ALL_SITES_XLSX, sheet_name="Literature").dropna(subset=["Lat", "Long"])
paper_gdf = gpd.GeoDataFrame(
    paper_df,
    geometry=gpd.points_from_xy(paper_df["Long"], paper_df["Lat"]),
    crs="EPSG:4326"
).to_crs(TARGET_CRS)

n_paper = len(paper_gdf)
n_datashed = len(datashed_gdf)
n_backval = len(backval_gdf)

print("Counts:")
print("  Literature:", n_paper)
print("  DataShed:", n_datashed)
print("  Back-validation:", n_backval)


# ## 4. Styling
# 
# Site colors are fixed as:
# 
# - Literature sites: black
# - DataShed sites: green
# - Back-validation sites: orange
# 
# Coal polygons are filled by rank and drawn without bold outlines.
# County boundaries are drawn in black.

# In[ ]:


# Coal fill colors
RANK_COLORS = {
    "High-Volatile Bituminous":  "#c7dbf0",
    "Medium-Volatile Bituminous": "#8ab6e6",
    "Low-Volatile Bituminous":   "#4f85c5",
    "Semi-Anthracite":           "#d7c3ef",
    "Anthracite":                "#6d4fa8",
}

# Fixed site colors
SITE_COLORS = {
    "literature": "black",
    "datashed": "green",
    "back_validation": "orange",
}

# Marker settings
SIZE = 20
BACKVAL_SIZE = int(SIZE * 4)  # back-validation marker a bit larger
ALPHA = 0.95

# Polygon outline controls (coal grades should not have bold black outlines)
COAL_EDGE_COLOR = "none"
COAL_EDGE_WIDTH = 0.0

# Counties outline controls
COUNTY_EDGE_COLOR = "black"
COUNTY_EDGE_WIDTH = 1.0

# Back-validation marker:
# - Prefer an SVG marker if available and the SVG exists
# - Otherwise fall back to a simple built-in marker
USE_SVG_BACKVAL = True

def svg_to_marker(svg_path: Path):
    """Parse an SVG and return a Matplotlib Path suitable for use as a marker.

    Notes:
    - Many SVG icons are defined in a screen coordinate system where Y increases downward.
      Matplotlib uses Y increasing upward, so we flip the Y axis.
    - SVG paths can have arbitrary scale; we normalize the path to a ~unit box so marker sizing is stable.
    """
    doc = minidom.parse(str(svg_path))
    path_strings = [p.getAttribute("d") for p in doc.getElementsByTagName("path")]
    doc.unlink()

    if len(path_strings) == 0:
        raise ValueError("No <path> elements found in the SVG. Use an SVG with <path d='...'> elements.")

    mpl_paths = [parse_path(d) for d in path_strings]
    from matplotlib.path import Path as MplPath

    if len(mpl_paths) == 1:
        path = mpl_paths[0]
    else:
        path = MplPath.make_compound_path(*mpl_paths)

    # Center the path
    verts = path.vertices.copy()
    verts -= verts.mean(axis=0)

    # Flip Y (SVG screen coords -> Matplotlib coords)
    verts[:, 1] *= -1

    # Normalize scale so the marker isn't tiny/huge
    x_span = verts[:, 0].max() - verts[:, 0].min()
    y_span = verts[:, 1].max() - verts[:, 1].min()
    span = max(x_span, y_span)
    if span == 0:
        raise ValueError("SVG path span is zero; cannot normalize marker.")
    verts /= span

    path.vertices = verts
    return path

BACKVAL_MARKER = ">"  # fallback if SVG not used
BACKVAL_SVG_MARKER = None

if USE_SVG_BACKVAL and SVG_SUPPORT and BACKVAL_SVG.exists():
    try:
        BACKVAL_SVG_MARKER = svg_to_marker(BACKVAL_SVG)
        print("Using SVG marker for back-validation sites:", BACKVAL_SVG.name)
    except Exception as e:
        warnings.warn(f"Could not use SVG marker ({e}); falling back to built-in marker.")
else:
    if USE_SVG_BACKVAL and not BACKVAL_SVG.exists():
        print("SVG marker not found (optional):", BACKVAL_SVG.name, " -> using built-in marker instead.")


# ## 5. Plotting helpers
# 
# Legend layout is forced into three columns:
# 
# - Column 1: Bituminous grades (high, medium, low)
# - Column 2: Anthracite grades (semi-anthracite, anthracite)
# - Column 3: Site categories (back-validation, literature, datashed)
# 
# A blank spacer is included so the site categories stay in their own column.

# In[ ]:


def build_legend_groups(n_backval: int, n_lit: int, n_ds: int):
    """Return three legend handle lists: bituminous, anthracite, data."""
    # Coal patches
    hv = Patch(facecolor=RANK_COLORS["High-Volatile Bituminous"], edgecolor="black", label="High-Volatile Bituminous")
    mv = Patch(facecolor=RANK_COLORS["Medium-Volatile Bituminous"], edgecolor="black", label="Medium-Volatile Bituminous")
    lv = Patch(facecolor=RANK_COLORS["Low-Volatile Bituminous"], edgecolor="black", label="Low-Volatile Bituminous")
    sa = Patch(facecolor=RANK_COLORS["Semi-Anthracite"], edgecolor="black", label="Semi-Anthracite")
    an = Patch(facecolor=RANK_COLORS["Anthracite"], edgecolor="black", label="Anthracite")

    # Site handles
    back_marker = BACKVAL_SVG_MARKER if BACKVAL_SVG_MARKER is not None else BACKVAL_MARKER

    h_lit = Line2D([0], [0], marker="o", linestyle="",
                   markerfacecolor=SITE_COLORS["literature"], markeredgecolor=SITE_COLORS["literature"],
                   markersize=10, label=f"Literature Sites, n={n_lit}")
    h_ds = Line2D([0], [0], marker="o", linestyle="",
                  markerfacecolor=SITE_COLORS["datashed"], markeredgecolor=SITE_COLORS["datashed"],
                  markersize=10, label=f"DataShed Sites, n={n_ds}")
    h_bv = Line2D([0], [0], marker=back_marker, linestyle="",
                  markerfacecolor=SITE_COLORS["back_validation"], markeredgecolor=SITE_COLORS["back_validation"],
                  markersize=10, label=f"Back-validation Sites, n={n_backval}")

    bituminous = [lv, mv, hv]          # low, medium, high
    anthracite = [an, sa]              # anthracite, semi-anthracite
    data = [h_lit, h_ds, h_bv]         # literature, datashed, back-validation
    return bituminous, anthracite, data


def add_three_column_legend(fig, ax, n_backval: int, n_lit: int, n_ds: int):
    """Add three separate legends aligned as columns below the plot."""
    bituminous, anthracite, data = build_legend_groups(n_backval, n_lit, n_ds)

    # Common styling
    legend_kwargs = dict(frameon=False, handletextpad=0.8, borderaxespad=0.0, fontsize=14)

    # Place three legends under the axis.
    # Use figure coordinates so spacing is stable across exports.
    leg1 = fig.legend(handles=bituminous, ncol=1, loc="lower left",
                      bbox_to_anchor=(0.10, 0.02), **legend_kwargs)
    leg2 = fig.legend(handles=anthracite, ncol=1, loc="lower left",
                      bbox_to_anchor=(0.44, 0.02), **legend_kwargs)
    leg3 = fig.legend(handles=data, ncol=1, loc="lower left",
                      bbox_to_anchor=(0.72, 0.02), **legend_kwargs)

    # Ensure legends stay on top
    for leg in (leg1, leg2, leg3):
        leg.set_zorder(10)


# ## 6. Generate figures
# Run this cell to write all figures to the outputs folder.

# In[ ]:


# Plotting helpers (self-contained)
# This cell defines all functions used to build and export the figures.

def plot_base(ax):
    # Counties boundary
    counties.boundary.plot(ax=ax, linewidth=COUNTY_EDGE_WIDTH, color=COUNTY_EDGE_COLOR)

    # Coal polygons by rank (fills, no bold outlines)
    for rank, color in RANK_COLORS.items():
        subset = coal[coal["Rank"] == rank]
        if not subset.empty:
            subset.plot(
                ax=ax,
                color=color,
                edgecolor=COAL_EDGE_COLOR,
                linewidth=COAL_EDGE_WIDTH,
                alpha=0.8
            )


def plot_sites(ax, mode: str):
    """mode in {'all','literature','datashed','back_validation'}"""
    if mode in ("all", "literature"):
        paper_gdf.plot(ax=ax, color=SITE_COLORS["literature"], markersize=SIZE, alpha=ALPHA, marker="o")

    if mode in ("all", "datashed"):
        datashed_gdf.plot(ax=ax, color=SITE_COLORS["datashed"], markersize=SIZE, alpha=ALPHA, marker="o")

    if mode in ("all", "back_validation"):
        marker = BACKVAL_SVG_MARKER if BACKVAL_SVG_MARKER is not None else BACKVAL_MARKER
        # Use ax.scatter() so the custom path marker renders as a crisp vector shape.
        xs = backval_gdf.geometry.x.values
        ys = backval_gdf.geometry.y.values
        ax.scatter(xs, ys, marker=marker, s=BACKVAL_SIZE * 4,
           color=SITE_COLORS["back_validation"], alpha=ALPHA, zorder=5,
           edgecolors="black", linewidths=0.5)


def add_legend(ax, n_backval, n_lit, n_ds):
    """Three ax.legend() calls placed inside the axes as separate columns.

    Legends are anchored in axes-fraction coordinates so they always stay
    within the map extent regardless of bbox_inches="tight".
    """
    # Column 1 — Bituminous grades
    col1 = [
        Patch(facecolor=RANK_COLORS["Low-Volatile Bituminous"],    edgecolor="black", label="Low-Volatile Bituminous"),
        Patch(facecolor=RANK_COLORS["Medium-Volatile Bituminous"],  edgecolor="black", label="Medium-Volatile Bituminous"),
        Patch(facecolor=RANK_COLORS["High-Volatile Bituminous"],    edgecolor="black", label="High-Volatile Bituminous"),
    ]

    # Column 2 — Anthracite grades
    col2 = [
        Patch(facecolor=RANK_COLORS["Anthracite"],      edgecolor="black", label="Anthracite"),
        Patch(facecolor=RANK_COLORS["Semi-Anthracite"], edgecolor="black", label="Semi-Anthracite"),
    ]

    # Column 3 — Site categories
    back_marker = BACKVAL_SVG_MARKER if BACKVAL_SVG_MARKER is not None else BACKVAL_MARKER
    col3 = [
        Line2D([0],[0], marker="o", linestyle="",
               markerfacecolor=SITE_COLORS["literature"], markeredgecolor=SITE_COLORS["literature"],
               markersize=9, label=f"Literature Sites, n={n_lit}"),
        Line2D([0],[0], marker="o", linestyle="",
               markerfacecolor=SITE_COLORS["datashed"], markeredgecolor=SITE_COLORS["datashed"],
               markersize=9, label=f"DataShed Sites, n={n_ds}"),
        Line2D([0],[0], marker=back_marker, linestyle="", markerfacecolor=SITE_COLORS["back_validation"],
               markeredgecolor="black", markeredgewidth=0.5,
               markersize=9, label=f"Back-validation Sites, n={n_backval}"),
    ]

    common = dict(
        frameon=False,
        facecolor="white",
        edgecolor="none",
        fontsize=10,
        handletextpad=0.5,
        labelspacing=0.5,
        handlelength=1.8,
        borderpad=0.4,
        borderaxespad=0.0,
        labelcolor="black",
        loc="lower left",
    )

    # x positions spread columns across the bottom of the map.
    # y=-0.04 places them just inside the lower edge of the axes.
    leg1 = ax.legend(handles=col1, bbox_to_anchor=(0.10, -0.10), **common)
    ax.add_artist(leg1)

    leg2 = ax.legend(handles=col2, bbox_to_anchor=(0.40, -0.10), **common)
    ax.add_artist(leg2)

    leg3 = ax.legend(handles=col3, bbox_to_anchor=(0.62, -0.10), **common)


def make_figure(mode, filename, add_legend_flag=True):
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    plot_base(ax)

    if mode != "coal_only":
        plot_sites(ax, mode)

    ax.set_axis_off()

    if add_legend_flag:
        add_legend(ax, n_backval, n_paper, n_datashed)

    out = OUTPUTS_DIR / filename
    fig.savefig(out, dpi=300, bbox_inches="tight", transparent=True)
    plt.close(fig)
    return out


# In[ ]:


written = []
written.append(make_figure("coal_only", "01_coal_grades_only.png", add_legend_flag=True))
written.append(make_figure("all", "02_all_sites.png", add_legend_flag=True))
written.append(make_figure("literature", "03_literature_only.png", add_legend_flag=True))
written.append(make_figure("datashed", "04_datashed_only.png", add_legend_flag=True))
written.append(make_figure("back_validation", "05_back_validation_only.png", add_legend_flag=True))

print("Wrote:")
for p in written:
    print(" -", p.resolve())


# In[ ]:





# In[ ]:




