import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import deque
from dataclasses import dataclass
from typing import List, Optional
import time


class PeakDetection:
    """
    Z-score based peak detection using smoothed moving statistics
    Detects statistical anomalies in real-time
    """
    DEFAULT_LAG = 32
    DEFAULT_THRESHOLD = 2
    DEFAULT_INFLUENCE = 0.5
    DEFAULT_EPSILON = 0.01

    def __init__(self, lag=None, threshold=None, influence=None):
        """
        lag: Number of samples to use for the moving window
        threshold: The z-score at which the algorithm signals a peak
        influence: The influence (between 0 and 1) of new signals on the mean
        """
        self.lag = lag if lag is not None else self.DEFAULT_LAG
        self.threshold = threshold if threshold is not None else self.DEFAULT_THRESHOLD
        self.influence = influence if influence is not None else self.DEFAULT_INFLUENCE

        self.EPSILON = self.DEFAULT_EPSILON
        self.index = 0
        self.peak = 0

        # Circular buffers
        self.data = [0.0] * self.lag
        self.avg = [0.0] * self.lag
        self.std = [0.0] * self.lag

    def set_epsilon(self, epsilon):
        self.EPSILON = epsilon

    def get_epsilon(self):
        return self.EPSILON

    def add(self, new_sample):
        self.peak = 0

        i = self.index % self.lag       # current index
        j = (self.index + 1) % self.lag # next index

        deviation = new_sample - self.avg[i]

        if deviation > self.threshold * self.std[i]:
            self.data[j] = (
                self.influence * new_sample +
                (1.0 - self.influence) * self.data[i]
            )
            self.peak = 1

        elif deviation < -self.threshold * self.std[i]:
            self.data[j] = (
                self.influence * new_sample +
                (1.0 - self.influence) * self.data[i]
            )
            self.peak = -1

        else:
            self.data[j] = new_sample

        self.avg[j] = self._get_avg(j, self.lag)
        self.std[j] = self._get_std(j, self.lag)

        self.index += 1
        if self.index >= 16383:
            self.index = self.lag + j

        return self.std[j]

    def get_filtered(self):
        return self.avg[self.index % self.lag]

    def get_peak(self):
        return self.peak

    def _get_avg(self, start, length):
        total = 0.0
        for i in range(length):
            total += self.data[(start + i) % self.lag]
        return total / length

    def _get_point(self, start, length):
        total = 0.0
        for i in range(length):
            x = self.data[(start + i) % self.lag]
            total += x * x
        return total / length

    def _get_std(self, start, length):
        mean = self._get_avg(start, length)
        mean_sq = self._get_point(start, length)

        variance = mean_sq - (mean * mean)

        if -self.EPSILON < variance < self.EPSILON:
            return -self.EPSILON if variance < 0.0 else self.EPSILON

        return math.sqrt(variance)
    
    def update(self, new_sample):
        self.add(new_sample)
        return (
            new_sample,
            self.get_peak(),
            self.get_filtered()
        )


@dataclass
class DetectionConfig:
    """Configuration for the two-stage detection system"""
    # First stage (coarse filtering)
    stage1_lag: int = 5
    stage1_threshold: float = 5.0
    stage1_influence: float = 0.001
    
    # Second stage (fine filtering)
    stage2_lag: int = 15
    stage2_threshold: float = 5.0
    stage2_influence: float = 0.001
    
    # Peak classification
    peak_group_window: int = 100  # samples
    min_peak_distance: int = 10   # minimum samples between peaks


@dataclass 
class Peak:
    """Represents a detected peak"""
    index: int
    value: float
    timestamp: float
    peak_type: Optional[str] = None
    filtered_value: float = 0.0


