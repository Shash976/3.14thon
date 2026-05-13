"""
Triboelectric characterization plots v4.

Produces:
  1. Jsc sweep (PDA/MIC only) — all frequencies side by side
  2. Voc sweep (PDA/MIC only) — all frequencies side by side
  3-6. Per-frequency comparison (Bare left | MIC right, same time axis)

All current density values displayed in scientific notation (e.g. 4.70E-03 mA/m²).
I_p-p = |highest peak| + |lowest trough|.

USAGE:
  1. Put all CSV files in DATA_DIR (default: ./data)
  2. Run: python plot_tribo_v4.py
"""

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_FOLDER = r"C:\\Users\\shash\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot"  # where to find CSV files
OUTPUT_FOLDER = r"C:\\Users\\shash\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot\\converted"  # where to save plots
DATA_DIR = Path(OUTPUT_FOLDER)  # folder containing CSVs
os.chdir(INPUT_FOLDER)  # change working directory to data folder for easier file handling
CURRENT_SCALE = 2500  # raw current (A) × 2500 → mA/m²
CROP_DURATION_CURRENT = 5.0
CROP_DURATION_VOLTAGE = 2.0

FREQUENCIES = [1, 2.5, 5, 10]
FREQ_LABELS = ["1 Hz", "2.5 Hz", "5 Hz", "10 Hz"]

BAND_COLORS = ["#4A90D9", "#5CB85C", "#F0AD4E", "#E8667A"]
BAND_ALPHA = 0.15

BARE_COLOR = "#333333"
MIC_COLOR = "#D94452"

BAND_GAP = 0


# ============================================================
# HELPERS
# ============================================================
def find_files():
    files = {"Isc_Bare": {}, "Isc_PDA": {}, "Voc_Bare": {}, "Voc_PDA": {}}
    for f in sorted(DATA_DIR.glob("*.csv")):
        name = f.stem
        if name.startswith("Isc_Bare"):     key = "Isc_Bare"
        elif name.startswith("Isc_PDA"):    key = "Isc_PDA"
        elif name.startswith("Voc_Bare"):   key = "Voc_Bare"
        elif name.startswith("Voc_PDA"):    key = "Voc_PDA"
        else: continue
        for freq in FREQUENCIES:
            pattern = f"_{freq}Hz_"
            if pattern in name or pattern in name.replace(" ", ""):
                if freq not in files[key]:
                    files[key][freq] = f
                break
    return files


def load_and_crop(filepath, crop_duration=5.0):
    try:
        df = pd.read_csv(filepath, header=None, skiprows=1)
    except Exception:
        df = pd.read_csv(filepath, header=None, sep='\t', skiprows=1)
    if df.shape[1] == 1:
        df = pd.read_csv(filepath, header=None, skiprows=1, sep=',')
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    if df.shape[1] < 2:
        raise ValueError(f"Need 2 numeric columns in {filepath}")
    time = df.iloc[:, 0].values
    signal = df.iloc[:, 1].values
    total = time[-1] - time[0]
    if total <= crop_duration:
        return time - time[0], signal
    start = time[0] + 0.2 * total
    end = start + crop_duration
    if end > time[-1]:
        end = time[-1]; start = end - crop_duration
    mask = (time >= start) & (time <= end)
    return time[mask] - time[mask][0], signal[mask]


def calc_ipp(signal):
    return abs(np.max(signal)) + abs(np.min(signal))


def auto_ylim(*signals, padding_frac=0.15):
    all_v = np.concatenate([s for s in signals if s is not None and len(s) > 0])
    if len(all_v) == 0: return -1, 1
    lo, hi = np.min(all_v), np.max(all_v)
    span = hi - lo
    if span == 0: return -1, 1
    pad = padding_frac * span
    if lo < 0 and hi > 0:
        ext = max(abs(hi), abs(lo))
        return -(ext + pad), ext + pad
    return lo - pad, hi + pad


def fmt_ipp(val, is_current):
    """Format I_p-p value: scientific notation for current, 2 decimals for voltage."""
    if is_current:
        return f"I$_{{p-p}}$ = {val:.2E} mA/m²"
    else:
        return f"V$_{{p-p}}$ = {val:.2f} V"


def set_sci_yaxis(ax, is_current):
    """Use scientific notation on y-axis tick labels for current plots."""
    if is_current:
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(axis='y', style='scientific', scilimits=(-3, 3))
        ax.yaxis.get_offset_text().set_fontsize(10)


