#!/usr/bin/env python3
"""
Universal Downloader - Download books and manga from legal, free sources
"""
import argparse
import requests
import subprocess
import sys
import os
import glob
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
from rich import print
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Try to import Playwright for browser automation
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Create a persistent session for human-like requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
})

# Book API endpoints
GUTENDEX_API = "https://gutendex.com/books?search="
OPENLIBRARY_API = "https://openlibrary.org/search.json?q="
IA_METADATA_API = "https://archive.org/metadata/"
STANDARD_EBOOKS_API = "https://standardebooks.org/opds/all"
FEEDBOOKS_SEARCH = "https://www.feedbooks.com/search.json?query="
FREEBOOK123_SEARCH = "https://123freebook.com/?s="
ANNAS_ARCHIVE_SEARCH = "https://annas-archive.org/search"
ANNAS_ARCHIVE_KEY = "DVMRwJdUHGMmyaTr2ntCSSX2ULJY8"  # API key for Anna's Archive

# Supported manga sites
MANGA_SITES = [
    {"name": "Asura Scans", "url": "https://asuratoon.com"},
    {"name": "Chapmanganato", "url": "https://chapmanganato.to"},
    {"name": "InManga", "url": "https://inmanga.com"},
    {"name": "LHTranslation", "url": "https://lhtranslation.net"},
    {"name": "LSComic", "url": "https://lscomic.com"},
    {"name": "Manga Monks", "url": "https://mangamonks.com"},
    {"name": "MangaBat", "url": "https://mangabat.com"},
    {"name": "MangaDex", "url": "https://mangadex.org"},
    {"name": "Mangakakalot.com", "url": "https://mangakakalot.com"},
    {"name": "Mangakakalot.tv", "url": "https://mangakakalot.tv"},
    {"name": "Manganato", "url": "https://manganato.com"},
    {"name": "Manganelo.com", "url": "https://manganelo.com"},
    {"name": "Manganelo.tv", "url": "https://manganelo.tv"},
    {"name": "MangaPanda", "url": "https://mangapanda.in"},
    {"name": "NatoManga", "url": "https://www.natomanga.com"},
    {"name": "ReadMangaBat", "url": "https://readmangabat.com"},
    {"name": "TCB Scans (.com)", "url": "https://tcbscans.com"},
    {"name": "TCB Scans (.net)", "url": "https://www.tcbscans.net"},
    {"name": "TCB Scans (.org)", "url": "https://www.tcbscans.org"},
]

# ============== BOOK FUNCTIONS ==============

def search_gutendex(query):
    """Search Project Gutenberg"""
    print("[bold blue]Searching Project Gutenberg...[/bold blue]")
    try:
        response = requests.get(GUTENDEX_API + requests.utils.quote(query), timeout=30)
        response.raise_for_status()
        results = response.json().get("results", [])
        return [{
            "source": "Gutenberg",
            "title": r["title"],
            "author": ", ".join([a["name"] for a in r["authors"]]) if r.get("authors") else "Unknown",
            "formats": r["formats"]
        } for r in results]
    except Exception as e:
        print(f"[yellow]Warning: Gutenberg search failed: {e}[/yellow]")
        return []

def search_openlibrary(query):
    """Search Open Library / Internet Archive"""
    print("[bold blue]Searching Open Library...[/bold blue]")
    try:
        response = requests.get(OPENLIBRARY_API + requests.utils.quote(query), timeout=30)
        response.raise_for_status()
        results = response.json().get("docs", [])
        openlibrary_results = []
        for r in results[:10]:
            if "ia" in r and r["ia"]:
                openlibrary_results.append({
                    "source": "Internet Archive",
                    "title": r.get("title", "Unknown Title"),
                    "author": ", ".join(r.get("author_name", ["Unknown"])),
                    "ia_id": r["ia"][0]
                })
        return openlibrary_results
    except Exception as e:
        print(f"[yellow]Warning: Open Library search failed: {e}[/yellow]")
        return []

def search_standard_ebooks(query):
    """Search Standard Ebooks"""
    print("[bold blue]Searching Standard Ebooks...[/bold blue]")
    try:
        # Standard Ebooks provides OPDS feed, we'll scrape their website search instead
        search_url = f"https://standardebooks.org/ebooks/?query={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find book entries
        books = soup.select('li[typeof="schema:Book"]')[:10]

        for book in books:
            # Get title
            title_elem = book.select_one('span[property="schema:name"]')
            if not title_elem:
                continue

            title = title_elem.text.strip()

            # Get author - it's nested inside the author property
            author = "Unknown"
            author_container = book.select_one('[property="schema:author"]')
            if author_container:
                author_name = author_container.select_one('span[property="schema:name"]')
                if author_name:
                    author = author_name.text.strip()

            # Get link
            link_elem = book.select_one('a[property="schema:url"]')
            if link_elem:
                book_url = "https://standardebooks.org" + link_elem.get('href', '')
                results.append({
                    "source": "Standard Ebooks",
                    "title": title,
                    "author": author,
                    "book_url": book_url
                })

        return results
    except Exception as e:
        print(f"[yellow]Warning: Standard Ebooks search failed: {e}[/yellow]")
        return []

def search_feedbooks(query):
    """Search Feedbooks public domain"""
    print("[bold blue]Searching Feedbooks...[/bold blue]")
    try:
        # Feedbooks public domain catalog
        search_url = f"https://catalog.feedbooks.com/search.json?query={requests.utils.quote(query)}&category=FBPUB"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get('books', [])[:10]:
            # Extract author names
            authors = ", ".join([a.get('name', 'Unknown') for a in item.get('authors', [])])

            results.append({
                "source": "Feedbooks",
                "title": item.get('title', 'Unknown Title'),
                "author": authors if authors else "Unknown",
                "book_id": item.get('id', ''),
                "epub_url": item.get('epub_url', '')
            })

        return results
    except Exception as e:
        print(f"[yellow]Warning: Feedbooks search failed: {e}[/yellow]")
        return []

def search_123freebook(query):
    """Search 123freebook.com"""
    print("[bold blue]Searching 123FreeBook...[/bold blue]")
    try:
        search_url = f"https://123freebook.com/?s={requests.utils.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find book entries - they're typically in article or div containers
        # Common selectors for WordPress book sites
        books = soup.select('article.post, div.book-item, div.search-item')[:10]

        if not books:
            # Fallback: try finding links with book patterns
            books = soup.select('h2 a, h3 a, .entry-title a')[:10]

        for book in books:
            if book.name == 'a':
                # Direct link element
                title_elem = book
                link_elem = book
            else:
                # Container element
                title_elem = book.select_one('h2 a, h3 a, .entry-title a, a.book-title')
                link_elem = title_elem

            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                book_url = link_elem.get('href', '')

                # Try to find author
                author_elem = book.select_one('.author, .book-author, span[rel="author"]')
                author = author_elem.get_text(strip=True) if author_elem else "Unknown"

                # Only add if we have a valid URL
                if book_url and ('123freebook.com' in book_url or book_url.startswith('/')):
                    if book_url.startswith('/'):
                        book_url = f"https://123freebook.com{book_url}"

                    results.append({
                        "source": "123FreeBook",
                        "title": title,
                        "author": author,
                        "book_url": book_url
                    })

        return results
    except Exception as e:
        print(f"[yellow]Warning: 123FreeBook search failed: {e}[/yellow]")
        return []