class TwoStageDetector:
    """
    Two-stage z-score peak detection system
    Stage 1: Coarse filtering with small lag
    Stage 2: Fine filtering with larger lag
    """
    
    def __init__(self, config: DetectionConfig = None):
        self.config = config or DetectionConfig()
        
        # Initialize two detectors
        self.detector_1 = PeakDetection(
            lag=self.config.stage1_lag,
            threshold=self.config.stage1_threshold,
            influence=self.config.stage1_influence
        )
        
        self.detector_2 = PeakDetection(
            lag=self.config.stage2_lag,
            threshold=self.config.stage2_threshold,
            influence=self.config.stage2_influence
        )
        
        # Storage
        self.sample_count = 0
        self.peak_history: List[Peak] = []
        self.last_peak_index = -1000  # Initialize far back
        
    def process_sample(self, value: float, timestamp: float) -> dict:
        """
        Process a single sample through both stages
        
        Returns:
            dict with raw, filtered, peak info
        """
        # Stage 1: First detector
        sample1, peak1, filt1 = self.detector_1.update(value)
        
        # Stage 2: Second detector on filtered output
        sample2, peak2, filt2 = self.detector_2.update(filt1)
        
        result = {
            'timestamp': timestamp,
            'raw_value': value,
            'stage1_filtered': filt1,
            'stage2_filtered': filt2,
            'peak_detected': peak2,
            'peak_value': value if peak2 > 0 else None
        }
        
        # Track positive peaks
        if peak2 > 0:
            # Enforce minimum distance between peaks
            if self.sample_count - self.last_peak_index >= self.config.min_peak_distance:
                peak = Peak(
                    index=self.sample_count,
                    value=value,
                    timestamp=timestamp,
                    filtered_value=filt2
                )
                self.peak_history.append(peak)
                self.last_peak_index = self.sample_count
                result['is_new_peak'] = True
            else:
                result['is_new_peak'] = False
        else:
            result['is_new_peak'] = False
        
        self.sample_count += 1
        return result
    
    def classify_peak_triplets(self) -> List[tuple]:
        """
        Classify peaks into P1, P2, P3 groups
        Returns list of (P1, P2, P3) tuples
        """
        if len(self.peak_history) < 2:
            return []
        
        triplets = []
        i = 0
        
        while i < len(self.peak_history) - 1:
            p1 = self.peak_history[i]
            
            # Look for P2 within window
            for j in range(i + 1, len(self.peak_history)):
                if self.peak_history[j].index - p1.index > self.config.peak_group_window:
                    break
                
                p2 = self.peak_history[j]
                
                # Look for P3
                p3 = None
                for k in range(j + 1, len(self.peak_history)):
                    if self.peak_history[k].index - p2.index > self.config.peak_group_window:
                        break
                    
                    # P3 might be smaller
                    if self.peak_history[k].value >= p2.value * 0.2:  # At least 20% of P2
                        p3 = self.peak_history[k]
                        break
                
                # Classify
                p1.peak_type = 'P1'
                p2.peak_type = 'P2'
                if p3:
                    p3.peak_type = 'P3'
                    triplets.append((p1, p2, p3))
                    i = k + 1
                else:
                    triplets.append((p1, p2, None))
                    i = j + 1
                break
            else:
                i += 1
        
        return triplets
    
    def get_recent_peaks(self, n: int = 100) -> List[Peak]:
        """Get the most recent n peaks"""
        return self.peak_history[-n:] if len(self.peak_history) > n else self.peak_history


class RealTimeHeartRateDetector:
    """
    Complete real-time heart rate detection system using z-score method
    """
    
    def __init__(self, config: DetectionConfig = None):
        self.config = config or DetectionConfig()
        self.detector = TwoStageDetector(config)
        
        # Statistics
        self.total_samples = 0
        self.total_peaks = 0
        self.processing_times = []
        
    def process_sample(self, value: float, timestamp: float) -> dict:
        """Process a single sample"""
        start_time = time.time()
        
        result = self.detector.process_sample(value, timestamp)
        
        if result['is_new_peak']:
            self.total_peaks += 1
        
        self.total_samples += 1
        
        # Track processing time
        proc_time = time.time() - start_time
        self.processing_times.append(proc_time)
        
        # Add classification info
        result['total_peaks'] = self.total_peaks
        result['total_samples'] = self.total_samples
        
        return result
    
    def get_peaks(self) -> List[Peak]:
        """Get all detected peaks"""
        return self.detector.peak_history
    
    def get_heartbeats(self) -> List[tuple]:
        """Get classified heartbeat triplets"""
        return self.detector.classify_peak_triplets()
    
    def get_statistics(self) -> dict:
        """Get processing statistics"""
        return {
            'total_samples': self.total_samples,
            'total_peaks': self.total_peaks,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'max_processing_time': np.max(self.processing_times) if self.processing_times else 0
        }


