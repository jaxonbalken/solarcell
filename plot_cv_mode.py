import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
import csv

# ==== FILE SELECTION ====
root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename(
    title="Select IV/PV CSV file",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if not file_path:
    print("❌ No file selected. Exiting.")
    exit()

# ==== DATA LOADING ====
voltages = []
currents = []
powers = []

with open(file_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            v = float(row["Voltage (V)"])
            i = float(row["Current (A)"])
            p = float(row["Power (W)"])
            if v > 0 and i > 0 and p > 0:  # Filter out 0s and negatives
                voltages.append(v)
                currents.append(i)
                powers.append(p)
        except ValueError:
            continue

if not voltages:
    print("⚠️ No valid data after filtering. Check CSV content.")
    exit()

voltages = np.array(voltages)
currents = np.array(currents)
powers = np.array(powers)

# ==== MAX POWER POINT ====
max_idx = np.argmax(powers)
v_mpp = voltages[max_idx]
i_mpp = currents[max_idx]
p_mpp = powers[max_idx]

# ==== PLOTTING ====
plt.figure(figsize=(10, 6))

plt.plot(voltages, currents, 'b.-', label='I-V Curve')
plt.plot(voltages, powers, 'r.-', label='P-V Curve')
plt.plot(v_mpp, p_mpp, 'ko', label=f'MPP: {p_mpp:.2f} W @ {v_mpp:.2f} V')
plt.plot([0, v_mpp], [p_mpp, p_mpp], 'k--', alpha=0.6)
plt.plot([v_mpp, v_mpp], [0, p_mpp], 'k--', alpha=0.6)
plt.title("I-V and P-V Curves (CV)")
plt.xlabel("Voltage (V)")
plt.ylabel("Current (A) / Power (W)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
