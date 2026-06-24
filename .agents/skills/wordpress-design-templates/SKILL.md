---
name: wordpress-design-templates
description: Guidelines, design skills, block templates, pattern workflows, and customization guidelines to build professional modern sites using wordpress-builder.
---

# WordPress Design & Template Customization Skill

This skill equips agents with the professional design systems, Full Site Editing (FSE) block structures, legacy content migration guidelines, and verification checklists necessary to compile high-end, responsive WordPress mockup sites.

---

## 1. Block Theme Architecture & theme.json Presets

Modern WordPress design relies on block-based themes (Full Site Editing / FSE) controlled by `theme.json` rather than arbitrary styling in PHP templates.

### Theme File Structure
A professional FSE theme must include:
*   `style.css`: Contains block theme header metadata.
*   `theme.json`: Defines the design tokens (colors, font-sizes, fluid typography, spacing).
*   `templates/`: Structured HTML templates containing Gutenberg blocks (`index.html`, `home.html`, `page.html`).
*   `parts/`: Shared layout segments (`header.html`, `footer.html`).
*   `patterns/`: Pre-designed reusable blocks automatically discovered by WordPress (e.g. `hero-split.php`, `services-grid.php`).

### The Global Settings Configuration (`theme.json`)
The theme's settings must declare fluid typography, preset palettes, and responsive layouts:
```json
{
  "$schema": "https://schemas.wp.org/trunk/theme.json",
  "version": 2,
  "settings": {
    "appearanceTools": true,
    "color": {
      "palette": [
        { "slug": "primary", "color": "#09090b", "name": "Primary Dark" },
        { "slug": "secondary", "color": "#2563eb", "name": "Secondary Accent Blue" },
        { "slug": "background", "color": "#ffffff", "name": "Base Light Background" },
        { "slug": "muted", "color": "#f4f4f5", "name": "Muted Gray" }
      ]
    },
    "typography": {
      "fontSizes": [
        { "slug": "small", "size": "0.875rem", "name": "Small" },
        { "slug": "normal", "size": "1rem", "name": "Normal" },
        { "slug": "medium", "size": "1.25rem", "name": "Medium" },
        { "slug": "large", "size": "clamp(1.75rem, 4vw, 2.5rem)", "name": "Large (Clamped)" },
        { "slug": "huge", "size": "clamp(2.5rem, 6vw, 4rem)", "name": "Huge (Clamped)" }
      ]
    }
  }
}
```

---

## 2. Dynamic Spacing & Responsive Typography Rules

Broken layout scaling on mobile viewports is a key indicator of poor quality. You must enforce these rules:

1.  **Clamped Fonts**: Never use large fixed font sizes (e.g. `50px`) for headings. Enforce fluid typography using CSS `clamp()` variables defined in the theme (e.g. `var(--wp--preset--font-size--huge)` which resolves to `clamp(2.5rem, 6vw, 4rem)`).
2.  **Fluid Spacing**: Avoid raw pixels for margins or paddings. Use viewport-clamped spacers:
    ```css
    padding-top: clamp(3rem, 8vw, 6rem);
    padding-bottom: clamp(3rem, 8vw, 6rem);
    ```
3.  **Variable Color Reference**: DO NOT write hardcoded hex values (like `color: #ff0000`) within post block markup. Reference the CSS variables mapping:
    *   `var(--wp--preset--color--primary)`
    *   `var(--wp--preset--color--secondary)`
    *   `var(--wp--preset--color--background)`
    *   `var(--wp--preset--color--muted)`

---

## 3. Legacy Site Content Ingestion & Conversion

When converting a legacy website to a modern WordPress site, follow these migration steps:

1.  **Tag Parsing**: Scan the legacy HTML files. Identify key content segments (Hero copy, Service sections, Client reviews, Contact data). Exclude tracking elements, analytics snippets, and absolute asset URLs.
2.  **Media Registration**: Save the legacy site's images locally, copy them to the WordPress app container, and register them as media attachments to get local `wp-content/uploads/` URLs.
3.  **Modernize Copy**: Rewrite headlines to be action-focused, update dates/contexts to represent the current year (2026), but preserve critical operational details (phone numbers, physical addresses, taglines).
4.  **Layout to Pattern Mapping**: Map legacy layout structures directly to modern FSE block patterns:
    *   *Hero Sliders* ➡️ Premium Split Hero block pattern.
    *   *Bullet Lists / Grid Features* ➡️ Premium Services Grid.
    *   *Text testimonials* ➡️ Premium Testimonials Grid.
    *   *Address details / Forms* ➡️ Premium Contact Split Section.

---

## 4. The Dynamic Pattern Injection Workflow

To generate page content cleanly and prevent syntax errors, load pre-styled theme patterns and dynamically populate placeholders rather than compiling massive blocks programmatically.

### Pre-configured Theme Block Patterns
Ensure these files are present inside the theme's `/patterns/` directory:

*   `hero-split.php`: A split layout featuring a high-contrast H1 heading, description, visual CTA buttons, and a showcase image.
*   `services-grid.php`: A 3-column service grid utilizing cards with subtle borders, muted backgrounds, and hover indicators.
*   `testimonials-grid.php`: A 2-column client testimonial section with blockquotes and author metadata.
*   `contact-details.php`: A split contact section displaying phone/email/address details next to a message card.
*   `about-media.php`: An editorial "About Us" split container with side-by-side team narrative and image.

### Placeholder Replacement Pattern
When compiling page content, load the block file contents, replace placeholders, and insert the parsed blocks directly into the page's post content fields:

```python
# python template parsing reference
def parse_pattern_template(file_path: str, replacements: dict) -> str:
    with open(file_path, "r") as f:
        code = f.read()
    # Strip metadata PHP header
    if "<?php" in code:
        code = code.split("?>", 1)[1].strip()
    # Substitute values
    for k, v in replacements.items():
        code = code.replace(k, v)
    return code
```

---

## 5. Advanced Styling Utilities

Use registered CSS helper classes inside your Gutenberg templates to deliver premium visual interactions:

### A. Glassmorphism Panels
Apply the `.premium-glass-card` class on group cards, headers, or estimation sections to render a modern glass shined look:
```css
.premium-glass-card {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08);
}
```

### B. Micro-Animations
Enqueue custom hover scaling for interactive elements:
```css
.wp-block-button__link {
    transition: all 0.2s ease-in-out;
}
.wp-block-button__link:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}
```

---

## 6. Design Auditing Checklist

A site is only ready when it passes these checks:

*   [ ] **Responsiveness Check**: Verify that the homepage does not overflow on a `320px` wide mobile layout. Text must fit cleanly.
*   [ ] **Theme variable compliance**: Ensure there are no hardcoded color codes (`#ffffff`, `#000000`) inside the block style attributes. They must reference `--wp--preset--color--*`.
*   [ ] **Dynamic Link Mapping**: Check that all navigation, footer, and portfolio link strings lead to appropriate page routing slugs without loop redirects.
*   [ ] **No Placeholders**: Confirm that all images utilize valid `wp-content/uploads/` path strings instead of external placeholder URLs.
*   [ ] **SEO Integrity**: Heading levels must scale sequentially (`H1` -> `H2` -> `H3`) to preserve semantic accessibility.
