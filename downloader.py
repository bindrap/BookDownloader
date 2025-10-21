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
from rich import print
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Book API endpoints
GUTENDEX_API = "https://gutendex.com/books?search="
OPENLIBRARY_API = "https://openlibrary.org/search.json?q="
IA_METADATA_API = "https://archive.org/metadata/"

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
            response = requests.get(IA_METADATA_API + ia_id, timeout=10)
            response.raise_for_status()
            files = response.json().get("files", [])
            for ext in [".epub", ".pdf", ".txt"]:
                for f in files:
                    if f["name"].endswith(ext):
                        return f"https://archive.org/download/{ia_id}/{f['name']}"
        except Exception as e:
            print(f"[red]Error getting download link: {e}[/red]")
    return None

def download_file(url, title):
    """Download a book file"""
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = filename.replace(" ", "_")[:100]

    # Extract extension from URL, but filter out invalid extensions
    ext = os.path.splitext(url.split('?')[0])[1]
    valid_extensions = ['.epub', '.pdf', '.txt', '.mobi', '.azw3']

    # If no extension or invalid extension, default to .epub
    if not ext or ext.lower() not in valid_extensions:
        ext = ".epub"

    filename += ext

    print(f"[green]Downloading:[/green] {filename}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
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
        print(f"\n[bold green]Saved to {filename}[/bold green]")
        return True
    except Exception as e:
        print(f"\n[red]Download failed: {e}[/red]")
        if os.path.exists(filename):
            os.remove(filename)
        return False

def handle_book_download(book_title):
    """Handle book search and download"""
    print(f"\n[bold cyan]Searching for book: {book_title}[/bold cyan]\n")

    all_results = search_gutendex(book_title) + search_openlibrary(book_title)

    if not all_results:
        print("[red]No results found.[/red]")
        return

    print(f"\n[bold]Found {len(all_results)} results:[/bold]\n")
    for idx, item in enumerate(all_results):
        print(f"[{idx}] [cyan]{item['title']}[/cyan] by [magenta]{item['author']}[/magenta] ([yellow]{item['source']}[/yellow])")

    print("\n")
    selection = Prompt.ask("Enter the number of the book to download", choices=[str(i) for i in range(len(all_results))])
    selected = all_results[int(selection)]

    print(f"\n[bold]Selected:[/bold] {selected['title']} by {selected['author']}\n")
    url = get_download_links(selected)

    if url:
        print(f"[blue]Download URL:[/blue] {url}\n")
        download_file(url, selected["title"])
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

def cleanup_non_english_manga():
    """Remove manga files with language suffixes, keeping only English (no suffix) versions"""
    cbz_files = glob.glob("*.cbz")

    if not cbz_files:
        return 0, 0

    # Pattern to detect language suffixes
    # English files: "Title - Chapter XXXX.cbz"
    # Non-English: "Title - Chapter XXXX SomeText.cbz" or "Title - Chapter XXXX SomeText v2.cbz"
    # Match files that have text after chapter number and before .cbz
    non_english_pattern = re.compile(r'- Chapter \d{4} .+\.cbz$', re.IGNORECASE)

    english_files = []
    non_english_files = []

    for file in cbz_files:
        if non_english_pattern.search(file):
            non_english_files.append(file)
        else:
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

    if url:
        cmd.append(url)

    if chapters:
        cmd.append(chapters)

    if bundle:
        cmd.append("--bundle")

    # Only add language filter if explicitly specified
    # Note: Without language filter, ALL available languages will be downloaded
    # If english_only is True, we download all and clean up after
    if language and not english_only:
        cmd.extend(["--language", language])

    print(f"\n[bold cyan]Running:[/bold cyan] {' '.join(cmd)}\n")

    try:
        subprocess.run(cmd, check=True)

        # Clean up non-English files if requested
        if english_only:
            print("\n[bold cyan]Cleaning up non-English files...[/bold cyan]")
            english_count, removed_count = cleanup_non_english_manga()
            if removed_count > 0:
                print(f"\n[bold green]✓ Kept {english_count} English file(s)[/bold green]")
                print(f"[bold yellow]✓ Removed {removed_count} non-English file(s)[/bold yellow]")
            elif english_count > 0:
                print(f"\n[bold green]✓ All {english_count} file(s) are English - no cleanup needed[/bold green]")
            else:
                print("\n[bold yellow]⚠ No files found to clean up[/bold yellow]")

    except subprocess.CalledProcessError as e:
        print(f"\n[red]Error: Download failed with exit code {e.returncode}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        print("[red]Error: manga-downloader binary not found in current directory[/red]")
        print("[yellow]Make sure you're running this script from the BookDownloader directory[/yellow]")
        sys.exit(1)

def handle_manga_download(url=None, chapters=None, bundle=False, language=None, english_only=False, interactive=False):
    """Handle manga download"""
    if interactive or not url:
        print("\n[bold cyan]Manga Download - Interactive Mode[/bold cyan]\n")
        show_manga_sites()

        print("\n")
        url = Prompt.ask("[cyan]Enter the manga series URL[/cyan]")

        chapters = Prompt.ask(
            "[cyan]Enter chapter range (e.g., '1-10' or '1,3,5-10')[/cyan]",
            default=""
        )

        bundle_choice = Prompt.ask(
            "[cyan]Bundle all chapters into one file?[/cyan]",
            choices=["yes", "no"],
            default="no"
        )
        bundle = bundle_choice.lower() == "yes"

        print("\n[bold cyan]Language Options:[/bold cyan]")
        print("[yellow]1. English only (downloads all, keeps only English versions)[/yellow]")
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

  # Download manga (English only - RECOMMENDED)
  python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10 --english-only

  # Download manga (specific language)
  python3 downloader.py --manga --url https://mangadex.org/title/XXXXX/one-piece --chapters 1-10 --language es

  # Interactive manga download
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
            print("[cyan]python3 downloader.py --manga --url [URL] --english-only[/cyan]")
        else:
            handle_manga_download(args.url, args.chapters, args.bundle, args.language, getattr(args, 'english_only', False))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
