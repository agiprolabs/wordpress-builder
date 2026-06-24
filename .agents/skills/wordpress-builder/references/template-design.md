# WordPress Block Theme & Template Design Guide

This reference details the construction of block themes (FSE - Full Site Editing), configuration of `theme.json`, custom Gutenberg blocks styling, clamped typography, dynamic gradients, and layout structure patterns.

---

## 1. Block Theme Architecture

A modern WordPress block theme relies on HTML template files and a `theme.json` file rather than PHP templates. The directory structure is flat and modular:

```text
custom-theme/
├── theme.json            # Global settings, style definitions, and layout schema
├── style.css             # Theme metadata header (and optional custom utility styles)
├── functions.php         # Theme support declaration and enqueue scripts/styles
├── templates/            # Entire page templates
│   ├── index.html        # Fallback template
│   ├── home.html         # Front page template
│   ├── page.html         # Default page template
│   └── 404.html          # Error page template
└── parts/                # Reusable structural components
    ├── header.html       # Shared header section
    └── footer.html       # Shared footer section
```

### `style.css` Metadata Header
Must include the following format to trigger block-theme engine recognition:
```css
/*
Theme Name: Custom Agent Premium Block Theme
Theme URI: https://github.com/jonathanowens/wordpress-builder
Author: Antigravity Code Builder
Description: A high-performance, responsive FSE theme generated dynamically for mockups.
Version: 1.0.0
Requires at least: 6.0
Tested up to: 6.5
Requires PHP: 7.4
License: GNU General Public License v2 or later
Text Domain: custom-theme
*/
```

---

## 2. Configured Customizing with `theme.json`

The `theme.json` file is the central nervous system of modern theme design, defining CSS variables, block configurations, editor UI permissions, and styling structures.

### Standard `theme.json` Configuration Schema

```json
{
  "$schema": "https://schemas.wp.org/trunk/theme.json",
  "version": 2,
  "settings": {
    "appearanceTools": true,
    "border": {
      "color": true,
      "radius": true,
      "style": true,
      "width": true
    },
    "color": {
      "custom": true,
      "customGradient": true,
      "link": true,
      "palette": [
        {
          "slug": "primary",
          "color": "#111827",
          "name": "Primary Dark"
        },
        {
          "slug": "secondary",
          "color": "#3b82f6",
          "name": "Secondary Accent Blue"
        },
        {
          "slug": "background",
          "color": "#ffffff",
          "name": "Base Light Background"
        },
        {
          "slug": "muted",
          "color": "#f3f4f6",
          "name": "Muted Gray"
        }
      ],
      "gradients": [
        {
          "slug": "primary-gradient",
          "gradient": "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
          "name": "Primary Dark Shimmer"
        },
        {
          "slug": "accent-gradient",
          "gradient": "linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)",
          "name": "Accent Gradient Blue"
        }
      ]
    },
    "layout": {
      "contentSize": "800px",
      "wideSize": "1200px"
    },
    "spacing": {
      "blockGap": true,
      "margin": true,
      "padding": true,
      "units": ["px", "em", "rem", "vh", "vw", "%"]
    },
    "typography": {
      "customFontSize": true,
      "fontSizes": [
        {
          "slug": "small",
          "size": "0.875rem",
          "name": "Small"
        },
        {
          "slug": "normal",
          "size": "1rem",
          "name": "Normal"
        },
        {
          "slug": "medium",
          "size": "1.25rem",
          "name": "Medium"
        },
        {
          "slug": "large",
          "size": "clamp(1.75rem, 4vw, 2.5rem)",
          "name": "Large (Clamped)"
        },
        {
          "slug": "huge",
          "size": "clamp(2.25rem, 6vw, 4rem)",
          "name": "Huge (Clamped)"
        }
      ],
      "fontFamilies": [
        {
          "fontFamily": "System-UI, -apple-system, sans-serif",
          "slug": "system",
          "name": "System UI"
        }
      ]
    }
  },
  "styles": {
    "color": {
      "background": "var(--wp--preset--color--background)",
      "text": "var(--wp--preset--color--primary)"
    },
    "typography": {
      "fontFamily": "var(--wp--preset--font-family--system)",
      "lineHeight": "1.6"
    },
    "elements": {
      "link": {
        "color": {
          "text": "var(--wp--preset--color--secondary)"
        },
        "typography": {
          "textDecoration": "none"
        },
        ":hover": {
          "typography": {
            "textDecoration": "underline"
          }
        }
      },
      "button": {
        "color": {
          "text": "#ffffff",
          "background": "var(--wp--preset--color--secondary)"
        },
        "border": {
          "radius": "8px"
        },
        "spacing": {
          "padding": {
            "top": "0.75rem",
            "bottom": "0.75rem",
            "left": "1.5rem",
            "right": "1.5rem"
          }
        }
      }
    }
  }
}
```

---

## 3. Clamped Typography & Premium Styles

To achieve modern premium aesthetics that display elegantly on mobile, tablet, and desktop without ad-hoc CSS media queries, apply these best practices:

