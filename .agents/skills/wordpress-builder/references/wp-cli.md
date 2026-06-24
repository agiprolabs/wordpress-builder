# WP-CLI Command Reference for Agentic Builders

WP-CLI is the command-line interface for WordPress. It allows administrative actions to be executed without a web browser. The standalone WordPress builder container exposes WP-CLI through Docker Compose under the service name `wp-cli`.

---

## 1. Core Verification & Installation

### Check Installation Status
```bash
docker compose run --rm wp-cli wp core is-installed
```

### Install WordPress Core
```bash
docker compose run --rm wp-cli wp core install \
  --url=http://localhost:8080 \
  --title="My Business" \
  --admin_user=admin \
  --admin_password=adminpassword \
  --admin_email=admin@example.com \
  --skip-email
```

### Reset / Re-create Database
```bash
# Create DB if not exists
docker compose run --rm wp-cli wp db create --defaults

# Reset existing database tables (destructive)
docker compose run --rm wp-cli wp db reset --yes --defaults
```

---

## 2. Post & Page Management

### Create a Gutenberg Block Page
When creating pages with Gutenberg blocks, you must pass the Gutenberg HTML comments (`<!-- wp:... -->`) directly in the post content. Ensure all internal double quotes are correctly escaped if executing from shell wrappers, or write from Python/JS scripts.
```bash
docker compose run --rm wp-cli wp post create \
  --post_title="Services" \
  --post_name="services" \
  --post_type=page \
  --post_status=publish \
  --post_content='<!-- wp:paragraph --><p>Our services include expert installation.</p><!-- /wp:paragraph -->' \
  --porcelain
```
*Note: The `--porcelain` flag returns only the newly created Post ID.*

### Delete Default/Sample Content
```bash
# Delete Sample Page (ID 2) and Hello World Post (ID 1)
docker compose run --rm wp-cli wp post delete 1 2 --force
```

### List Pages & Slugs
```bash
docker compose run --rm wp-cli wp post list --post_type=page --format=table
```

---

## 3. Configuration & Options API

The Options API is used to store settings, feature toggles, and metadata. You can access and update settings dynamically:

### Get Option Value
```bash
docker compose run --rm wp-cli wp option get blogdescription
```

### Update Core Option Values
```bash
# Set static homepage
docker compose run --rm wp-cli wp option update show_on_front page
docker compose run --rm wp-cli wp option update page_on_front 12

# Update Site Slogan
docker compose run --rm wp-cli wp option update blogdescription "Premium Roofing Contractor"
```

### Inject Custom Mockup Metadata
```bash
docker compose run --rm wp-cli wp option update wp_mockup_vertical "home_services"
docker compose run --rm wp-cli wp option update wp_mockup_phone "(555) 019-2834"
```

---

## 4. Navigation Menu Assembly

### Create a Custom Menu
```bash
docker compose run --rm wp-cli wp menu create "Primary Menu"
```

### Add a Page to a Menu
```bash
docker compose run --rm wp-cli wp menu item add-post "Primary Menu" [page_id]
```

### Assign Menu to Theme Location
```bash
# Assumes the theme defines a location named 'primary'
docker compose run --rm wp-cli wp menu location assign "Primary Menu" primary
```

---

## 5. Themes & Plugins

### List Active Plugins / Themes
```bash
docker compose run --rm wp-cli wp plugin list
docker compose run --rm wp-cli wp theme list
```

### Activate a Theme
```bash
docker compose run --rm wp-cli wp theme activate twentytwentyfour
```

### Activate a Custom Plugin
```bash
docker compose run --rm wp-cli wp plugin activate my-custom-plugin
```

---

## 6. Migration & Domain Search-Replace

When moving the database SQL dump to a production host, all occurrences of the local development domain must be replaced to prevent layout breakages:

```bash
docker compose run --rm wp-cli wp search-replace "http://localhost:8080" "https://my-live-site.com"
```
