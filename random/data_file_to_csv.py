import os
# from zipfile import Path
# import pandas as pd

INPUT_FOLDER = r"C:\\Users\\shash\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot"  # where to find CSV files
OUTPUT_FOLDER = r"C:\\Users\\shash\OneDrive - purdue.edu\\Pulse Rate Wearable Sensor\\Data for your final plot\\converted"  # where to save plots
os.chdir(INPUT_FOLDER)  # change working directory to data folder for easier file handling

# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# def parse_data_file(filepath):
#     with open(filepath, 'r') as f:
#         lines = f.readlines()

#     # Find where data starts
#     start_idx = None
#     for i, line in enumerate(lines):
#         if "***End_of_Header***" in line:
#             start_idx = i + 1
#             break

#     if start_idx is None:
#         print(f"Header not found in {filepath}")
#         return None

#     # Extract data lines
#     data_lines = lines[start_idx:]

#     cleaned_data = []
#     for line in data_lines:
#         parts = line.strip().split()
#         if len(parts) >= 2:
#             try:
#                 time = float(parts[0])
#                 value = float(parts[1])
#                 cleaned_data.append([time, value])
#             except:
#                 continue  # skip bad rows

#     if not cleaned_data:
#         return None

#     df = pd.DataFrame(cleaned_data, columns=["Time", "Value"])
#     return df


# def infer_type(filename):
#     name = filename.lower()
#     if "volt" in name or "vt" in name:
#         return "Voltage"
#     elif "curr" in name or "it" in name:
#         return "Current"
#     else:
#         return "Unknown"


# def extract_frequency(filename):
#     # Example: "10Hz_Vt.data" → 10
#     import re
#     match = re.search(r'(\d+\.?\d*)\s*hz', filename.lower())
#     return match.group(1) if match else "unknown"


# for file in os.listdir(INPUT_FOLDER):
#     if file.endswith(".data"):
#         path = os.path.join(INPUT_FOLDER, file)

#         df = parse_data_file(path)
#         if df is None:
#             continue

#         data_type = infer_type(file)
#         freq = extract_frequency(file)

#         # Rename column for clarity
#         df.rename(columns={"Value": data_type}, inplace=True)

#         # Output filenames
#         base_name = os.path.splitext(file)[0]
#         csv_path = os.path.join(OUTPUT_FOLDER, base_name + ".csv")
#         xlsx_path = os.path.join(OUTPUT_FOLDER, base_name + ".xlsx")

#         # Save
#         df.to_csv(csv_path, index=False)
#         df.to_excel(xlsx_path, index=False)

#         print(f"Converted: {file} → CSV + Excel")

import pandas as pd
import matplotlib.pyplot as plt

# Path to your data file
data_file = r"C:\Users\shash\OneDrive - purdue.edu\Pulse Rate Wearable Sensor\Data for your final plot\heartrate.bmp.data"  # change this to your actual filename

# Read the data file, skipping the header
with open(data_file, 'r') as f:
    lines = f.readlines()

# Find where the actual data starts (after ***End_of_Header***)
for i, line in enumerate(lines):
    if '***End_of_Header***' in line:
        start_idx = i + 2  # skip header line + column names
        break

# Extract data lines
data_lines = lines[start_idx:]
data = [line.strip().split() for line in data_lines if line.strip()]

# Convert to DataFrame
df = pd.DataFrame(data, columns=['Time', 'Current'], dtype=float)

# Save as CSV and Excel
df.to_csv('output.csv', index=False)
df.to_excel('output.xlsx', index=False)

# Plot first 10,000 values
df.iloc[4000:8000].plot(x='Time', y='Current', title='Current vs Time', figsize=(10, 6))
plt.xlabel('Time (s)')
plt.ylabel('Current (A)')
plt.grid(True)
plt.savefig('output.png')