#!/usr/bin/env python3
import argparse
import requests
import sys
import os
from rich import print
from rich.prompt import Prompt

GUTENDEX_API = "https://gutendex.com/books?search="
OPENLIBRARY_API = "https://openlibrary.org/search.json?q="
IA_METADATA_API = "https://archive.org/metadata/"

def search_gutendex(query):
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
    # Sanitize filename
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = filename.replace(" ", "_")[:100]  # Limit filename length

    # Get file extension from URL, but filter out invalid extensions
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

def main():
    parser = argparse.ArgumentParser(description="Search and download free ebooks legally from Project Gutenberg and Internet Archive.")
    parser.add_argument('--book', type=str, help='Book title to search for')
    args = parser.parse_args()

    if not args.book:
        print("[red]Please provide a book title with --book[/red]")
        print("\nExample: python3 book_downloader.py --book \"Pride and Prejudice\"")
        sys.exit(1)

    print(f"\n[bold cyan]Searching for: {args.book}[/bold cyan]\n")

    all_results = search_gutendex(args.book) + search_openlibrary(args.book)

    if not all_results:
        print("[red]No results found.[/red]")
        sys.exit(0)

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

if __name__ == "__main__":
    main()
