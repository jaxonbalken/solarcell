#!/usr/bin/env python3
# MPPT Sweep Script for Rigol DL3031
import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt
from datetime import datetime
import csv

# === Sweep Configuration ===
R_START = 15000     # Ohms (open circuit)
R_STOP = 0.05       # Ohms (short circuit)
R_STEP = -100       # Decreasing resistance
DWELL = 0.3         # Time between points (seconds)
VOLTAGE_LIMIT = 10  # Max voltage limit for protection

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# === Initialize VISA ===
rm = pyvisa.ResourceManager('/Library/Frameworks/VISA.framework/VISA')
instruments = [r for r in rm.list_resources() if 'USB' in r]
if not instruments:
    raise RuntimeError("No Rigol device found.")
inst = rm.open_resource(instruments[0])
inst.timeout = 5000
inst.write_termination = '\n'
inst.read_termination = '\n'

print("Connected to:", inst.query("*IDN?"))

# === Configure DL3031 ===
inst.write(":FUNC RES")
inst.write(":INPUT ON")
inst.write(f":VOLT:LIM {VOLTAGE_LIMIT:.2f}")

# === Sweep ===
resistances = []
voltages = []
currents = []
powers = []

print("\nStarting MPPT sweep...")

try:
    R = R_START
    while R >= R_STOP:
        inst.write(f":RES {R:.2f}")
        time.sleep(DWELL)

        V = float(inst.query(":MEAS:VOLT?"))
        I = float(inst.query(":MEAS:CURR?"))
        P = V * I

        print(f"R={R:.2f} Ω | V={V:.2f} V | I={I:.2f} A | P={P:.2f} W")

        resistances.append(R)
        voltages.append(V)
        currents.append(I)
        powers.append(P)

        if V < 0.05:  # Assume Isc reached
            print("Voltage near zero — stopping sweep.")
            break

        R += R_STEP

except KeyboardInterrupt:
    print("Interrupted manually.")

finally:
    inst.write(":INPUT OFF")
    print("Load disabled.")

# === Analyze ===
voltages = np.array(voltages)
currents = np.array(currents)
powers = np.array(powers)

max_idx = np.argmax(powers)
v_mpp, i_mpp, p_mpp = voltages[max_idx], currents[max_idx], powers[max_idx]

print(f"\n✅ MPP = {p_mpp:.2f} W @ {v_mpp:.2f} V, {i_mpp:.2f} A")

# === Save CSV ===
filename = f"dl3031_mppt_data_{timestamp}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Resistance (Ohm)", "Voltage (V)", "Current (A)", "Power (W)"])
    writer.writerows(zip(resistances, voltages, currents, powers))
print(f"Data saved to {filename}")

# === Plot ===
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(voltages, currents, 'b.-')
plt.xlabel("Voltage (V)")
plt.ylabel("Current (A)")
plt.title("I-V Curve")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(voltages, powers, 'r.-')
plt.plot(v_mpp, p_mpp, 'ko', label=f'MPP: {p_mpp:.2f} W')
plt.xlabel("Voltage (V)")
plt.ylabel("Power (W)")
plt.title("P-V Curve")
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
