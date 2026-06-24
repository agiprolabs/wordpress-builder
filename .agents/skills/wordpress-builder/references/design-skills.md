# Professional Web Design & Ingestion Guide for WordPress Blocks

This guide outlines the core design skills, structural blueprints, and template modification practices required for an AI agent to build a high-end, modern website from an existing legacy site using the `wordpress-builder` pipeline.

---

## 1. WordPress Block Editor (Gutenberg) Design System

To construct visually stunning websites that align with professional modern design trends (clean grids, high-contrast accents, typography hierarchy, and glassmorphism), you must utilize the theme-wide FSE configurations via `theme.json` instead of inline styles.

### A. The Core Color Palette
Always map the vertical classification of the business to a precise HSL/RGB palette:
*   **Trust-based Professional (Law, Medical, Corporate)**: Navy Blue (`#09090b` base, `#1e3a8a` primary, `#2563eb` secondary, `#fafaf9` light).
*   **Warm/Organic (Wellness, Food, Editorial)**: Earthy Stone (`#1c1917` base, `#78716c` primary, `#b45309` bronze accent, `#fdfaf7` background).
*   **High-Contrast Action (Home Services, Contracting)**: Dark Charcoal (`#09090b` base, `#1e293b` slate primary, `#ea580c` amber warning accent, `#ffffff` card back).

### B. Inline Variables vs. Hex Codes
**CRITICAL RULE**: Do not write hardcoded hex values (like `color: #ff0000`) within block parameters. If you need custom color styles, reference WordPress CSS custom properties:
*   `var(--wp--preset--color--primary)`
*   `var(--wp--preset--color--secondary)`
*   `var(--wp--preset--color--background)`
*   `var(--wp--preset--color--muted)`

This ensures that if the user alters theme settings in the admin panel, the custom block patterns automatically update.

---

## 2. Structural Typography & Mobile-Responsive Design

A major failure point in naive agent site generation is broken text layout on mobile devices. You must implement viewport-relative clamped spacing:

### A. Clamped Font Size Rules
Define your sizes in the theme config using CSS `clamp()`:
1.  **H1 (Hero Headers)**: `clamp(2.25rem, 6vw, 4rem)` – Scales down on mobile (320px wide) without overflow.
2.  **H2 (Section Titles)**: `clamp(1.75rem, 4.5vw, 2.75rem)`
3.  **H3 (Card Headings)**: `clamp(1.25rem, 3vw, 1.75rem)`
4.  **Body Text**: Enforce static `1rem` to `1.125rem` for optimal reading density.

### B. High-Converting Gutenberg Layout Architecture
Never throw plain paragraphs or columns together. Construct sections using modular nests:
*   **The Section Group Wrapper**: Wrap every major section in a `core/group` block with `alignfull` or `alignwide` and constrained layout settings to prevent horizontal scrolling.
*   **Responsive Spacing**: Enforce consistent padding on sections using relative `rem` or `vh` units:
    ```json
    "style": {
        "spacing": {
            "padding": {
                "top": "clamp(3rem, 8vw, 6rem)",
                "bottom": "clamp(3rem, 8vw, 6rem)"
            }
        }
    }
    ```
*   **Dividers and Spacers**: Avoid raw `core/spacer` blocks. Use `blockGap` in `theme.json` to define uniform margins between structural blocks.

---

## 3. Legacy Site Asset Ingestion & Re-use

When migrating a client site, you must extract structural layouts and sanitise content for re-use:

### A. Ingestion Workflow
1.  **Asset Parsing**: Scan the legacy HTML file for tags (`<img>`, `<video>`, `<picture>`). Exclude tracking pixels and external social avatars.
2.  **Media Upload**: Save the raw images locally, copy them to the WordPress container, and register them as media attachments.
3.  **Copy Writing Modernization**: Rewrite legacy headlines to be action-oriented, updating references to the current year (2026), but preserving exact phone numbers, physical addresses, and primary taglines.

### B. Layout Mapping & Block Patterns
Transform legacy elements into clean Gutenberg blocks by matching them to registered block patterns inside `premium-fse-theme/patterns/`:
*   **Legacy Hero Header / Slider** ➡️ Convert to the Split Hero block pattern (`premium-fse-theme/hero-split`), mapping the main scraped header to the H1 block and the primary call-to-action details.
*   **Services Listing / Core Offerings** ➡️ Convert to the Services Grid pattern (`premium-fse-theme/services-grid`), mapping legacy bullet lists or columns into structured, responsive card elements.
*   **Customer Reviews / Testimonials** ➡️ Convert to the Testimonials Grid pattern (`premium-fse-theme/testimonials-grid`), mapping scraped reviews into standard quote layouts.
*   **Address, Maps, & Forms** ➡️ Convert to the Contact Split Section pattern (`premium-fse-theme/contact-details`), replacing placeholders (`{{BUSINESS_PHONE}}`, `{{BUSINESS_EMAIL}}`, `{{BUSINESS_ADDRESS}}`) with the actual contact details from the legacy website.
*   **Legacy Tables / Floating Sidebars** ➡️ If custom data structures are present, convert to core Columns or Table blocks, maintaining padding and responsive widths.

---

## 4. Advanced Styling Skills (Premium Elements)

To build websites that look premium and custom-coded, incorporate advanced design features:

### A. Glassmorphism Panels
Use this styling class for cards, header blocks, and estimate panels to give a sleek glass shined aesthetic:
```css
.premium-glass-card {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08);
}
```

### B. Custom CSS Utility Injection
Add custom styles in the theme's functions or assets enqueue scripts to enable micro-animations (e.g. lift on hover):
```css
.wp-block-button__link:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}
```

---

## 5. Deployment Verification Checklist

A site is only ready when it passes these checks:
1.  **Responsiveness SE Test**: Render page at `320px` width. Verify no structural blocks overlap and text is legible.
2.  **Redirect Prevention**: Ensure `WP_HOME` and `WP_SITEURL` definitions read the dynamic proxy headers.
3.  **Semantic Hierarchy**: Check that header structure strictly follows nested levels (`H1` -> `H2` -> `H3`) to guarantee SEO integrity and accessibility compliance.
4.  **No Placeholders**: Ensure all images point to valid `wp-content/uploads/` files, not external filler image links.
