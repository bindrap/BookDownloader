# BookDownloader

A unified tool for downloading books and manga legally from free sources.

## Quick Start

### Installation

```bash
# Install Python dependencies
pip install requests rich
```

### Universal Downloader (Recommended)

The easiest way to download both books and manga using a single script:

```bash
# Interactive mode - just run and follow the prompts
python3 downloader.py

# Download a book
python3 downloader.py --book "Pride and Prejudice"

# Download manga (interactive)
python3 downloader.py --manga

# Download manga (direct)
python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10

# List supported manga sites
python3 downloader.py --manga --list
```

## Features

- **Single unified interface** for both books and manga
- **Interactive mode** - no need to remember commands
- **Book search** from Project Gutenberg and Internet Archive
- **Manga download** from 18+ supported sites
- **Smart formatting** with rich colors and progress bars
- **Multiple formats** - EPUB, PDF, TXT for books; CBZ for manga
- **Language filtering** - Specify language code to download only one translation (recommended: use `--language en`)
- **Validated file extensions** - Ensures books download with correct formats (.epub, .pdf, etc.)

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
# Interactive mode (easiest)
python3 downloader.py --manga

# Direct download with chapter range
python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-50

# Download specific chapters
python3 downloader.py --manga --url [URL] --chapters 1,3,5-10

# Download and bundle into single file
python3 downloader.py --manga --url [URL] --chapters 1-10 --bundle

# Download in specific language
python3 downloader.py --manga --url [URL] --chapters 1-10 --language es

# Download with all options
python3 downloader.py --manga --url [URL] --chapters 1-50 --bundle --language en
```

## Supported Manga Sites

**Note**: Manga sites frequently change their structure and APIs, which can cause download issues. The manga-downloader tool is actively maintained, but some sites may temporarily not work.

- Asura Scans (asuratoon.com)
- Chapmanganato (chapmanganato.to)
- InManga (inmanga.com)
- LHTranslation (lhtranslation.net)
- LSComic (lscomic.com)
- Manga Monks (mangamonks.com)
- MangaBat (mangabat.com)
- **MangaDex (mangadex.org)** ✅ *Confirmed working - use `--language` to filter*
- Mangakakalot (mangakakalot.com, mangakakalot.tv)
- Manganato (manganato.com)
- Manganelo (manganelo.com, manganelo.tv)
- MangaPanda (mangapanda.in)
- ReadMangaBat (readmangabat.com)
- TCB Scans (tcbscans.com, tcbscans.net, tcbscans.org)

To see this list anytime, run:
```bash
python3 downloader.py --manga --list
```

### Known Issues with Manga Sites

**MangaDex**: Works correctly! The downloader will fetch all available languages unless you specify `--language en` (or another code). If you get "no chapters found" or 404 errors, the manga might not have the language you requested available.

**Site Availability**: Manga sites frequently go down, change URLs, or implement anti-scraping measures. If one site doesn't work, try an alternative site for the same manga.

## Recent Improvements

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

### For Books
- Be specific with book titles for better search results
- Classic literature works best (public domain)
- Check both sources as they may have different formats available
- Downloaded files will have validated extensions (.epub, .pdf, .txt)

### For Manga
- Always use the series URL, not a chapter URL
- **⚠️ IMPORTANT**: Use `--language en` to download only English (otherwise ALL languages will download)
- Use `--bundle` to combine chapters into a single CBZ file
- Downloads are saved in CBZ format, readable with most comic readers
- To avoid downloading dozens of duplicate files, ALWAYS specify `--language [code]`
- **MangaDex works!** - It downloads successfully, just specify a language or accept all languages
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

**Manga: Binary not found**
- Make sure you're in the BookDownloader directory when running scripts

**Manga: Download failed**
- Check if the URL is correct and points to a series page (not a chapter)
- Verify the site is supported: `python3 downloader.py --manga --list`
- Try a different manga site if the current one is not working
- Some sites may be temporarily down or blocking automated downloads

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
