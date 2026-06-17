import json
import sys
import os
from datetime import datetime

def generate_report(json_file, output_dir="."):
    with open(json_file, 'r') as f:
        data = json.load(f)

    name = data.get('name', 'Unknown')
    role = data.get('role', 'Unknown')
    department = data.get('department', 'Unknown')

    report = f"""========================================
   EMPLOYEE ONBOARDING SUMMARY
========================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Welcome, {name}!

Role:        {role}
Department:  {department}

Your onboarding has been initiated.
HR will reach out regarding IT setup,
orientation, and team introductions.

We're excited to have you on board!
========================================
"""

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"onboarding_{name.replace(' ', '_')}.txt")
    with open(output_file, 'w') as f:
        f.write(report)

    print(f"Report generated: {output_file}")
    print(report)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <employee_file.json> [output_dir]")
        sys.exit(1)

    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    generate_report(sys.argv[1], out_dir)