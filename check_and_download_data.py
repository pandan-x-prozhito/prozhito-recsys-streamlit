import os
import sys
import urllib.request

data_path = os.getenv("DATA_PATH")
data_download_url = os.getenv("DATA_DOWNLOAD_URL")

if not data_path:
    print("DATA_PATH is not set")
    sys.exit(1)


def download_with_progress(url, path):
    response = urllib.request.urlopen(url)
    total = int(response.info().get("Content-Length").strip())
    block_size = 1024
    wrote = 0
    progress_threshold = 0
    with open(path, "wb") as f:
        while True:
            data = response.read(block_size)
            if not data:
                break
            wrote += len(data)
            f.write(data)
            progress = wrote / total
            if progress >= progress_threshold:
                done = int(50 * progress)
                sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {2*done}%")
                sys.stdout.flush()
                progress_threshold += 0.05
    if total != 0 and wrote != total:
        print(f"\nERROR: Downloaded file size ({wrote}) does not match expected size ({total})")
        sys.exit(1)
    else:
        print("\nDownload completed.")


if not os.path.isfile(data_path):
    if not data_download_url:
        print("DATA_DOWNLOAD_URL is not set")
        sys.exit(1)
    print("File not found. Downloading from DATA_DOWNLOAD_URL...")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    try:
        download_with_progress(data_download_url, data_path)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)
else:
    print("File already exists.")
