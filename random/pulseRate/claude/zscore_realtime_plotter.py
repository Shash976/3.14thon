import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import time
import pandas as pd
from zscore_heart_rate_detector import RealTimeHeartRateDetector, DetectionConfig


class ZScoreRealTimePlotter:
    """
    Real-time plotter for z-score peak detection
    Shows scrolling window with raw, filtered, and peaks
    """
    
    def __init__(self, window_size=500, update_interval=10, figsize=(14, 8)):
        self.window_size = window_size
        self.update_interval = update_interval
        
        # Data buffers
        self.time_buffer = deque(maxlen=window_size)
        self.raw_buffer = deque(maxlen=window_size)
        self.stage1_buffer = deque(maxlen=window_size)
        self.stage2_buffer = deque(maxlen=window_size)
        
        # Peak tracking
        self.peak_times = deque(maxlen=window_size)
        self.peak_values = deque(maxlen=window_size)
        
        self.sample_count = 0
        self.peak_count = 0
        
        self.setup_plot(figsize)
    
    def setup_plot(self, figsize):
        """Initialize the plot"""
        plt.ion()
        
        self.fig, self.axes = plt.subplots(3, 1, figsize=figsize,
                                           gridspec_kw={'height_ratios': [2, 2, 1]})
        
        # Top: Raw + Stage 2 filtered
        self.ax_top = self.axes[0]
        self.line_raw, = self.ax_top.plot([], [], 'b-', alpha=0.4, 
                                          linewidth=1, label='Raw Signal')
        self.line_filtered, = self.ax_top.plot([], [], 'r-', 
                                               linewidth=2, label='Filtered (Stage 2)')
        self.scatter_top = self.ax_top.scatter([], [], c='black', s=100, 
                                               marker='o', zorder=5, label='Peaks')
        
        self.ax_top.set_ylabel('Amplitude', fontsize=10)
        self.ax_top.set_title('Z-Score Peak Detection - Real-Time View', 
                              fontsize=12, fontweight='bold')
        self.ax_top.legend(loc='upper left')
        self.ax_top.grid(True, alpha=0.3)
        
        # Middle: Both filter stages
        self.ax_mid = self.axes[1]
        self.line_stage1, = self.ax_mid.plot([], [], 'g-', alpha=0.6,
                                             linewidth=1.5, label='Stage 1 Filter')
        self.line_stage2, = self.ax_mid.plot([], [], 'r-',
                                             linewidth=2, label='Stage 2 Filter')
        self.scatter_mid = self.ax_mid.scatter([], [], c='black', s=100,
                                               marker='o', zorder=5)
        
        self.ax_mid.set_ylabel('Amplitude', fontsize=10)
        self.ax_mid.set_title('Two-Stage Filtering', fontsize=11, fontweight='bold')
        self.ax_mid.legend(loc='upper left')
        self.ax_mid.grid(True, alpha=0.3)
        
        # Bottom: Stats
        self.ax_stats = self.axes[2]
        self.ax_stats.axis('off')
        self.stats_text = self.ax_stats.text(0.05, 0.5, '',
                                            transform=self.ax_stats.transAxes,
                                            fontsize=10, verticalalignment='center',
                                            family='monospace')
        
        plt.tight_layout()
        plt.show(block=False)
    
    def add_sample(self, result: dict):
        """
        Add a sample from detector result
        
        Args:
            result: Dictionary from detector.process_sample()
        """
        self.sample_count += 1
        
        # Add to buffers
        self.time_buffer.append(result['timestamp'])
        self.raw_buffer.append(result['raw_value'])
        self.stage1_buffer.append(result['stage1_filtered'])
        self.stage2_buffer.append(result['stage2_filtered'])
        
        # Track peaks
        if result['is_new_peak']:
            self.peak_times.append(result['timestamp'])
            self.peak_values.append(result['raw_value'])
            self.peak_count += 1
        
        # Update plot periodically
        if self.sample_count % self.update_interval == 0:
            self.update_plot()
    
    def update_plot(self):
        """Redraw the plot"""
        if len(self.time_buffer) < 2:
            return
        
        times = np.array(self.time_buffer)
        raw = np.array(self.raw_buffer)
        stage1 = np.array(self.stage1_buffer)
        stage2 = np.array(self.stage2_buffer)
        
        # Update top plot
        self.line_raw.set_data(times, raw)
        self.line_filtered.set_data(times, stage2)
        
        if len(self.peak_times) > 0:
            # Filter peaks within window
            window_start, window_end = times[0], times[-1]
            visible_peaks = [(t, v) for t, v in zip(self.peak_times, self.peak_values)
                           if window_start <= t <= window_end]
            
            if visible_peaks:
                peak_t, peak_v = zip(*visible_peaks)
                self.scatter_top.set_offsets(np.c_[peak_t, peak_v])
        
        # Set x limits
        if len(times) >= self.window_size:
            xlim = (times[0], times[-1])
        else:
            xlim = (times[0], times[0] + self.window_size * 0.01)
        
        self.ax_top.set_xlim(xlim)
        
        # Auto-scale y
        y_min = np.min(raw)
        y_max = np.max(raw)
        y_range = y_max - y_min
        self.ax_top.set_ylim(y_min - 0.1 * y_range, y_max + 0.2 * y_range)
        
        # Update middle plot
        self.line_stage1.set_data(times, stage1)
        self.line_stage2.set_data(times, stage2)
        
        if len(self.peak_times) > 0 and visible_peaks:
            # Show peaks on filtered signal
            peak_t, _ = zip(*visible_peaks)
            peak_stage2 = [stage2[list(times).index(min(times, key=lambda x: abs(x-t)))] 
                          for t in peak_t]
            self.scatter_mid.set_offsets(np.c_[peak_t, peak_stage2])
        
        self.ax_mid.set_xlim(xlim)
        
        # Auto-scale y for filtered
        y_min_f = min(np.min(stage1), np.min(stage2))
        y_max_f = max(np.max(stage1), np.max(stage2))
        y_range_f = y_max_f - y_min_f
        self.ax_mid.set_ylim(y_min_f - 0.1 * y_range_f, y_max_f + 0.2 * y_range_f)
        
        # Update stats
        time_range = times[-1] - times[0]
        stats = f"Samples: {self.sample_count:>6} | "
        stats += f"Window: {len(self.time_buffer):>4}/{self.window_size} | "
        stats += f"Time: {time_range:>6.2f}s | "
        stats += f"Peaks: {self.peak_count:>4} | "
        stats += f"Peak Rate: {self.peak_count/self.sample_count*100:>5.2f}%"
        
        self.stats_text.set_text(stats)
        
        # Redraw
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
    
    def close(self):
        """Close the plot"""
        plt.close(self.fig)


