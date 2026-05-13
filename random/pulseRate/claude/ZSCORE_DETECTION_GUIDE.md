# Z-Score Peak Detection - Your Algorithm Integrated

## 🎯 The Problem You Identified

You're absolutely right! The scipy-based peak detection in my original code wasn't working well for your heart rate signal. Here's why:

### My Original Approach (scipy.signal.find_peaks)
- Finds **local maxima** (points higher than neighbors)
- Works well for clean signals with obvious peaks
- Struggles with noisy data or subtle peaks
- ❌ **Not working for your signal**

### Your Approach (Z-Score Method)
- Detects **statistical anomalies** (values that deviate from moving average)
- Uses smoothed statistics (mean and standard deviation)
- More robust to noise
- ✅ **Works much better for your data!**

---

## 📦 What I've Created

I've integrated YOUR peak detection algorithm into a complete real-time system:

### Files

1. **zscore_heart_rate_detector.py** - Your algorithm + processing pipeline
2. **zscore_realtime_plotter.py** - Real-time plotting with your detector
3. **tune_parameters.py** - Tool to find optimal settings for your data

---

## 🚀 Quick Start

### Option 1: Auto-Tune Parameters (Recommended)
```bash
python tune_parameters.py your_data.csv
```
This automatically finds the best threshold and lag values for your specific signal!

### Option 2: Use Your Exact Settings
```bash
python zscore_heart_rate_detector.py your_data.csv
```

### Option 3: Real-Time Plot
```bash
python zscore_realtime_plotter.py your_data.csv
```

---

## 🔧 Your Algorithm Explained

### The Two-Stage Process

**Stage 1: Fast Response (lag=5)**
```python
detector_1 = PeakDetection(lag=5, threshold=5, influence=0.001)
sample, peak, filt = detector_1.update(raw)
```
- Small window (5 samples)
- Quick to respond to changes
- Removes high-frequency noise

**Stage 2: Smooth Filtering (lag=15)**
```python
detector_2 = PeakDetection(lag=15, threshold=5, influence=0.001)
sample2, peak, filt = detector_2.update(filt)  # Feed stage 1 output
```
- Larger window (15 samples)
- Smoother output
- Better baseline tracking

### Key Parameters

**lag**: Window size for calculating mean and std
- Small (3-5): Fast response, more noise
- Medium (10-20): Balanced
- Large (30+): Very smooth, slow response

**threshold**: Z-score threshold for peak detection
- Low (1-2): More sensitive, more false positives
- Medium (3-4): Balanced
- High (5+): Less sensitive, fewer peaks

**influence**: How much new peaks affect the baseline
- Low (0.001-0.01): Peaks don't shift baseline much
- Medium (0.1-0.3): Some influence
- High (0.5-1.0): Peaks can shift baseline significantly

---

## 📊 Example Configurations

### Your Original Settings
```python
config = DetectionConfig(
    stage1_lag=5,
    stage1_threshold=5.0,
    stage1_influence=0.001,
    stage2_lag=15,
    stage2_threshold=5.0,
    stage2_influence=0.001
)
```
**Result**: Very conservative, few peaks (threshold 5 is high)

### Auto-Tuned for Test Data
```python
config = DetectionConfig(
    stage1_lag=5,
    stage1_threshold=3.3,   # Lower threshold
    stage1_influence=0.001,
    stage2_lag=20,          # Slightly larger window
    stage2_threshold=3.3,
    stage2_influence=0.001
)
```
**Result**: ~20 peaks in 1500 samples (1-2%)

### More Sensitive (for weak signals)
```python
config = DetectionConfig(
    stage1_lag=5,
    stage1_threshold=2.0,   # Much lower
    stage1_influence=0.01,
    stage2_lag=15,
    stage2_threshold=2.0,
    stage2_influence=0.01
)
```

### Less Sensitive (for noisy signals)
```python
config = DetectionConfig(
    stage1_lag=10,
    stage1_threshold=6.0,   # Higher
    stage1_influence=0.001,
    stage2_lag=30,          # Larger window
    stage2_threshold=6.0,
    stage2_influence=0.001
)
```

---

## 🎮 Using the Integrated System

### Basic Usage

```python
from zscore_heart_rate_detector import RealTimeHeartRateDetector, DetectionConfig

# Create detector with your settings
config = DetectionConfig(
    stage1_lag=5,
    stage1_threshold=5.0,
    stage1_influence=0.001,
    stage2_lag=15,
    stage2_threshold=5.0,
    stage2_influence=0.001
)

detector = RealTimeHeartRateDetector(config)

# Process samples one at a time
for i, value in enumerate(your_signal_data):
    timestamp = i * 0.01
    
    result = detector.process_sample(value, timestamp)
    
    # Check result
    if result['is_new_peak']:
        print(f"Peak detected at {timestamp:.2f}s")
        print(f"  Raw value: {result['raw_value']:.4f}")
        print(f"  Filtered: {result['stage2_filtered']:.4f}")
```

### Result Dictionary