### A. Viewport-Relative Clamped Typography
Using `clamp(min, preferred, max)` scales font sizes dynamically.
*   **Hero Headers**: `clamp(2.5rem, 8vw, 4.5rem)`
*   **Section Title (H2)**: `clamp(1.75rem, 5vw, 2.75rem)`
*   **Body Copy**: `1.125rem` (clamped text size doesn't benefit body paragraphs).

### B. Custom Spacing & Column Alignments
Always align text layout structures inside Gutenberg block parameters using preset spacings:
*   Use `blockGap` configurations to maintain consistent padding between paragraph and list blocks inside groups.
*   Prefer `gap: 2rem` layout constraints on flexbox wrappers over hardcoded margins.

### C. Glassmorphism and Backdrop Filters
For premium styling blocks (like hero cards and overlays), register standard CSS configurations:
```css
.premium-glass-card {
    background: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.08);
}
```

---

## 4. Open-Source Block Theme Standards & Reference Patterns

To build websites that compete with professional modern designers, agents should study and match the design standards of leading open-source WordPress Full Site Editing (FSE) block themes:
*   **Ona / Ollie**: Known for high-whitespace editorial aesthetics, clean geometric sans-serif font choices, and smooth neutral background scaling.
*   **Kadence FSE**: Focuses on rich functional business grids, bold call-to-actions, and robust preset custom color schemes.
*   **Spectra One / Raft**: Extremely lightweight, focusing on clean grid spacing, flex layout controls, and minimal custom stylesheet bloat.

### A. The Theme `/patterns/` Directory Layout
To enable modular page compilation and allow users to insert pre-designed sections directly in the Site Editor, define templates inside the theme's `/patterns/` directory. WordPress automatically registers any PHP files placed here.

Each pattern file must start with a metadata comment block:
```php
<?php
/**
 * Title: Premium Split Hero
 * Slug: premium-fse-theme/hero-split
 * Categories: header, featured
 * Description: A professional split hero section with text, CTA buttons, and a showcase image.
 */
?>
<!-- Gutenberg HTML markup follows -->
```

### B. Registering Core Visual Patterns
Below are the reference block patterns that must be placed inside the `custom-theme/premium-fse-theme/patterns/` directory:

1.  **Split Hero Banner (`hero-split.php`)**: Split grid with a high-contrast H1 heading, description, visual CTA buttons, and side image container.
2.  **Services Columns Grid (`services-grid.php`)**: A 3-column service grid with cards using subtle borders, light background colors, and clean margins.
3.  **Testimonials Grid (`testimonials-grid.php`)**: A 2-column client review section with italic text, block quotes, and author subtitles.
4.  **Contact Split Section (`contact-details.php`)**: A responsive contact layout containing phone/email/address details alongside a message block.

### C. Naive Agent Ingestion & Dynamic Placeholder Pattern
Instead of compiling massive inline block markup manually (which is prone to nesting errors), the agent must load these pre-styled patterns and replace placeholders programmatically:

```python
def generate_page_content_from_pattern(pattern_path: str, replacements: dict) -> str:
    """Reads a theme pattern file, strips the PHP header, and replaces placeholders."""
    with open(pattern_path, 'r') as f:
        content = f.read()
    
    # Strip the PHP header if present
    if "<?php" in content:
        content = content.split("?>", 1)[1].strip()
        
    # Apply replacements
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
        
    return content
```

#### Example Usage for Home/Contact Pages:
```python
replacements = {
    "{{BUSINESS_PHONE}}": "+1 (555) 019-2834",
    "{{BUSINESS_EMAIL}}": "hello@designstudio.com",
    "{{BUSINESS_ADDRESS}}": "123 Creative Way, Suite 400"
}
homepage_content = (
    generate_page_content_from_pattern("patterns/hero-split.php", {}) +
    generate_page_content_from_pattern("patterns/services-grid.php", {}) +
    generate_page_content_from_pattern("patterns/testimonials-grid.php", {}) +
    generate_page_content_from_pattern("patterns/contact-details.php", replacements)
)
```

---

## 5. Design Auditing Checklist

Before packaging a theme mockup, perform this compliance checklist:

1.  **Clamping Verification**: Ensure header fonts scale down to at least `2rem` on small phone screens (iPhone SE viewport width: 320px).
2.  **No Core Layout Bleeds**: Check that group blocks aligned as `alignwide` or `alignfull` do not produce horizontal scrollbars.
3.  **Color Preset Compliance**: Verify that all inline styling definitions refer to `--wp--preset--color--*` instead of hardcoded hex values. This guarantees that user color palette changes inside WordPress Admin Site Editor automatically propagate everywhere.
4.  **Semantic Nesting**: Heading elements should follow hierarchical order (`H1` -> `H2` -> `H3` -> `H4`) to ensure accessibility (a11y) and SEO compliance.
5.  **Valid Media URL Registration**: Check that all images utilize valid `wp-content/uploads/` path strings instead of absolute source paths from the legacy scraped site.
