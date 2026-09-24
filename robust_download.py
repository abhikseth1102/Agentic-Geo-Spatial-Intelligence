import os
import time
import requests

url = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2023/AIS_2023_08_28.zip"
file_path = os.path.join("data", "AIS_2023_08_28.zip")

def download_with_resume(url, filepath):
    headers = {}
    if os.path.exists(filepath):
        downloaded = os.path.getsize(filepath)
        headers['Range'] = f"bytes={downloaded}-"
        mode = 'ab'
        print(f"Resuming download from {downloaded} bytes...")
    else:
        downloaded = 0
        mode = 'wb'
        print("Starting new download...")

    response = requests.get(url, headers=headers, stream=True, timeout=10)
    
    if response.status_code == 416:
        print("File is already fully downloaded.")
        return True
    
    if response.status_code not in [200, 206]:
        print(f"Failed to connect. Status: {response.status_code}")
        return False

    total_length = response.headers.get('content-length')
    if total_length is None:
        total_size = downloaded
    else:
        total_size = downloaded + int(total_length)

    print(f"Total target size: {total_size / (1024*1024):.2f} MB")

    try:
        with open(filepath, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
    except Exception as e:
        print(f"\nConnection dropped: {e}")
        return False

    if downloaded >= total_size:
        print("Download complete!")
        return True
    return False

def main():
    os.makedirs("data", exist_ok=True)
    success = False
    retries = 0
    max_retries = 50
    
    print("Starting robust download to bypass NOAA rate limits...")
    while not success and retries < max_retries:
        try:
            success = download_with_resume(url, file_path)
        except Exception as e:
            print(f"Unexpected error: {e}")
            success = False
            
        if not success:
            retries += 1
            wait = min(retries * 2, 10)
            print(f"Retrying in {wait} seconds (Attempt {retries}/{max_retries})...")
            time.sleep(wait)

if __name__ == "__main__":
    main()
