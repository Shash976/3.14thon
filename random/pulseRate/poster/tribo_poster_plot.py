"""
Triboelectric characterization plots v5.

Changes from v4:
  - Reads .data files (LabView format) instead of CSV
  - Voc crops from the END of the recording (steady state)
  - Main sweep shows BOTH bare and MIC
  - Only uses 1, 2.5, 5 Hz (10 Hz dropped)
  - I_p-p = |highest peak| + |lowest trough|
  - Scientific notation for current, decimal for voltage

USAGE:
  1. Put all .data files in DATA_DIR (default: ./data)
  2. Run: python plot_tribo_v5.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
import re
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================
DATA_DIR = Path(r"C:\\Users\\shash\\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot") # TODO: Change with data filepath
OUTPUT_DIR = Path("plots")

CURRENT_SCALE = 2500
CROP_DURATION_CURRENT = 2.0
CROP_DURATION_VOLTAGE = 2.0

FREQUENCIES = [1, 2.5, 5]  # dropped 10 Hz
FREQ_LABELS = ["1 Hz", "2.5 Hz", "5 Hz"]

BAND_COLORS = ["#4A90D9", "#5CB85C", "#F0AD4E"]
BAND_ALPHA = 0.15

BARE_COLOR = "#333333"
MIC_COLOR = "#D94452"

BAND_GAP = 0


# ============================================================
# .DATA FILE PARSER
# ============================================================
def parse_data_file(filepath):
    """
    Parse LabView .data files.
    Skips header lines until ***End_of_Header***, then reads
    tab-separated columns. Takes columns 1 (Time) and 2 (Current/Voltage).
    """
    lines = []
    header_passed = False

    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            if '***End_of_Header***' in line:
                header_passed = True
                # Skip the column header line that follows
                next(f, None)
                continue
            if header_passed:
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)

    if not lines:
        raise ValueError(f"No data found after header in {filepath}")

    time_vals = []
    signal_vals = []

    for line in lines:
        parts = line.split('\t')
        # Filter out empty strings
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            try:
                t = float(parts[0])
                s = float(parts[1])
                time_vals.append(t)
                signal_vals.append(s)
            except ValueError:
                continue

    if not time_vals:
        raise ValueError(f"Could not parse numeric data from {filepath}")

    return np.array(time_vals), np.array(signal_vals)


# ============================================================
# HELPERS
# ============================================================
def find_files():
    files = {"Isc_Bare": {}, "Isc_PDA": {}, "Voc_Bare": {}, "Voc_PDA": {}}
    for f in sorted(DATA_DIR.glob("*.data")):
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


def load_and_crop(filepath, crop_duration, from_end=False, trim_tail=0):
    """
    Load .data file, crop a segment.
    from_end=True: take last crop_duration seconds (for Voc steady state)
    from_end=False: take from 20% in (skip transients)
    trim_tail: seconds to shave off the end of the crop (removes machine-stop artifacts)
    """
    time, signal = parse_data_file(filepath)

    total = time[-1] - time[0]
    if total <= crop_duration:
        return time - time[0], signal

    if from_end:
        # Crop from the very end for steady-state
        end = time[-1]
        start = end - crop_duration
    else:
        # Crop from 20% in to skip initial transients
        start = time[0] + 0.2 * total
        end = start + crop_duration
        if end > time[-1]:
            end = time[-1]
            start = end - crop_duration

    # Trim tail to remove machine-stop artifacts
    end = end - trim_tail

    mask = (time >= start) & (time <= end)
    t_crop = time[mask]
    return t_crop - t_crop[0], signal[mask]


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
    if is_current:
        return f"I$_{{p-p}}$ = {val:.2E} mA/m²"
    else:
        return f"V$_{{p-p}}$ = {val:.2f} V"


def set_sci_yaxis(ax, is_current):
    if is_current:
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(axis='y', style='scientific', scilimits=(-3, 3))
        ax.yaxis.get_offset_text().set_fontsize(10)


# ============================================================
# PLOT 1 & 2: MAIN SWEEP (BOTH BARE AND MIC)
# ============================================================
def plot_main_sweep(bare_files, pda_files, ylabel, scale, output, title_text, is_current, forced_ylim=None):
    """All frequencies side by side, BOTH bare and MIC plotted."""
    crop = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    from_end = not is_current  # Voc: crop from end

    fig, ax = plt.subplots(figsize=(6, 5), dpi=200)
    offset = 0
    bands = []
    all_sigs = []

    for i, freq in enumerate(FREQUENCIES):
        has_bare = freq in bare_files
        has_mic = freq in pda_files

        if not has_bare and not has_mic:
            offset += crop + BAND_GAP
            continue

        # Plot bare — always crop from middle; trim tail for Voc to remove machine-stop dip
        if has_bare:
            tail = 0.3 if not is_current else 0  # trim 0.3s for voltage bare files
            t_b, s_b = load_and_crop(bare_files[freq], crop, from_end=False, trim_tail=tail)
            s_b = s_b * scale
            ax.plot(t_b + offset, s_b, color=BARE_COLOR, linewidth=0.8, zorder=3)
            all_sigs.append(s_b)
            pp_b = calc_ipp(s_b)
        else:
            pp_b = None

        # Plot MIC — crop from end for Voc (steady state), middle for Isc
        if has_mic:
            t_p, s_p = load_and_crop(pda_files[freq], crop, from_end)
            s_p = s_p * scale
            ax.plot(t_p + offset, s_p, color=MIC_COLOR, linewidth=0.8, zorder=3)
            all_sigs.append(s_p)
            pp_p = calc_ipp(s_p)
        else:
            pp_p = None

        bands.append((offset, offset + crop, i, pp_b, pp_p))
        offset += crop + BAND_GAP

    if forced_ylim is not None:
        ylo, yhi = forced_ylim
    else:
        ylo, yhi = auto_ylim(*all_sigs, padding_frac=0.22)
    ax.set_ylim(ylo, yhi)
    yr = yhi - ylo

    for bs, be, idx, pp_b, pp_p in bands:
        ax.axvspan(bs, be, color=BAND_COLORS[idx], alpha=BAND_ALPHA, zorder=0)
        ax.text((bs + be) / 2, yhi - 0.04 * yr, FREQ_LABELS[idx],
                ha='center', va='top', fontsize=13, fontweight='bold',
                color=BAND_COLORS[idx], zorder=5)

        # Annotations — bare above MIC
        annot_y = ylo + 0.12 * yr
        if pp_b is not None:
            lbl = fmt_ipp(pp_b, is_current)
            ax.annotate(lbl, xy=((bs + be) / 2, annot_y),
                        fontsize=8, color=BARE_COLOR, ha='center',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor=BARE_COLOR, alpha=0.85))
        if pp_p is not None:
            lbl = fmt_ipp(pp_p, is_current)
            ax.annotate(lbl, xy=((bs + be) / 2, ylo + 0.04 * yr),
                        fontsize=8, color=MIC_COLOR, ha='center',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                  edgecolor=MIC_COLOR, alpha=0.85))

    # Legend — only if both bare and MIC are present
    from matplotlib.patches import Patch
    has_any_bare = any(freq in bare_files for freq in FREQUENCIES)
    has_any_mic = any(freq in pda_files for freq in FREQUENCIES)
    if has_any_bare and has_any_mic:
        handles = [Patch(color=BARE_COLOR, label='Without MIC'),
                   Patch(color=MIC_COLOR, label='With MIC')]
        ax.legend(handles=handles, loc='upper left', fontsize=11,
                  framealpha=0.9, edgecolor='gray')

    ax.set_xlabel("Time (s)", fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.tick_params(axis='both', labelsize=11)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xlim(0 if BAND_GAP == 0 else -0.3, offset - BAND_GAP + (0 if BAND_GAP == 0 else 0.3))
    set_sci_yaxis(ax, is_current)

    plt.title(title_text, fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    out_path = OUTPUT_DIR / output
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig(str(out_path).replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
    print(f"  Saved: {out_path}")
    plt.close()


# ============================================================
# PLOT 3+: PER-FREQUENCY SIDE-BY-SIDE (BARE LEFT | MIC RIGHT)
# ============================================================
def plot_comparison(bare_files, pda_files, ylabel, scale, output_prefix, is_current):
    """
    One figure per frequency.
    Bare on left half, MIC on right half, continuous x-axis.
    """
    crop = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    from_end = not is_current
    available = [f for f in FREQUENCIES if f in bare_files or f in pda_files]

    for freq in available:
        fig, ax = plt.subplots(figsize=(6, 5), dpi=200)
        sigs = []

        # BARE — left half (always crop from middle, trim tail for Voc)
        bare_end = crop  # default if no bare data
        if freq in bare_files:
            tail = 0.5 if not is_current else 0
            t_b, s_b = load_and_crop(bare_files[freq], crop, from_end=False, trim_tail=tail)
            s_b = s_b * scale
            ax.plot(t_b, s_b, color=BARE_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_b)
            pp_b = calc_ipp(s_b)
            bare_end = t_b[-1]  # actual end of bare data
        else:
            pp_b = None

        # MIC — right half, starts right where bare ends (no gap)
        mic_offset = bare_end
        if freq in pda_files:
            t_p, s_p = load_and_crop(pda_files[freq], crop, from_end)
            s_p = s_p * scale
            ax.plot(t_p + mic_offset, s_p, color=MIC_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_p)
            pp_p = calc_ipp(s_p)
            mic_end = mic_offset + t_p[-1]
        else:
            pp_p = None
            mic_end = mic_offset + crop

        total_width = mic_end

        # Auto y-limits from both signals
        if sigs:
            ylo, yhi = auto_ylim(*sigs, padding_frac=0.18)
            ax.set_ylim(ylo, yhi)
        ylo, yhi = ax.get_ylim()
        yr = yhi - ylo

        # Background shading — splits at bare_end
        ax.axvspan(0, bare_end, color='#CCCCCC', alpha=0.12, zorder=0)
        ax.axvspan(bare_end, total_width, color=MIC_COLOR, alpha=0.06, zorder=0)

        # Divider at the junction
        ax.axvline(bare_end, color='#999999', linewidth=1, linestyle='--', zorder=1)

        # Labels — centered in each half
        ax.text(bare_end * 0.5, yhi - 0.05 * yr, "Without MIC",
                ha='center', va='top', fontsize=14, fontweight='bold',
                color=BARE_COLOR, zorder=5)
        ax.text(bare_end + (total_width - bare_end) * 0.5, yhi - 0.05 * yr, "With MIC",
                ha='center', va='top', fontsize=14, fontweight='bold',
                color=MIC_COLOR, zorder=5)

        # I_p-p annotations
        if pp_b is not None:
            lbl = fmt_ipp(pp_b, is_current)
            ax.text(bare_end * 0.5, ylo + 0.05 * yr, lbl,
                    ha='center', va='bottom', fontsize=10, color=BARE_COLOR,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=BARE_COLOR, alpha=0.85))

        if pp_p is not None:
            lbl = fmt_ipp(pp_p, is_current)
            ax.text(bare_end + (total_width - bare_end) * 0.5, ylo + 0.05 * yr, lbl,
                    ha='center', va='bottom', fontsize=10, color=MIC_COLOR,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                              edgecolor=MIC_COLOR, alpha=0.85))

        ax.set_xlabel("Time (s)", fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
        panel_title = "Short-Circuit Current" if is_current else "Open-Circuit Voltage"
        ax.set_title(f"{panel_title} | f = {freq} Hz", fontsize=10, fontweight='bold', pad=8)
        ax.tick_params(axis='both', labelsize=11)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xlim(0, total_width)
        set_sci_yaxis(ax, is_current)

        freq_str = str(freq).replace('.', '_')
        fname = f"{output_prefix}_{freq_str}Hz.png"
        out_path = OUTPUT_DIR / fname
        plt.tight_layout()
        plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.savefig(str(out_path).replace('.png', '.svg'), bbox_inches='tight', facecolor='white')
        print(f"  Saved: {out_path}")
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
        print(f"Put your .data files in it. Expected names like:")
        print(f"  Isc_Bare vs Parafilm blue_1Hz_001.data")
        print(f"  Isc_PDA vs Parafilm blue_1Hz_001.data")
        print(f"  Voc_Bare vs Parafilm blue_1Hz_001.data")
        print(f"  Voc_PDA vs Parafilm blue_5Hz_correct_001.data")
        return

    files = find_files()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nDiscovered files:")
    for key, fd in files.items():
        print(f"\n  {key}:")
        if not fd: print("    (none)")
        for freq, fp in sorted(fd.items()):
            print(f"    {freq} Hz -> {fp.name}")

    # --- Compute shared y-limits for Isc sweeps ---
    isc_ylim = None
    if files["Isc_Bare"] or files["Isc_PDA"]:
        all_isc_sigs = []
        crop_i = CROP_DURATION_CURRENT
        for freq in FREQUENCIES:
            if freq in files["Isc_Bare"]:
                _, s = load_and_crop(files["Isc_Bare"][freq], crop_i, from_end=False)
                all_isc_sigs.append(s * CURRENT_SCALE)
            if freq in files["Isc_PDA"]:
                _, s = load_and_crop(files["Isc_PDA"][freq], crop_i, from_end=False)
                all_isc_sigs.append(s * CURRENT_SCALE)
        if all_isc_sigs:
            isc_ylim = auto_ylim(*all_isc_sigs, padding_frac=0.22)

    # --- Compute shared y-limits for Voc sweeps ---
    voc_ylim = None
    if files["Voc_Bare"] or files["Voc_PDA"]:
        all_voc_sigs = []
        crop_v = CROP_DURATION_VOLTAGE
        for freq in FREQUENCIES:
            if freq in files["Voc_Bare"]:
                _, s = load_and_crop(files["Voc_Bare"][freq], crop_v, from_end=False)
                all_voc_sigs.append(s)
            if freq in files["Voc_PDA"]:
                _, s = load_and_crop(files["Voc_PDA"][freq], crop_v, from_end=True)
                all_voc_sigs.append(s)
        if all_voc_sigs:
            voc_ylim = auto_ylim(*all_voc_sigs, padding_frac=0.22)

    # 1. Main Isc sweep — both bare and MIC
    if files["Isc_Bare"] or files["Isc_PDA"]:
        print("\n[1] Main Isc sweep (bare + MIC)...")
        plot_main_sweep(
            files["Isc_Bare"], files["Isc_PDA"],
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_sweep_both.png",
            "Short-Circuit Current — Bare vs MIC",
            is_current=True, forced_ylim=isc_ylim)

    # 2. Bare-only Isc sweep
    if files["Isc_Bare"]:
        print("\n[2] Bare-only Isc sweep...")
        plot_main_sweep(
            files["Isc_Bare"], {},
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_sweep_bare.png",
            "Short-Circuit Current — Without MIC",
            is_current=True, forced_ylim=isc_ylim)

    # 3. MIC-only Isc sweep
    if files["Isc_PDA"]:
        print("\n[3] MIC-only Isc sweep...")
        plot_main_sweep(
            {}, files["Isc_PDA"],
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_sweep_MIC.png",
            "Short-Circuit Current — With MIC",
            is_current=True, forced_ylim=isc_ylim)

    # 4. Main Voc sweep — both bare and MIC
    if files["Voc_Bare"] or files["Voc_PDA"]:
        print("\n[4] Main Voc sweep (bare + MIC)...")
        plot_main_sweep(
            files["Voc_Bare"], files["Voc_PDA"],
            "V$_{oc}$ (V)", 1.0,
            "Voc_sweep_both.png",
            "Open-Circuit Voltage — Bare vs MIC",
            is_current=False, forced_ylim=voc_ylim)

    # 5. MIC-only Voc sweep
    if files["Voc_PDA"]:
        print("\n[5] MIC-only Voc sweep...")
        plot_main_sweep(
            {}, files["Voc_PDA"],
            "V$_{oc}$ (V)", 1.0,
            "Voc_sweep_MIC.png",
            "Open-Circuit Voltage — With MIC",
            is_current=False, forced_ylim=voc_ylim)

    # 6. Per-frequency Isc comparison
    if files["Isc_Bare"] or files["Isc_PDA"]:
        print("\n[6] Isc comparison (side-by-side per frequency)...")
        plot_comparison(
            files["Isc_Bare"], files["Isc_PDA"],
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            "Isc_compare", is_current=True)

    # 7. Per-frequency Voc comparison
    if files["Voc_Bare"] or files["Voc_PDA"]:
        print("\n[7] Voc comparison (side-by-side per frequency)...")
        plot_comparison(
            files["Voc_Bare"], files["Voc_PDA"],
            "V$_{oc}$ (V)", 1.0,
            "Voc_compare", is_current=False)

    print("\n" + "=" * 60)
    print(f"All plots saved to: {OUTPUT_DIR.resolve()}")
    print("  Isc_sweep_both.png/.svg         Bare + MIC current")
    print("  Isc_sweep_bare.png/.svg         Bare-only current")
    print("  Isc_sweep_MIC.png/.svg          MIC-only current")
    print("  Voc_sweep_both.png/.svg         Bare + MIC voltage")
    print("  Voc_sweep_MIC.png/.svg          MIC-only voltage")
    print("  Isc_compare_*Hz.png/.svg        Side-by-side per frequency")
    print("  Voc_compare_*Hz.png/.svg        Side-by-side per frequency")
    print("=" * 60)


if __name__ == "__main__":
    main()