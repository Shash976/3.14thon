import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation


file_path = "heartrate_bmp_data.csv"
df = pd.read_csv(file_path)

time_array = df['Time']
current_array = df['Current']


import math

class PeakDetection:
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





# # ---- Streaming + animation ----
# detector = PeakDetection(lag=10)

# raw_data = []
# filtered_data = []
# x_vals = []

# t = 0

# fig, ax = plt.subplots()
# raw_line, = ax.plot([], [], label="Raw signal")
# filt_line, = ax.plot([], [], label="Filtered signal")

# ax.set_xlim(0,  10)
# ax.set_ylim(5.5e-10, 6.5e-10)
# ax.legend()
# ax.set_title("Real-time Signal Filtering")

# def update(frame):
#     global t

#     current = current_array.iloc[t]
#     sample, peak, filt = detector.update(current)

#     raw_data.append(sample)
#     filtered_data.append(filt)
#     x_vals.append(time_array.iloc[t])
#     raw_line.set_data(x_vals[:frame], raw_data[:frame])
#     filt_line.set_data(x_vals[:frame], filtered_data[:frame])
#     print("Frame:", frame, "Sample:", sample, "Filtered:", filt, "Time:", time_array.iloc[t])
#     t+=1
#     return raw_line, filt_line


# ani = animation.FuncAnimation(
#     fig,
#     update,
#     interval=10,
#     blit=True,
#     cache_frame_data=False
# )


# plt.show()
import math
import random
import matplotlib.pyplot as plt
import time

# # ----- PeakDetection (filter-only version) -----
# class PeakDetection:
#     def __init__(self, lag=10):
#         self.lag = lag
#         self.index = 0
#         self.data = [0.0] * lag
#         self.avg = [0.0] * lag

#     def add(self, x):
#         i = self.index % self.lag
#         self.data[i] = x
#         self.avg[i] = sum(self.data) / self.lag
#         self.index += 1
#         return self.avg[i]

#     def get_filtered(self):
#         return self.avg[(self.index - 1) % self.lag]


# ----- Live plot setup -----
plt.ion()  # IMPORTANT: interactive mode ON

fig, ax = plt.subplots()
raw_line, = ax.plot([], [], label="Raw")
filt_line, = ax.plot([], [], label="Filtered")

ax.set_xlim(0, 200)
ax.set_ylim(6e-10, 6.5e-10)
ax.legend()

detector = PeakDetection(lag=10, threshold=10, influence=0.001)


x_vals = []
raw_vals = []
filt_vals = []

t = 0

prev = 0

# ----- Live loop -----
while True:
    # Simulated signal (replace with Arduino later)
    
    raw = current_array.iloc[t]

    sample, peak, filt = detector.update(raw-prev)
    prev = raw

    x_vals.append(time_array.iloc[t])
    raw_vals.append(raw)
    filt_vals.append(filt)

    # Sliding window
    if len(x_vals) > 200:
        x_vals.pop(0)
        raw_vals.pop(0)
        filt_vals.pop(0)

    raw_line.set_data(x_vals, raw_vals)
    filt_line.set_data(x_vals, filt_vals)

    ax.set_xlim(x_vals[0], x_vals[-1])

    fig.canvas.draw()
    fig.canvas.flush_events()

    t += 1
    time.sleep(0.05)
