# Solarcell
Python script to generate I-V and P-V curves using the Rigol DL3031 electronic load, with max power point detection.
# Rigol DL3031 IV/PV Curve Tool

This Python script communicates with a **Rigol DL3031** electronic load to:
- Sweep input voltage
- Measure current and power at each step
- Plot the I-V and P-V curves
- Find and report the **Maximum Power Point (MPP)**

## 📸 Example Use Case
Ideal for solar cell characterization or power supply testing.

---

## 📦 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
