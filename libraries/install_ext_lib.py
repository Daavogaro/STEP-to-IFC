import subprocess
import sys
# Enable pip
subprocess.call([sys.executable, "-m", "ensurepip"])
# Upgrade pip to latest version
subprocess.call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
# Packages
packages = ["pandas","csv","ifcopenshell"]

for pack in packages:
    # Install any package
    subprocess.call([sys.executable, "-m", "pip", "install", pack])