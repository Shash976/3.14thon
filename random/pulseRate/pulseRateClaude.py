import numpy as np
import pandas as pd
from scipy import signal
from collections import deque
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time


@dataclass
class Peak:
    """Represents a detected peak in the signal"""
    index: int
    value: float
    timestamp: float
    peak_type: Optional[str] = None  # 'P1', 'P2', or 'P3'


@dataclass
class ProcessingConfig:
    """Configuration for signal processing parameters"""
    # Artifact rejection
    artifact_threshold: float = 3.0  # Standard deviations from mean
    
    # Baseline parameters
    baseline_window: int = 200  # samples for baseline calculation
    baseline_percentile: float = 10  # percentile for baseline
    
    # Smoothing parameters
    smoothing_window: int = 5  # moving average window
    use_savgol: bool = True  # Use Savitzky-Golay filter
    savgol_window: int = 11  # must be odd
    savgol_polyorder: int = 3
    
    # Peak detection
    peak_distance: int = 20  # minimum distance between peaks
    peak_prominence: float = 0.1  # minimum prominence
    peak_height_ratio: float = 0.3  # relative to max in window
    
    # Heart rate specific
    max_peak_group_distance: int = 100  # max samples between P1, P2, P3


class SignalBuffer:
    """Manages a rolling buffer of signal data"""
    
    def __init__(self, max_size: int = 1000):
        self.buffer = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self.max_size = max_size
        
    def add(self, value: float, timestamp: float):
        """Add a new sample to the buffer"""
        self.buffer.append(value)
        self.timestamps.append(timestamp)
        
    def get_array(self) -> np.ndarray:
        """Get buffer as numpy array"""
        return np.array(self.buffer)
    
    def get_recent(self, n: int) -> np.ndarray:
        """Get last n samples"""
        return np.array(list(self.buffer)[-n:])
    
    def __len__(self):
        return len(self.buffer)


class SignalProcessor:
    """Handles all signal processing operations"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.baseline_buffer = deque(maxlen=config.baseline_window)
        
    def reject_artifacts(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Detect and remove artifacts based on statistical outliers
        Returns: (cleaned_data, artifact_mask)
        """
        if len(data) < 3:
            return data, np.zeros(len(data), dtype=bool)
        
        # Calculate rolling statistics
        mean = np.mean(data)
        std = np.std(data)
        
        # Identify artifacts
        z_scores = np.abs((data - mean) / (std + 1e-10))
        artifact_mask = z_scores > self.config.artifact_threshold
        
        # Replace artifacts with interpolated values
        cleaned_data = data.copy()
        if np.any(artifact_mask):
            # Simple linear interpolation
            artifact_indices = np.where(artifact_mask)[0]
            for idx in artifact_indices:
                # Find nearest non-artifact neighbors
                left_idx = idx - 1
                right_idx = idx + 1
                
                while left_idx >= 0 and artifact_mask[left_idx]:
                    left_idx -= 1
                while right_idx < len(data) and artifact_mask[right_idx]:
                    right_idx += 1
                
                if left_idx >= 0 and right_idx < len(data):
                    # Linear interpolation
                    cleaned_data[idx] = (data[left_idx] + data[right_idx]) / 2
                elif left_idx >= 0:
                    cleaned_data[idx] = data[left_idx]
                elif right_idx < len(data):
                    cleaned_data[idx] = data[right_idx]
        
        return cleaned_data, artifact_mask
    
    def calculate_baseline(self, data: np.ndarray) -> float:
        """Calculate baseline using percentile method"""
        if len(data) < 10:
            return np.median(data)
        
        return np.percentile(data, self.config.baseline_percentile)
    
    def remove_baseline(self, data: np.ndarray) -> np.ndarray:
        """Remove baseline from signal"""
        baseline = self.calculate_baseline(data)
        return data - baseline
    
    def smooth_signal(self, data: np.ndarray) -> np.ndarray:
        """Apply smoothing to the signal"""
        if len(data) < self.config.smoothing_window:
            return data
        
        if self.config.use_savgol and len(data) >= self.config.savgol_window:
            # Savitzky-Golay filter - better preserves peaks
            smoothed = signal.savgol_filter(
                data, 
                self.config.savgol_window, 
                self.config.savgol_polyorder
            )
        else:
            # Simple moving average
            window = np.ones(self.config.smoothing_window) / self.config.smoothing_window
            smoothed = np.convolve(data, window, mode='same')
        
        return smoothed
    
    def process(self, data: np.ndarray) -> Tuple[np.ndarray, dict]:
        """
        Complete processing pipeline
        Returns: (processed_data, processing_info)
        """
        info = {}
        
        # Step 1: Artifact rejection
        cleaned, artifact_mask = self.reject_artifacts(data)
        info['artifacts_detected'] = np.sum(artifact_mask)
        
        # Step 2: Baseline removal
        baselined = self.remove_baseline(cleaned)
        info['baseline'] = self.calculate_baseline(cleaned)
        
        # Step 3: Smoothing
        smoothed = self.smooth_signal(baselined)
        
        return smoothed, info