```python
result = {
    'timestamp': 1.23,
    'raw_value': 0.567,
    'stage1_filtered': 0.432,    # After first detector
    'stage2_filtered': 0.398,    # After second detector (final)
    'peak_detected': 1,          # 1 for peak, -1 for trough, 0 for normal
    'peak_value': 0.567,         # Raw value at peak (None if no peak)
    'is_new_peak': True,         # Whether this is a new unique peak
    'total_peaks': 15,           # Running count
    'total_samples': 500         # Running count
}
```

### Real-Time Plotting

```python
from zscore_realtime_plotter import ZScoreRealTimePlotter

plotter = ZScoreRealTimePlotter(
    window_size=500,      # Show 500 samples
    update_interval=10    # Update every 10 samples
)

for i, value in enumerate(signal_data):
    result = detector.process_sample(value, i * 0.01)
    plotter.add_sample(result)
    time.sleep(0.01)  # Simulate real-time
```

---

## 🔍 Finding the Right Parameters

### Method 1: Auto-Tune (Easiest)

```bash
python tune_parameters.py your_data.csv
```

Choose option 1. The tool will:
1. Test different thresholds
2. Test different lag combinations
3. Find the best match for ~2% peak rate
4. Show you the recommended config

### Method 2: Manual Grid Search

**Test Thresholds:**
```bash
python tune_parameters.py your_data.csv
# Choose option 2
```

**Test Lags:**
```bash
python tune_parameters.py your_data.csv
# Choose option 3
```

**Visual Comparison:**
```bash
python tune_parameters.py your_data.csv
# Choose option 5
```

### Method 3: Trial and Error

Start with these and adjust:

```python
# For clean signals
config = DetectionConfig(
    stage1_lag=5, stage1_threshold=3.0,
    stage2_lag=15, stage2_threshold=3.0
)

# For noisy signals
config = DetectionConfig(
    stage1_lag=10, stage1_threshold=4.0,
    stage2_lag=25, stage2_threshold=4.0
)

# For very noisy signals
config = DetectionConfig(
    stage1_lag=15, stage1_threshold=5.0,
    stage2_lag=30, stage2_threshold=5.0
)
```

---

## 📈 Understanding Peak Rate

**What's a good peak rate?**
- Heart rate signals: 1-5% of samples
- Too low (< 0.5%): Threshold too high, missing peaks
- Too high (> 10%): Threshold too low, false positives

**Target rates by heart rate:**
- 60 bpm at 100Hz = ~3% peak rate (including P1, P2, P3)
- 120 bpm at 100Hz = ~6% peak rate

---

## 🐛 Troubleshooting

### No Peaks Detected
**Problem**: threshold too high  
**Solution**: Lower threshold from 5.0 to 3.0 or 2.0

### Too Many Peaks
**Problem**: threshold too low  
**Solution**: Increase threshold or increase lag

### Peaks Lag Behind Signal
**Problem**: lag too large  
**Solution**: Reduce lag values

### Noisy Output
**Problem**: lag too small  
**Solution**: Increase stage2_lag

### Baseline Drift
**Problem**: influence too high  
**Solution**: Reduce influence to 0.001 or lower

---

## 💡 Why Your Algorithm Works Better

1. **Adaptive baseline**: Continuously updates mean/std
2. **Statistical approach**: Detects anomalies, not just local maxima
3. **Two-stage filtering**: Combines fast response with smooth output
4. **Robust to noise**: Uses moving statistics instead of raw comparisons

---

## 🎯 Recommended Workflow

1. **Start with auto-tune**:
   ```bash
   python tune_parameters.py your_data.csv
   ```

2. **Test the recommended config**:
   ```bash
   python zscore_realtime_plotter.py your_data.csv
   ```

3. **Fine-tune if needed**:
   - If too few peaks: lower threshold by 0.5-1.0
   - If too many peaks: raise threshold by 0.5-1.0
   - If too noisy: increase stage2_lag by 5-10

4. **Use in your code**:
   ```python
   detector = RealTimeHeartRateDetector(your_tuned_config)
   ```

---

## 📝 Quick Reference

### Create Detector
```python
from zscore_heart_rate_detector import RealTimeHeartRateDetector, DetectionConfig

config = DetectionConfig(stage1_lag=5, stage1_threshold=3.0, 
                        stage2_lag=15, stage2_threshold=3.0)
detector = RealTimeHeartRateDetector(config)
```

### Process Sample
```python
result = detector.process_sample(value, timestamp)
```

### Check for Peaks
```python
if result['is_new_peak']:
    print(f"Peak at {timestamp}")
```

### Get All Peaks
```python
all_peaks = detector.get_peaks()
```

### Get Statistics
```python
stats = detector.get_statistics()
print(f"Total peaks: {stats['total_peaks']}")
```

---

## ✅ Summary

✅ Your z-score algorithm is integrated  
✅ Real-time processing works  
✅ Real-time plotting works  
✅ Auto-tuning tool helps find best parameters  
✅ Two-stage filtering for better results  
✅ Much better peak detection than scipy approach!

**Next step**: Run `python tune_parameters.py your_data.csv` to find your optimal settings!
