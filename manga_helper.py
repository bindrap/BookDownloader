#!/usr/bin/env python3
"""
Manga Downloader Helper Script
Provides information about supported manga sites and helps with manga downloads
"""
import argparse
import subprocess
import sys
import glob
import os
import re
from rich import print
from rich.table import Table
from rich.prompt import Prompt

# Supported manga sites from manga-downloader
SUPPORTED_SITES = [
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

def show_sites():
    """Display all supported manga sites"""
    table = Table(title="Supported Manga Sites", show_header=True, header_style="bold magenta")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Site Name", style="green")
    table.add_column("URL", style="blue")

    for idx, site in enumerate(SUPPORTED_SITES, 1):
        table.add_row(str(idx), site["name"], site["url"])

    print(table)
    print("\n[yellow]To download manga:[/yellow]")
    print("1. Visit one of the sites above")
    print("2. Find the manga series page (NOT a chapter page)")
    print("3. Copy the URL")
    print("4. Use: [cyan]./manga-downloader [URL][/cyan]")
    print("5. Or use: [cyan]./manga-downloader [URL] [chapter-range][/cyan]")
    print("\n[yellow]Examples:[/yellow]")
    print("[green]./manga-downloader https://mangadex.org/title/XXXXX/one-piece[/green]")
    print("[green]./manga-downloader https://mangadex.org/title/XXXXX/one-piece 1-10[/green]")
    print("[green]./manga-downloader https://mangadex.org/title/XXXXX/one-piece 1-10 --bundle[/green]")

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

def interactive_mode():
    """Interactive mode to guide users through manga download"""
    print("\n[bold cyan]Manga Download Helper - Interactive Mode[/bold cyan]\n")

    show_sites()

    print("\n")
    choice = Prompt.ask(
        "Would you like to download a manga now?",
        choices=["yes", "no"],
        default="no"
    )

    if choice.lower() == "yes":
        url = Prompt.ask("\n[cyan]Enter the manga series URL[/cyan]")

        chapters = Prompt.ask(
            "[cyan]Enter chapter range (e.g., '1-10' or '1,3,5-10')[/cyan]",
            default=""
        )

        bundle = Prompt.ask(
            "[cyan]Bundle all chapters into one file?[/cyan]",
            choices=["yes", "no"],
            default="no"
        )

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
            bundle.lower() == "yes",
            language if language else None,
            english_only
        )

def main():
    parser = argparse.ArgumentParser(
        description="Manga Downloader Helper - Shows supported sites and helps with downloads"
    )
    parser.add_argument('--list', action='store_true', help='List all supported manga sites')
    parser.add_argument('--url', type=str, help='Manga series URL to download')
    parser.add_argument('--chapters', type=str, help='Chapter range (e.g., "1-10" or "1,3,5-10")')
    parser.add_argument('--bundle', action='store_true', help='Bundle all chapters into one file')
    parser.add_argument('--language', type=str, help='Language code (e.g., "en", "es", "ja")')

    args = parser.parse_args()

    if args.list:
        show_sites()
    elif args.url:
        download_manga(args.url, args.chapters, args.bundle, args.language)
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
