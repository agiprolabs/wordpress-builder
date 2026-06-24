# WordPress REST API Reference for Agentic Builders

The WordPress REST API provides API endpoints for applications, allowing agents to interact with a site by sending and receiving JSON objects.

---

## 1. Authentication Strategies

To perform write actions (create/update/delete posts, plugins, configurations), API requests must be authenticated.

### Strategy A: Application Passwords (Recommended for Local Dev)
Introduced in WordPress 5.6. You can generate a unique password for a specific user from the WordPress Profile screen:
1. Navigate to **Users > Profile** in the admin dashboard.
2. Scroll to **Application Passwords**.
3. Generate a new password (e.g. `abcd efgh ijkl mnop`).

#### Using Application Passwords in HTTP Headers
Encode the credentials as Basic Auth (`Username:Application_Password` base64 encoded):
```http
Authorization: Basic YWRtaW46YWJjZCBlZmdoIGlqa2wgbW5vcA==
Content-Type: application/json
```

### Strategy B: JWT Authentication (Production Integration)
Requires a JWT plugin (e.g., *JWT Authentication for WP REST API*).
1. Send credentials to `/wp-json/jwt-auth/v1/token`.
2. Extract token from response.
3. Attach to headers:
```http
Authorization: Bearer [your-jwt-token]
```

---

## 2. Core REST API Endpoints

All routes are relative to `/wp-json/`.

### Pages (Mockup Structural Units)
*   **List Pages**: `GET /wp/v2/pages`
*   **Create Page**: `POST /wp/v2/pages`
*   **Update Page**: `POST /wp/v2/pages/<id>`
*   **Delete Page**: `DELETE /wp/v2/pages/<id>`

#### Payload Example: Create Gutenberg Page
```json
{
  "title": "Services",
  "slug": "services",
  "status": "publish",
  "content": "<!-- wp:paragraph --><p>Our services are top-rated.</p><!-- /wp:paragraph -->"
}
```

### Media Assets (Logo, Images, PDFs)
*   **List Media**: `GET /wp/v2/media`
*   **Upload Media**: `POST /wp/v2/media`

#### Request Format for Media Uploads
Must use `multipart/form-data`.
*   Header: `Content-Disposition: attachment; filename="hero-roof.jpg"`
*   Header: `Content-Type: image/jpeg`
*   Body: Binary file stream.

### Site Options & Metadata
*   **Get Settings**: `GET /wp/v2/settings`
*   **Update Settings**: `POST /wp/v2/settings` (Requires Administrator capability)

#### Payload Example: Update Site Title
```json
{
  "title": "Santa Fe Roofing",
  "description": "Professional Gutters & Roof Repair"
}
```

---

## 3. Defining Custom REST API Routes

To build bespoke backend tools (calculators, leads pipelines, scraper dashboards), custom PHP routes can be registered using the `rest_api_init` hook.

Add the following pattern to `custom-plugins/mu-plugins/custom-api.php`:

```php
<?php
/**
 * Plugin Name: Bespoke REST Endpoints
 * Description: Dynamically registers endpoints for agentic tools or widget integration.
 */

add_action('rest_api_init', function () {
    register_rest_route('custom/v1', '/estimate', array(
        'methods' => 'POST',
        'callback' => 'handle_custom_estimate_submission',
        'permission_callback' => '__return_true' // Restrict as appropriate for security
    ));
});

function handle_custom_estimate_submission($request) {
    $params = $request->get_json_params();
    $business_type = sanitize_text_field($params['type'] ?? '');
    
    // Process calculation logic
    $total = 0;
    if ($business_type === 'roofing') {
        $total = 5000;
    }
    
    return new WP_REST_Response(array(
        'status' => 'success',
        'estimated_cost' => $total,
        'message' => 'Quote generated dynamically.'
    ), 200);
}
```
*Accessible via: `POST http://localhost:8080/wp-json/custom/v1/estimate`*
