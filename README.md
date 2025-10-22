# BookDownloader

A unified tool for downloading books and manga legally from free sources.

## ⚠️ Network Requirements

| Feature | Work/School | Home | Mobile Hotspot |
|---------|-------------|------|----------------|
| **Manga Search** | ❌ Blocked | ✅ Works | ✅ Works |
| **Manga Download** | ❌ Blocked | ✅ Works | ✅ Works |
| **Book Search** | ✅ Works | ✅ Works | ✅ Works |
| **Project Gutenberg** | ✅ Usually Works | ✅ Works | ✅ Works |
| **Internet Archive** | ❌ Often Blocked | ✅ Works | ✅ Works |

**TL;DR**: Use this tool at home for best results. Most features are blocked on corporate/school networks.

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install requests rich beautifulsoup4
```

### Universal Downloader (Recommended)

The easiest way to download both books and manga using a single script:

```bash
# Interactive mode - just run and follow the prompts
python3 downloader.py

# Download a book
python3 downloader.py --book "Pride and Prejudice"

# Search for manga by title (NEW!)
python3 downloader.py --manga --search "one punch man"

# Download manga (interactive)
python3 downloader.py --manga

# Download manga (direct URL)
python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10

# List supported manga sites
python3 downloader.py --manga --list
```

## Features

- **Single unified interface** for both books and manga
- **Interactive mode** - no need to remember commands
- **Book search** from 5 sources: Project Gutenberg, Internet Archive, Standard Ebooks, Feedbooks, and 123FreeBook
- **Manga search** - NEW! Search across 19+ sites by title
- **Manga download** from 19+ supported sites including NatoManga
- **Smart formatting** with rich colors and progress bars
- **Multiple formats** - EPUB, PDF, TXT for books; CBZ for manga
- **English-only mode** - Improved language detection keeps English manga, removes non-English versions
- **Validated file extensions** - Ensures books download with correct formats (.epub, .pdf, etc.)
- **Network-resilient** - Multiple book sources provide alternatives when one is blocked
- **68,000+ books** available through 123FreeBook alone

## Contents

1. **downloader.py** (Recommended) - Unified script for books and manga
2. **book_downloader.py** - Standalone book downloader
3. **manga_helper.py** - Standalone manga helper
4. **manga-downloader** - Binary for direct manga downloads

## Usage Examples

### Books

```bash
# Interactive book search
python3 downloader.py --book "1984"
python3 downloader.py --book "Pride and Prejudice"
python3 downloader.py --book "The Great Gatsby"
```

**How it works:**
1. Searches both Project Gutenberg and Internet Archive
2. Displays all available results
3. Lets you choose which book to download
4. Downloads in available formats (EPUB, PDF, or TXT)

### Manga

```bash
# NEW! Search for manga by title across all sites
python3 downloader.py --manga --search "one punch man"
python3 downloader.py --manga --search "attack on titan"

# Interactive mode (easiest - now includes search option)
python3 downloader.py --manga

# Direct download with chapter range
python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-50

# Download specific chapters
python3 downloader.py --manga --url [URL] --chapters 1,3,5-10

# Download and bundle into single file
python3 downloader.py --manga --url [URL] --chapters 1-10 --bundle

# Download in specific language
python3 downloader.py --manga --url [URL] --chapters 1-10 --language es