class PeakDetector:
    """Detects and classifies peaks in the signal"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.detected_peaks: List[Peak] = []
        
    def detect_peaks(self, data: np.ndarray, timestamps: np.ndarray) -> List[Peak]:
        """Detect all peaks in the signal"""
        if len(data) < self.config.peak_distance:
            return []
        
        # Calculate adaptive threshold
        peak_threshold = np.max(data) * self.config.peak_height_ratio
        
        # Use scipy's find_peaks
        peak_indices, properties = signal.find_peaks(
            data,
            distance=self.config.peak_distance,
            prominence=self.config.peak_prominence,
            height=peak_threshold
        )
        
        peaks = []
        for idx in peak_indices:
            if idx < len(timestamps):
                peaks.append(Peak(
                    index=idx,
                    value=data[idx],
                    timestamp=timestamps[idx]
                ))
        
        return peaks
    
    def classify_peak_triplets(self, peaks: List[Peak]) -> List[Tuple[Peak, Peak, Optional[Peak]]]:
        """
        Group peaks into triplets (P1, P2, P3)
        P1 and P2 should be large, P3 may be smaller or missing
        """
        if len(peaks) < 2:
            return []
        
        triplets = []
        i = 0
        
        while i < len(peaks) - 1:
            p1 = peaks[i]
            
            # Look for P2 within reasonable distance
            for j in range(i + 1, len(peaks)):
                if peaks[j].index - p1.index > self.config.max_peak_group_distance:
                    break
                    
                p2 = peaks[j]
                
                # Look for P3
                p3 = None
                for k in range(j + 1, len(peaks)):
                    if peaks[k].index - p2.index > self.config.max_peak_group_distance:
                        break
                    
                    # P3 might be smaller
                    if peaks[k].value >= p2.value * 0.3:  # At least 30% of P2
                        p3 = peaks[k]
                        break
                
                # Store triplet
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


class HeartRateDetector:
    """Main class for real-time heart rate detection"""
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.signal_buffer = SignalBuffer(max_size=2000)
        self.processor = SignalProcessor(self.config)
        self.peak_detector = PeakDetector(self.config)
        
        # Statistics
        self.total_samples = 0
        self.total_heartbeats = 0
        self.processing_times = []
        
    def process_sample(self, value: float, timestamp: float) -> dict:
        """Process a single new sample"""
        start_time = time.time()
        
        # Add to buffer
        self.signal_buffer.add(value, timestamp)
        self.total_samples += 1
        
        result = {
            'timestamp': timestamp,
            'raw_value': value,
            'processed_value': None,
            'peaks_detected': [],
            'heartbeats': [],
            'processing_info': {}
        }
        
        # Need minimum samples before processing
        if len(self.signal_buffer) < self.config.baseline_window:
            return result
        
        # Get recent data for processing
        data = self.signal_buffer.get_array()
        timestamps = np.array(self.signal_buffer.timestamps)
        
        # Process signal
        processed_data, proc_info = self.processor.process(data)
        result['processed_value'] = processed_data[-1]
        result['processing_info'] = proc_info
        
        # Detect peaks in processed data
        peaks = self.peak_detector.detect_peaks(processed_data, timestamps)
        result['peaks_detected'] = peaks
        
        # Classify into heartbeat triplets
        triplets = self.peak_detector.classify_peak_triplets(peaks)
        result['heartbeats'] = triplets
        self.total_heartbeats = len(triplets)
        
        # Track processing time
        processing_time = time.time() - start_time
        self.processing_times.append(processing_time)
        
        return result
    
    def get_heart_rate(self, window_seconds: float = 10.0) -> Optional[float]:
        """Calculate heart rate from recent detections"""
        if len(self.signal_buffer.timestamps) < 2:
            return None
        
        timestamps = np.array(self.signal_buffer.timestamps)
        current_time = timestamps[-1]
        
        # Count heartbeats in time window
        recent_mask = timestamps >= (current_time - window_seconds)
        # This is simplified - in practice you'd count actual heartbeat triplets
        
        return None  # Implement based on your specific needs
    
    def get_statistics(self) -> dict:
        """Get processing statistics"""
        return {
            'total_samples': self.total_samples,
            'buffer_size': len(self.signal_buffer),
            'total_heartbeats': self.total_heartbeats,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'max_processing_time': np.max(self.processing_times) if self.processing_times else 0
        }


def simulate_realtime_from_csv(csv_file: str, 
                               sample_delay: float = 0.01,
                               plot_update_interval: int = 50):
    """
    Simulate real-time processing from a CSV file
    
    Args:
        csv_file: Path to CSV file with signal data
        sample_delay: Delay between samples (seconds) to simulate real-time
        plot_update_interval: Update plot every N samples
    """
    # Load CSV
    print(f"Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Assume first column is signal data or use column named 'signal'
    if 'signal' in df.columns:
        signal_data = df['signal'].values
    else:
        signal_data = df.iloc[:, 0].values
    
    print(f"Loaded {len(signal_data)} samples")
    
    # Initialize detector
    config = ProcessingConfig(
        artifact_threshold=3.0,
        baseline_window=200,
        smoothing_window=7,
        savgol_window=11,
        peak_distance=20,
        peak_prominence=0.1
    )
    detector = HeartRateDetector(config)
    
    # Storage for visualization
    timestamps = []
    raw_signals = []
    processed_signals = []
    detected_peaks = []
    
    # Set up real-time plotting
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    print("\nStarting real-time processing...")
    print("Press Ctrl+C to stop\n")
    
    try:
        for i, value in enumerate(signal_data):
            timestamp = i * sample_delay
            
            # Process sample
            result = detector.process_sample(value, timestamp)
            
            # Store for plotting
            timestamps.append(timestamp)
            raw_signals.append(value)
            if result['processed_value'] is not None:
                processed_signals.append(result['processed_value'])
            else:
                processed_signals.append(np.nan)
            
            # Update plot periodically
            if i % plot_update_interval == 0 and i > 0:
                ax1.clear()
                ax2.clear()
                
                # Plot raw signal
                ax1.plot(timestamps, raw_signals, 'b-', alpha=0.5, label='Raw Signal')
                ax1.set_ylabel('Amplitude')
                ax1.set_title('Raw Signal with Detected Peaks')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                
                # Plot processed signal
                ax2.plot(timestamps, processed_signals, 'g-', label='Processed Signal')
                
                # Mark detected peaks
                if result['peaks_detected']:
                    peak_times = [p.timestamp for p in result['peaks_detected']]
                    peak_values = [p.value for p in result['peaks_detected']]
                    peak_types = [p.peak_type or 'Unknown' for p in result['peaks_detected']]
                    
                    for pt, pv, ptype in zip(peak_times, peak_values, peak_types):
                        color = 'r' if ptype == 'P1' else 'orange' if ptype == 'P2' else 'yellow'
                        ax2.plot(pt, pv, 'o', color=color, markersize=8, label=ptype)
                
                ax2.set_xlabel('Time (s)')
                ax2.set_ylabel('Amplitude')
                ax2.set_title('Processed Signal with Peak Classification')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.draw()
                plt.pause(0.001)
                
                # Print statistics
                stats = detector.get_statistics()
                print(f"Sample {i}/{len(signal_data)} | "
                      f"Heartbeats: {stats['total_heartbeats']} | "
                      f"Avg proc time: {stats['avg_processing_time']*1000:.2f}ms")
            
            # Simulate real-time delay
            time.sleep(sample_delay)
            
    except KeyboardInterrupt:
        print("\n\nProcessing stopped by user")
    
    # Final statistics
    print("\n" + "="*50)
    print("FINAL STATISTICS")
    print("="*50)
    stats = detector.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    plt.ioff()
    plt.show()
    
    return detector


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        print("Usage: python heart_rate_detector.py <csv_file>")
        print("\nGenerating sample data for demonstration...")
        
        # Generate synthetic heart rate data
        t = np.linspace(0, 10, 1000)
        # Simulate heartbeat with 3 peaks per beat
        heartbeat = np.zeros_like(t)
        for beat_time in np.arange(0, 10, 0.8):  # ~75 bpm
            # P1
            heartbeat += 1.0 * np.exp(-((t - beat_time) ** 2) / 0.001)
            # P2
            heartbeat += 1.2 * np.exp(-((t - (beat_time + 0.15)) ** 2) / 0.001)
            # P3 (smaller, might be noisy)
            heartbeat += 0.6 * np.exp(-((t - (beat_time + 0.25)) ** 2) / 0.001)
        
        # Add noise
        heartbeat += np.random.normal(0, 0.1, len(t))
        
        # Save to CSV
        csv_file = '/home/claude/sample_heartrate.csv'
        pd.DataFrame({'signal': heartbeat}).to_csv(csv_file, index=False)
        print(f"Sample data saved to {csv_file}")
    
    # Run simulation
    detector = simulate_realtime_from_csv(
        csv_file,
        sample_delay=0.01,  # 10ms between samples (100 Hz)
        plot_update_interval=50
    )