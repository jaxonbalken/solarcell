import pyvisa

def list_visa_resources():
    rm = pyvisa.ResourceManager('/Library/Frameworks/VISA.framework/VISA')
    resources = rm.list_resources()
    if resources:
        print("Available VISA resources:")
        for r in resources:
            print(f"  - {r}")
    else:
        print("No VISA resources found. Check your instrument connection and drivers.")

if __name__ == "__main__":
    list_visa_resources()
