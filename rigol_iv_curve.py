import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time
import csv
import sys

# ==== CONFIGURATION ====
V_START = 0.0          # Start voltage (V)
V_STOP = 10.0          # Max voltage limit (V)
V_STEP = 0.1           # Voltage step size (V)
DWELL_TIME = 0.3       # Wait time after setting load before measuring
ESTIMATED_CURRENT = 3  # Estimated max current (Amps)
CSV_FILENAME = "iv_pv_data.csv"

MAX_CURRENT = 5.0      # Safety current limit (Amps)
MAX_POWER = 50.0       # Safety power limit (Watts)
MAX_SWEEP_TIME = 300   # Max sweep time in seconds

print("=== Starting Rigol DL3031 IV/PV sweep script with enhanced safeguards ===")

# ==== VISA SETUP ====
rm = pyvisa.ResourceManager()
usb_instruments = [r for r in rm.list_resources() if 'USB' in r]

if not usb_instruments:
    raise RuntimeError("No USB instruments found. Check connections and drivers.")

resource = usb_instruments[0]
print(f"Connecting to: {resource}")
inst = rm.open_resource(resource)

inst.timeout = 5000
inst.write_termination = '\n'
inst.read_termination = '\n'

print("Instrument ID:", inst.query("*IDN?").strip())

# ==== OPEN CIRCUIT VOLTAGE CHECK ====
print("\nMeasuring open-circuit voltage (load off)...")
inst.write(":INPUT OFF")
time.sleep(1)
voc = float(inst.query(":MEAS:VOLT?"))
print(f"Open-circuit voltage (Voc) = {voc:.2f} V")

# Adjust sweep stop voltage to slightly above Voc, but not exceed configured max
adjusted_v_stop = min(voc + 1.0, V_STOP)
print(f"Adjusted sweep stop voltage = {adjusted_v_stop:.2f} V")

# ==== HELPER FUNCTION: Smooth resistance ramping ====
def ramp_resistance(current_res, target_res, step=0.05, delay=0.1):
    steps = int(abs(target_res - current_res) / step)
    direction = 1 if target_res > current_res else -1
    for i in range(steps):
        intermediate_res = current_res + direction * (i + 1) * step
        inst.write(f":RES {intermediate_res:.3f}")
        time.sleep(delay)

# ==== LOAD SETUP ====
inst.write(":FUNC RES")     # Constant Resistance mode
inst.write(":INPUT ON")     # Turn on load

voltages = []
currents = []
powers = []

print("\nStarting voltage sweep with enhanced safeguards...\n")

start_time = time.time()
current_resistance = 0.0  # track current resistance for ramping

for v_target in np.arange(V_START, adjusted_v_stop + V_STEP, V_STEP):
    elapsed_time = time.time() - start_time
    if elapsed_time > MAX_SWEEP_TIME:
        print(f"⚠️ WARNING: Max sweep time of {MAX_SWEEP_TIME}s exceeded, stopping sweep.")
        break

    print(f"Setting target voltage: {v_target:.2f} V")

    if v_target == 0:
        target_resistance = 0.01  # avoid division by zero
    else:
        target_resistance = v_target / ESTIMATED_CURRENT

    # Ramp resistance smoothly
    ramp_resistance(current_resistance, target_resistance)
    current_resistance = target_resistance

    time.sleep(DWELL_TIME)

    try:
        voltage = float(inst.query(":MEAS:VOLT?"))
        current = float(inst.query(":MEAS:CURR?"))
    except pyvisa.VisaIOError as e:
        print(f"Communication error: {e}")
        inst.write(":INPUT OFF")
        sys.exit(1)

    power = voltage * current

    print(f"Measured V={voltage:.3f} V | I={current:.3f} A | P={power:.3f} W")

    # Safeguards
    if current > MAX_CURRENT:
        print(f"⚠️ WARNING: Current {current:.3f} A exceeded max limit of {MAX_CURRENT} A")
        print("Stopping sweep to protect solar cell and load.")
        break

    if power > MAX_POWER:
        print(f"⚠️ WARNING: Power {power:.2f} W exceeded max limit of {MAX_POWER} W")
        print("Stopping sweep to protect the load.")
        break

    voltages.append(voltage)
    currents.append(current)
    powers.append(power)

print("\nTurning off load input...")
inst.write(":INPUT OFF")

# ==== POST SWEEP ANALYSIS ====
voltages = np.array(voltages)
currents = np.array(currents)
powers = np.array(powers)

if len(powers) == 0:
    print("No data collected! Exiting.")
    sys.exit(1)

max_idx = np.argmax(powers)
v_mpp = voltages[max_idx]
i_mpp = currents[max_idx]
p_mpp = powers[max_idx]

print(f"\n==> Maximum Power Point (MPP): {p_mpp:.2f} W at {v_mpp:.2f} V, {i_mpp:.2f} A")

# ==== PROMPT TO SAVE CSV ====
save_input = input("\nSave I-V/P-V data to CSV? (y/n): ").strip().lower()

if save_input == 'y':
    with open(CSV_FILENAME, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Voltage (V)", "Current (A)", "Power (W)"])
        writer.writerows(zip(voltages, currents, powers))
    print(f"✅ Data saved to {CSV_FILENAME}")
else:
    print("❌ Data not saved.")

# ==== PLOT RESULTS ====
print("Plotting I-V and P-V curves...")
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.plot(voltages, currents, 'b.-')
plt.title('I-V Curve')
plt.xlabel('Voltage (V)')
plt.ylabel('Current (A)')
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(voltages, powers, 'r.-')
plt.plot(v_mpp, p_mpp, 'ko', label=f'MPP: {p_mpp:.2f} W @ {v_mpp:.2f} V')
plt.title('P-V Curve')
plt.xlabel('Voltage (V)')
plt.ylabel('Power (W)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

print("Script finished.")