# English-only mode (downloads all, keeps only English)
python3 downloader.py --manga --url [URL] --chapters 1-10 --english-only
```

## Supported Manga Sites

**Note**: Manga sites frequently change their structure and APIs, which can cause download issues. The manga-downloader tool is actively maintained, but some sites may temporarily not work.

- Asura Scans (asuratoon.com)
- Chapmanganato (chapmanganato.to) - *Search enabled*
- InManga (inmanga.com)
- LHTranslation (lhtranslation.net)
- LSComic (lscomic.com)
- Manga Monks (mangamonks.com)
- MangaBat (mangabat.com)
- **MangaDex (mangadex.org)** ✅ *Confirmed working - Search enabled via API*
- Mangakakalot (mangakakalot.com, mangakakalot.tv) - *Search enabled*
- Manganato (manganato.com) - *Search enabled*
- Manganelo (manganelo.com, manganelo.tv)
- MangaPanda (mangapanda.in)
- **NatoManga (natomanga.com)** 🆕 *Newly added - Search enabled*
- ReadMangaBat (readmangabat.com)
- TCB Scans (tcbscans.com, tcbscans.net, tcbscans.org)

To see this list anytime, run:
```bash
python3 downloader.py --manga --list
```

### Manga Search Feature (NEW!)

The new search feature lets you search for manga by title across all supported sites simultaneously. Instead of manually browsing sites or knowing the exact URL, just search by title!

**How it works:**
1. Searches 5 major sites with search support (MangaDex, Manganato, Mangakakalot, Chapmanganato, NatoManga)
2. Shows you all results in a nice table format
3. Lets you choose which one to download
4. Shows which sites succeeded, failed, or were blocked

**Example:**
```bash
python3 downloader.py --manga --search "one punch man"
```

**⚠️ IMPORTANT - Network Restrictions:**
- **Corporate/Work Networks**: Most manga sites will be BLOCKED by firewalls
  - You'll see "blocked/unreachable" errors for most sites
  - Search will return 0 results even though the feature works correctly
  - **Recommendation**: Use this feature at home or on mobile hotspot
- **School Networks**: Similar restrictions apply
- **Home Networks**: Should work without issues
- **If blocked**: Use `--url` method if you already have a direct manga URL

### Known Issues with Manga Sites

**Network Blocking**: Some networks (work, school, public WiFi) may block manga sites. If search returns no results, check the error messages to see which sites were blocked. You can try:
- Using a different network (home, mobile hotspot)
- Using the `--url` method if you have a direct link
- Using a VPN (if allowed by your network policy)

**MangaDex**: Works correctly! The downloader will fetch all available languages unless you specify `--language en` (or another code). If you get "no chapters found" or 404 errors, the manga might not have the language you requested available.

**Site Availability**: Manga sites frequently go down, change URLs, or implement anti-scraping measures. If one site doesn't work, try an alternative site for the same manga.

## Recent Improvements

### v2.2 - Added 123FreeBook Source (Latest!)
**Added**: New book source with massive collection
- **123FreeBook** - 68,000+ public domain books in EPUB and PDF formats
- Now searches **5 sources** total (was 4)
- Even more alternatives when some sources are blocked
- Improved book availability across all genres

### v2.1 - Enhanced Language Detection & More Book Sources
**Fixed**: Critical bug in English-only manga filter
- **Old behavior**: Deleted ALL files including English ones (kept 0 files)
- **New behavior**: Detects actual language codes (es, ja, pt, etc.) in filenames
- Only removes files with non-English language indicators
- Keeps English files even if they have chapter titles
- Supports 18+ language codes and names

**Added**: Alternative book sources for network resilience
- **Standard Ebooks** - High-quality, beautifully formatted public domain books
- **Feedbooks** - Public domain catalog with direct epub downloads
- Provides alternatives when Internet Archive is blocked (401 errors)
- Better success rate on restricted networks

### v2.0 - Manga Search Feature
**Added**: Cross-site manga search functionality
- Search for manga by title across multiple sites simultaneously
- Interactive selection from search results
- Clear feedback on which sites succeeded, failed, or were blocked
- Added NatoManga support
- Improved error handling and network resilience
- Default to English-only downloads in interactive mode

**Dependency**: Requires `beautifulsoup4` - install with `pip install beautifulsoup4`

### Language Filtering (Manga) - Important Change!
**The Situation**: Many manga sites (especially MangaDex) host the same chapters in multiple languages. When you don't specify a language, the downloader will grab ALL available translations (Spanish, Turkish, Russian, Arabic, Chinese, etc.), creating dozens of files.

**How It Works Now**:
- **No language specified** = Downloads ALL available languages (many files)
- **Language specified** = Downloads ONLY that language (one file per chapter)

**The Tradeoff**:
- Some manga don't have English translations available, so forcing English would result in no downloads
- The best approach is to specify your preferred language if you want just one version

**How to use**:
```bash
# Downloads ALL available languages (may create many files)
python3 downloader.py --manga --url [URL] --chapters 1-10

# Downloads ONLY English (recommended if available)
python3 downloader.py --manga --url [URL] --chapters 1-10 --language en

# Downloads ONLY Spanish
python3 downloader.py --manga --url [URL] --chapters 1-10 --language es