def demo_realtime_zscore(csv_file, sample_delay=0.01):
    """
    Demo of real-time z-score detection with live plotting
    """
    print("\n" + "="*70)
    print("REAL-TIME Z-SCORE PEAK DETECTION DEMO")
    print("="*70)
    print("Using YOUR detection algorithm with real-time scrolling plot")
    print()
    
    # Load data
    df = pd.read_csv(csv_file)
    if 'signal' in df.columns:
        signal_data = df['signal'].values
    else:
        signal_data = df.iloc[:, 0].values
    
    print(f"Loaded {len(signal_data)} samples")
    
    # Your exact configuration
    config = DetectionConfig(
        stage1_lag=5,
        stage1_threshold=5.0,
        stage1_influence=0.001,
        stage2_lag=15,
        stage2_threshold=5.0,
        stage2_influence=0.001
    )
    
    # Initialize detector and plotter
    detector = RealTimeHeartRateDetector(config)
    plotter = ZScoreRealTimePlotter(
        window_size=500,
        update_interval=10
    )
    
    print("\nProcessing with real-time plot...")
    print("Watch the scrolling window - peaks are marked in black!")
    print("Press Ctrl+C to stop\n")
    
    try:
        for i, value in enumerate(signal_data):
            timestamp = i * 0.01
            
            # Process sample
            result = detector.process_sample(value, timestamp)
            
            # Update plot
            plotter.add_sample(result)
            
            # Simulate real-time
            time.sleep(sample_delay)
            
            if (i + 1) % 500 == 0:
                stats = detector.get_statistics()
                print(f"  Sample {i+1}/{len(signal_data)} | "
                      f"Peaks: {stats['total_peaks']} | "
                      f"Proc time: {stats['avg_processing_time']*1000:.3f}ms")
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        
        stats = detector.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Heartbeat classification
        heartbeats = detector.get_heartbeats()
        print(f"\nHeartbeat triplets detected: {len(heartbeats)}")
        
        print("\nClose the plot window to exit.")
        plt.ioff()
        plt.show()
        
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        plotter.close()
    
    return detector


def compare_with_window_view(csv_file):
    """
    Compare different window sizes for real-time viewing
    """
    window_sizes = [200, 500, 1000]
    
    for window_size in window_sizes:
        print(f"\n{'='*70}")
        print(f"Testing window size: {window_size} samples ({window_size*0.01:.1f} seconds)")
        print('='*70)
        
        df = pd.read_csv(csv_file)
        signal_data = df['signal'].values[:800]  # Use subset for demo
        
        config = DetectionConfig(
            stage1_lag=5, stage1_threshold=5.0, stage1_influence=0.001,
            stage2_lag=15, stage2_threshold=5.0, stage2_influence=0.001
        )
        
        detector = RealTimeHeartRateDetector(config)
        plotter = ZScoreRealTimePlotter(window_size=window_size, update_interval=10)
        
        for i, value in enumerate(signal_data):
            result = detector.process_sample(value, i * 0.01)
            plotter.add_sample(result)
            time.sleep(0.003)
        
        print(f"\nProcessed {len(signal_data)} samples")
        print(f"Peaks detected: {detector.total_peaks}")
        input("Press Enter to try next window size...")
        plotter.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = '/home/claude/realistic_heartrate.csv'
    
    print("\nOptions:")
    print("1. Real-time demo with scrolling plot")
    print("2. Compare window sizes")
    print("3. Fast processing (no delay)")
    
    choice = input("\nSelect option (1-3) or Enter for option 1: ").strip()
    
    if not choice or choice == '1':
        demo_realtime_zscore(csv_file, sample_delay=0.005)
    elif choice == '2':
        compare_with_window_view(csv_file)
    elif choice == '3':
        demo_realtime_zscore(csv_file, sample_delay=0)  # No delay
    else:
        print("Invalid choice")
