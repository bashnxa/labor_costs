import re
import subprocess  # nosec B404
import sys

BAD_GRADES = {"C", "D", "E", "F"}

# nosec B603 B607
result = subprocess.run(
    ["radon", "cc", ".", "-s"],
    capture_output=True,
    text=True,
)  # nosec B603 B607

if result.returncode != 0:
    print("❌ Radon check failed: error executing Radon.")
    sys.exit(1)

output = result.stdout.strip()

if not output:
    print("❌ Radon check failed: no analyzable code found.")
    sys.exit(1)

bad = False
print("\n[radon] Analyzing complexity...\n")

RADON_PATTERN = re.compile(
    r"^(?P<type>[FMC])\s+"
    r"(?P<name>.*?)\s+"
    r"(?P<lineno>\d+):\d+\s+"
    r"(?P<grade>[A-F])\s+"
    r"(?P<complexity>\d+)"
)

for line in output.splitlines():
    match = RADON_PATTERN.match(line.strip())
    if match:
        grade = match.group("grade")
        if grade in BAD_GRADES:
            bad = True
            print("❌", line)

if bad:
    print("\n❌ Radon check failed: complexity found in BAD_GRADES set.")
    sys.exit(1)
else:
    print("\nRadon check passed.")