def search_annas_archive(query):
    """Search Anna's Archive"""
    print("[bold blue]Searching Anna's Archive...[/bold blue]")
    try:
        search_url = f"{ANNAS_ARCHIVE_SEARCH}?q={requests.utils.quote(query)}&acc=1"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find title links (they have specific classes and link to /md5/)
        # Look for the main title links with font-semibold text-lg
        title_links = soup.select('a.font-semibold.text-lg[href^="/md5/"]')[:15]

        for title_link in title_links:
            # Get the MD5 hash from the URL
            href = title_link.get('href', '')
            md5_hash = href.replace('/md5/', '').split('?')[0] if '/md5/' in href else None

            if not md5_hash:
                continue

            # Extract title
            title = title_link.get_text(strip=True)

            # Find the parent div that contains all the book info
            parent = title_link.find_parent('div')

            # Extract author - look for link with user-edit icon
            author = "Unknown"
            author_link = None
            if parent:
                # Find all links in parent
                for link in parent.find_all('a', class_='text-sm'):
                    # Check if this link has the user icon
                    icon = link.find('span', class_=lambda c: c and 'icon-[mdi--user-edit]' in c)
                    if icon:
                        author_link = link
                        break

            if author_link:
                # Extract author text, removing the icon
                author_text = author_link.get_text(strip=True)
                author = author_text.strip()

            results.append({
                "source": "Anna's Archive",
                "title": title,
                "author": author,
                "md5": md5_hash,
                "book_url": f"https://annas-archive.org/md5/{md5_hash}"
            })

        return results
    except Exception as e:
        print(f"[yellow]Warning: Anna's Archive search failed: {e}[/yellow]")
        return []

