# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Anna's Archive Downloads Fail (DDoS-Guard)

**Symptoms:**
```
⚠ Could not find automatic download link
The partner page is: https://annas-archive.org/slow_download/...
```

**Why it happens:**
- Anna's Archive uses **DDoS-Guard** anti-bot protection
- This is an advanced security system that blocks automated downloads
- Even with browser automation, it's very difficult to bypass

**Solutions:**

1. **Use Alternative Sources (Recommended)**
   - The downloader now prioritizes other sources first
   - Try books from: Gutenberg, Standard Ebooks, Feedbooks
   - These work reliably without anti-bot issues

2. **Manual Download from Anna's Archive**
   - Visit the book URL in your browser
   - Click "Slow Partner Server #1"
   - Wait 3-5 seconds for verification
   - Download button will appear
   - This works because you're a human, not a bot

3. **Search Again and Pick Different Source**
   - Run the search again
   - Look for `[Gutenberg]` or `[Standard Ebooks]` results
   - These are now prioritized and appear first

**Example:**
```bash
python3 downloader.py --book "Life of Pi"

# You'll now see (in order of priority):
[0] Life of Pi - Standard Ebooks  ← Try these first
[1] Life of Pi - Gutenberg         ← Try these first
[2] Life of Pi - Feedbooks          ← Try these first
...
[10] Life of Pi - Anna's Archive    ← Avoid if possible
```

---

### Issue 2: Manga Downloads - "No Files to Pack"

**Symptoms:**
```
- error saving file Black Clover 3 - Chapter 0003.cbz: no files to pack
⚠ No files were downloaded
```

**Why it happens:**
- Network/firewall blocking the manga site
- Chapters don't exist in the requested language
- MangaDex API changes or rate limiting
- Site structure changed

**Solutions:**

1. **Check Network Access**
   ```bash
   # Test if you can access MangaDex
   curl -I https://mangadex.org

   # Or visit in browser:
   # https://mangadex.org
   ```
   - If blocked at work/school, try at home
   - Use mobile hotspot if needed

2. **Try Without Language Filter**
   ```bash
   # Instead of --english-only, try all languages:
   python3 downloader.py --manga --url [URL] --chapters 1-5
   ```
   - This will show if ANY language is available
   - You can then filter manually

3. **Try Different Manga**
   - Search for a different manga from the results
   - Some manga may not be available in English

4. **Check Chapter Availability**
   - The script shows available chapter range
   - Example: "Range: Chapter 1 - 386"
   - Make sure your requested range exists

5. **Try Different Site**
   - If MangaDex fails, try Manganato or Mangakakalot
   - Different sites host different content

**Example:**
```bash
# This might fail if chapters 1-50 don't exist in English:
python3 downloader.py --manga --search "Black Clover" --chapters 1-50 --english-only

# Instead, try:
# 1. Search and select
python3 downloader.py --manga --search "Black Clover"
# 2. Check available chapters shown
# 3. Request smaller range: 1-10
# 4. Try without --english-only first
```

---

### Issue 3: Book Search Timeouts

**Symptoms:**
```
Warning: Gutenberg search failed: Read timed out. (read timeout=30)
```

**Why it happens:**
- Slow network connection
- API server is slow to respond
- Network firewall delaying requests

**Solutions:**

1. **Already Fixed in v2.3!**
   - Timeout increased from 10s to 30s
   - Retry logic added (3 attempts)
   - Should work much better now

2. **If Still Timing Out:**
   - Check your internet connection
   - Try on a different network
   - Some sources may be temporarily down

---

### Issue 4: Internet Archive - 401 Unauthorized

**Symptoms:**
```
✗ 401 Unauthorized - Internet Archive requires authentication
This book may require borrowing/lending on archive.org
```

**Why it happens:**
- Some books require "borrowing" (like a library)
- Not all books are freely downloadable
- Network firewall blocking archive.org

**Solutions:**

1. **Use Alternative Sources**
   - Select a different result from the search
   - Try Gutenberg, Standard Ebooks, or Feedbooks
   - These have direct downloads without borrowing

2. **Manual Borrow**
   - Visit the book URL in browser
   - Create a free archive.org account
   - "Borrow" the book for 14 days
   - Download while borrowed

---

## Network Recommendations

### 🏢 Work/School Networks
**What Works:**
- ✅ Gutenberg (usually)
- ✅ Standard Ebooks (usually)
- ✅ Feedbooks (sometimes)

**What Doesn't Work:**
- ❌ Anna's Archive (blocked)
- ❌ Internet Archive (often blocked)
- ❌ Manga sites (blocked)

**Recommendation:** Don't use this tool at work. Wait until you're home.

### 🏠 Home Networks
**What Works:**
- ✅ Everything!
- ✅ All book sources
- ✅ Manga downloads
- ✅ Anna's Archive (with manual steps)

**Recommendation:** This is the ideal environment for the tool.

### 📱 Mobile Hotspot
**What Works:**
- ✅ Usually works like home network
- ✅ Good alternative if home internet has issues

**Recommendation:** Use this if you need to download urgently and home internet isn't available.

---

## Quick Diagnosis

### Books Not Downloading?
1. Is the error "Anna's Archive" or "DDoS-Guard"? → Use different source
2. Is the error "401 Unauthorized"? → Use Gutenberg/Standard Ebooks instead
3. Is the error "timeout"? → Check your internet connection
4. No results found? → Try different search terms

### Manga Not Downloading?
1. Error "no files to pack"? → Check network access to manga site
2. Error "0 results"? → Sites may be blocked, try at home
3. Downloaded 0 files? → Try without --english-only
4. Wrong language? → Use --language en explicitly

---

## Getting Help

### Before Asking for Help:
1. **Check which source failed** (Gutenberg, Anna's Archive, etc.)
2. **Try alternative sources** from search results
3. **Check network environment** (work vs home)
4. **Read error messages carefully** - they usually explain the issue

### When Reporting Issues:
Include:
- Book/manga title you searched for
- Source that failed (e.g., "Anna's Archive", "Gutenberg")
- Full error message
- Network type (work, school, home)
- Command you ran

**Example good issue report:**
```
Title: Life of Pi
Source: Anna's Archive
Error: "Could not find automatic download link"
Network: Home WiFi
Command: python3 downloader.py --book "Life of Pi"
Selected: Option [0] Anna's Archive
```

---

## Updates

### Update manga-downloader binary
```bash
cd BookDownloader
rm manga-downloader
curl -L -o manga-downloader.tar.gz \
  https://github.com/elboletaire/manga-downloader/releases/latest/download/manga-downloader-linux-amd64.tar.gz
tar -xzf manga-downloader.tar.gz
rm manga-downloader.tar.gz
chmod +x manga-downloader
```

### Update Python dependencies
```bash
pip install -r requirements.txt --upgrade
```

---

## Summary

**For Books:**
- ✅ Prefer Gutenberg, Standard Ebooks, Feedbooks
- ⚠️ Avoid Anna's Archive (unless you can download manually)
- ⚠️ Internet Archive may require borrowing

**For Manga:**
- ✅ Works best at home
- ⚠️ Blocked at work/school
- ✅ Always use --english-only or --language en
- ⚠️ Check chapter availability before downloading

**General:**
- ✅ Use at home for best results
- ✅ Read error messages - they're helpful
- ✅ Try alternative sources when one fails
- ✅ Check IMPROVEMENTS.md for technical details