# Downloads ONLY Japanese
python3 downloader.py --manga --url [URL] --chapters 1-10 --language ja
```

**Recommendation**: Always use `--language en` (or your preferred language) to avoid downloading dozens of duplicate files.

**Common language codes**: `en` (English), `es` (Spanish), `ja` (Japanese), `fr` (French), `de` (German), `pt` (Portuguese), `ru` (Russian), `zh` (Chinese), `tr` (Turkish), `ar` (Arabic)

### File Extension Validation (Books)
**Problem Fixed**: Books were sometimes downloaded with invalid extensions like `.images` instead of proper formats.

**Solution**: The downloader now validates file extensions and only accepts valid book formats (`.epub`, `.pdf`, `.txt`, `.mobi`, `.azw3`). If an invalid extension is detected, it defaults to `.epub`.

**Result**: Your books will now have the correct file extensions and open properly in e-readers.

## Tips

### Network Recommendations

**🏢 At Work/School:**
- ❌ Manga search will likely NOT work (most sites blocked)
- ❌ Internet Archive downloads may fail (401 errors)
- ✅ Project Gutenberg books may work
- **Best practice**: Don't use this tool at work - save it for home

**🏠 At Home:**
- ✅ All features work perfectly
- ✅ Manga search across all sites
- ✅ Both book sources work
- **Best practice**: This is where you should use the tool

**📱 On Mobile Hotspot:**
- ✅ Should work like home network
- Good alternative if you need to download something urgently

### For Books
- Be specific with book titles for better search results
- Classic literature works best (public domain)
- Now searches 4 sources: Project Gutenberg, Internet Archive, Standard Ebooks, and Feedbooks
- If one source is blocked, others may still work
- Downloaded files will have validated extensions (.epub, .pdf, .txt)
- **Standard Ebooks** provides beautifully formatted, high-quality editions
- **Feedbooks** often works well on restricted networks

### For Manga
- **⚠️ USE AT HOME**: Corporate networks block most manga sites
- Use the new search feature to find manga across multiple sites
- Always use the series URL, not a chapter URL
- Interactive mode defaults to English-only downloads
- Use `--bundle` to combine chapters into a single CBZ file
- Downloads are saved in CBZ format, readable with most comic readers
- **MangaDex works great at home** - Has the most reliable API
- **Manga site changes**: Sites frequently change URLs and structure. If downloads fail, try:
  1. A different site hosting the same manga
  2. Updating the manga-downloader binary (see Updates section)
  3. Checking the manga-downloader GitHub issues page for known problems

## File Outputs

- **Books**: Downloaded as .epub, .pdf, or .txt files
- **Manga**: Downloaded as .cbz files (comic book archive)

## Legal Notice

This tool only downloads content from legal, free sources:
- Project Gutenberg (public domain books)
- Internet Archive (freely available books)
- Manga from sites that host content legally

Always respect copyright laws and only download content that is legally available.

## Troubleshooting

### Common Issues

**Module not found**
```bash
pip install requests rich
```

**Book: No results found**
- Try different search terms or variations of the title
- Classic literature works best (public domain)

**Book: Download failed**
- The file might be temporarily unavailable, try again later

**Book: 401 Unauthorized error from Internet Archive**
- This is caused by network restrictions (common at work/school)
- Corporate firewalls often block direct downloads from archive.org
- **Solutions**:
  - The downloader now searches 4 sources automatically
  - Try selecting a book from Project Gutenberg, Standard Ebooks, or Feedbooks instead
  - These alternative sources often work better through firewalls
  - Example: `python3 downloader.py --book "Pride and Prejudice"`
  - Look for results marked with [yellow]Project Gutenberg[/yellow], [yellow]Standard Ebooks[/yellow], or [yellow]Feedbooks[/yellow]

**Manga: Binary not found**
- Make sure you're in the BookDownloader directory when running scripts

**Manga: Search returns no results**
- Check if your network is blocking manga sites (common at work/school)
- Look at the error messages to see which sites are blocked vs. just no results
- Try using `--url` with a direct manga link instead of search
- Try on a different network (home WiFi, mobile hotspot)

**Manga: Download failed**
- Check if the URL is correct and points to a series page (not a chapter)
- Verify the site is supported: `python3 downloader.py --manga --list`
- Try a different manga site if the current one is not working
- Some sites may be temporarily down or blocking automated downloads
- Your network may be blocking the manga site

**Manga: 404 errors or "No chapters found"** when using `--language`
- The manga may not have the language you requested available
- Try without `--language` to see all available languages
- Try a different language code (e.g., `--language ja` for Japanese, `--language es` for Spanish)
- Some manga only have the original Japanese version available
- Try an alternative manga site

**Manga: Too many files downloaded (multiple languages)**
- This happens when you DON'T specify `--language`
- To fix: ALWAYS use `--language en` (or your preferred language code)
- Example: `python3 downloader.py --manga --url [URL] --chapters 1-10 --language en`
- Without `--language`, the downloader fetches ALL available translations

**Book: Wrong file extension**
- This issue has been fixed! File extensions are now validated
- Valid formats: .epub, .pdf, .txt, .mobi, .azw3
- Invalid extensions automatically default to .epub

## Alternative Scripts

If you prefer using standalone scripts instead of the unified downloader:

### Book Downloader (Standalone)
```bash
python3 book_downloader.py --book "Book Title"
```

### Manga Helper (Standalone)
```bash
# Interactive mode
python3 manga_helper.py

# Direct download
python3 manga_helper.py --url [URL] --chapters 1-10
```

### Direct Binary Usage
```bash
# Use manga-downloader binary directly
./manga-downloader [MANGA_URL] 1-10 --bundle
```

## Updates

To update the manga-downloader binary to the latest version:

```bash
cd BookDownloader
rm manga-downloader
curl -L -o manga-downloader.tar.gz https://github.com/elboletaire/manga-downloader/releases/latest/download/manga-downloader-linux-amd64.tar.gz
tar -xzf manga-downloader.tar.gz
rm manga-downloader.tar.gz
chmod +x manga-downloader
```

## Credits

- **manga-downloader**: Created by [elboletaire](https://github.com/elboletaire/manga-downloader)
- **Book sources**: Project Gutenberg and Internet Archive
