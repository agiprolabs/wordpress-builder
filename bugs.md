# WordPress Builder - Active Bugs and Fixes Log

This document tracks bugs encountered during the validation of the standalone WordPress Builder pipeline, specifically under the site-migration and plugin-audit dogfood workflows.

---

## Resolved Bugs

1. **MySQL TLS/SSL Socket Connection Failure**
   - **Symptom**: `mariadb-dump` inside the `wp-cli` container failed with `TLS/SSL error: SSL is required, but the server does not support it` when running `wp db export`.
   - **Cause**: The database container was explicitly booted with `--ssl=0`, and the MariaDB client command was called with `--no-defaults` (ignoring our local `disable-ssl.cnf`), forcing certificate validation on a non-secured port.
   - **Fix**: Removed `--ssl=0` from [docker-compose.yml](file:///Users/jonathanowens/Projects/wordpress-builder/docker-compose.yml) so MySQL auto-generates certificates and supports SSL. Additionally, refactored database exports in [builder.py](file:///Users/jonathanowens/Projects/wordpress-builder/builder.py) to run `mysqldump` directly on the `wp_mockup_db` container and pipe stdout to the host staging folder.

2. **Media Import Write Permission Mismatch**
   - **Symptom**: `wp media import` failed with `Unable to create directory wp-content/uploads/2026/06. Is its parent directory writable by the server?`.
   - **Cause**: The Alpine-based `wp-cli` container defaults to running as user `www-data` (UID 82), while the Debian-based `wordpress` container owns the `/var/www/html` volume as `www-data` (UID 33) with `755` permissions, blocking write access for UID 82.
   - **Fix**: Configured `wp-cli` service inside [docker-compose.yml](file:///Users/jonathanowens/Projects/wordpress-builder/docker-compose.yml) with `user: "33:33"` so that all WP-CLI commands execute with the same user ID as the web server.

3. **Legacy Host Network Unreachable (No Route to Host)**
   - **Symptom**: `[Errno 65] No route to host` when executing python media migration against legacy domains (like `https://armandgilbert.com`).
   - **Cause**: Occurs when the local runner loses internet access or the target domain is temporarily offline or blocking programmatic crawler requests.
   - **Fix**: Implemented robust try-except error catching in [builder.py](file:///Users/jonathanowens/Projects/wordpress-builder/builder.py) to skip failing asset downloads gracefully, log the network warning, and fall back to clean text-based Gutenberg block generation, ensuring the compilation completes successfully even in an offline environment.

