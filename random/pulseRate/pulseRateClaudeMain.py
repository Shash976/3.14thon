"""
Simple example of using the heart rate detector
"""
import numpy as np
import pandas as pd
from pulseRateClaude import HeartRateDetector, ProcessingConfig

# Example 1: Process data sample by sample
def example_basic_usage():
    print("Example 1: Basic Usage\n" + "="*50)
    
    # Create detector with custom configuration
    config = ProcessingConfig(
        artifact_threshold=3.0,      # Remove outliers beyond 3 std devs
        baseline_window=200,          # Use 200 samples for baseline
        smoothing_window=7,           # 7-point smoothing
        peak_distance=20,             # Minimum 20 samples between peaks
        peak_prominence=0.1,          # Minimum peak prominence
    )
    
    detector = HeartRateDetector(config)
    
    # Simulate incoming data
    for i in range(100):
        value = np.random.randn() + np.sin(i/10)  # Dummy data
        timestamp = i * 0.01  # 100 Hz sampling
        
        result = detector.process_sample(value, timestamp)
        
        if i % 20 == 0:
            print(f"Sample {i}: Raw={value:.3f}, "
                  f"Processed={result['processed_value']}, "
                  f"Peaks={len(result['peaks_detected'])}")
    
    stats = detector.get_statistics()
    print(f"\nTotal samples: {stats['total_samples']}")
    print(f"Total heartbeats detected: {stats['total_heartbeats']}")


# Example 2: Process from CSV file
def example_csv_processing(csv_file):
    print("\n\nExample 2: CSV Processing\n" + "="*50)
    
    # Load CSV
    df = pd.read_csv(csv_file)
    signal_data = df['Current'].values
    
    print(f"Loaded {len(signal_data)} samples from {csv_file}")
    
    # Initialize detector
    detector = HeartRateDetector()
    
    # Process all samples
    heartbeat_count = 0
    for i, value in enumerate(signal_data):
        timestamp = i * 0.01
        result = detector.process_sample(value, timestamp)
        
        if result['heartbeats']:
            heartbeat_count = len(result['heartbeats'])
    
    print(f"Processing complete!")
    print(f"Detected {heartbeat_count} heartbeat triplets")
    
    return detector


# Example 3: Custom configuration for noisy signals
def example_noisy_signal():
    print("\n\nExample 3: Noisy Signal Configuration\n" + "="*50)
    
    config = ProcessingConfig(
        artifact_threshold=2.5,       # More aggressive artifact removal
        baseline_window=300,          # Longer baseline window
        use_savgol=True,              # Use Savitzky-Golay filter
        savgol_window=15,             # Larger smoothing window
        savgol_polyorder=3,
        peak_prominence=0.2,          # Higher prominence threshold
    )
    
    detector = HeartRateDetector(config)
    
    # Generate noisy signal with peaks
    t = np.linspace(0, 5, 500)
    signal = np.zeros_like(t)
    
    # Add periodic peaks
    for peak_time in np.arange(0.5, 5, 0.8):
        signal += np.exp(-((t - peak_time) ** 2) / 0.01)
    
    # Add significant noise
    signal += np.random.normal(0, 0.3, len(t))
    
    # Process
    peak_count = 0
    for i, value in enumerate(signal):
        result = detector.process_sample(value, t[i])
        peak_count = len(result['peaks_detected'])
    
    print(f"Detected {peak_count} peaks in noisy signal")
    
    return detector


# Example 4: Monitoring processing performance
def example_performance_monitoring():
    print("\n\nExample 4: Performance Monitoring\n" + "="*50)
    
    detector = HeartRateDetector()
    
    # Process many samples
    for i in range(1000):
        value = np.sin(i / 20) + np.random.randn() * 0.1
        detector.process_sample(value, i * 0.01)
    
    stats = detector.get_statistics()
    
    print(f"Total samples processed: {stats['total_samples']}")
    print(f"Buffer size: {stats['buffer_size']}")
    print(f"Average processing time: {stats['avg_processing_time']*1000:.3f} ms")
    print(f"Max processing time: {stats['max_processing_time']*1000:.3f} ms")


if __name__ == "__main__":
    # Run examples
    #example_basic_usage()
    
    # Uncomment to run other examples
    example_csv_processing('heartrate_bmp_data.csv')
    # example_noisy_signal()
    # example_performance_monitoring()