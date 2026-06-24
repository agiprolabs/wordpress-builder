# Claude Code: Project Hand-Off & Setup Reference

This document serves as the project status, structural reference, and context for Claude Code to resume task execution.

---

## 1. Project Goal
Recreate the website `https://armandgilbert.com` as a new WordPress block theme running locally on port 8080, matching the original layout, styling, content structures, typography, subpage forms, and sidebars 1:1.

---

## 2. Directory Layout & Paths
*   **Active Workspace**: `/Users/jonathanowens/Projects/prospector`
*   **WordPress Builder Project**: `/Users/jonathanowens/Projects/wordpress-builder`
    *   *Docker Environment*: Run commands in this folder using `docker compose` (WordPress web server, MySQL db, and WP-CLI containers).
*   **Block Theme Directory**: `/Users/jonathanowens/Projects/wordpress-builder/custom-theme/premium-fse-theme`
    *   `templates/front-page.html`: The layout structure for the static homepage.
    *   `templates/page.html`: The layout structure for subpages (e.g. About, FAQ, Contact).
    *   `parts/header.html` & `parts/footer.html`: Global header/footer blocks.
    *   `theme.json`: Theme colors, palettes, and global FSE rules.
*   **Style Overrides Plugin**: `/Users/jonathanowens/Projects/wordpress-builder/premium-mockup-styles.php`
    *   Must-Use plugin containing CSS overrides (`vertical-armand_gilbert`) and text variables.
    *   Copied dynamically into the container at `/var/www/html/wp-content/mu-plugins/premium-mockup-styles.php`.
*   **Staged Images Folder**: `/Users/jonathanowens/Projects/prospector/scratch/imported_images/uploads/2026/06`
*   **Crawled Raw HTML Files**: `/Users/jonathanowens/Projects/prospector/scratch/crawled_pages`

---

## 3. Core Automation Scripts
All helper and validation scripts are written in `/Users/jonathanowens/Projects/prospector/scratch/`:

1.  **Migration Pipeline**: [migrate_armand_gilbert.py](file:///Users/jonathanowens/Projects/wordpress-builder/migrate_armand_gilbert.py)
    *   *Function*: Resets the database, purges container uploads, stages 726 media files, secures permissions (`chown www-data:www-data`), batch-imports media, generates clean Gutenberg page blocks from raw scraped subpages, maps URLs/IDs fuzzy-matched, and activates plugins.
    *   *Execution*: `python /Users/jonathanowens/Projects/wordpress-builder/migrate_armand_gilbert.py`
2.  **Missing Assets Downloader**: [download_subpage_images.py](file:///Users/jonathanowens/Projects/prospector/scratch/download_subpage_images.py)
    *   *Function*: Scrapes subpage HTML, downloads missing live assets (testimonials, link overlays, logos), and stores them in the staging folder.
3.  **Image Validation**: [check_images.py](file:///Users/jonathanowens/Projects/prospector/scratch/check_images.py)
    *   *Function*: Checks the HTML image `src` tags on the homepage/about page and queries HTTP response codes (returns 200 for local media).
4.  **Console Diagnostic**: [check_console.py](file:///Users/jonathanowens/Projects/prospector/scratch/check_console.py)
    *   *Function*: Checks browser console errors and CORS blocks during rendering.
5.  **Layout Comparison**: [inspect_comparison.py](file:///Users/jonathanowens/Projects/prospector/scratch/inspect_comparison.py)
    *   *Function*: Compares local and original CSS computed styles, body classes, headings, and wrapper hierarchies.

---

## 4. Current Status
*   **Templates & Routing**: Resolved static front page collision by migrating layouts to `front-page.html`. Closed all container nesting hacks. Layout matches original layout hierarchy: `content-full` -> `home-top`, `hr`, `hr-center`, `intro` slider, `center-highlight` content columns.
*   **Assets & Links**: Imported **726 media library files**. All image urls on home and about pages point to local folders (`http://localhost:8080/wp-content/uploads/2026/06/...`) and return status 200. Zero broken links.
*   **Typography (CORS Fix)**: Downloaded `ColaborateThinRegular` web fonts to `/fonts/` inside the theme folder and serving relative paths to resolve browser CORS blocks. Zero console errors.
*   **Visual comparison screenshots**: Saved in `/Users/jonathanowens/.gemini/antigravity-cli/brain/0ea6aea4-f8eb-43db-837b-923566dd2022/`:
    *   `compare_local_desktop.png` vs `compare_original_desktop.png` (Homepage)
    *   `local_about.png` vs `original_about.png` (About page)
    *   Showcase carousel summary: [armand_gilbert_showcase.md](file:///Users/jonathanowens/.gemini/antigravity-cli/brain/0ea6aea4-f8eb-43db-837b-923566dd2022/armand_gilbert_showcase.md)

---

## 5. Next Steps for Claude Code
To achieve a complete 1:1 pixel-perfect replication, fine-tune the following items:

1.  **Form Layout & Overrides (Gravity Forms)**:
    *   Compare the custom pricing calculator forms on `/get-started/` and contact forms on `/contact-us/`.
    *   Adjust CSS rules inside [premium-mockup-styles.php](file:///Users/jonathanowens/Projects/wordpress-builder/premium-mockup-styles.php) under the `vertical-armand_gilbert` section to match form column layouts, padding, gold buttons, borders, and input fields 1:1.
2.  **Navigation Submenu & Search Styling**:
    *   Align menu list item offsets, gold markers, dropdown indicators, and the search form search icon inside the header part.
3.  **FAQ Accordions/Tabs Javascript**:
    *   Verify if there is any active accordion logic on `/faq/` page and ensure the styling overrides toggle correctly.
4.  **Sidebar Alignment**:
    *   Check sidebar border lines, vertical separator height repeating background alignment, list padding, and widget title heading margins.
