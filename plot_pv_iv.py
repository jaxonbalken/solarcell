import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
import tkinter as tk
from tkinter import filedialog

# Prompt for CSV file
def select_csv_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    filepath = filedialog.askopenfilename(
        title="Select a CSV file",
        filetypes=[("CSV Files", "*.csv")]
    )
    return filepath

# Filter outliers using z-score and min thresholds
def filter_outliers(df, z_thresh=3.0, voltage_min=0.05, current_min=0.001):
    df_filtered = df[
        (df["Voltage (V)"] > voltage_min) & 
        (df["Current (A)"] > current_min)
    ]
    df_filtered = df_filtered[(zscore(df_filtered["Power (W)"]) < z_thresh)]
    return df_filtered

# Plot IV and PV curves side-by-side with MPP marker
def plot_filtered_curves(df):
    max_idx = df["Power (W)"].idxmax()
    max_row = df.loc[max_idx]

    plt.figure(figsize=(12, 6))

    # I-V Curve subplot
    plt.subplot(1, 2, 1)
    plt.plot(df["Voltage (V)"], df["Current (A)"], 'bo-', label='I-V Curve')
    plt.plot(max_row["Voltage (V)"], max_row["Current (A)"], 'r*', markersize=15, label='MPP Point')
    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (A)")
    plt.title("Filtered I-V Curve")
    plt.grid(True)
    plt.legend()

    # P-V Curve subplot
    plt.subplot(1, 2, 2)
    plt.plot(df["Voltage (V)"], df["Power (W)"], 'ro-', label='P-V Curve')
    plt.plot(max_row["Voltage (V)"], max_row["Power (W)"], 'k*', markersize=15,
             label=f'MPP: {max_row["Power (W)"]:.2f} W @ {max_row["Voltage (V)"]:.2f} V')
    plt.xlabel("Voltage (V)")
    plt.ylabel("Power (W)")
    plt.title("Filtered Power Curve")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

    print(f"\n✅ MPP: {max_row['Power (W)']:.2f} W at {max_row['Voltage (V)']:.2f} V, {max_row['Current (A)']:.2f} A")

# --- Main Execution ---
csv_path = select_csv_file()
if not csv_path:
    print("❌ No file selected. Exiting.")
else:
    try:
        df = pd.read_csv(csv_path)
        filtered_df = filter_outliers(df)
        plot_filtered_curves(filtered_df)
    except Exception as e:
        print(f"❌ Error: {e}")