def get_download_links(item):
    """Get download link for a book"""
    if item["source"] == "Gutenberg":
        formats = item["formats"]
        for preferred in ["application/epub+zip", "application/pdf", "text/plain"]:
            if preferred in formats:
                return formats[preferred]

    elif item["source"] == "Internet Archive":
        ia_id = item["ia_id"]
        try:
            # Use session with referer to appear more legitimate
            metadata_url = IA_METADATA_API + ia_id
            response = session.get(metadata_url, timeout=10)
            response.raise_for_status()
            files = response.json().get("files", [])

            # Look for downloadable formats
            for ext in [".epub", ".pdf", ".txt"]:
                for f in files:
                    if f["name"].endswith(ext):
                        # Return the item ID and filename for special handling
                        return {
                            'url': f"https://archive.org/download/{ia_id}/{f['name']}",
                            'ia_id': ia_id,
                            'filename': f['name'],
                            'needs_ia_handling': True
                        }
        except Exception as e:
            print(f"[red]Error getting download link: {e}[/red]")

    elif item["source"] == "Standard Ebooks":
        # Get download page and extract epub link
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(item["book_url"], headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for epub download link
            epub_link = soup.select_one('a[href*=".epub"]')
            if epub_link:
                return urljoin("https://standardebooks.org", epub_link['href'])
        except Exception as e:
            print(f"[red]Error getting Standard Ebooks download link: {e}[/red]")

    elif item["source"] == "Feedbooks":
        # Feedbooks provides direct epub URL
        if item.get("epub_url"):
            return item["epub_url"]
        # Fallback: construct download URL from book ID
        elif item.get("book_id"):
            return f"https://www.feedbooks.com/book/{item['book_id']}.epub"

    elif item["source"] == "123FreeBook":
        # Get book page and extract download link
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(item["book_url"], headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for download buttons/links for EPUB (preferred) or PDF
            # Common patterns: download buttons, direct links
            download_link = None

            # Try multiple selectors for download links
            selectors = [
                'a[href*=".epub"]',
                'a[href*=".pdf"]',
                'a.download-button[href*="epub"]',
                'a.download-button[href*="pdf"]',
                'a[class*="download"][href*="epub"]',
                'a[class*="download"][href*="pdf"]',
                'button[onclick*="download"]',
            ]

            for selector in selectors:
                link = soup.select_one(selector)
                if link:
                    href = link.get('href', '')
                    if href:
                        # Prioritize EPUB over PDF
                        if '.epub' in href.lower():
                            return urljoin(item["book_url"], href)
                        elif not download_link:  # Use PDF as fallback
                            download_link = urljoin(item["book_url"], href)

            if download_link:
                return download_link

        except Exception as e:
            print(f"[red]Error getting 123FreeBook download link: {e}[/red]")

    elif item["source"] == "Anna's Archive":
        # Anna's Archive uses /slow_download/{md5}/0/0 for free downloads
        # (fast_download requires membership/donation)
        md5 = item.get('md5')
        if md5:
            # Use the first slow partner server (free, no membership required)
            download_url = f"https://annas-archive.org/slow_download/{md5}/0/0"
            return {
                'url': download_url,
                'md5': md5,
                'needs_annas_handling': True
            }

    return None

def download_annas_archive_browser(md5, title, download_dir=None):
    """Download from Anna's Archive using browser automation to bypass DDoS-Guard"""
    if not PLAYWRIGHT_AVAILABLE:
        print(f"[red]Playwright not available. Install with: pip install playwright && playwright install chromium[/red]")
        return False

    if download_dir is None:
        download_dir = os.getcwd()

    book_url = f"https://annas-archive.org/md5/{md5}"

    print(f"[cyan]Attempting automated download with browser...[/cyan]")
    print(f"[dim]Note: Anna's Archive has strong anti-bot protection.[/dim]")
    print(f"[dim]If automation fails, manual download instructions will be provided.[/dim]\n")

    try:
        with sync_playwright() as p:
            # Launch browser - use headless mode
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            page = context.new_page()

            # Step 1: Visit the book page
            print(f"[dim]Step 1: Loading book page...[/dim]")
            page.goto(book_url, wait_until='networkidle', timeout=30000)

            # Wait for the page to fully load (DDoS-Guard check may appear)
            time.sleep(2)

            # Step 2: Look for slow download links
            print(f"[dim]Step 2: Finding slow download link...[/dim]")
            try:
                # Wait for slow download section to be visible
                page.wait_for_selector('a[href^="/slow_download/"]', timeout=10000)
                slow_links = page.query_selector_all('a[href^="/slow_download/"]')

                if not slow_links:
                    print(f"[yellow]No slow download links found[/yellow]")
                    browser.close()
                    return False

                # Click the first slow download link
                print(f"[dim]Step 3: Clicking slow download link...[/dim]")
                slow_download_url = slow_links[0].get_attribute('href')
                page.goto(f"https://annas-archive.org{slow_download_url}", wait_until='networkidle', timeout=30000)

                # Wait for DDoS-Guard JavaScript challenge to complete
                print(f"[dim]Step 4: Waiting for DDoS-Guard verification and page refresh...[/dim]")

                # The slow download page typically refreshes after 5 seconds
                # Wait for that refresh to happen
                initial_url = page.url

                # Wait up to 20 seconds for either:
                # 1. URL to change (redirect to partner)
                # 2. Page to reload/refresh (same URL but new content)
                # 3. Download link to appear
                try:
                    print(f"[dim]Waiting for page to refresh (typically 5-10 seconds)...[/dim]")

                    # Strategy: Wait for either URL change OR for download link to appear
                    for i in range(20):
                        time.sleep(1)
                        current_url = page.url

                        # Check if we've been redirected
                        if 'annas-archive.org/slow_download' not in current_url:
                            print(f"[dim]✓ Redirected to partner site after {i+1} seconds[/dim]")
                            break

                        # Check if download link appeared on current page
                        test_links = page.query_selector_all('a[href^="http"]')
                        for link in test_links:
                            href = link.get_attribute('href') or ""
                            text = link.inner_text().lower() if link.inner_text() else ""
                            if href and 'annas-archive.org' not in href and 'ddos-guard' not in href:
                                if any(word in text for word in ['download', 'get', 'click']):
                                    print(f"[dim]✓ Download link appeared after {i+1} seconds[/dim]")
                                    break
                        else:
                            continue
                        break

                except Exception as e:
                    print(f"[dim]Wait completed with: {e}[/dim]")

                # Step 3: Look for download button or automatic redirect
                print(f"[dim]Step 5: Looking for download link...[/dim]")
                current_url = page.url
                print(f"[dim]Current URL: {current_url}[/dim]")

                # Wait a bit more for any final JS to execute
                time.sleep(1)

                # Look for download links
                download_link = None

                # Check if we're on a partner site or still on Anna's Archive
                if 'annas-archive.org' not in current_url:
                    # We're on a partner site - look for download button
                    print(f"[dim]On partner site, looking for download...[/dim]")

                    # Try to find a download button or link
                    selectors = [
                        'a[href*=".epub"]',
                        'a[href*=".pdf"]',
                        'a[href*="download"]',
                        'button:has-text("download")',
                        'a:has-text("download")',
                        'a[class*="download"]',
                        'a[class*="btn"]'
                    ]

                    for selector in selectors:
                        try:
                            element = page.query_selector(selector)
                            if element:
                                href = element.get_attribute('href')
                                if href:
                                    download_link = href
                                    print(f"[dim]Found download link: {href[:100]}...[/dim]")
                                    break
                        except:
                            continue
                else:
                    # Still on Anna's Archive - the slow download might have failed or need more time
                    print(f"[yellow]Still on Anna's Archive - trying alternate approach...[/yellow]")

                    # Save page content for debugging
                    content = page.content()

                    # Check for specific messages
                    if 'wait' in content.lower() or 'queue' in content.lower() or 'busy' in content.lower():
                        print(f"[yellow]Partner server appears busy - servers may be at capacity[/yellow]")
                        browser.close()
                        return False

                    # Look for "Download now" button or similar on the slow download page itself
                    download_buttons = page.query_selector_all('a, button')
                    for button in download_buttons:
                        text = button.inner_text().lower() if button.inner_text() else ""
                        href = button.get_attribute('href') or ""

                        if any(keyword in text for keyword in ['download now', 'get', 'download', 'click here']):
                            if href and href.startswith('http') and 'annas-archive.org' not in href:
                                download_link = href
                                print(f"[dim]Found download button with external link[/dim]")
                                break

                    # If still no link, try finding any external link as last resort
                    if not download_link:
                        all_links = page.query_selector_all('a[href^="http"]')
                        for link in all_links:
                            href = link.get_attribute('href')
                            if href and 'annas-archive.org' not in href and 'ddos-guard' not in href:
                                download_link = href
                                print(f"[dim]Found external link: {href[:80]}...[/dim]")
                                break

                if download_link:
                    print(f"[dim]Step 6: Downloading file...[/dim]")

                    # Handle the download
                    with page.expect_download(timeout=60000) as download_info:
                        if download_link.startswith('http'):
                            page.goto(download_link, timeout=60000)
                        else:
                            page.click(f'a[href="{download_link}"]', timeout=10000)

                    download = download_info.value

                    # Generate filename
                    filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = filename.replace(" ", "_")[:100]

                    # Get extension from suggested filename
                    suggested = download.suggested_filename
                    ext = os.path.splitext(suggested)[1] if suggested else ".epub"
                    filename += ext

                    filepath = os.path.join(download_dir, filename)

                    # Save the download
                    download.save_as(filepath)

                    print(f"\n[bold green]✓ Successfully downloaded to {filename}[/bold green]")
                    browser.close()
                    return True
                else:
                    # No download link found - print page URL for manual download
                    current_url = page.url
                    print(f"[yellow]⚠ Could not find automatic download link[/yellow]")
                    print(f"[cyan]The partner page is:[/cyan] {current_url}")
                    print(f"[dim]You may need to click the download button manually on that page.[/dim]")
                    browser.close()
                    return False

            except Exception as e:
                print(f"[yellow]⚠ Error during browser automation: {e}[/yellow]")
                browser.close()
                return False

    except Exception as e:
        print(f"[red]✗ Browser automation failed: {e}[/red]")
        return False

def sanitize_folder_name(name):
    """Sanitize a name for use as a folder name"""
    # Remove invalid characters for folder names
    sanitized = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    sanitized = sanitized.replace(" ", "_")[:100]
    return sanitized

def download_file_ia(ia_id, filename_on_server, title, download_dir=None):
    """Download a file from Internet Archive with retry logic"""
    # Use current directory if not specified
    if download_dir is None:
        download_dir = os.getcwd()

    print(f"[cyan]Attempting Internet Archive download...[/cyan]")

    # Clean up the title for local filename
    local_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    local_filename = local_filename.replace(" ", "_")[:100]

    # Extract extension from server filename
    ext = os.path.splitext(filename_on_server)[1]
    if not ext or ext.lower() not in ['.epub', '.pdf', '.txt', '.mobi', '.azw3']:
        ext = ".epub"
    local_filename += ext
    filepath = os.path.join(download_dir, local_filename)

    item_page_url = f"https://archive.org/details/{ia_id}"

    # Try multiple download strategies with retry logic
    strategies = [
        {
            'name': 'Direct download',
            'url': f"https://archive.org/download/{ia_id}/{filename_on_server}",
            'headers': {
                'Referer': item_page_url,
                'Accept': 'application/epub+zip,application/pdf,*/*',
            }
        },
        {
            'name': 'Archive.org serve endpoint',
            'url': f"https://archive.org/serve/{ia_id}/{filename_on_server}",
            'headers': {
                'Referer': item_page_url,
            }
        }
    ]

    for strategy in strategies:
        print(f"[dim]Trying: {strategy['name']}...[/dim]")

        # Retry logic: 3 attempts with exponential backoff
        for attempt in range(3):
            try:
                # Visit item page first (like a human would)
                if attempt == 0:
                    session.get(item_page_url, timeout=15)
                    time.sleep(0.5)

                with session.get(strategy['url'], stream=True, timeout=45, headers=strategy['headers']) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0

                    print(f"[green]Downloading:[/green] {local_filename}")
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"Progress: {percent:.1f}%", end='\r')

                print(f"\n[bold green]✓ Successfully downloaded to {filepath}[/bold green]")
                return True

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    # 401 error - this book requires authentication
                    break  # No point retrying, move to next strategy or fail
                elif e.response.status_code == 403:
                    # 403 Forbidden - might be temporary
                    if attempt < 2:
                        wait_time = 2 ** attempt  # 1s, 2s
                        print(f"[yellow]Forbidden, retrying in {wait_time}s...[/yellow]")
                        time.sleep(wait_time)
                        continue
                    break
                elif e.response.status_code == 503:
                    # 503 Service Unavailable - temporary issue
                    if attempt < 2:
                        wait_time = 2 ** attempt
                        print(f"[yellow]Service unavailable, retrying in {wait_time}s...[/yellow]")
                        time.sleep(wait_time)
                        continue
                    break
                else:
                    break  # Other HTTP errors, don't retry
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"[yellow]Network error, retrying in {wait_time}s...[/yellow]")
                    time.sleep(wait_time)
                    continue
                break
            except Exception as e:
                break  # Unknown error, don't retry

    # All strategies failed
    print(f"\n[red]✗ All download attempts failed[/red]")
    print(f"[yellow]This book may require borrowing/lending on archive.org[/yellow]")
    print(f"[yellow]Or it may not be freely available for download[/yellow]")
    print(f"[cyan]Try manually visiting: {item_page_url}[/cyan]")

    if os.path.exists(filepath):
        os.remove(filepath)
    return False

