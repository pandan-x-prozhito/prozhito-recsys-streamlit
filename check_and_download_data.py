import argparse
import os
import sys
import urllib.request


def download_with_progress(url: str, path: str) -> str:
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
        raise ValueError(f"ERROR: Downloaded file size ({wrote}) does not match expected size ({total})")

    return path


def main():
    parser = argparse.ArgumentParser(description="Download a file with progress.")
    parser.add_argument("--data-path", required=True, help="Path to save the downloaded file")
    parser.add_argument("--data-download-url", required=True, help="URL to download the file from")

    args = parser.parse_args()

    data_path = args.data_path
    data_download_url = args.data_download_url

    if os.path.isfile(data_path):
        print("File already exists.")
        sys.exit(0)

    if not data_download_url:
        print("data-download-url is not set")
        sys.exit(1)

    print("File not found. Downloading from data-download-url...")
    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    try:
        download_with_progress(data_download_url, data_path)
    except Exception as e:
        print(f"Download failed: {e}")
        sys.exit(1)
    finally:
        print("Download finished.")


if __name__ == "__main__":
    main()
