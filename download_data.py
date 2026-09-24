import os
import subprocess
import time

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# 1. HURDAT2 Hurricane Data
# Contains historical tracks for all Atlantic hurricanes
HURDAT2_URL = "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt"
HURDAT2_FILE = os.path.join(DATA_DIR, "hurdat2.txt")

# 2. NOAA AIS Data (Focused on Hurricane Idalia: Aug 28 - Aug 31, 2023)
# Hurricane Idalia made landfall in Florida on Aug 30, 2023.
# We download a few days of data to see ship behavior before, during, and after.
AIS_DATES = ["2023_08_28", "2023_08_29", "2023_08_30", "2023_08_31"]
AIS_BASE_URL = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2023/"

def download_file(url, dest):
    if os.path.exists(dest):
        print(f"Already exists: {dest}")
        return
    print(f"Downloading {url} to {dest}...")
    try:
        # Using curl.exe for reliable SSL handling on Windows
        subprocess.run(["curl.exe", "-L", "-o", dest, url], check=True)
        print(f"Success: {dest}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {url}: {e}")

if __name__ == "__main__":
    print("--- Starting Phase 1: Data Acquisition ---")
    
    # Download Storm Tracks
    download_file(HURDAT2_URL, HURDAT2_FILE)
    
    # Download AIS Data (approx 350MB per zip file, unzips to larger CSVs)
    for date in AIS_DATES:
        filename = f"AIS_{date}.zip"
        url = f"{AIS_BASE_URL}{filename}"
        dest = os.path.join(DATA_DIR, filename)
        download_file(url, dest)
        
    print("--- Downloads Complete! ---")
    print("Next step: Unzip the AIS data and begin geospatial preprocessing.")