# ============================================================
# PLOT 1 & 2: MAIN SWEEP (PDA / MIC ONLY)
# ============================================================
def plot_main_sweep(pda_files, ylabel, scale, output, title_text, is_current):
    crop = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    fig, ax = plt.subplots(figsize=(14, 5), dpi=150)
    offset = 0
    bands = []
    all_sigs = []

    for i, freq in enumerate(FREQUENCIES):
        if freq not in pda_files:
            offset += crop + BAND_GAP; continue
        t, s = load_and_crop(pda_files[freq], crop)
        s = s * scale
        ax.plot(t + offset, s, color=MIC_COLOR, linewidth=0.8, zorder=3)
        all_sigs.append(s)
        pp = calc_ipp(s)
        bands.append((offset, offset + crop, i, pp))
        offset += crop + BAND_GAP

    ylo, yhi = auto_ylim(*all_sigs, padding_frac=0.20)
    ax.set_ylim(ylo, yhi)
    yr = yhi - ylo

    for bs, be, idx, pp in bands:
        ax.axvspan(bs, be, color=BAND_COLORS[idx], alpha=BAND_ALPHA, zorder=0)
        ax.text((bs + be) / 2, yhi - 0.05 * yr, FREQ_LABELS[idx],
                ha='center', va='top', fontsize=13, fontweight='bold',
                color=BAND_COLORS[idx], zorder=5)
        lbl = fmt_ipp(pp, is_current)
        ax.annotate(lbl, xy=((bs + be) / 2, ylo + 0.06 * yr),
                    fontsize=9, color=MIC_COLOR, ha='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                              edgecolor=MIC_COLOR, alpha=0.85))

    ax.set_xlabel("Time (s)", fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.tick_params(axis='both', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(-0.3, offset - BAND_GAP + 0.3)
    set_sci_yaxis(ax, is_current)

    plt.title(title_text, fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(output.replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
    print(f"  Saved: {output}")
    plt.close()


# ============================================================
# PLOT 3-6: PER-FREQUENCY SIDE-BY-SIDE (BARE LEFT | MIC RIGHT)
# ============================================================
def plot_comparison(bare_files, pda_files, ylabel, scale, output_prefix, is_current):
    """
    One figure per frequency.
    Bare signal on left half, MIC on right half — continuous time axis.
    Matches the 'Without ITO | With ITO' reference style.
    """
    crop = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    available = [f for f in FREQUENCIES if f in bare_files or f in pda_files]

    for freq in available:
        fidx = FREQUENCIES.index(freq)
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        sigs = []

        # BARE — left half: t = 0 to crop
        if freq in bare_files:
            t_b, s_b = load_and_crop(bare_files[freq], crop)
            s_b = s_b * scale
            ax.plot(t_b, s_b, color=BARE_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_b)
            pp_b = calc_ipp(s_b)
        else:
            pp_b = None

        # MIC — right half: t = crop to 2*crop
        if freq in pda_files:
            t_p, s_p = load_and_crop(pda_files[freq], crop)
            s_p = s_p * scale
            ax.plot(t_p + crop, s_p, color=MIC_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_p)
            pp_p = calc_ipp(s_p)
        else:
            pp_p = None

        # Auto y-limits from both signals
        if sigs:
            ylo, yhi = auto_ylim(*sigs, padding_frac=0.18)
            ax.set_ylim(ylo, yhi)
        ylo, yhi = ax.get_ylim()
        yr = yhi - ylo

        # Background shading — light gray left, light red right
        ax.axvspan(0, crop, color='#CCCCCC', alpha=0.12, zorder=0)
        ax.axvspan(crop, crop * 2, color=MIC_COLOR, alpha=0.06, zorder=0)

        # Divider line at the boundary
        ax.axvline(crop, color='#999999', linewidth=1, linestyle='--', zorder=1)

        # "Without MIC" / "With MIC" labels at top of each half
        ax.text(crop * 0.5, yhi - 0.05 * yr, "Without MIC",
                ha='center', va='top', fontsize=14, fontweight='bold',
                color=BARE_COLOR, zorder=5)
        ax.text(crop * 1.5, yhi - 0.05 * yr, "With MIC",
                ha='center', va='top', fontsize=14, fontweight='bold',
                color=MIC_COLOR, zorder=5)

        # I_p-p annotations at bottom of each half
        if pp_b is not None:
            lbl = fmt_ipp(pp_b, is_current)
            ax.text(crop * 0.5, ylo + 0.05 * yr, lbl,
                    ha='center', va='bottom', fontsize=10, color=BARE_COLOR,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=BARE_COLOR, alpha=0.85))

        if pp_p is not None:
            lbl = fmt_ipp(pp_p, is_current)
            ax.text(crop * 1.5, ylo + 0.05 * yr, lbl,
                    ha='center', va='bottom', fontsize=10, color=MIC_COLOR,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=MIC_COLOR, alpha=0.85))

        # Frequency box — top right
        ax.text(0.97, 0.95, f"f = {freq} Hz", transform=ax.transAxes,
                fontsize=13, fontweight='bold', ha='right', va='top',
                color=BAND_COLORS[fidx],
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                          edgecolor=BAND_COLORS[fidx], linewidth=1.5, alpha=0.9))

        ax.set_xlabel("Time (s)", fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
        ax.tick_params(axis='both', labelsize=11)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xlim(0, crop * 2)
        set_sci_yaxis(ax, is_current)

        freq_str = str(freq).replace('.', '_')
        fname = f"{output_prefix}_{freq_str}Hz.png"
        plt.tight_layout()
        plt.savefig(fname, dpi=300, bbox_inches='tight', facecolor='white')
        plt.savefig(fname.replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
        print(f"  Saved: {fname}")
        plt.close()


# ============================================================
# MAIN
# ============================================================
def main():
    if not DATA_DIR.exists():
        print(f"\n{'='*60}")
        print(f"DATA DIRECTORY NOT FOUND: {DATA_DIR}")
        print(f"{'='*60}")
        print(f"\nCreate a folder called 'data/' next to this script.")
        print(f"Put your CSVs in it. Expected names like:")
        print(f"  Isc_Bare vs Parafilm blue_1Hz_001.csv")
        print(f"  Isc_PDA vs Parafilm blue_1Hz_001.csv")
        print(f"  Voc_Bare vs Parafilm blue_1Hz_001.csv")
        print(f"  Voc_PDA vs Parafilm blue_5Hz_correct_001.csv")
        return

    files = find_files()

    print("\nDiscovered files:")
    for key, fd in files.items():
        print(f"\n  {key}:")
        if not fd: print("    (none)")
        for freq, fp in sorted(fd.items()):
            print(f"    {freq} Hz -> {fp.name}")

    # 1. Main Isc sweep — PDA only
    if files["Isc_PDA"]:
        print("\n[1] Main Isc sweep (MIC)...")
        plot_main_sweep(
            files["Isc_PDA"], "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_sweep_MIC.png",
            "Short-Circuit Current — With MIC",
            is_current=True)

    # 2. Main Voc sweep — PDA only
    if files["Voc_PDA"]:
        print("\n[2] Main Voc sweep (MIC)...")
        plot_main_sweep(
            files["Voc_PDA"], "V$_{oc}$ (V)", 1.0,
            "Voc_sweep_MIC.png",
            "Open-Circuit Voltage — With MIC",
            is_current=False)

    # 3. Per-frequency Isc: Bare vs MIC overlaid
    if files["Isc_Bare"] or files["Isc_PDA"]:
        print("\n[3] Isc comparison (overlaid per frequency)...")
        plot_comparison(
            files["Isc_Bare"], files["Isc_PDA"],
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_compare", is_current=True)

    # 4. Per-frequency Voc: Bare vs MIC overlaid
    if files["Voc_Bare"] or files["Voc_PDA"]:
        print("\n[4] Voc comparison (overlaid per frequency)...")
        plot_comparison(
            files["Voc_Bare"], files["Voc_PDA"],
            "V$_{oc}$ (V)", 1.0,
            "Voc_compare", is_current=False)

    print("\n" + "=" * 60)
    print("Output files:")
    print("  Isc_sweep_MIC.png/.svg          Main current sweep (no gaps)")
    print("  Voc_sweep_MIC.png/.svg          Main voltage sweep (no gaps)")
    print("  Isc_compare_*Hz.png/.svg        Bare vs MIC overlaid (5s)")
    print("  Voc_compare_*Hz.png/.svg        Bare vs MIC overlaid (2s)")
    print("=" * 60)


if __name__ == "__main__":
    main()