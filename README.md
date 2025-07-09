# Solarcell
Python script to generate I-V and P-V curves using the Rigol DL3031 electronic load, with max power point detection.
# Rigol DL3031 IV/PV Curve Tool

This Python script communicates with a **Rigol DL3031** electronic load to:
- Sweep across a voltage range (Constant Resistance mode)
- Measure voltage, current, and power
- Automatically detect the **Maximum Power Point (MPP)**
- Optionally save the I-V and P-V data to CSV
- Plot both I-V and P-V curves using matplotlib

---

## 🔧 Configuration

Edit these values at the top of the script to match your test setup:

```python
V_START = 0.5       # Start voltage
V_STOP = 22.0       # Stop voltage (e.g., solar Voc)
V_STEP = 0.5        # Step size
DWELL_TIME = 0.3    # Delay before measurement (sec)
ESTIMATED_CURRENT = 5  # Used to estimate resistance setting
CSV_FILENAME = "iv_pv_data.csv"
📦 Requirements
Install required packages with:

bash
Copy code
pip install -r requirements.txt
Requires NI-VISA or equivalent installed.
