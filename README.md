# 🖼 Bing Wallpaper Downloader
**⚠️~~This is a project fully generated by windsurf.~~**

Automatically downloads Bing's daily wallpaper.

## ⚙️ Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ✨ Features
- ~~🌐 Dual-mode operation (Web Scraping + Official API)~~
- 🗂 Smart filename organization with original dates
- 🔍 SHA-256 duplicate detection
- 🌍 Multi-region support (15+ locales)
- ⏳ Historical wallpaper retrieval
- 🗄 SQLite download history tracking

## 🛠️ Usage
```bash
python bing_wallpaper_downloader.py [-f CUSTOM_PATH] [--override]

Options:
-f, --filepath   Set custom save directory (default: wallpapers)
--override       Overwrite existing files (default: skip duplicates)
```

Wallpapers will be saved in the format:
`YYYY-MM-DD_{ImageID}.jpg`

## 💡 Advanced Features

### Hash-based Duplicate Checking
- Uses SHA-256 to detect identical images even with different filenames
- Enabled by default (use `--override` to bypass)

### Download History
- SQLite database tracks all downloads
- View history:
  ```bash
  python bing_wallpaper_downloader.py --history
  ```
- Cleanup old entries:
  ```bash
  # Delete entries older than 30 days
  python bing_wallpaper_downloader.py --cleanup-days -30
  ```

## 🔌 API Features

### API Mode Parameters
```bash
--use-api       # 🔌 Enable third-party API (Always enabled)
--resolution    # 🖼 Set image quality [UHD|1920x1080|1366x768|...] (default: 1920x1080)
--region        # 🌎 Choose content region [zh-CN|en-US|ja-JP|...] (default: en-AU)
--index         # 📆 Historical index (0=today, 1=yesterday, etc) (default: 0)
```

### Usage Examples
```bash
# 🌅 Default web scraping mode
python bing_wallpaper_downloader.py

# 🇨🇳 API mode with 4K Japanese content
python bing_wallpaper_downloader.py --use-api --resolution UHD --region ja-JP

# 🗓 Get yesterday's German wallpaper
python bing_wallpaper_downloader.py --use-api --index 1 --region de-DE

# 🗓 Batch download last 7 days (API mode)
for i in {0..6}; do
  python bing_wallpaper_downloader.py --use-api --index $i
done
```

### Key Improvements
- Filenames now use the wallpaper's original date from API metadata
- Added regional content selection through `--region` parameter
- Supports historical wallpaper retrieval via `--index`

## 🗓 Scheduling (Optional)
Use cron to run daily:
```
0 12 * * * cd /path/to/directory && .venv/bin/python bing_wallpaper_downloader.py
```

## ⏰ Advanced Scheduling

### systemd User Service (Recommended)
```bash
# 📝 Create service and timer files
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/bing-wallpaper.service <<EOF
[Unit]
Description=Bing Wallpaper Downloader

[Service]
Type=oneshot
ExecStart=/home/xtayex/Documents/bing_wallpaper_crawler/.venv/bin/python bing_wallpaper_downloader.py
WorkingDirectory=/home/xtayex/Documents/bing_wallpaper_crawler
EOF

cat > ~/.config/systemd/user/bing-wallpaper.timer <<EOF
[Unit]
Description=Run Bing Wallpaper Downloader every 3 hours

[Timer]
OnBootSec=1min
OnUnitActiveSec=3h

[Install]
WantedBy=timers.target
EOF

# Enable and start
systemctl --user enable --now bing-wallpaper.timer

# Verify
systemctl --user list-timers
```

### Cron Alternative (If Available)
```bash
# 📝 Add to crontab
(crontab -l 2>/dev/null; echo "0 */3 * * * cd /path/to/directory && .venv/bin/python bing_wallpaper_downloader.py >> cron.log 2>&1") | crontab -
```

### View Logs
```bash
journalctl --user -u bing-wallpaper.service -f
```
