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
        response = requests.get(GUTENDEX_API + requests.utils.quote(query), timeout=10)
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
        response = requests.get(OPENLIBRARY_API + requests.utils.quote(query), timeout=10)
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

    return None

def download_file_ia(ia_id, filename_on_server, title):
    """Download a file from Internet Archive with proper authentication"""
    print(f"[cyan]Attempting Internet Archive download with browser simulation...[/cyan]")

    # Clean up the title for local filename
    local_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    local_filename = local_filename.replace(" ", "_")[:100]

    # Extract extension from server filename
    ext = os.path.splitext(filename_on_server)[1]
    if not ext or ext.lower() not in ['.epub', '.pdf', '.txt', '.mobi', '.azw3']:
        ext = ".epub"
    local_filename += ext

    try:
        # Step 1: Visit the item page first (like a human would)
        item_page_url = f"https://archive.org/details/{ia_id}"
        print(f"[dim]Step 1: Visiting book page...[/dim]")
        session.get(item_page_url, timeout=10)
        time.sleep(0.5)  # Brief delay like human browsing

        # Step 2: Try direct download with referer
        download_url = f"https://archive.org/download/{ia_id}/{filename_on_server}"
        print(f"[dim]Step 2: Initiating download...[/dim]")

        headers = {
            'Referer': item_page_url,
            'Accept': 'application/epub+zip,application/pdf,*/*',
        }

        with session.get(download_url, stream=True, timeout=30, headers=headers) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0

            print(f"[green]Downloading:[/green] {local_filename}")
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"Progress: {percent:.1f}%", end='\r')

        print(f"\n[bold green]✓ Successfully downloaded to {local_filename}[/bold green]")
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"\n[red]✗ 401 Unauthorized - Internet Archive requires authentication[/red]")
            print(f"[yellow]This book may require borrowing/lending on archive.org[/yellow]")
            print(f"[yellow]Try manually visiting: {item_page_url}[/yellow]")
        else:
            print(f"\n[red]✗ Download failed: {e}[/red]")
        if os.path.exists(local_filename):
            os.remove(local_filename)
        return False
    except Exception as e:
        print(f"\n[red]✗ Download failed: {e}[/red]")
        if os.path.exists(local_filename):
            os.remove(local_filename)
        return False

def download_file(url, title):
    """Download a book file"""
    # Handle string URLs (simple downloads)
    if isinstance(url, str):
        filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = filename.replace(" ", "_")[:100]

        # Extract extension from URL
        ext = os.path.splitext(url.split('?')[0])[1]
        valid_extensions = ['.epub', '.pdf', '.txt', '.mobi', '.azw3']

        if not ext or ext.lower() not in valid_extensions:
            ext = ".epub"

        filename += ext

        print(f"[green]Downloading:[/green] {filename}")
        try:
            # Add referer header for better compatibility
            headers = {'Referer': url.rsplit('/', 1)[0] + '/'}
            with session.get(url, stream=True, timeout=30, headers=headers) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"Progress: {percent:.1f}%", end='\r')
            print(f"\n[bold green]✓ Saved to {filename}[/bold green]")
            return True
        except Exception as e:
            print(f"\n[red]✗ Download failed: {e}[/red]")
            if os.path.exists(filename):
                os.remove(filename)
            return False

    # Handle dict URLs (Internet Archive special handling)
    elif isinstance(url, dict) and url.get('needs_ia_handling'):
        return download_file_ia(url['ia_id'], url['filename'], title)

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

def handle_book_download(book_title):
    """Handle book search and download"""
    print(f"\n[bold cyan]Searching for book: {book_title}[/bold cyan]\n")

    # Search all sources
    all_results = (
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
        # Display URL info
        if isinstance(url, dict):
            print(f"[blue]Source:[/blue] Internet Archive")
            print(f"[blue]Item ID:[/blue] {url['ia_id']}\n")
        else:
            print(f"[blue]Download URL:[/blue] {url}\n")

        success = download_file(url, selected["title"])

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

def download_manga(url, chapters=None, bundle=False, language=None, english_only=False):
    """Download manga using the manga-downloader binary"""
    cmd = ["./manga-downloader"]

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

        # Clean up non-English files if requested (safety net - shouldn't be needed with --language en)
        if english_only:
            print("\n[bold cyan]Verifying English-only download...[/bold cyan]")
            english_count, removed_count = cleanup_non_english_manga()
            if removed_count > 0:
                print(f"\n[bold yellow]⚠ Found and removed {removed_count} non-English file(s) (this shouldn't happen)[/bold yellow]")
                print(f"[bold green]✓ Kept {english_count} English file(s)[/bold green]")
            elif english_count > 0:
                print(f"\n[bold green]✓ All {english_count} file(s) are English - download successful[/bold green]")
            else:
                print("\n[bold yellow]⚠ No files found[/bold yellow]")

    except subprocess.CalledProcessError as e:
        print(f"\n[red]Error: Download failed with exit code {e.returncode}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        print("[red]Error: manga-downloader binary not found in current directory[/red]")
        print("[yellow]Make sure you're running this script from the BookDownloader directory[/yellow]")
        sys.exit(1)

def handle_manga_download(url=None, chapters=None, bundle=False, language=None, english_only=False, interactive=False, search_mode=False, search_query=None):
    """Handle manga download"""
    if interactive or not url or search_mode:
        print("\n[bold cyan]Manga Download - Interactive Mode[/bold cyan]\n")

        # Search mode - let user search for manga by title
        if search_mode or search_query:
            if not search_query:
                search_query = Prompt.ask("[cyan]Enter manga title to search[/cyan]")

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

        # Ask for chapters
        chapters = Prompt.ask(
            "[cyan]Enter chapter range (e.g., '1-10' or '1,3,5-10')[/cyan]",
            default=""
        )

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

    download_manga(
        url,
        chapters if chapters else None,
        bundle,
        language if language else None,
        english_only
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