def download_file(url, title, download_dir=None):
    """Download a book file"""
    # Use current directory if not specified
    if download_dir is None:
        download_dir = os.getcwd()

    # Handle string URLs (simple downloads with retry logic)
    if isinstance(url, str):
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = filename.replace(" ", "_")[:100]

        # Extract extension from URL
        ext = os.path.splitext(url.split('?')[0])[1]
        valid_extensions = ['.epub', '.pdf', '.txt', '.mobi', '.azw3']

        if not ext or ext.lower() not in valid_extensions:
            ext = ".epub"

        filename += ext
        filepath = os.path.join(download_dir, filename)

        print(f"[green]Downloading:[/green] {filename}")

        # Retry logic: 3 attempts with exponential backoff
        for attempt in range(3):
            try:
                # Add referer header for better compatibility
                headers = {'Referer': url.rsplit('/', 1)[0] + '/'}
                with session.get(url, stream=True, timeout=45, headers=headers) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', 0))
                    downloaded = 0
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"Progress: {percent:.1f}%", end='\r')
                print(f"\n[bold green]✓ Saved to {filepath}[/bold green]")
                return True
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < 2:
                    wait_time = 2 ** attempt
                    print(f"\n[yellow]Network error, retrying in {wait_time}s... (attempt {attempt + 2}/3)[/yellow]")
                    time.sleep(wait_time)
                    continue
                print(f"\n[red]✗ Download failed after 3 attempts: {e}[/red]")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False
            except Exception as e:
                print(f"\n[red]✗ Download failed: {e}[/red]")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return False

    # Handle dict URLs (Internet Archive special handling)
    elif isinstance(url, dict) and url.get('needs_ia_handling'):
        return download_file_ia(url['ia_id'], url['filename'], title, download_dir)

    # Handle dict URLs (Anna's Archive special handling)
    elif isinstance(url, dict) and url.get('needs_annas_handling'):
        md5 = url.get('md5')
        book_url = f"https://annas-archive.org/md5/{md5}"

        # Try browser automation first if Playwright is available
        if PLAYWRIGHT_AVAILABLE:
            return download_annas_archive_browser(md5, title, download_dir)

        # Fallback to manual instructions if Playwright not available
        print(f"[cyan]Attempting Anna's Archive multi-step download...[/cyan]")
        print(f"[dim]Note: Install Playwright for automatic downloads: pip install playwright && playwright install chromium[/dim]\n")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Step 1: Visit book page and get slow download link
            print(f"[dim]Step 1: Fetching book page...[/dim]")
            response = session.get(book_url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the first slow download link
            slow_download_link = soup.select_one('a[href^="/slow_download/"]')
            if not slow_download_link:
                print(f"[yellow]⚠ Could not find slow download link[/yellow]")
                print(f"[cyan]Please visit manually:[/cyan] {book_url}")
                return False

            slow_download_url = "https://annas-archive.org" + slow_download_link.get('href')
            print(f"[dim]Step 2: Following slow download link...[/dim]")

            time.sleep(0.5)  # Brief delay
            headers['Referer'] = book_url

            # Step 2: Visit slow download page
            response = session.get(slow_download_url, headers=headers, timeout=20)

            # Check if we got redirected or blocked by DDoS-Guard
            if response.status_code == 403 or 'ddos-guard' in response.text.lower():
                print(f"[yellow]⚠ DDoS-Guard protection detected[/yellow]")
                print(f"[dim]Anna's Archive requires JavaScript verification to prevent bots.[/dim]\n")
                print(f"[bold cyan]📖 Book Page:[/bold cyan] {book_url}")
                print(f"\n[bold yellow]Quick Download Steps:[/bold yellow]")
                print(f"  1. Open the URL above in your browser")
                print(f"  2. Scroll to '🐢 Slow downloads' section")
                print(f"  3. Click 'Slow Partner Server #1'")
                print(f"  4. Wait ~3 seconds for verification")
                print(f"  5. Click the download button on the partner page")
                print(f"\n[dim]💡 Tip: The download usually starts automatically after step 4![/dim]")
                return False

            soup = BeautifulSoup(response.content, 'html.parser')

            # Step 3: Look for the actual download link on the partner page
            # Anna's Archive partner pages typically have a download button or auto-redirect
            print(f"[dim]Step 3: Searching for download button...[/dim]")

            # Try to find download links - they might be in different formats
            download_candidates = []

            # Look for direct file links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                # Check if it's a file download link
                if any(ext in href.lower() for ext in ['.epub', '.pdf', '.mobi', '.azw', '.azw3']):
                    download_candidates.append(href)
                # Check for download buttons
                elif 'download' in href.lower() or 'get' in link.get_text().lower():
                    download_candidates.append(href)

            # Also check for meta refresh or JavaScript redirects
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta_refresh:
                content = meta_refresh.get('content', '')
                if 'url=' in content.lower():
                    redirect_url = content.split('url=', 1)[1].strip()
                    download_candidates.insert(0, redirect_url)

            if not download_candidates:
                # Try to extract any external links that might be the download
                external_links = [a.get('href') for a in soup.find_all('a', href=True)
                                if a.get('href', '').startswith('http') and 'annas-archive.org' not in a.get('href', '')]
                if external_links:
                    download_candidates.extend(external_links[:3])

            if download_candidates:
                print(f"[dim]Step 4: Attempting to download file...[/dim]")

                for candidate_url in download_candidates[:5]:  # Try up to 5 candidates
                    try:
                        # Make URL absolute if needed
                        if not candidate_url.startswith('http'):
                            if candidate_url.startswith('/'):
                                candidate_url = urljoin(slow_download_url, candidate_url)
                            else:
                                candidate_url = urljoin(response.url, candidate_url)

                        headers['Referer'] = slow_download_url
                        file_response = session.get(candidate_url, headers=headers, timeout=30, stream=True, allow_redirects=True)

                        content_type = file_response.headers.get('content-type', '').lower()

                        # Check if we got an actual file
                        if file_response.status_code == 200 and (
                            'application' in content_type or
                            'octet-stream' in content_type or
                            any(ext in content_type for ext in ['epub', 'pdf', 'mobi'])
                        ):
                            filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            filename = filename.replace(" ", "_")[:100]

                            # Get extension
                            ext = ".epub"
                            if 'content-disposition' in file_response.headers:
                                cd = file_response.headers['content-disposition']
                                fname_match = re.search(r'filename="?([^"]+)"?', cd)
                                if fname_match:
                                    file_ext = os.path.splitext(fname_match.group(1))[1]
                                    if file_ext:
                                        ext = file_ext
                            elif 'pdf' in content_type:
                                ext = ".pdf"
                            elif 'mobi' in content_type:
                                ext = ".mobi"

                            filename += ext

                            print(f"[green]Downloading:[/green] {filename}")

                            total_size = int(file_response.headers.get('content-length', 0))
                            downloaded = 0

                            with open(filename, 'wb') as f:
                                for chunk in file_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        percent = (downloaded / total_size) * 100
                                        print(f"Progress: {percent:.1f}%", end='\r')

                            print(f"\n[bold green]✓ Successfully downloaded to {filename}[/bold green]")
                            return True

                    except Exception as e:
                        continue  # Try next candidate

            # If we get here, automated download failed
            print(f"[yellow]⚠ Automated download unsuccessful[/yellow]\n")
            print(f"[bold]Book page:[/bold] {book_url}")
            print(f"\n[yellow]Please download manually:[/yellow]")
            print(f"  1. Visit the URL above in your browser")
            print(f"  2. Click a 'Slow Partner Server' link")
            print(f"  3. Click the download button on the partner page")
            return False

        except Exception as e:
            print(f"[yellow]⚠ Download failed: {e}[/yellow]")
            print(f"[cyan]Please visit manually:[/cyan] {book_url}")
            return False

    else:
        print(f"[red]Invalid URL format[/red]")
        return False

def calculate_relevance(query, title):
    """Calculate relevance score for a book title compared to search query"""
    query_lower = query.lower().strip()
    title_lower = title.lower().strip()

    # Exact match = highest score
    if query_lower == title_lower:
        return 100

    # Title starts with query = very high score
    if title_lower.startswith(query_lower):
        return 90

    # Query is in title as complete phrase = high score
    if query_lower in title_lower:
        return 80

    # Check if all query words are in title
    query_words = set(query_lower.split())
    title_words = set(title_lower.split())

    if not query_words:
        return 0

    # Calculate percentage of query words found in title
    matching_words = query_words.intersection(title_words)
    match_percentage = len(matching_words) / len(query_words) * 100

    # At least 70% of words must match
    if match_percentage >= 70:
        return int(match_percentage)

    return 0

def handle_book_download(book_title, download_dir=None):
    """Handle book search and download"""
    # Create folder based on search term if not specified
    if download_dir is None:
        download_dir = os.path.join(os.getcwd(), sanitize_folder_name(book_title))

    # Create the download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)

    print(f"\n[bold cyan]Searching for book: {book_title}[/bold cyan]\n")
    print(f"[dim]Downloads will be saved to: {download_dir}[/dim]\n")

    # Search all sources - Anna's Archive first as it has the most comprehensive collection
    all_results = (
        search_annas_archive(book_title) +
        search_gutendex(book_title) +
        search_openlibrary(book_title) +
        search_standard_ebooks(book_title) +
        search_feedbooks(book_title) +
        search_123freebook(book_title)
    )

    if not all_results:
        print("[red]No results found.[/red]")
        return

    # Calculate relevance scores and filter
    scored_results = []
    for result in all_results:
        score = calculate_relevance(book_title, result['title'])
        if score > 0:  # Only keep results with some relevance
            result['relevance'] = score
            scored_results.append(result)

    # Sort by relevance (highest first)
    scored_results.sort(key=lambda x: x['relevance'], reverse=True)

    # Limit to top 15 most relevant results
    top_results = scored_results[:15]

    if not top_results:
        print("[red]No relevant results found.[/red]")
        print("[yellow]Try different search terms or check spelling.[/yellow]")
        return

    print(f"\n[bold]Found {len(top_results)} relevant results:[/bold]\n")
    for idx, item in enumerate(top_results):
        print(f"[{idx}] [cyan]{item['title']}[/cyan] by [magenta]{item['author']}[/magenta] ([yellow]{item['source']}[/yellow])")

    print("\n")
    selection = Prompt.ask("Enter the number of the book to download", choices=[str(i) for i in range(len(top_results))])
    selected = top_results[int(selection)]

    print(f"\n[bold]Selected:[/bold] {selected['title']} by {selected['author']}\n")
    url = get_download_links(selected)

    if url:
        # Display URL info based on source
        if isinstance(url, dict):
            if url.get('needs_ia_handling'):
                print(f"[blue]Source:[/blue] Internet Archive")
                print(f"[blue]Item ID:[/blue] {url['ia_id']}\n")
            elif url.get('needs_annas_handling'):
                print(f"[blue]Source:[/blue] Anna's Archive")
                print(f"[blue]Book ID:[/blue] {url['md5']}\n")
        else:
            print(f"[blue]Download URL:[/blue] {url}\n")

        success = download_file(url, selected["title"], download_dir)

        # If download failed, suggest alternatives
        if not success and len(top_results) > 1:
            print("\n[yellow]Download failed. Here are your options:[/yellow]")
            if selected['source'] == 'Internet Archive':
                print("[yellow]1. Internet Archive books may require borrowing/authentication[/yellow]")
                print("[yellow]2. Many are blocked on work/school networks[/yellow]")
                print(f"[yellow]3. Try other sources from the {len(top_results)} results above:[/yellow]")
                for idx, result in enumerate(top_results):
                    if result['source'] != 'Internet Archive':
                        print(f"   [{idx}] {result['title']} - [green]{result['source']}[/green]")
            else:
                print("[yellow]Try selecting a different result from the search results above.[/yellow]")
    else:
        print("[red]No downloadable format found for this entry.[/red]")

# ============== MANGA FUNCTIONS ==============

def show_manga_sites():
    """Display all supported manga sites"""
    table = Table(title="Supported Manga Sites", show_header=True, header_style="bold magenta")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Site Name", style="green")
    table.add_column("URL", style="blue")

    for idx, site in enumerate(MANGA_SITES, 1):
        table.add_row(str(idx), site["name"], site["url"])

    print(table)

def search_manga_site(site, query):
    """Search a specific manga site for a query"""
    results = []
    error_msg = None

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Site-specific search implementations
        if 'mangadex.org' in site['url']:
            # MangaDex API search
            api_url = f"https://api.mangadex.org/manga?title={quote(query)}&limit=10"
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', []):
                    title = item.get('attributes', {}).get('title', {}).get('en', 'Unknown')
                    manga_id = item.get('id', '')
                    url = f"https://mangadex.org/title/{manga_id}"
                    results.append({
                        'title': title,
                        'url': url,
                        'site': site['name']
                    })

        elif 'manganato.com' in site['url']:
            # Manganato search
            search_url = f"https://manganato.com/search/story/{quote(query.replace(' ', '_'))}"
            response = requests.get(search_url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.select('.search-story-item')
                for item in items[:10]:
                    link = item.select_one('a.item-img')
                    title_elem = item.select_one('h3.item-title a')
                    if link and title_elem:
                        results.append({
                            'title': title_elem.text.strip(),
                            'url': link['href'],
                            'site': site['name']
                        })

        elif 'mangakakalot.com' in site['url']:
            # Mangakakalot search
            search_url = f"https://mangakakalot.com/search/story/{quote(query.replace(' ', '_'))}"
            response = requests.get(search_url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.select('.story_item')
                for item in items[:10]:
                    link = item.select_one('a')
                    if link:
                        results.append({
                            'title': link.text.strip(),
                            'url': link['href'],
                            'site': site['name']
                        })

        elif 'natomanga.com' in site['url']:
            # NatoManga search
            search_url = f"https://www.natomanga.com/search?q={quote(query)}"
            response = requests.get(search_url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.select('.manga-item, .search-item, article')
                for item in items[:10]:
                    link = item.select_one('a[href*="/manga/"]')
                    title_elem = item.select_one('.manga-title, .title, h3, h2')
                    if link and title_elem:
                        full_url = urljoin(site['url'], link['href'])
                        results.append({
                            'title': title_elem.text.strip(),
                            'url': full_url,
                            'site': site['name']
                        })

        elif 'chapmanganato.to' in site['url']:
            # Chapmanganato search
            search_url = f"https://chapmanganato.to/search/story/{quote(query.replace(' ', '_'))}"
            response = requests.get(search_url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.select('.search-story-item')
                for item in items[:10]:
                    link = item.select_one('a.item-img')
                    title_elem = item.select_one('h3 a')
                    if link and title_elem:
                        results.append({
                            'title': title_elem.text.strip(),
                            'url': link['href'],
                            'site': site['name']
                        })

    except requests.exceptions.Timeout:
        error_msg = "timeout"
    except requests.exceptions.ConnectionError:
        error_msg = "blocked/unreachable"
    except Exception as e:
        error_msg = "error"

    return results, error_msg

def search_all_manga_sites(query):
    """Search all manga sites for a query"""
    print(f"\n[bold cyan]Searching for '{query}' across all sites...[/bold cyan]\n")
    all_results = []
    success_count = 0
    failed_count = 0
    blocked_sites = []

    for site in MANGA_SITES:
        print(f"[yellow]Searching {site['name']}...[/yellow]", end=" ")
        results, error = search_manga_site(site, query)

        if error:
            failed_count += 1
            blocked_sites.append(f"{site['name']} ({error})")
            print(f"[red]✗ {error}[/red]")
        elif results:
            success_count += 1
            all_results.extend(results)
            print(f"[green]✓ Found {len(results)} result(s)[/green]")
        else:
            print(f"[dim]- No results[/dim]")

    # Summary
    print(f"\n[bold]Search Summary:[/bold]")
    print(f"[green]✓ {success_count} site(s) returned results[/green]")
    if failed_count > 0:
        print(f"[red]✗ {failed_count} site(s) failed or blocked[/red]")
        if blocked_sites:
            print(f"[dim]  Failed sites: {', '.join(blocked_sites[:5])}{'...' if len(blocked_sites) > 5 else ''}[/dim]")
    print(f"[cyan]Total results: {len(all_results)}[/cyan]")

    return all_results

def deduplicate_chapters():
    """Remove duplicate chapter versions, keeping only one version per chapter number within the same manga series"""
    cbz_files = glob.glob("*.cbz")

    if not cbz_files:
        return 0, 0

    # Pattern to extract manga series name and chapter number
    # Most manga files follow: "Series Name Volume - Chapter XXXX Title.cbz"
    # We'll use everything before the volume/chapter indicator as the series identifier
    series_chapter_pattern = re.compile(r'^(.+?)\s+(?:\d+\s+-\s+)?Chapter\s+(\d+)', re.IGNORECASE)

    # Group files by (series, chapter_number)
    chapters_map = {}
    for file in cbz_files:
        match = series_chapter_pattern.search(file)
        if match:
            series_name = match.group(1).strip()
            chapter_num = match.group(2)
            key = (series_name, chapter_num)

            if key not in chapters_map:
                chapters_map[key] = []
            chapters_map[key].append(file)

    # For each chapter with duplicates, keep the shortest filename (usually the cleanest)
    # and remove the rest
    removed_count = 0
    kept_count = 0

    for (series, chapter_num), files in chapters_map.items():
        if len(files) > 1:
            # Sort by length (shorter = cleaner filename usually)
            # Then alphabetically as tiebreaker
            files.sort(key=lambda x: (len(x), x))

            # Keep the first one (shortest/cleanest)
            keep_file = files[0]
            duplicate_files = files[1:]

            print(f"\n[yellow]Found {len(files)} versions of {series} Chapter {chapter_num}:[/yellow]")
            print(f"  [green]✓ Keeping:[/green] {keep_file}")

            # Remove duplicates
            for file in duplicate_files:
                try:
                    os.remove(file)
                    removed_count += 1
                    print(f"  [red]✗ Removed:[/red] {file}")
                except Exception as e:
                    print(f"  [red]Error removing {file}: {e}[/red]")

            kept_count += 1
        else:
            kept_count += 1

    return kept_count, removed_count

def cleanup_non_english_manga():
    """Remove manga files with non-English language indicators, keeping English versions"""
    cbz_files = glob.glob("*.cbz")

    if not cbz_files:
        return 0, 0

    # Pattern to detect non-English language codes and indicators
    # Look for common language codes in parentheses, brackets, or standalone
    # Common patterns: (es), [ja], - pt -, Spanish, etc.
    non_english_patterns = [
        # Language codes in parentheses/brackets
        r'\(es\)',  # Spanish
        r'\(ja\)', r'\(jp\)',  # Japanese
        r'\(pt\)', r'\(pt-br\)',  # Portuguese
        r'\(fr\)',  # French
        r'\(de\)',  # German
        r'\(ru\)',  # Russian
        r'\(zh\)', r'\(cn\)',  # Chinese
        r'\(tr\)',  # Turkish
        r'\(ar\)',  # Arabic
        r'\(it\)',  # Italian
        r'\(ko\)', r'\(kr\)',  # Korean
        r'\(pl\)',  # Polish
        r'\(nl\)',  # Dutch
        r'\(sv\)',  # Swedish
        r'\(vi\)',  # Vietnamese
        r'\(th\)',  # Thai
        r'\(id\)',  # Indonesian

        r'\[es\]', r'\[ja\]', r'\[jp\]', r'\[pt\]', r'\[fr\]', r'\[de\]',
        r'\[ru\]', r'\[zh\]', r'\[cn\]', r'\[tr\]', r'\[ar\]', r'\[it\]',
        r'\[ko\]', r'\[kr\]', r'\[pl\]', r'\[nl\]', r'\[sv\]', r'\[vi\]',
        r'\[th\]', r'\[id\]',

        # Language names (standalone or with separators)
        r'\bspanish\b', r'\bespañol\b',
        r'\bjapanese\b', r'\b日本語\b',
        r'\bportuguese\b', r'\bportuguês\b',
        r'\bfrench\b', r'\bfrançais\b',
        r'\bgerman\b', r'\bdeutsch\b',
        r'\brussian\b', r'\bрусский\b',
        r'\bchinese\b', r'\b中文\b',
        r'\bturkish\b', r'\btürkçe\b',
        r'\barabic\b', r'\bعربي\b',
        r'\bitalian\b', r'\bitaliano\b',
        r'\bkorean\b', r'\b한국어\b',
    ]

    # Compile all patterns into one regex (case-insensitive)
    combined_pattern = re.compile('|'.join(non_english_patterns), re.IGNORECASE)

    english_files = []
    non_english_files = []

    for file in cbz_files:
        # If file contains any non-English language indicator, mark for removal
        if combined_pattern.search(file):
            non_english_files.append(file)
        else:
            # No language indicator found = assume English (or English by default)
            english_files.append(file)

    # Remove non-English files
    removed_count = 0
    for file in non_english_files:
        try:
            os.remove(file)
            removed_count += 1
            print(f"[yellow]Removed:[/yellow] {file}")
        except Exception as e:
            print(f"[red]Error removing {file}: {e}[/red]")

    return len(english_files), removed_count

def get_mangadex_chapter_info(manga_url, language='en'):
    """Get available chapter information from MangaDex"""
    try:
        # Extract manga ID from URL
        manga_id = manga_url.split('/title/')[-1].split('/')[0].split('?')[0]

        # Get chapters from MangaDex API
        api_url = f"https://api.mangadex.org/manga/{manga_id}/feed"
        params = {
            'translatedLanguage[]': language,
            'limit': 500,  # Get many chapters
            'order[chapter]': 'asc'
        }

        response = requests.get(api_url, params=params, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()

        # Extract chapter numbers
        chapters = []
        for item in data.get('data', []):
            attrs = item.get('attributes', {})
            chapter_num = attrs.get('chapter')
            if chapter_num:
                try:
                    chapters.append(float(chapter_num))
                except:
                    pass

        if not chapters:
            return None

        chapters.sort()
        return {
            'total': len(chapters),
            'first': chapters[0],
            'last': chapters[-1],
            'all_chapters': chapters
        }
    except Exception as e:
        return None

def download_manga(url, chapters=None, bundle=False, language=None, english_only=False, download_dir=None):
    """Download manga using the manga-downloader binary"""
    # Save current directory and change to download directory
    original_dir = os.getcwd()

    # Get the absolute path to the manga-downloader binary
    script_dir = os.path.dirname(os.path.abspath(__file__))
    manga_downloader_path = os.path.join(script_dir, "manga-downloader")

    if download_dir:
        os.makedirs(download_dir, exist_ok=True)
        os.chdir(download_dir)
        print(f"[dim]Downloads will be saved to: {download_dir}[/dim]\n")

    cmd = [manga_downloader_path]

    # Add flags first (before URL and chapters)
    # Add language filter
    # If english_only is True, download only English
    # Otherwise, use specified language or download all languages
    if english_only:
        cmd.extend(["--language", "en"])
    elif language:
        cmd.extend(["--language", language])

    if bundle:
        cmd.append("--bundle")

    # Then add URL and chapters
    if url:
        cmd.append(url)

    if chapters:
        cmd.append(chapters)

    print(f"\n[bold cyan]Running:[/bold cyan] {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True)

        # Verify download completed
        cbz_files = glob.glob("*.cbz")
        if cbz_files:
            print(f"\n[bold green]✓ Successfully downloaded {len(cbz_files)} chapter(s)[/bold green]")
            if english_only:
                print(f"[dim]Language filter: English only[/dim]")
        else:
            print("\n[bold yellow]⚠ No files were downloaded[/bold yellow]")

        # Always deduplicate chapters (remove duplicate versions of the same chapter)
        print("\n[bold cyan]Checking for duplicate chapter versions...[/bold cyan]")
        kept_count, dedup_removed_count = deduplicate_chapters()
        if dedup_removed_count > 0:
            print(f"\n[bold green]✓ Removed {dedup_removed_count} duplicate chapter version(s)[/bold green]")
            print(f"[bold green]✓ Final chapter count: {kept_count}[/bold green]")
        else:
            print(f"[bold green]✓ No duplicates found - {kept_count} unique chapter(s) downloaded[/bold green]")

    except subprocess.CalledProcessError as e:
        print(f"\n[red]Error: Download failed with exit code {e.returncode}[/red]")

        # Check if it's a "No chapters found" error
        if chapters:
            print(f"\n[yellow]Possible issues:[/yellow]")
            print(f"  1. The specified chapter range '{chapters}' might not exist")
            print(f"  2. Some manga use decimal numbers (1.1, 1.2) or special chapters")
            print(f"  3. 'Official Colored' versions may have different numbering")
            print(f"\n[cyan]Suggestions:[/cyan]")
            print(f"  • Try without specifying chapters to download all available")
            print(f"  • Try a different result from the search (e.g., non-colored version)")
            print(f"  • Use the manga URL directly with './manga-downloader {url}'")
        # Restore original directory before exiting
        if download_dir:
            os.chdir(original_dir)
        sys.exit(1)
    except FileNotFoundError:
        print("[red]Error: manga-downloader binary not found in current directory[/red]")
        print("[yellow]Make sure you're running this script from the BookDownloader directory[/yellow]")
        # Restore original directory before exiting
        if download_dir:
            os.chdir(original_dir)
        sys.exit(1)
    finally:
        # Always restore original directory
        if download_dir:
            os.chdir(original_dir)

def handle_manga_download(url=None, chapters=None, bundle=False, language=None, english_only=False, interactive=False, search_mode=False, search_query=None, download_dir=None):
    """Handle manga download"""
    manga_title = None  # Track manga title for folder creation

    if interactive or not url or search_mode:
        print("\n[bold cyan]Manga Download - Interactive Mode[/bold cyan]\n")

        # Search mode - let user search for manga by title
        if search_mode or search_query:
            if not search_query:
                search_query = Prompt.ask("[cyan]Enter manga title to search[/cyan]")

            manga_title = search_query  # Save for folder creation
            results = search_all_manga_sites(search_query)

            if not results:
                print("\n[red]No results found.[/red]")
                print("[yellow]Note: Some sites may be blocked by your network/firewall.[/yellow]")
                print("[yellow]Try using --url with a direct manga URL instead.[/yellow]")
                return

            print(f"\n[bold green]Found {len(results)} results:[/bold green]\n")

            # Display results in a table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("No.", style="cyan", width=4)
            table.add_column("Title", style="green")
            table.add_column("Site", style="yellow")

            for idx, result in enumerate(results):
                table.add_row(str(idx + 1), result['title'], result['site'])

            print(table)
            print()

            # Let user select a result
            selection = Prompt.ask(
                "[cyan]Enter the number of the manga to download (or 'exit' to cancel)[/cyan]",
                choices=[str(i + 1) for i in range(len(results))] + ["exit"]
            )

            if selection.lower() == "exit":
                print("Cancelled.")
                return

            selected = results[int(selection) - 1]
            url = selected['url']
            print(f"\n[bold]Selected:[/bold] [green]{selected['title']}[/green] from [yellow]{selected['site']}[/yellow]")
            print(f"[blue]URL:[/blue] {url}\n")

        # Direct URL mode - show supported sites
        else:
            show_manga_sites()
            print("\n")
            url = Prompt.ask("[cyan]Enter the manga series URL[/cyan]")

        # Check available chapters for MangaDex
        if 'mangadex.org' in url:
            print(f"[dim]Checking available chapters...[/dim]")
            chapter_info = get_mangadex_chapter_info(url, language='en')
            if chapter_info:
                print(f"\n[bold cyan]Available Chapters:[/bold cyan]")
                print(f"  Total: {chapter_info['total']} chapters")
                print(f"  Range: Chapter {chapter_info['first']:.0f} - {chapter_info['last']:.0f}")

                # Show warning if chapters don't start at 1
                if chapter_info['first'] > 1:
                    print(f"  [yellow]⚠ Note: This version starts at Chapter {chapter_info['first']:.0f}, not Chapter 1[/yellow]")
                    print(f"  [yellow]  (Colored/special versions often only have certain chapters)[/yellow]")
                print()

        # Ask for chapters
        chapters = Prompt.ask(
            "[cyan]Enter chapter range (e.g., '1-10', '1,3,5-10', or leave empty for all)[/cyan]",
            default=""
        )

        if not chapters:
            print("[yellow]No chapter range specified - will prompt to download all chapters[/yellow]")

        # Ask for bundle option
        bundle_choice = Prompt.ask(
            "[cyan]Bundle all chapters into one file?[/cyan]",
            choices=["yes", "no"],
            default="no"
        )
        bundle = bundle_choice.lower() == "yes"

        # Language selection - default to English only
        print("\n[bold cyan]Language Options:[/bold cyan]")
        print("[yellow]1. English only (downloads only English versions) [DEFAULT][/yellow]")
        print("[yellow]2. Specific language (e.g., 'en', 'es', 'ja')[/yellow]")
        print("[yellow]3. All languages (downloads everything)[/yellow]")

        lang_choice = Prompt.ask(
            "[cyan]Choose option[/cyan]",
            choices=["1", "2", "3"],
            default="1"
        )

        if lang_choice == "1":
            english_only = True
            language = None
        elif lang_choice == "2":
            language = Prompt.ask(
                "[cyan]Enter language code (e.g., 'en', 'es', 'ja')[/cyan]"
            )
            english_only = False
        else:
            language = None
            english_only = False

    # Create download directory based on manga title or search query
    if download_dir is None and manga_title:
        download_dir = os.path.join(os.getcwd(), sanitize_folder_name(manga_title))

    download_manga(
        url,
        chapters if chapters else None,
        bundle,
        language if language else None,
        english_only,
        download_dir
    )

# ============== MAIN ==============

def main():
    parser = argparse.ArgumentParser(
        description="Universal Downloader - Download books and manga from legal sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download a book
  python3 downloader.py --book "Pride and Prejudice"

  # Search for manga across all sites (NEW!)
  python3 downloader.py --manga --search "one punch man"

  # Download manga by URL (English only - RECOMMENDED)
  python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10 --english-only

  # Download manga (specific language)
  python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10 --language es

  # Interactive mode (will ask if you want to search or use URL)
  python3 downloader.py --manga

  # List manga sites
  python3 downloader.py --manga --list
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--book', type=str, metavar='TITLE', help='Search and download a book')
    mode_group.add_argument('--manga', action='store_true', help='Manga download mode')

    # Manga-specific options
    parser.add_argument('--url', type=str, help='Manga series URL (for manga mode)')
    parser.add_argument('--chapters', type=str, help='Chapter range, e.g., "1-10" (for manga mode)')
    parser.add_argument('--bundle', action='store_true', help='Bundle chapters into one file (for manga mode)')
    parser.add_argument('--language', type=str, help='Language code, e.g., "en" (for manga mode)')
    parser.add_argument('--english-only', action='store_true', help='Download all languages but keep only English versions (for manga mode)')
    parser.add_argument('--list', action='store_true', help='List supported manga sites')
    parser.add_argument('--search', type=str, metavar='TITLE', help='Search for manga by title across all sites (for manga mode)')

    args = parser.parse_args()

    # If no arguments, show interactive menu
    if not any(vars(args).values()):
        print("\n[bold cyan]Universal Downloader[/bold cyan]")
        print("[yellow]Download books and manga from legal, free sources[/yellow]\n")

        choice = Prompt.ask(
            "What would you like to download?",
            choices=["book", "manga", "exit"],
            default="book"
        )

        if choice == "book":
            book_title = Prompt.ask("\n[cyan]Enter book title to search[/cyan]")
            handle_book_download(book_title)
        elif choice == "manga":
            # Ask if user wants to search or use direct URL
            manga_mode = Prompt.ask(
                "\n[cyan]How would you like to find your manga?[/cyan]",
                choices=["search", "url"],
                default="search"
            )
            if manga_mode == "search":
                handle_manga_download(interactive=True, search_mode=True)
            else:
                handle_manga_download(interactive=True)
        else:
            print("Goodbye!")
            sys.exit(0)

    # Handle book mode
    elif args.book:
        handle_book_download(args.book)

    # Handle manga mode
    elif args.manga:
        if args.list:
            show_manga_sites()
            print("\n[yellow]To download manga, use:[/yellow]")
            print("[cyan]python3 downloader.py --manga --search \"manga title\"[/cyan]")
            print("[cyan]python3 downloader.py --manga --url [URL] --english-only[/cyan]")
        elif args.search:
            handle_manga_download(
                chapters=args.chapters,
                bundle=args.bundle,
                language=args.language,
                english_only=getattr(args, 'english_only', False),
                search_mode=True,
                search_query=args.search
            )
        else:
            handle_manga_download(
                args.url,
                args.chapters,
                args.bundle,
                args.language,
                getattr(args, 'english_only', False)
            )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
