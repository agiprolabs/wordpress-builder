---
name: wordpress-builder
description: Automate, orchestrate, build, debug, and package custom WordPress mockups and sites. Contains knowledge of WordPress REST API, WP-CLI, and Model Context Protocol (MCP) Abilities integrations.
---

# WordPress AI Custom Site Builder & Packager Agent Skill

This skill equips agentic developers (like Antigravity, Claude Code, and others) with the operational context, patterns, and troubleshooting protocols required to build, customize, and compile WordPress mockup installations using the standalone WordPress Builder.

---

## 1. Directory Blueprint & Scaffolding

When working inside the `wordpress-builder` workspace, you must adhere to the following scaffolding directory layout:

*   [builder.py](file:///Users/jonathanowens/Projects/wordpress-builder/builder.py): The primary CLI orchestrator for setup, Gutenberg block rendering, options injection, and compiler packaging.
*   [docker-compose.yml](file:///Users/jonathanowens/Projects/wordpress-builder/docker-compose.yml): Runs the WordPress app, MySQL 8.0, and WP-CLI containers.
*   `custom-plugins/`: Write single-file or folder-based custom plugins here. They are auto-copied and activated inside the container.
    *   `mu-plugins/`: Must-use plugins copied to `/wp-content/mu-plugins/` for auto-activation without database entry requirements.
*   `custom-theme/`: Standard theme directory. If a child theme (containing `style.css`) is dropped here, it is activated.
*   `dist/`: Location where the final compiler outputs (e.g. `wp_build_business-name.zip`) are placed.

---

## 2. Core Operational Workflow

To successfully generate and package a mockup site:

1.  **Resolve Inputs**: Ensure you have business details (via CLI options, YAML requirements, or a pre-generated Gutenberg blueprint).
2.  **Verify Containers**: Run the docker services. The builder will automatically boot them if they are stopped.
3.  **Core Installation**: The builder resets the DB and does a fresh install.
4.  **Inject Pages & Gutenberg Layout**:
    *   Gutenberg blocks (from blueprint or queried on-the-fly via Claude AI) are injected into the Homepage.
    *   Inner pages (Services, About, Contact) are auto-generated based on design systems mapped to specific business verticals.
5.  **Load Custom Apps**: Place custom apps/plugins inside `custom-plugins/` to deploy custom calculator scripts, contact forms, or custom hooks.
6.  **Compile and Package**:
    *   The database is exported directly via `mysqldump` on the database container to avoid container permission conflicts.
    *   The `wp-content/` directory, database dump, and a custom `INSTALL.md` guide are compressed into `dist/wp_build_[slug].zip`.

---

## 3. Reference Documentation Index

To explore detailed technical implementations of WordPress integrations, consult the following included references:

1.  **WP-CLI Command Reference**: [wp-cli.md](file:///Users/jonathanowens/Projects/wordpress-builder/.agents/skills/wordpress-builder/references/wp-cli.md) – Essential WP-CLI command sequences for creating posts, options, menus, and theme assets.
2.  **WordPress REST API Reference**: [wordpress-api.md](file:///Users/jonathanowens/Projects/wordpress-builder/.agents/skills/wordpress-builder/references/wordpress-api.md) – Endpoints, payload structures, authentication (Application Passwords, JWT), and custom endpoints.
3.  **Model Context Protocol (MCP) & Abilities API Reference**: [mcp-integration.md](file:///Users/jonathanowens/Projects/wordpress-builder/.agents/skills/wordpress-builder/references/mcp-integration.md) – Implementing, exposing, and consuming WordPress functions and data models using the official `wordpress/mcp-adapter` and WordPress 6.9+ Abilities API.
4.  **Professional Web Design & Ingestion Guide**: [design-skills.md](file:///Users/jonathanowens/Projects/wordpress-builder/.agents/skills/wordpress-builder/references/design-skills.md) – Step-by-step layout strategies, theme customization rules, dynamic font variables, and visual design skills required to build premium modern sites from legacy pages.
5.  **WordPress Design & Template Customization Skill**: [SKILL.md](file:///Users/jonathanowens/Projects/wordpress-builder/.agents/skills/wordpress-design-templates/SKILL.md) – Dedicated customization skill for Full Site Editing (FSE) block themes, custom spacing rules, pattern structures, and design compliance checks.

---

## 4. Troubleshooting Checklist

*   **MySQL SSL/TLS Connection Errors**:
    *   *Symptom*: Client fails with `TLS/SSL error: SSL is required, but the server does not support it`.
    *   *Fix*: Ensure the database container does **NOT** run with `--ssl=0` in `docker-compose.yml`. Let MySQL auto-generate its self-signed certificates.
*   **Write Permission Mismatches (UID/GID)**:
    *   *Symptom*: `mariadb-dump: Can't create/write to file ... (Permission denied)`.
    *   *Fix*: Do not try to run database dumps via `wp-cli wp db export` into volumes mounted to the container (e.g. `/var/www/html/`), because the Alpine-based `wp-cli` container runs as UID 82 (`www-data` in Alpine), while Debian-based `wordpress` directories are owned by UID 33 (`www-data` in Debian).
    *   *Solution*: Run `mysqldump` directly inside the database container (`wp_mockup_db`) and pipe the output to the host file system.
