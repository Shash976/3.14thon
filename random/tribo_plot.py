"""
Triboelectric characterization plots v4.

Reads LabVIEW `.data` files exported from current (It) and voltage (Vt)
measurements, then produces publication-quality matplotlib figures:

  1. Isc sweep (PDA/MIC only) — all four frequencies concatenated side by side
  2. Voc sweep (PDA/MIC only) — all four frequencies concatenated side by side
  3–6. Per-frequency comparison (Bare left | MIC right, shared time axis)

FILE FORMAT (.data):
  Each file has a variable-length ASCII header ending with the line
  "***End_of_Header***", followed by a blank line, a tab-separated column-name
  line, and then the numeric data rows (tab-separated, leading tab per row).

  Current file columns: Time | Current | Filtered Current
  Voltage file columns: Time | Voltage | Filtered Voltage
  Only the first two numeric columns (Time and raw signal) are used.

FILE NAMING CONVENTION:
  Files must start with one of the four recognised prefixes and contain a
  frequency token of the form "_<freq>Hz_" (spaces are stripped before matching):
    Isc_Bare_<freq>Hz_<anything>.data
    Isc_PDA_<freq>Hz_<anything>.data
    Voc_Bare_<freq>Hz_<anything>.data
    Voc_PDA_<freq>Hz_<anything>.data

SIGNAL PROCESSING:
  • A 5 s (current) or 2 s (voltage) window is extracted starting at 20 % of
    the total recording duration to skip any transient at the beginning.
  • Raw current (A) is multiplied by CURRENT_SCALE to convert to mA/m².
  • I_p-p (or V_p-p) = |max| + |min| of the cropped window.

USAGE:
  1. Place all .data files in DATA_DIR
  2. Run: python tribo_plot.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURATION
# ============================================================
DATA_DIR = Path(r"C:\\Users\\shash\\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot") # TODO: Change with data filepath
OUTPUT_DIR = Path("plots")  # All generated PNG/SVG files go here
# Conversion factor: raw current (A) → current density (mA/m²)
CURRENT_SCALE = 2500

# Duration (seconds) of the signal window extracted from each recording
CROP_DURATION_CURRENT = 5.0
CROP_DURATION_VOLTAGE = 2.0

# Frequencies (Hz) expected across the dataset
FREQUENCIES = [1, 2.5, 5, 10]
FREQ_LABELS = ["1 Hz", "2.5 Hz", "5 Hz", "10 Hz"]

# Background band colours for each frequency in the sweep plot
BAND_COLORS = ["#4A90D9", "#5CB85C", "#F0AD4E", "#E8667A"]
BAND_ALPHA = 0.15

# Line colours for bare substrate and MIC-coated sample
BARE_COLOR = "#333333"
MIC_COLOR  = "#D94452"

# Gap (seconds) inserted between frequency bands in sweep plots
BAND_GAP = 0


# ============================================================
# HELPERS
# ============================================================

def find_files():
    """
    Scan DATA_DIR for `.data` files and map them by sample type and frequency.

    Returns
    -------
    dict[str, dict[float, Path]]
        Nested mapping ``{sample_key: {freq_hz: filepath}}``.
        Sample keys are "Isc_Bare", "Isc_PDA", "Voc_Bare", "Voc_PDA".
        Only the first file found per (key, frequency) pair is kept.
    """
    files = {"Isc_Bare": {}, "Isc_PDA": {}, "Voc_Bare": {}, "Voc_PDA": {}}
    for f in sorted(DATA_DIR.glob("*.data")):
        name = f.stem
        if   name.startswith("Isc_Bare"): key = "Isc_Bare"
        elif name.startswith("Isc_PDA"):  key = "Isc_PDA"
        elif name.startswith("Voc_Bare"): key = "Voc_Bare"
        elif name.startswith("Voc_PDA"):  key = "Voc_PDA"
        else: continue
        for freq in FREQUENCIES:
            pattern = f"_{freq}Hz_"
            if pattern in name or pattern in name.replace(" ", ""):
                if freq not in files[key]:
                    files[key][freq] = f
                break
    return files


def load_and_crop(filepath, crop_duration=5.0):
    """
    Parse a LabVIEW `.data` file and return a cropped (time, signal) window.

    The file format has a multi-line ASCII header ending with the marker
    ``***End_of_Header***``, then a blank line, then a column-name line, and
    then tab-separated numeric rows (with a leading tab on each data line).
    Only the first two numeric values on each row (Time and raw signal) are used.

    The extracted window starts at 20 % of the total recording duration to
    avoid the initial transient, and spans ``crop_duration`` seconds forward.
    If the total recording is shorter than ``crop_duration`` the entire
    recording is returned (time re-zeroed to 0).

    Parameters
    ----------
    filepath : str or Path
        Path to the `.data` file.
    crop_duration : float
        Length of the window to extract, in seconds.

    Returns
    -------
    time : np.ndarray
        Time values (seconds), re-zeroed so the window starts at 0.
    signal : np.ndarray
        Raw signal values (A for current files, V for voltage files).

    Raises
    ------
    ValueError
        If the header marker is missing or no numeric rows are found.
    """
    filepath = Path(filepath)
    lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()

    # Locate the end-of-header marker
    header_end = None
    for i, line in enumerate(lines):
        if "***End_of_Header***" in line:
            header_end = i
            break
    if header_end is None:
        raise ValueError(f"No ***End_of_Header*** marker found in {filepath}")

    # Layout after the marker:  [marker] [blank] [column names] [data ...]
    data_start = header_end + 3

    rows = []
    for line in lines[data_start:]:
        parts = line.strip().split("\t")
        nums = []
        for p in parts:
            p = p.strip()
            if p:
                try:
                    nums.append(float(p))
                except ValueError:
                    pass
        if len(nums) >= 2:
            rows.append(nums[:2])

    if not rows:
        raise ValueError(f"No numeric data found after header in {filepath}")

    arr    = np.array(rows)
    time   = arr[:, 0]
    signal = arr[:, 1]

    total = time[-1] - time[0]
    if total <= crop_duration:
        return time - time[0], signal

    start = time[0] + 0.2 * total
    end   = start + crop_duration
    if end > time[-1]:
        end = time[-1]
        start = end - crop_duration

    mask = (time >= start) & (time <= end)
    return time[mask] - time[mask][0], signal[mask]


def calc_ipp(signal):
    """
    Compute peak-to-peak amplitude as |max| + |min| of the signal array.

    Parameters
    ----------
    signal : np.ndarray
        1-D array of signal values.

    Returns
    -------
    float
        Peak-to-peak value (always ≥ 0).
    """
    return abs(np.max(signal)) + abs(np.min(signal))


def auto_ylim(*signals, padding_frac=0.15):
    """
    Compute y-axis limits that encompass all provided signal arrays.

    When the signal crosses zero the limits are made symmetric around zero
    so the baseline is visually centred. A fractional padding is added on
    both ends.

    Parameters
    ----------
    *signals : np.ndarray
        One or more 1-D signal arrays (None or empty arrays are ignored).
    padding_frac : float
        Fraction of the full range to add as padding on each side.

    Returns
    -------
    (float, float)
        (lower_limit, upper_limit)
    """
    all_v = np.concatenate([s for s in signals if s is not None and len(s) > 0])
    if len(all_v) == 0:
        return -1, 1
    lo, hi = np.min(all_v), np.max(all_v)
    span = hi - lo
    if span == 0:
        return -1, 1
    pad = padding_frac * span
    if lo < 0 and hi > 0:
        ext = max(abs(hi), abs(lo))
        return -(ext + pad), ext + pad
    return lo - pad, hi + pad


def fmt_ipp(val, is_current):
    """
    Format a peak-to-peak value for use in a plot annotation.

    Parameters
    ----------
    val : float
        Peak-to-peak amplitude (already scaled to the display units).
    is_current : bool
        True for current density (→ scientific notation with mA/m² units),
        False for voltage (→ two decimal places with V units).

    Returns
    -------
    str
        LaTeX-compatible annotation string.
    """
    if is_current:
        return f"I$_{{p-p}}$ = {val:.2E} mA/m²"
    else:
        return f"V$_{{p-p}}$ = {val:.2f} V"


def set_sci_yaxis(ax, is_current):
    """
    Apply scientific-notation tick formatting to the y-axis of current plots.

    Voltage plots are left with default (decimal) formatting.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to modify.
    is_current : bool
        If True, switch y-axis to scientific notation with a shared exponent.
    """
    if is_current:
        ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        ax.ticklabel_format(axis="y", style="scientific", scilimits=(-3, 3))
        ax.yaxis.get_offset_text().set_fontsize(10)


# ============================================================
# PLOT 1 & 2: MAIN SWEEP (PDA / MIC ONLY)
# ============================================================

def plot_main_sweep(pda_files, ylabel, scale, output, title_text, is_current):
    """
    Produce a sweep plot showing MIC-coated sample data at all frequencies.

    The cropped signal windows for each frequency are placed end-to-end on a
    single shared time axis. Each frequency band is shaded with a distinct
    colour and labelled at the top; the I_p-p (or V_p-p) value is annotated
    at the bottom of each band.

    Parameters
    ----------
    pda_files : dict[float, Path]
        Mapping of frequency → .data file path for the MIC sample.
    ylabel : str
        Y-axis label string (may contain LaTeX math).
    scale : float
        Multiplicative factor applied to the raw signal before plotting
        (use CURRENT_SCALE for current density, 1.0 for voltage).
    output : str
        Output filename for the PNG (a matching SVG is also saved).
    title_text : str
        Figure title.
    is_current : bool
        True when plotting current density, False for voltage.
    """
    crop    = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    fig, ax = plt.subplots(figsize=(14, 5), dpi=150)
    offset   = 0
    bands    = []
    all_sigs = []

    for i, freq in enumerate(FREQUENCIES):
        if freq not in pda_files:
            offset += crop + BAND_GAP
            continue
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
                ha="center", va="top", fontsize=13, fontweight="bold",
                color=BAND_COLORS[idx], zorder=5)
        lbl = fmt_ipp(pp, is_current)
        ax.annotate(lbl, xy=((bs + be) / 2, ylo + 0.06 * yr),
                    fontsize=9, color=MIC_COLOR, ha="center",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor=MIC_COLOR, alpha=0.85))

    ax.set_xlabel("Time (s)", fontsize=14, fontweight="bold")
    ax.set_ylabel(ylabel,     fontsize=14, fontweight="bold")
    ax.tick_params(axis="both", labelsize=11)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(-0.3, offset - BAND_GAP + 0.3)
    set_sci_yaxis(ax, is_current)

    plt.title(title_text, fontsize=16, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(output.replace(".png", ".svg"), bbox_inches="tight", facecolor="white")
    print(f"  Saved: {output}")
    plt.close()


# ============================================================
# PLOT 3-6: PER-FREQUENCY SIDE-BY-SIDE (BARE LEFT | MIC RIGHT)
# ============================================================

def plot_comparison(bare_files, pda_files, ylabel, scale, output_prefix, is_current):
    """
    Produce one comparison figure per frequency showing Bare vs MIC side by side.

    The left half of the plot shows the bare-substrate signal; the right half
    shows the MIC-coated signal. Both halves span ``crop_duration`` seconds and
    share the same y-axis limits so the enhancement is visually apparent.
    A dashed vertical divider separates the two halves.

    One PNG + SVG pair is written per frequency with names:
    ``<output_prefix>_<freq_str>Hz.png/.svg``

    Parameters
    ----------
    bare_files : dict[float, Path]
        Mapping of frequency → .data file path for the bare substrate.
    pda_files : dict[float, Path]
        Mapping of frequency → .data file path for the MIC-coated sample.
    ylabel : str
        Y-axis label string (may contain LaTeX math).
    scale : float
        Multiplicative factor applied to the raw signal before plotting.
    output_prefix : str
        Common prefix for all output filenames (e.g. "Isc_compare").
    is_current : bool
        True when plotting current density, False for voltage.
    """
    crop      = CROP_DURATION_CURRENT if is_current else CROP_DURATION_VOLTAGE
    available = [f for f in FREQUENCIES if f in bare_files or f in pda_files]

    for freq in available:
        fidx    = FREQUENCIES.index(freq)
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        sigs    = []

        # Left half: bare substrate (t = 0 … crop)
        if freq in bare_files:
            t_b, s_b = load_and_crop(bare_files[freq], crop)
            s_b = s_b * scale
            ax.plot(t_b, s_b, color=BARE_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_b)
            pp_b = calc_ipp(s_b)
        else:
            pp_b = None

        # Right half: MIC-coated sample (t = crop … 2*crop)
        if freq in pda_files:
            t_p, s_p = load_and_crop(pda_files[freq], crop)
            s_p = s_p * scale
            ax.plot(t_p + crop, s_p, color=MIC_COLOR, linewidth=0.8, zorder=3)
            sigs.append(s_p)
            pp_p = calc_ipp(s_p)
        else:
            pp_p = None

        if sigs:
            ylo, yhi = auto_ylim(*sigs, padding_frac=0.18)
            ax.set_ylim(ylo, yhi)
        ylo, yhi = ax.get_ylim()
        yr = yhi - ylo

        # Background shading: light grey (bare) and light red (MIC)
        ax.axvspan(0,    crop,     color="#CCCCCC", alpha=0.12, zorder=0)
        ax.axvspan(crop, crop * 2, color=MIC_COLOR, alpha=0.06, zorder=0)

        # Divider at the half-way boundary
        ax.axvline(crop, color="#999999", linewidth=1, linestyle="--", zorder=1)

        # Section labels at the top of each half
        ax.text(crop * 0.5, yhi - 0.05 * yr, "Without MIC",
                ha="center", va="top", fontsize=14, fontweight="bold",
                color=BARE_COLOR, zorder=5)
        ax.text(crop * 1.5, yhi - 0.05 * yr, "With MIC",
                ha="center", va="top", fontsize=14, fontweight="bold",
                color=MIC_COLOR, zorder=5)

        # I_p-p / V_p-p annotations at the bottom of each half
        if pp_b is not None:
            lbl = fmt_ipp(pp_b, is_current)
            ax.text(crop * 0.5, ylo + 0.05 * yr, lbl,
                    ha="center", va="bottom", fontsize=10, color=BARE_COLOR,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                              edgecolor=BARE_COLOR, alpha=0.85))

        if pp_p is not None:
            lbl = fmt_ipp(pp_p, is_current)
            ax.text(crop * 1.5, ylo + 0.05 * yr, lbl,
                    ha="center", va="bottom", fontsize=10, color=MIC_COLOR,
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                              edgecolor=MIC_COLOR, alpha=0.85))

        # Frequency label box in the top-right corner
        ax.text(0.97, 0.95, f"f = {freq} Hz", transform=ax.transAxes,
                fontsize=13, fontweight="bold", ha="right", va="top",
                color=BAND_COLORS[fidx],
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                          edgecolor=BAND_COLORS[fidx], linewidth=1.5, alpha=0.9))

        ax.set_xlabel("Time (s)", fontsize=14, fontweight="bold")
        ax.set_ylabel(ylabel,     fontsize=14, fontweight="bold")
        ax.tick_params(axis="both", labelsize=11)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(0, crop * 2)
        set_sci_yaxis(ax, is_current)

        freq_str = str(freq).replace(".", "_")
        fname = f"{output_prefix}_{freq_str}Hz.png"
        plt.tight_layout()
        plt.savefig(fname, dpi=300, bbox_inches="tight", facecolor="white")
        plt.savefig(fname.replace(".png", ".svg"), bbox_inches="tight", facecolor="white")
        print(f"  Saved: {fname}")
        plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    """
    Entry point: discover files, run all four plot routines, and report outputs.

    Exits early with a usage message if DATA_DIR does not exist.
    """
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

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {OUTPUT_DIR.resolve()}")

    files = find_files()

    print("\nDiscovered files:")
    for key, fd in files.items():
        print(f"\n  {key}:")
        if not fd:
            print("    (none)")
        for freq, fp in sorted(fd.items()):
            print(f"    {freq} Hz -> {fp.name}")

    # Plot 1: Isc sweep — MIC only, all frequencies
    if files["Isc_PDA"]:
        print("\n[1] Main Isc sweep (MIC)...")
        plot_main_sweep(
            files["Isc_PDA"], "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            str(OUTPUT_DIR / "Isc_sweep_MIC.png"),
            "Short-Circuit Current — With MIC",
            is_current=True)

    # Plot 2: Voc sweep — MIC only, all frequencies
    if files["Voc_PDA"]:
        print("\n[2] Main Voc sweep (MIC)...")
        plot_main_sweep(
            files["Voc_PDA"], "V$_{oc}$ (V)", 1.0,
            str(OUTPUT_DIR / "Voc_sweep_MIC.png"),
            "Open-Circuit Voltage — With MIC",
            is_current=False)

    # Plots 3–6: Isc Bare vs MIC, one figure per frequency
    if files["Isc_Bare"] or files["Isc_PDA"]:
        print("\n[3] Isc comparison (Bare vs MIC, per frequency)...")
        plot_comparison(
            files["Isc_Bare"], files["Isc_PDA"],
            "I$_{sc}$ (mA/m²)", CURRENT_SCALE,
            str(OUTPUT_DIR / "Isc_compare"), is_current=True)

    # Plots 7–10: Voc Bare vs MIC, one figure per frequency
    if files["Voc_Bare"] or files["Voc_PDA"]:
        print("\n[4] Voc comparison (Bare vs MIC, per frequency)...")
        plot_comparison(
            files["Voc_Bare"], files["Voc_PDA"],
            "V$_{oc}$ (V)", 1.0,
            str(OUTPUT_DIR / "Voc_compare"), is_current=False)

    print("\n" + "=" * 60)
    print(f"All output files written to: {OUTPUT_DIR.resolve()}/")
    print("  Isc_sweep_MIC.png/.svg          Main current sweep (MIC only)")
    print("  Voc_sweep_MIC.png/.svg          Main voltage sweep (MIC only)")
    print("  Isc_compare_*Hz.png/.svg        Bare vs MIC, current (5 s window)")
    print("  Voc_compare_*Hz.png/.svg        Bare vs MIC, voltage (2 s window)")
    print("=" * 60)


if __name__ == "__main__":
    main()
