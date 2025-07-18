import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time
import csv
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# ==== CONFIGURATION ====
V_START = 0.0         # Start voltage (V)
V_STOP = 10.0           # Max sweep voltage (V)
V_STEP = 0.1            # Voltage step size (V)
DWELL_TIME = 0.3        # Wait time per step (seconds)
ESTIMATED_CURRENT = 5.0 # Estimated max current (A)

# === SAFETY LIMITS ===
MAX_CURRENT = 20.0       # Max current limit (A)
MAX_POWER = 50.0        # Max power limit (W)
MIN_RESISTANCE = 0.08   # Ohms, minimum resistance command
MAX_RESISTANCE = 15000  # Ohms, maximum resistance command (15 kΩ)

# === RESISTANCE RANGE LIMITS (from Rigol manual) ===
LOW_RANGE_MIN = 0.08    # Ohms
LOW_RANGE_MAX = 15.0    # Ohms
HIGH_RANGE_MIN = 2.0    # Ohms
HIGH_RANGE_MAX = 15000  # Ohms (15 kΩ)

# === FILE NAMING ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=== Starting Rigol DL3031 IV/PV sweep script with enhanced safeguards ===")

# ==== VISA SETUP ====
rm = pyvisa.ResourceManager('/Library/Frameworks/VISA.framework/VISA')
usb_instruments = [r for r in rm.list_resources() if 'USB' in r]

if not usb_instruments:
    raise RuntimeError("No USB instruments found. Check connections and drivers.")

resource = usb_instruments[0]
print(f"✅ Connecting to: {resource}")
inst = rm.open_resource(resource)

inst.timeout = 5000
inst.write_termination = '\n'
inst.read_termination = '\n'

# ==== VERIFY COMMUNICATION ====
print("🆔 Instrument ID:", inst.query("*IDN?"))

# ==== LOAD SETUP ====
inst.write(":FUNC RES")          # Set function mode to Constant Resistance (CR)
inst.write(":INPUT ON")          # Turn on the electronic load
inst.write(f":VOLT:LIM {V_STOP:.2f}")    # Set voltage limit
inst.write(f":CURR:LIM {MAX_CURRENT:.2f}")  # Set current limit

voltages = []
currents = []
powers = []

try:
    print("\n⚡ Starting sweep...")
    for v_target in np.arange(V_START, V_STOP + V_STEP, V_STEP):
        resistance = v_target / ESTIMATED_CURRENT if v_target > 0 else MIN_RESISTANCE

        # Clamp resistance within allowed bounds
        if resistance < MIN_RESISTANCE:
            resistance = MIN_RESISTANCE
        elif resistance > MAX_RESISTANCE:
            resistance = MAX_RESISTANCE

        inst.write(":RANGE LOW")

        # Set resistance
        inst.write(f":RES {resistance:.3f}")

        time.sleep(DWELL_TIME)

        voltage = float(inst.query(":MEAS:VOLT?"))
        current = float(inst.query(":MEAS:CURR?"))
        power = voltage * current

        print(f"📍 V={voltage:.2f} V | I={current:.2f} A | P={power:.2f} W")

        if current > MAX_CURRENT:
            print(f"🚨 Current limit exceeded! ({current:.2f} A > {MAX_CURRENT} A). Stopping sweep.")
            break

        if power > MAX_POWER:
            print(f"🚨 Power limit exceeded! ({power:.2f} W > {MAX_POWER} W). Stopping sweep.")
            break

        voltages.append(voltage)
        currents.append(current)
        powers.append(power)

except KeyboardInterrupt:
    print("\n⛔ Sweep manually interrupted.")

finally:
    inst.write(":INPUT OFF")
    print("\n🛑 Load disabled. Sweep complete or aborted.")

# ==== ANALYSIS ====
if voltages:
    voltages = np.array(voltages)
    currents = np.array(currents)
    powers = np.array(powers)

    max_idx = np.argmax(powers)
    v_mpp = voltages[max_idx]
    i_mpp = currents[max_idx]
    p_mpp = powers[max_idx]

    print(f"\n✅ Maximum Power Point (MPP): {p_mpp:.2f} W at {v_mpp:.2f} V, {i_mpp:.2f} A")

    # ==== ASK TO SAVE CSV WITH FILE DIALOG ====
    save_input = input("\n💾 Would you like to save the I-V/P-V data to CSV? (y/n): ").strip().lower()
    if save_input == 'y':
        # Tkinter file save dialog
        root = tk.Tk()
        root.withdraw()  # Hide main window
        default_filename = f"iv_pv_data_{timestamp}.csv"
        file_path = filedialog.asksaveasfilename(
            title="Save CSV file",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Voltage (V)", "Current (A)", "Power (W)"])
                writer.writerows(zip(voltages, currents, powers))
            print(f"📁 Data saved to {file_path}")
        else:
            print("❌ Save cancelled. CSV not saved.")
    else:
        print("❌ CSV not saved.")

    # ==== PLOTTING ====
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(voltages, currents, 'b.-')
    plt.title(f'I-V Curve ({timestamp})')
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (A)')
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(voltages, powers, 'r.-')
    plt.plot(v_mpp, p_mpp, 'ko', label=f'MPP: {p_mpp:.2f}W @ {v_mpp:.2f}V')
    plt.title(f'P-V Curve ({timestamp})')
    plt.xlabel('Voltage (V)')
    plt.ylabel('Power (W)')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()

else:
    print("⚠️ No data collected. Check sweep limits and setup.")