def process_csv_file(csv_file: str, 
                     config: DetectionConfig = None,
                     plot_window: tuple = None,
                     show_stats: bool = True):
    """
    Process a CSV file with the two-stage detector
    
    Args:
        csv_file: Path to CSV file
        config: Detection configuration
        plot_window: (min_index, max_index) for plotting window, None for all
        show_stats: Whether to print statistics
    """
    # Load data
    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    if 'signal' in df.columns:
        signal_data = df['signal'].values
    else:
        signal_data = df.iloc[:, 0].values
    
    print(f"Loaded {len(signal_data)} samples")
    
    # Create detector
    detector = RealTimeHeartRateDetector(config)
    
    # Process all samples
    results = []
    print("Processing samples...")
    
    for i, value in enumerate(signal_data):
        timestamp = i * 0.01  # Assuming 100Hz
        result = detector.process_sample(value, timestamp)
        results.append(result)
        
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i+1}/{len(signal_data)} samples")
    
    # Extract data for plotting
    times = [r['timestamp'] for r in results]
    original = [r['raw_value'] for r in results]
    filtered = [r['stage2_filtered'] for r in results]
    peaks_signal = [r['peak_detected'] for r in results]
    
    # Statistics
    if show_stats:
        stats = detector.get_statistics()
        print("\n" + "="*60)
        print("PROCESSING STATISTICS")
        print("="*60)
        print(f"Total samples processed: {stats['total_samples']}")
        print(f"Total peaks detected: {stats['total_peaks']}")
        print(f"Peak rate: {stats['total_peaks'] / stats['total_samples'] * 100:.2f}%")
        print(f"Avg processing time: {stats['avg_processing_time']*1000:.3f} ms")
        print(f"Max processing time: {stats['max_processing_time']*1000:.3f} ms")
        
        # Heartbeat classification
        heartbeats = detector.get_heartbeats()
        print(f"\nHeartbeat triplets detected: {len(heartbeats)}")
        
        # Show first few triplets
        print("\nFirst 5 heartbeat triplets:")
        for i, (p1, p2, p3) in enumerate(heartbeats[:5]):
            p3_str = f"P3={p3.value:.4f}" if p3 else "P3=None"
            print(f"  {i+1}. P1={p1.value:.4f}, P2={p2.value:.4f}, {p3_str}")
    
    # Plotting
    if plot_window:
        min_idx, max_idx = plot_window
    else:
        min_idx, max_idx = 0, len(times)
    
    print(f"\nPlotting window: samples {min_idx} to {max_idx}")
    
    plt.figure(figsize=(15, 7))
    
    # Plot original and filtered
    plt.plot(times[min_idx:max_idx], 
             original[min_idx:max_idx], 
             label='Original Data', 
             color='grey', 
             alpha=0.35,
             linewidth=1)
    
    plt.plot(times[min_idx:max_idx], 
             filtered[min_idx:max_idx], 
             label='Filtered Data', 
             color='red',
             linewidth=2)
    
    # Mark peaks
    peak_indices = [i for i in range(min_idx, max_idx) if peaks_signal[i] > 0]
    if peak_indices:
        plt.scatter([times[i] for i in peak_indices],
                   [original[i] for i in peak_indices],
                   color='black',
                   s=100,
                   marker='o',
                   label='Detected Peaks',
                   zorder=5)
    
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Signal Amplitude', fontsize=12)
    plt.title('Two-Stage Z-Score Peak Detection', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('detection_result.png', dpi=150)
    print(f"Plot saved to detection_result.png")
    plt.show()
    
    return detector, results


def compare_configurations(csv_file: str, window: tuple = (2000, 3000)):
    """
    Compare different detection configurations
    """
    configs = {
        'Your Settings': DetectionConfig(
            stage1_lag=5, stage1_threshold=5.0, stage1_influence=0.001,
            stage2_lag=15, stage2_threshold=5.0, stage2_influence=0.001
        ),
        'More Sensitive': DetectionConfig(
            stage1_lag=5, stage1_threshold=3.0, stage1_influence=0.01,
            stage2_lag=15, stage2_threshold=3.0, stage2_influence=0.01
        ),
        'More Aggressive': DetectionConfig(
            stage1_lag=10, stage1_threshold=4.0, stage1_influence=0.005,
            stage2_lag=20, stage2_threshold=4.0, stage2_influence=0.005
        )
    }
    
    print("\n" + "="*70)
    print("COMPARING DIFFERENT CONFIGURATIONS")
    print("="*70)
    
    for name, config in configs.items():
        print(f"\n--- {name} ---")
        print(f"Stage 1: lag={config.stage1_lag}, threshold={config.stage1_threshold}, influence={config.stage1_influence}")
        print(f"Stage 2: lag={config.stage2_lag}, threshold={config.stage2_threshold}, influence={config.stage2_influence}")
        
        detector, _ = process_csv_file(csv_file, config, plot_window=window, show_stats=True)
        print()


if __name__ == "__main__":
    import sys
    
    # Use provided file or default
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/home/claude/realistic_heartrate.csv'
        print(f"Using default test file: {csv_file}")
    
    print("\n" + "="*70)
    print("TWO-STAGE Z-SCORE PEAK DETECTION")
    print("="*70)
    print("\nThis uses YOUR peak detection algorithm!")
    print("Stage 1: Fast response (lag=5)")
    print("Stage 2: Smooth filtering (lag=15)")
    print()
    
    # Your exact settings
    config = DetectionConfig(
        stage1_lag=5,
        stage1_threshold=5.0,
        stage1_influence=0.001,
        stage2_lag=15,
        stage2_threshold=5.0,
        stage2_influence=0.001
    )
    
    # Process the file
    detector, results = process_csv_file(
        csv_file,
        config=config,
        plot_window=(2000, 3000),  # Your window
        show_stats=True
    )
    
    # Optional: Compare configurations
    # compare_configurations(csv_file, window=(2000, 3000))
