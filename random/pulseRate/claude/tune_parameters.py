"""
Parameter tuning tool for z-score peak detection
Helps find optimal settings for your specific signal
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from zscore_heart_rate_detector import RealTimeHeartRateDetector, DetectionConfig


def test_configuration(signal_data, config, verbose=False):
    """Test a configuration and return peak count"""
    detector = RealTimeHeartRateDetector(config)
    
    for i, value in enumerate(signal_data):
        detector.process_sample(value, i * 0.01)
    
    stats = detector.get_statistics()
    
    if verbose:
        print(f"Config: lag1={config.stage1_lag}, thresh1={config.stage1_threshold}, "
              f"lag2={config.stage2_lag}, thresh2={config.stage2_threshold}")
        print(f"  Peaks: {stats['total_peaks']}, Rate: {stats['total_peaks']/stats['total_samples']*100:.2f}%")
    
    return stats['total_peaks'], detector


def grid_search_thresholds(signal_data, lag1=5, lag2=15):
    """
    Grid search over different threshold values
    """
    print(f"\nGrid search with lag1={lag1}, lag2={lag2}")
    print(f"Testing thresholds from 0.5 to 8.0\n")
    
    thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]
    results = []
    
    for thresh in thresholds:
        config = DetectionConfig(
            stage1_lag=lag1,
            stage1_threshold=thresh,
            stage1_influence=0.001,
            stage2_lag=lag2,
            stage2_threshold=thresh,
            stage2_influence=0.001
        )
        
        peak_count, _ = test_configuration(signal_data, config)
        results.append((thresh, peak_count))
        print(f"Threshold {thresh:>4.1f}: {peak_count:>4} peaks ({peak_count/len(signal_data)*100:>5.2f}%)")
    
    # Find optimal
    # Typically want 1-5% peak rate for heart signals
    target_rate = 0.02  # 2%
    best_thresh = min(results, key=lambda x: abs(x[1]/len(signal_data) - target_rate))
    
    print(f"\nRecommended threshold: {best_thresh[0]} (gives {best_thresh[1]} peaks)")
    
    return results


def grid_search_lags(signal_data, threshold=3.0):
    """
    Grid search over different lag values
    """
    print(f"\nGrid search with threshold={threshold}")
    print(f"Testing different lag combinations\n")
    
    lag_pairs = [
        (3, 10),
        (5, 15),
        (5, 20),
        (10, 20),
        (10, 30),
        (15, 30)
    ]
    
    results = []
    
    for lag1, lag2 in lag_pairs:
        config = DetectionConfig(
            stage1_lag=lag1,
            stage1_threshold=threshold,
            stage1_influence=0.001,
            stage2_lag=lag2,
            stage2_threshold=threshold,
            stage2_influence=0.001
        )
        
        peak_count, _ = test_configuration(signal_data, config)
        results.append((lag1, lag2, peak_count))
        print(f"Lags ({lag1:>2}, {lag2:>2}): {peak_count:>4} peaks ({peak_count/len(signal_data)*100:>5.2f}%)")
    
    # Find best
    target_rate = 0.02
    best = min(results, key=lambda x: abs(x[2]/len(signal_data) - target_rate))
    
    print(f"\nRecommended lags: ({best[0]}, {best[1]}) (gives {best[2]} peaks)")
    
    return results


def grid_search_influence(signal_data, lag1=5, lag2=15, threshold=3.0):
    """
    Grid search over influence values
    """
    print(f"\nGrid search for influence parameter")
    print(f"Using lag1={lag1}, lag2={lag2}, threshold={threshold}\n")
    
    influences = [0.0001, 0.001, 0.01, 0.05, 0.1, 0.3, 0.5]
    results = []
    
    for infl in influences:
        config = DetectionConfig(
            stage1_lag=lag1,
            stage1_threshold=threshold,
            stage1_influence=infl,
            stage2_lag=lag2,
            stage2_threshold=threshold,
            stage2_influence=infl
        )
        
        peak_count, _ = test_configuration(signal_data, config)
        results.append((infl, peak_count))
        print(f"Influence {infl:>6.4f}: {peak_count:>4} peaks ({peak_count/len(signal_data)*100:>5.2f}%)")
    
    return results


def visualize_comparison(signal_data, configs_dict, window=None):
    """
    Visually compare different configurations
    """
    n_configs = len(configs_dict)
    fig, axes = plt.subplots(n_configs, 1, figsize=(15, 4*n_configs))
    
    if n_configs == 1:
        axes = [axes]
    
    # Auto-determine window if not specified
    if window is None:
        min_idx = max(0, len(signal_data) // 3)
        max_idx = min(len(signal_data), min_idx + 1000)
    else:
        min_idx, max_idx = window
    
    # Ensure window is within bounds
    min_idx = max(0, min(min_idx, len(signal_data) - 1))
    max_idx = min(len(signal_data), max(max_idx, min_idx + 100))
    times = np.arange(len(signal_data)) * 0.01
    
    for idx, (name, config) in enumerate(configs_dict.items()):
        _, detector = test_configuration(signal_data, config)
        
        # Get results
        results = []
        detector_temp = RealTimeHeartRateDetector(config)
        for i, value in enumerate(signal_data):
            result = detector_temp.process_sample(value, i * 0.01)
            results.append(result)
        
        filtered = [r['stage2_filtered'] for r in results]
        peaks_signal = [r['peak_detected'] for r in results]
        
        # Plot
        ax = axes[idx]
        ax.plot(times[min_idx:max_idx], signal_data[min_idx:max_idx], 
               'b-', alpha=0.3, label='Raw')
        ax.plot(times[min_idx:max_idx], filtered[min_idx:max_idx], 
               'r-', linewidth=2, label='Filtered')
        
        # Mark peaks
        peak_indices = [i for i in range(min_idx, max_idx) if peaks_signal[i] > 0]
        if peak_indices:
            ax.scatter([times[i] for i in peak_indices],
                      [signal_data[i] for i in peak_indices],
                      color='black', s=100, marker='o', zorder=5)
        
        total_peaks = sum(1 for p in peaks_signal if p > 0)
        ax.set_title(f"{name} - {total_peaks} total peaks", fontweight='bold')
        ax.set_ylabel('Amplitude')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Time (s)')
    plt.tight_layout()
    plt.savefig('config_comparison.png', dpi=150)
    print("Saved comparison plot to config_comparison.png")
    plt.show()


def auto_tune(signal_data, target_peak_rate=0.02):
    """
    Automatically find good parameters
    
    Args:
        signal_data: The signal to analyze
        target_peak_rate: Desired peak rate (default 2% = 0.02)
    """
    print("\n" + "="*70)
    print("AUTO-TUNING PARAMETERS")
    print("="*70)
    print(f"Target peak rate: {target_peak_rate*100:.1f}%")
    print(f"Signal samples: {len(signal_data)}")
    print()
    
    # Step 1: Find good threshold
    print("Step 1: Finding optimal threshold...")
    thresholds = np.linspace(0.5, 8.0, 20)
    best_thresh = None
    best_diff = float('inf')
    
    for thresh in thresholds:
        config = DetectionConfig(
            stage1_lag=5, stage1_threshold=thresh, stage1_influence=0.001,
            stage2_lag=15, stage2_threshold=thresh, stage2_influence=0.001
        )
        peaks, _ = test_configuration(signal_data, config)
        diff = abs(peaks/len(signal_data) - target_peak_rate)
        
        if diff < best_diff:
            best_diff = diff
            best_thresh = thresh
    
    print(f"  Optimal threshold: {best_thresh:.2f}")
    
    # Step 2: Fine-tune lags
    print("\nStep 2: Tuning lag values...")
    lag_combos = [(3,10), (5,15), (5,20), (10,20), (10,30)]
    best_lags = None
    best_diff = float('inf')
    
    for lag1, lag2 in lag_combos:
        config = DetectionConfig(
            stage1_lag=lag1, stage1_threshold=best_thresh, stage1_influence=0.001,
            stage2_lag=lag2, stage2_threshold=best_thresh, stage2_influence=0.001
        )
        peaks, _ = test_configuration(signal_data, config)
        diff = abs(peaks/len(signal_data) - target_peak_rate)
        
        if diff < best_diff:
            best_diff = diff
            best_lags = (lag1, lag2)
    
    print(f"  Optimal lags: stage1={best_lags[0]}, stage2={best_lags[1]}")
    
    # Final config
    final_config = DetectionConfig(
        stage1_lag=best_lags[0],
        stage1_threshold=best_thresh,
        stage1_influence=0.001,
        stage2_lag=best_lags[1],
        stage2_threshold=best_thresh,
        stage2_influence=0.001
    )
    
    peaks, detector = test_configuration(signal_data, final_config, verbose=True)
    
    print("\n" + "="*70)
    print("RECOMMENDED CONFIGURATION")
    print("="*70)
    print(f"DetectionConfig(")
    print(f"    stage1_lag={final_config.stage1_lag},")
    print(f"    stage1_threshold={final_config.stage1_threshold},")
    print(f"    stage1_influence={final_config.stage1_influence},")
    print(f"    stage2_lag={final_config.stage2_lag},")
    print(f"    stage2_threshold={final_config.stage2_threshold},")
    print(f"    stage2_influence={final_config.stage2_influence}")
    print(f")")
    print(f"\nThis gives {peaks} peaks ({peaks/len(signal_data)*100:.2f}% of samples)")
    
    return final_config


if __name__ == "__main__":
    import sys
    
    # Load data
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/home/claude/realistic_heartrate.csv'
    
    print(f"Loading {csv_file}...")
    df = pd.read_csv(csv_file)
    
    if 'signal' in df.columns:
        signal_data = df['signal'].values
    else:
        signal_data = df.iloc[:, 0].values
    
    print(f"Loaded {len(signal_data)} samples")
    
    print("\n" + "="*70)
    print("PARAMETER TUNING TOOL")
    print("="*70)
    print("\nOptions:")
    print("1. Auto-tune (finds best parameters automatically)")
    print("2. Grid search - thresholds")
    print("3. Grid search - lags")
    print("4. Grid search - influence")
    print("5. Compare configurations visually")
    
    choice = input("\nSelect option (1-5) or Enter for auto-tune: ").strip()
    
    if not choice or choice == '1':
        # Auto-tune
        config = auto_tune(signal_data, target_peak_rate=0.02)
        
        # Visualize result
        print("\nGenerating visualization...")
        visualize_comparison(signal_data, {
            'Auto-tuned': config,
            'Your Original (thresh=5)': DetectionConfig(
                stage1_lag=5, stage1_threshold=5.0, stage1_influence=0.001,
                stage2_lag=15, stage2_threshold=5.0, stage2_influence=0.001
            )
        })
    
    elif choice == '2':
        grid_search_thresholds(signal_data)
    
    elif choice == '3':
        grid_search_lags(signal_data)
    
    elif choice == '4':
        grid_search_influence(signal_data)
    
    elif choice == '5':
        # Compare multiple configs
        configs = {
            'Threshold 2.0': DetectionConfig(
                stage1_lag=5, stage1_threshold=2.0, stage1_influence=0.001,
                stage2_lag=15, stage2_threshold=2.0, stage2_influence=0.001
            ),
            'Threshold 3.0': DetectionConfig(
                stage1_lag=5, stage1_threshold=3.0, stage1_influence=0.001,
                stage2_lag=15, stage2_threshold=3.0, stage2_influence=0.001
            ),
            'Threshold 5.0 (Your Original)': DetectionConfig(
                stage1_lag=5, stage1_threshold=5.0, stage1_influence=0.001,
                stage2_lag=15, stage2_threshold=5.0, stage2_influence=0.001
            )
        }
        visualize_comparison(signal_data, configs)
