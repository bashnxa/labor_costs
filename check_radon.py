import subprocess  # nosec B404
import sys

BAD_GRADES = {"D", "E", "F"}

# nosec B603 B607
result = subprocess.run(
    ["radon", "cc", ".", "-s"], stdout=subprocess.PIPE, text=True
)  # nosec B603 B607
output = result.stdout

bad = False
for line in output.splitlines():
    if line.strip().startswith(("F", "M", "C")):
        parts = line.strip().split()
        if parts and parts[-1] in BAD_GRADES:
            bad = True
            print("❌", line)

if bad:
    print("\nRadon check failed: found complex code (D/E/F).")
    sys.exit(1)
else:
    print("Radon check passed.")
