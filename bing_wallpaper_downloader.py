import argparse
import sqlite3
import hashlib
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import re


def get_bing_wallpaper_url():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        response = requests.get("https://www.bing.com", headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Try multiple detection methods
        preload = (
            soup.find("link", {"id": "preloadBg"})
            or soup.find("meta", {"property": "og:image"})
            or soup.find("div", {"class": "img_cont"})
        )

        if preload:
            image_url = preload.get("href") or preload.get("content")
            if image_url and not image_url.startswith("http"):
                image_url = f"https://www.bing.com{image_url}"
            # Clean URL parameters
            return re.sub(r"&amp;.*", "", image_url) if image_url else None
        return None
    except Exception as e:
        print(f"Error fetching Bing page: {e}")
        return None


def get_bing_wallpaper_via_api(resolution="UHD", mkt="zh-CN", index=0):
    try:
        params = {
            "resolution": resolution,
            "format": "json",
            "index": index,
            "mkt": mkt,
        }
        response = requests.get("https://bing.biturl.top", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "url": data["url"],
            "copyright": data["copyright"],
            "date": datetime.strptime(data["start_date"], "%Y%m%d").strftime(
                "%Y-%m-%d"
            ),
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None


def init_db():
    conn = sqlite3.connect("download_history.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY,
            filepath TEXT UNIQUE,
            sha256 TEXT,
            download_date TEXT,
            source_url TEXT
        )
    """)
    conn.commit()
    return conn


def file_hash(content):
    return hashlib.sha256(content).hexdigest()


def record_download(conn, filepath, sha_hash, url):
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO downloads VALUES (NULL,?,?,?,?)",
        (filepath, sha_hash, datetime.now().isoformat(), url),
    )
    conn.commit()


def download_wallpaper(
    url,
    save_dir="wallpapers",
    override=False,
    conn=None,
    cleanup_days=None,
    wallpaper_date=None,
):
    try:
        os.makedirs(save_dir, exist_ok=True)

        # Get content and calculate hash
        response = requests.get(url, stream=True, timeout=20)
        response.raise_for_status()
        content = b"".join(response.iter_content(1024))
        sha_hash = file_hash(content)

        # Hash-based duplicate check
        if conn and not override:
            c = conn.cursor()
            c.execute("SELECT 1 FROM downloads WHERE sha256=?", (sha_hash,))
            if c.fetchone():
                print(f"Skipping duplicate (SHA256: {sha_hash[:16]}...)")
                return True

        # Create filename
        filename = url.split("id=")[1].split("&")[0]
        date_str = wallpaper_date or datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(save_dir, f"{date_str}_{filename}")

        # Write file
        with open(filepath, "wb") as f:
            f.write(content)

        # Record in history
        if conn:
            record_download(conn, filepath, sha_hash, url)

            # Auto-cleanup old entries
            if cleanup_days:
                cutoff = datetime.now() - timedelta(days=cleanup_days)
                c.execute(
                    "DELETE FROM downloads WHERE download_date < ?",
                    (cutoff.isoformat(),),
                )
                conn.commit()

        print(f"Downloaded: {filepath}")
        return True

    except Exception as e:
        print(f"Download failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bing Wallpaper Downloader")
    parser.add_argument(
        "-f", "--filepath", default="wallpapers", help="Custom save directory"
    )
    parser.add_argument(
        "--override", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument("--history", action="store_true", help="Show download history")
    parser.add_argument(
        "--cleanup-days", type=int, help="Delete history entries older than X days"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Use third-party API instead of web scraping",
    )
    parser.add_argument(
        "--resolution",
        default="UHD",
        help="Image resolution for API mode (default: UHD)",
    )
    parser.add_argument(
        "--region", default="zh-CN", help="Region code for API mode (default: zh-CN)"
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Wallpaper index for API mode (0=today, 1=yesterday, etc)",
    )
    args = parser.parse_args()

    conn = init_db()

    if args.history:
        c = conn.cursor()
        c.execute("SELECT * FROM downloads ORDER BY download_date DESC")
        for row in c.fetchall():
            print(f"[{row[3]}] {row[1]} (SHA256: {row[2][:16]}...)")
        conn.close()
        exit(0)

    if args.use_api:
        api_data = get_bing_wallpaper_via_api(
            resolution=args.resolution, mkt=args.region, index=args.index
        )
        if api_data:
            wallpaper_url = api_data["url"]
            print(
                f"Found {api_data['date']} wallpaper via API: {api_data['copyright']}"
            )
    else:
        wallpaper_url = get_bing_wallpaper_url()

    if wallpaper_url:
        success = download_wallpaper(
            wallpaper_url,
            save_dir=args.filepath,
            override=args.override,
            conn=conn,
            cleanup_days=args.cleanup_days,
            wallpaper_date=api_data["date"] if args.use_api else None,
        )
        conn.close()
        exit(0 if success else 1)
    else:
        print("Failed to find wallpaper URL")
        conn.close()
        exit(1)
