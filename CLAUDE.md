❯ cd Documents/BookDownloader
❯ python3 downloader.py

Universal Downloader
Download books and manga from legal, free sources

What would you like to download? [book/manga/exit] (book): book

Enter book title to search: The Life of Pi

Searching for book: The Life of Pi

Searching Project Gutenberg...
Warning: Gutenberg search failed: HTTPSConnectionPool(host='gutendex.com', port=443): Read timed out. (read timeout=10)
Searching Open Library...

Found 10 results:

[0] Life of Pi by Yann Martel (Internet Archive)
[1] Life on the Mississippi by Mark Twain (Internet Archive)
[2] King Lear by William Shakespeare (Internet Archive)
[3] Tao te Ching by 老子, James Legge, Gia-Fu Feng, Stacie Mallinson, Jeff Mallinson, Peter Kang, John Minford, Stephen Mitchell (Internet Archive)
[4] The Pickwick Papers by Charles Dickens (Internet Archive)
[5] Hong lou meng by Tsʻao, Hsüeh-chʻin., (qing) Cao, xue qin, Cao xue qin (Internet Archive)
[6] Essais by Montaigne, Michel de (Internet Archive)
[7] Hamlet by William Shakespeare (Internet Archive)
[8] Bible by Bible (Internet Archive)
[9] Paradise Lost by John Milton (Internet Archive)


Enter the number of the book to download [0/1/2/3/4/5/6/7/8/9]: 0

Selected: Life of Pi by Yann Martel

Download URL: https://archive.org/download/lhistoiredepirom0000mart/lhistoiredepirom0000mart.epub

Downloading: Life_of_Pi.epub

Download failed: 401 Client Error: Unauthorized for url: https://dn721700.ca.archive.org/0/items/lhistoiredepirom0000mart/lhistoiredepirom0000mart.epub
❯ python3 downloader.py

Universal Downloader
Download books and manga from legal, free sources

What would you like to download? [book/manga/exit] (book): manga

How would you like to find your manga? [search/url] (search): search

Manga Download - Interactive Mode

Enter manga title to search: Naruto

Searching for 'Naruto' across all sites...

Searching Asura Scans... - No results
Searching Chapmanganato... - No results
Searching InManga... - No results
Searching LHTranslation... - No results
Searching LSComic... - No results
Searching Manga Monks... - No results
Searching MangaBat... - No results
Searching MangaDex... ✓ Found 10 result(s)
Searching Mangakakalot.com... - No results
Searching Mangakakalot.tv... - No results
Searching Manganato... - No results
Searching Manganelo.com... - No results
Searching Manganelo.tv... - No results
Searching MangaPanda... - No results
Searching NatoManga... - No results
Searching ReadMangaBat... - No results
Searching TCB Scans (.com)... - No results
Searching TCB Scans (.net)... - No results
Searching TCB Scans (.org)... - No results

Search Summary:
✓ 1 site(s) returned results
Total results: 10

Found 10 results:

┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ No.  ┃ Title                                                             ┃ Site     ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 1    │ Naruto                                                            │ MangaDex │
│ 2    │ Naruto (Official Colored)                                         │ MangaDex │
│ 3    │ Boruto: Naruto Next Generations                                   │ MangaDex │
│ 4    │ Renge to Naruto!                                                  │ MangaDex │
│ 5    │ Naruto: Kai no Sho - Shin Ero Ninjutsu Kansei!!                   │ MangaDex │
│ 6    │ Naruto: Rin no Sho - Konoha Gaiden: Ichiraku nite…                │ MangaDex │
│ 7    │ NARUTO Fanfiction  : Reborn / Rebirth                             │ MangaDex │
│ 8    │ NARUTO: Konoha Shinden—Yukemuri Ninpouchou                        │ MangaDex │
│ 9    │ Naruto: The Whorl within the Spiral                               │ MangaDex │
│ 10   │ NARUTO: Sasuke Retsuden—Uchiha no Matsuei to Tenkyuu no Hoshikuzu │ MangaDex │
└──────┴───────────────────────────────────────────────────────────────────┴──────────┘

Enter the number of the manga to download (or 'exit' to cancel) [1/2/3/4/5/6/7/8/9/10/exit]: 2

Selected: Naruto (Official Colored) from MangaDex
URL: https://mangadex.org/title/a787b10a-02d0-46c0-8236-0d01d69ad4a3

Enter chapter range (e.g., '1-10' or '1,3,5-10') (): 1-2
Bundle all chapters into one file? [yes/no] (no): no

Language Options:
1. English only (downloads only English versions) [DEFAULT]
2. Specific language (e.g., 'en', 'es', 'ja')
3. All languages (downloads everything)
Choose option [1/2/3] (1): 1

Running: ./manga-downloader --language en https://mangadex.org/title/a787b10a-02d0-46c0-8236-0d01d69ad4a3 1-2

Naruto - Digital Colored Comics - Konohamaru!!:     46/46 [======================================] 100 % archiving 
Naruto - Digital Colored Comics - Naruto Uzumaki!!: 108/108 [======================================] 100 % archiving 

Verifying English-only download...
Removed: Naruto - Digital Colored Comics 1 - Chapter 0001 Naruto Uzumaki!!.cbz
Removed: Naruto - Digital Colored Comics 2 - Chapter 0002 Konohamaru!!.cbz

⚠ Found and removed 2 non-English file(s) (this shouldn't happen)
✓ Kept 0 English file(s)
❯ ls
book_downloader.py  downloader.py  LICENSE  manga-downloader  manga_helper.py  __pycache__  README.md

  ~/Documents/BookDownloader   master !1 ❯                    
