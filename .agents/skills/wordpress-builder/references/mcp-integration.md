# WordPress Model Context Protocol (MCP) & Abilities API Reference

The Model Context Protocol (MCP) is an open-source standard enabling AI models (such as Antigravity, Claude Code, and Cursor) to safely read and write data and run code on external services. In WordPress, MCP integration is built on top of the native **WordPress Abilities API**.

---

## 1. Architecture Overview

The integration relies on a three-tier model bridging natural language queries directly to secure execution:

```mermaid
graph LR
    Agent[AI Agent / LLM] <-->|MCP Protocol| Adapter[wordpress/mcp-adapter]
    Adapter <-->|Abilities API| WP[WordPress Core / Plugins]
```

*   **Abilities API**: Standardized registration of features (methods, inputs, and schemas) inside WordPress plugins/themes.
*   **wordpress/mcp-adapter**: A plugin that acts as an MCP server. It scans registered WordPress Abilities and exposes them as MCP Tools, Resources, and Prompts.

---

## 2. Registering custom Abilities (WordPress 6.9+)

To make a custom backend function, plugin manager, or styling tool visible to an AI agent, you must register it as an "Ability" in your theme's `functions.php` or a custom plugin.

Use the `wp_abilities_api_init` hook to register Abilities:

```php
<?php
/**
 * Plugin Name: Custom Business Mockup Abilities
 * Description: Registers customized capabilities and makes them accessible to AI agents.
 */

add_action('wp_abilities_api_init', 'register_custom_builder_abilities');

function register_custom_builder_abilities() {
    register_ability('builder/update_colors', array(
        'description' => 'Update the primary and secondary colors of the website theme options.',
        'permission_callback' => 'current_user_can_manage_options', // Enforces security
        'args' => array(
            'primary_color' => array(
                'type' => 'string',
                'description' => 'Hex code for the primary brand color (e.g. #1e293b).',
                'required' => true,
                'sanitize_callback' => 'sanitize_hex_color'
            ),
            'secondary_color' => array(
                'type' => 'string',
                'description' => 'Hex code for the secondary brand color (e.g. #ea580c).',
                'required' => true,
                'sanitize_callback' => 'sanitize_hex_color'
            )
        ),
        'callback' => 'execute_color_update'
    ));
}

function execute_color_update($args) {
    update_option('wp_mockup_primary_color', $args['primary_color']);
    update_option('wp_mockup_secondary_color', $args['secondary_color']);
    
    return array(
        'status' => 'success',
        'message' => 'Theme brand colors updated successfully.'
    );
}
```

---

## 3. Configuring the MCP Adapter

To make these abilities available to external agentic tools, install and activate the official `mcp-adapter` plugin.

### Exposing Specific Tools
By default, the `mcp-adapter` hides all registered abilities. You must specify which abilities to expose in your site's `wp-config.php` or via the database options:

```php
// In wp-config.php
define('WP_MCP_EXPOSE_ABILITIES', array(
    'builder/update_colors',
    'core/create_page',
    'core/get_site_info'
));
```

---

## 4. Connecting AI Clients (Transport Configurations)

AI agents can interact with the WordPress MCP server through two main connection transports:

### Transport A: STDIO via WP-CLI (Local Development)
Ideal for local agents (like Antigravity or Claude Code) running directly on the host system. You add the server to your agent's config file (e.g., `mcp_config.json`):

```json
{
  "mcpServers": {
    "wordpress-local": {
      "command": "docker",
      "args": [
        "compose",
        "run",
        "--rm",
        "wp-cli",
        "wp",
        "mcp",
        "run"
      ],
      "cwd": "/Users/jonathanowens/Projects/wordpress-builder"
    }
  }
}
```

### Transport B: HTTP/SSE (Remote Connections)
For remote or cloud-hosted agent instances. The `mcp-adapter` plugin starts a Server-Sent Events (SSE) server endpoint at `http://localhost:8080/wp-json/mcp/v1/sse`:

```json
{
  "mcpServers": {
    "wordpress-remote": {
      "url": "http://localhost:8080/wp-json/mcp/v1/sse",
      "headers": {
        "Authorization": "Basic YWRtaW46YWJjZCBlZmdoIGlqa2wgbW5vcA=="
      }
    }
  }
}
```
*Note: Ensure you include the Basic Auth header with your Application Password to authenticate the MCP session.*
