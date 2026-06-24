import os
import sys
import json
import yaml
import sqlite3
import subprocess
import time
import re
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import urllib.parse
import httpx

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
WP_BUILDER_DIR = PROJECT_ROOT
DEFAULT_DB_PATH = PROJECT_ROOT.parent / "prospector" / "prospects.db"
DEFAULT_CONFIG_PATH = PROJECT_ROOT.parent / "prospector" / "config.yaml"

def load_anthropic_key(config_path_opt: Optional[str] = None) -> str:
    """Load Anthropic API key from config.yaml or environment variables."""
    # Check custom path or default config
    paths_to_try = []
    if config_path_opt:
        paths_to_try.append(Path(config_path_opt))
    paths_to_try.append(DEFAULT_CONFIG_PATH)
    paths_to_try.append(PROJECT_ROOT / "config.yaml")

    for path in paths_to_try:
        if path.exists():
            try:
                with open(path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    key = config.get("api_keys", {}).get("anthropic", "")
                    if key:
                        return key
            except Exception as e:
                print(f"Warning: Failed to load config from {path}: {e}")
            
    # Try environment variable
    return os.environ.get("ANTHROPIC_API_KEY", "")

def slugify_name(name: str) -> str:
    """Helper to convert business names to URL safe slugs."""
    return "".join(c for c in name.lower() if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "-")

def get_lead_data_from_db(lead_id: int, db_path: str) -> Optional[Dict[str, Any]]:
    """Retrieve lead and crawled details from SQLite database (legacy mode)."""
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Error: Database not found at {db_file}")
        return None
        
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get basic lead data and scoring
    cursor.execute(
        """
        SELECT l.id, l.business_name, l.original_url, l.resolved_url, l.phone, l.address,
               l.rating, l.review_count, l.categories,
               s.opportunity_score, s.fit_score, s.teardown_brief,
               c.email, c.social_links_json
        FROM leads l
        LEFT JOIN scores s ON l.id = s.lead_id
        LEFT JOIN contacts c ON l.id = c.lead_id
        WHERE l.id = ?;
        """,
        (lead_id,)
    )
    lead_row = cursor.fetchone()
    if not lead_row:
        conn.close()
        return None
        
    lead = dict(lead_row)
    
    # Get homepage HTML content
    cursor.execute(
        "SELECT html_content FROM crawled_pages WHERE lead_id = ? AND is_homepage = 1 LIMIT 1;",
        (lead_id,)
    )
    page_row = cursor.fetchone()
    lead["html_content"] = page_row["html_content"] if page_row else ""
    
    # Get all crawled pages for migration/audits
    cursor.execute(
        "SELECT url, html_content FROM crawled_pages WHERE lead_id = ?;",
        (lead_id,)
    )
    lead["crawled_pages"] = [dict(r) for r in cursor.fetchall()]
    
    # Get signals list
    cursor.execute(
        "SELECT signal_name, note, score FROM signals WHERE lead_id = ?;",
        (lead_id,)
    )
    lead["signals"] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return lead

def load_lead_data_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load business requirements/info from a YAML or JSON file."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: Requirements file not found at {path}")
        return None
        
    try:
        with open(path, "r") as f:
            if path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        return data
    except Exception as e:
        print(f"Error reading requirements file: {e}")
        return None

def classify_vertical(categories_str: str) -> str:
    """Classify lead category into general verticals."""
    cats = (categories_str or "").lower()
    if any(k in cats for k in ["plumber", "hvac", "roof", "electrician", "landscap", "pool", "garage", "paint", "locksmith", "pest", "carpet", "tree", "drywall", "fence", "remodel", "solar", "floor", "clean", "masonry", "handyman", "repair", "towing"]):
        return "home_services"
    elif any(k in cats for k in ["spa", "salon", "barber", "beauty", "massage", "wellness", "yoga", "fitness"]):
        return "health_wellness"
    elif any(k in cats for k in ["dentist", "chiropractor", "optometrist", "veterinarian", "doctor", "clinic", "therapy", "medical", "physio"]):
        return "medical_professional"
    elif any(k in cats for k in ["restaurant", "food", "cafe", "bakery", "catering", "bar", "pub", "diner"]):
        return "restaurant_food"
    elif any(k in cats for k in ["software", "tech", "saas", "app", "digital", "agency", "consulting", "marketing"]):
        return "tech_saas"
    elif any(k in cats for k in ["law", "attorney", "legal", "account", "finance", "tax", "consult", "advisor", "broker", "real estate", "property"]):
        return "professional_services"
    return "medical_professional"  # Default clean style

def format_social_links(social_json: str) -> str:
    """Format social media links dictionary as HTML contact list."""
    if not social_json:
        return ""
    try:
        if isinstance(social_json, str):
            links = json.loads(social_json)
        else:
            links = social_json  # Already a dict
            
        if not links or not isinstance(links, dict):
            return ""
        html = '<div style="margin-top: 15px;"><strong>Find Us On:</strong><br/>'
        for platform, url in links.items():
            if url:
                html += f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="margin-right: 15px; text-decoration: none; font-weight: bold; text-transform: capitalize;">{platform} ↗</a> '
        html += '</div>'
        return html
    except Exception:
        return ""

def get_inner_pages_content(vertical: str, lead: Dict[str, Any]) -> tuple:
    """Generate beautiful, vertical-specific Gutenberg content for Services, About, and Contact pages."""
    vertical_colors = {
        "home_services": {"primary": "#1e293b", "secondary": "#ea580c", "light": "#f8fafc", "border": "#cbd5e1"},
        "health_wellness": {"primary": "#78716c", "secondary": "#d97706", "light": "#f5f5f4", "border": "#e7e5e4"},
        "medical_professional": {"primary": "#0f172a", "secondary": "#0d9488", "light": "#f1f5f9", "border": "#cbd5e1"},
        "restaurant_food": {"primary": "#18181b", "secondary": "#c2410c", "light": "#fffbeb", "border": "#e4e4e7"},
        "tech_saas": {"primary": "#09090b", "secondary": "#a855f7", "light": "#18181b", "border": "#27272a"},
        "professional_services": {"primary": "#1e3a8a", "secondary": "#b45309", "light": "#fafaf9", "border": "#e4e4e7"},
    }
    
    colors = vertical_colors.get(vertical, vertical_colors["medical_professional"])
    primary_hex = colors["primary"]
    secondary_hex = colors["secondary"]
    light_hex = colors["light"]
    border_hex = colors["border"]
    
    # Text colors
    body_text = "#334155" if vertical != "tech_saas" else "#a1a1aa"
    card_bg = "#ffffff" if vertical != "tech_saas" else "#18181b"
    title_text = primary_hex if vertical != "tech_saas" else "#ffffff"
    
    rating_val = lead.get("rating") or "5.0"
    review_cnt = lead.get("review_count") or "8"
    phone_val = lead.get("phone") or ""
    email_val = lead.get("email") or ""
    address_val = lead.get("address") or "Local Service Area"
    biz_name = lead.get("business_name") or "Our Business"

    social_html = format_social_links(lead.get("social_links_json", ""))
    
    # Generate Services list based on vertical Niches
    service_items = []
    service_options = ""
    if vertical == "home_services":
        service_items = [
            {"icon": "🛠️", "title": "Repair & Maintenance", "desc": "Preventative care and expert troubleshooting to fix system issues before they cause costly damage. Our certified technicians resolve concerns quickly."},
            {"icon": "🏗️", "title": "Complete Installation", "desc": "A full-system upgrade or clean install utilizing premium materials designed for longevity, efficiency, and peak performance under all conditions."},
            {"icon": "🚨", "title": "Emergency Support", "desc": "Fast-response local support when unexpected issues arise, ensuring your safety, property protection, and absolute peace of mind during urgent situations."},
            {"icon": "📜", "title": "Warrantied Work", "desc": "Every single service is backed by our comprehensive labor and materials warranty. If anything goes wrong, we make it right at no extra charge."}
        ]
        service_options = """
          <option value="repair">Repair &amp; Maintenance</option>
          <option value="installation">Complete Installation</option>
          <option value="emergency">Emergency Support</option>
          <option value="warranty">Warrantied Work</option>
        """
    elif vertical == "health_wellness":
        service_items = [
            {"icon": "🌸", "title": "General Consultation", "desc": "Comprehensive health diagnostics and wellness outlines to establish a customized treatment plan tailored to your personal goals and physical needs."},
            {"icon": "💆", "title": "Wellness Treatments", "desc": "Therapeutic sessions aimed at restoring physical balance, reducing stress, and building long-term health in a peaceful, welcoming environment."},
            {"icon": "🔬", "title": "Advanced Skin/Body Care", "desc": "State-of-the-art procedures addressing specific concerns with the highest degree of safety, clinical expertise, and modern restorative technology."},
            {"icon": "📅", "title": "Multi-Session Programs", "desc": "Curated treatment pathways that guide you stage-by-stage toward your long-term health, rejuvenation, and physical alignment goals."}
        ]
        service_options = """
          <option value="consultation">General Consultation</option>
          <option value="wellness">Wellness Treatment</option>
          <option value="advanced">Advanced Care</option>
          <option value="program">Multi-Session Program</option>
        """
    elif vertical == "restaurant_food":
        service_items = [
            {"icon": "🥗", "title": "Signature Appetizers", "desc": "Delightful starters crafted with house-made dressings, organic greens, and local cheeses. Perfect for sharing with friends and family."},
            {"icon": "🍖", "title": "Chef's Main Entrées", "desc": "Gourmet plates featuring locally sourced meats, fresh-caught seafood, and house-made pastas finished with rich, flavorful reductions."},
            {"icon": "🍰", "title": "Decadent Desserts", "desc": "A sweet selection of pastries, warm chocolate tortes, and hand-churned gelatos designed to provide the perfect finish to your dining experience."},
            {"icon": "🍷", "title": "Curated Wine Pairings", "desc": "A selected wine list, microbrew options, and hand-crafted botanical cocktails designed to pair beautifully with each item on our seasonal menu."}
        ]
        service_options = """
          <option value="reservation">Table Reservation</option>
          <option value="catering">Event Catering</option>
          <option value="group">Group Booking</option>
          <option value="private">Private Dining</option>
        """
    elif vertical == "tech_saas":
        service_items = [
            {"icon": "💻", "title": "Custom Engineering", "desc": "Robust, scalable cloud applications built on modern frameworks. We deliver optimized performance, secure APIs, and clean codebase integrations."},
            {"icon": "⚡", "title": "Stack Modernization", "desc": "Migrate legacy architectures to modular, serverless environments. We reduce latency, optimize resource utilization, and eliminate technical debt."},
            {"icon": "🔒", "title": "Security & Compliance", "desc": "Implement enterprise-grade encryption, role-based access control, and automated compliance auditing to safeguard sensitive customer data."},
            {"icon": "📈", "title": "Product Growth Consulting", "desc": "Define product analytics, conversion funnels, and automated marketing flows that capture user intent and drive customer lifetime value."}
        ]
        service_options = """
          <option value="engineering">Custom Engineering</option>
          <option value="modernization">Stack Modernization</option>
          <option value="security">Security &amp; Compliance</option>
          <option value="growth">Product Growth</option>
        """
    elif vertical == "professional_services":
        service_items = [
            {"icon": "💼", "title": "Corporate & Business Advisory", "desc": "Strategic business consulting, entity formulation, contract structures, and risk mitigation outlines to support stable commercial growth and compliance."},
            {"icon": "📊", "title": "Wealth & Asset Management", "desc": "Personalized investment allocation advisory, retirement preparedness reviews, and estate transition planning customized to protect generational wealth."},
            {"icon": "🏛️", "title": "Legal Counsel & Representation", "desc": "Professional legal advisement on civil matters, litigation defense, intellectual property protections, and transactional drafting."},
            {"icon": "📐", "title": "Tax Strategy & Audit Prep", "desc": "Advanced corporate tax planning, compliance audits, and proactive structuring to minimize exposure and optimize tax liability."}
        ]
        service_options = """
          <option value="advisory">Corporate Advisory</option>
          <option value="wealth">Wealth Management</option>
          <option value="legal">Legal Counsel</option>
          <option value="tax">Tax Strategy</option>
        """
    else:  # medical_professional
        service_items = [
            {"icon": "🩺", "title": "Primary Care & Exams", "desc": "Thorough health assessments, preventative screens, and custom diagnostics designed to identify risk factors early and maintain optimal well-being."},
            {"icon": "📋", "title": "Specialized Consulting", "desc": "Expert consulting services detailing treatment pathways, second opinions, and customized clinical guides tailored to complex cases."},
            {"icon": "⚡", "title": "Therapeutics & Recovery", "desc": "Advanced in-office therapy sessions, follow-up evaluations, and customized recovery plans designed to restore function and mobility quickly."},
            {"icon": "🛡️", "title": "Safety Standards", "desc": "We adhere to strict hygiene and clinical standards, utilizing sterile materials and modern equipment to ensure absolute safety and comfort."}
        ]
        service_options = """
          <option value="primary">Primary Care &amp; Exams</option>
          <option value="consulting">Specialized Consulting</option>
          <option value="recovery">Therapeutics &amp; Recovery</option>
          <option value="safety">Safety Standards</option>
        """

    # Generate Services HTML
    services = """<!-- wp:cover {"overlayColor":"primary","minHeight":320,"style":{"spacing":{"padding":{"top":"clamp(2rem, 5vw, 4rem)","bottom":"clamp(2rem, 5vw, 4rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-cover" style="background-color:var(--wp--preset--color--primary);min-height:320px;padding-top:clamp(2rem, 5vw, 4rem);padding-bottom:clamp(2rem, 5vw, 4rem);display:flex;align-items:center;justify-content:center;text-align:center;">
  <div class="wp-block-cover__inner-container">
    <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"huge","fontFamily":"var(--wp--preset--font-family--serif)"},"color":{"text":"#ffffff"}}} -->
    <h1 style="text-align:center;font-size:var(--wp--preset--font-size--huge);font-family:var(--wp--preset--font-family--serif);color:#ffffff;margin:0;">Our Professional Services</h1>
    <!-- /wp:heading -->
    <!-- wp:paragraph {"textAlign":"center","style":{"color":{"text":"var(--wp--preset--color--muted)"},"typography":{"fontSize":"medium"}}} -->
    <p style="text-align:center;color:var(--wp--preset--color--muted);font-size:var(--wp--preset--font-size--medium);margin-top:10px;margin-bottom:0;">Top-rated, certified services customized for {biz_name} clients.</p>
    <!-- /wp:paragraph -->
  </div>
</div>
<!-- /wp:cover -->

<!-- wp:group {"style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem);">
  <!-- wp:columns {"style":{"spacing":{"blockGap":"2rem"}}} -->
  <div class="wp-block-columns" style="gap:2rem;">
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <p style="font-size:32px;margin:0 0 16px;">{service_0_icon}</p>
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 12px;">{service_0_title}</h3>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;color:var(--wp--preset--color--primary);margin:0;">{service_0_desc}</p>
    </div>
    <!-- /wp:column -->
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <p style="font-size:32px;margin:0 0 16px;">{service_1_icon}</p>
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 12px;">{service_1_title}</h3>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;color:var(--wp--preset--color--primary);margin:0;">{service_1_desc}</p>
    </div>
    <!-- /wp:column -->
  </div>
  <!-- /wp:columns -->

  <!-- wp:columns {"style":{"spacing":{"blockGap":"2rem","margin":{"top":"2rem"}}}} -->
  <div class="wp-block-columns" style="gap:2rem;margin-top:2rem;">
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <p style="font-size:32px;margin:0 0 16px;">{service_2_icon}</p>
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 12px;">{service_2_title}</h3>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;color:var(--wp--preset--color--primary);margin:0;">{service_2_desc}</p>
    </div>
    <!-- /wp:column -->
    <!-- wp:column {"style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
    <div class="wp-block-column" style="padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <p style="font-size:32px;margin:0 0 16px;">{service_3_icon}</p>
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 12px;">{service_3_title}</h3>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;color:var(--wp--preset--color--primary);margin:0;">{service_3_desc}</p>
    </div>
    <!-- /wp:column -->
  </div>
  <!-- /wp:columns -->
</div>
<!-- /wp:group -->

<!-- wp:group {"align":"full","style":{"color":{"background":"var(--wp--preset--color--secondary)"},"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group alignfull" style="background-color:var(--wp--preset--color--secondary);color:#ffffff;padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem);text-align:center;">
  <!-- wp:heading {"textAlign":"center","level":2,"style":{"typography":{"fontSize":"large","fontFamily":"var(--wp--preset--font-family--serif)"},"color":{"text":"#ffffff"}}} -->
  <h2 style="text-align:center;font-size:var(--wp--preset--font-size--large);font-family:var(--wp--preset--font-family--serif);color:#ffffff;margin:0 0 12px;">Need Immediate Assistance or a Custom Quote?</h2>
  <!-- /wp:heading -->
  <!-- wp:paragraph {"textAlign":"center","style":{"typography":{"fontSize":"medium"},"color":{"text":"rgba(255,255,255,0.9)"}}} -->
  <p style="text-align:center;font-size:var(--wp--preset--font-size--medium);color:rgba(255,255,255,0.9);margin-bottom:28px;">Connect with our specialists today. We provide upfront pricing and quick professional responses.</p>
  <!-- /wp:paragraph -->
  <!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
  <div class="wp-block-buttons" style="display:flex;justify-content:center;">
    <!-- wp:button {"style":{"color":{"background":"#ffffff","text":"var(--wp--preset--color--primary)"},"typography":{"fontWeight":"800"}}} -->
    <div class="wp-block-button"><a class="wp-block-button__link" href="tel:{phone_val}" style="background-color:#ffffff;color:var(--wp--preset--color--primary);font-weight:800;border-radius:8px;padding:14px 28px;text-decoration:none;">📞 Call Now: {phone_val}</a></div>
    <!-- /wp:button -->
  </div>
  <!-- /wp:buttons -->
</div>
<!-- /wp:group -->"""

    # Generate About Us HTML
    about = """<!-- wp:cover {"overlayColor":"primary","minHeight":320,"style":{"spacing":{"padding":{"top":"clamp(2rem, 5vw, 4rem)","bottom":"clamp(2rem, 5vw, 4rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-cover" style="background-color:var(--wp--preset--color--primary);min-height:320px;padding-top:clamp(2rem, 5vw, 4rem);padding-bottom:clamp(2rem, 5vw, 4rem);display:flex;align-items:center;justify-content:center;text-align:center;">
  <div class="wp-block-cover__inner-container">
    <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"huge","fontFamily":"var(--wp--preset--font-family--serif)"},"color":{"text":"#ffffff"}}} -->
    <h1 style="text-align:center;font-size:var(--wp--preset--font-size--huge);font-family:var(--wp--preset--font-family--serif);color:#ffffff;margin:0;">About {biz_name}</h1>
    <!-- /wp:heading -->
    <!-- wp:paragraph {"textAlign":"center","style":{"color":{"text":"var(--wp--preset--color--muted)"},"typography":{"fontSize":"medium"}}} -->
    <p style="text-align:center;color:var(--wp--preset--color--muted);font-size:var(--wp--preset--font-size--medium);margin-top:10px;margin-bottom:0;">Raising the standard of workmanship, reliability, and service in our local community.</p>
    <!-- /wp:paragraph -->
  </div>
</div>
<!-- /wp:cover -->

<!-- wp:group {"style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem);">
  <!-- wp:columns {"style":{"spacing":{"blockGap":"3rem"}}} -->
  <div class="wp-block-columns" style="gap:3rem;">
    <!-- wp:column {"width":"60%"} -->
    <div class="wp-block-column" style="flex-basis:60%;">
      <!-- wp:heading {"level":2,"style":{"typography":{"fontSize":"large","fontFamily":"var(--wp--preset--font-family--serif)"}}} -->
      <h2 style="font-size:var(--wp--preset--font-size--large);font-family:var(--wp--preset--font-family--serif);margin:0 0 20px;">Dedicated to Quality &amp; Transparency</h2>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.75;margin-bottom:16px;">We are a locally owned and operated crew committed to raising the standard of workmanship in our community. Rooted in honesty, professional response times, and superior durability, we treat every single property as if it were our own.</p>
      <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.75;">Whether you are looking for routine maintenance or require a major replacement, our licensed team is fully equipped to get the job done right, on schedule, and on budget. Thank you for supporting a local business!</p>
    </div>
    <!-- /wp:column -->
    <!-- wp:column {"width":"40%","style":{"spacing":{"padding":{"top":"2rem","bottom":"2rem","left":"2rem","right":"2rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--muted)"}} -->
    <div class="wp-block-column" style="flex-basis:40%;padding-top:2rem;padding-bottom:2rem;padding-left:2rem;padding-right:2rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 10px;">★ {rating_val} Rating</h3>
      <!-- /wp:heading -->
      <!-- wp:paragraph {"style":{"typography":{"fontSize":"small"}},"spacing":{"margin":{"bottom":"20px"}}} -->
      <p style="font-size:var(--wp--preset--font-size--small);margin-bottom:20px;">Based on {review_cnt} verified customer reviews.</p>
      <!-- /wp:paragraph -->
      <div style="font-size:24px;color:var(--wp--preset--color--secondary);margin-bottom:16px;">⭐⭐⭐⭐⭐</div>
      <p style="font-size:var(--wp--preset--font-size--small);font-style:italic;line-height:1.5;margin:0;">"Proudly serving our community with 5-star local service."</p>
    </div>
    <!-- /wp:column -->
  </div>
  <!-- /wp:columns -->
</div>
<!-- /wp:group -->"""

    # Generate Contact Us HTML
    contact = """<!-- wp:cover {"overlayColor":"primary","minHeight":320,"style":{"spacing":{"padding":{"top":"clamp(2rem, 5vw, 4rem)","bottom":"clamp(2rem, 5vw, 4rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-cover" style="background-color:var(--wp--preset--color--primary);min-height:320px;padding-top:clamp(2rem, 5vw, 4rem);padding-bottom:clamp(2rem, 5vw, 4rem);display:flex;align-items:center;justify-content:center;text-align:center;">
  <div class="wp-block-cover__inner-container">
    <!-- wp:heading {"textAlign":"center","level":1,"style":{"typography":{"fontSize":"huge","fontFamily":"var(--wp--preset--font-family--serif)"},"color":{"text":"#ffffff"}}} -->
    <h1 style="text-align:center;font-size:var(--wp--preset--font-size--huge);font-family:var(--wp--preset--font-family--serif);color:#ffffff;margin:0;">Contact Us</h1>
    <!-- /wp:heading -->
    <!-- wp:paragraph {"textAlign":"center","style":{"color":{"text":"var(--wp--preset--color--muted)"},"typography":{"fontSize":"medium"}}} -->
    <p style="text-align:center;color:var(--wp--preset--color--muted);font-size:var(--wp--preset--font-size--medium);margin-top:10px;margin-bottom:0;">Have questions or need an estimate? Get in touch with {biz_name} today.</p>
    <!-- /wp:paragraph -->
  </div>
</div>
<!-- /wp:cover -->

<!-- wp:group {"style":{"spacing":{"padding":{"top":"clamp(3rem, 8vw, 6rem)","bottom":"clamp(3rem, 8vw, 6rem)"}}},"layout":{"type":"constrained"}} -->
<div class="wp-block-group" style="padding-top:clamp(3rem, 8vw, 6rem);padding-bottom:clamp(3rem, 8vw, 6rem);">
  <!-- wp:columns {"style":{"spacing":{"blockGap":"3rem"}}} -->
  <div class="wp-block-columns" style="gap:3rem;">
    <!-- wp:column {"width":"45%"} -->
    <div class="wp-block-column" style="flex-basis:45%;display:flex;flex-direction:column;gap:28px;">
      <div>
        <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
        <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 16px;">Contact Information</h3>
        <!-- /wp:heading -->
        
        <!-- wp:paragraph -->
        <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;margin-bottom:12px;"><strong>📞 Call Us:</strong><br/><a href="tel:{phone_val}" style="font-size: var(--wp--preset--font-size--medium); font-weight: 800; color: var(--wp--preset--color--secondary); text-decoration: none;">{phone_link_text}</a></p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;margin-bottom:12px;"><strong>✉️ Email:</strong><br/><a href="mailto:{email_val}" style="color: var(--wp--preset--color--secondary); font-weight: 600; text-decoration: none;">{email_link_text}</a></p>
        <!-- /wp:paragraph -->
        
        <!-- wp:paragraph -->
        <p style="font-size:var(--wp--preset--font-size--normal);line-height:1.6;"><strong>📍 Location &amp; Service Area:</strong><br/>{address_val}</p>
        <!-- /wp:paragraph -->
      </div>
      
      {social_html}
      
      <!-- wp:group {"style":{"spacing":{"padding":{"top":"1.5rem","bottom":"1.5rem","left":"1.5rem","right":"1.5rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--muted)"}} -->
      <div class="wp-block-group" style="padding-top:1.5rem;padding-bottom:1.5rem;padding-left:1.5rem;padding-right:1.5rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
        <!-- wp:heading {"level":4,"style":{"typography":{"fontSize":"small","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
        <h4 style="font-size:var(--wp--preset--font-size--small);font-family:var(--wp--preset--font-family--system);font-weight:800;margin:0 0 8px;">Business Hours</h4>
        <!-- /wp:heading -->
        <p style="font-size:var(--wp--preset--font-size--small);margin:0;line-height:1.5;">Monday – Friday: 7:00 AM – 6:00 PM<br/>Saturday: 8:00 AM – 3:00 PM<br/>Sunday: Closed (Emergency Service Available)</p>
      </div>
      <!-- /wp:group -->
    </div>
    <!-- /wp:column -->
    
    <!-- wp:column {"width":"55%","style":{"spacing":{"padding":{"top":"2.5rem","bottom":"2.5rem","left":"2.5rem","right":"2.5rem"}},"border":{"radius":"12px","width":"1px","style":"solid","color":"rgba(0,0,0,0.06)"}},"color":{"background":"var(--wp--preset--color--background)"}} -->
    <div class="wp-block-column" style="flex-basis:55%;padding-top:2.5rem;padding-bottom:2.5rem;padding-left:2.5rem;padding-right:2.5rem;border-radius:12px;border-width:1px;border-style:solid;border-color:rgba(0,0,0,0.06)">
      <!-- wp:heading {"level":3,"style":{"typography":{"fontSize":"medium","fontFamily":"var(--wp--preset--font-family--system)"}}} -->
      <h3 style="font-size:var(--wp--preset--font-size--medium);font-family:var(--wp--preset--font-family--system);margin:0 0 10px;">Send a Message</h3>
      <!-- /wp:heading -->
      <p style="font-size:var(--wp--preset--font-size--small);margin-bottom:28px;">Fill out the form below and an advisor will reach back shortly.</p>
      
      <!-- wp:html -->
      <form action="mailto:{email_val}" method="post" enctype="text/plain">
        <div>
          <label>Full Name *</label>
          <input type="text" name="name" required placeholder="John Doe" />
        </div>
        <div>
          <label>Phone Number *</label>
          <input type="tel" name="phone" required placeholder="(555) 000-0000" />
        </div>
        <div>
          <label>Email Address</label>
          <input type="email" name="email" placeholder="john@example.com" />
        </div>
        <div>
          <label>Service Needed</label>
          <select name="service" style="background:#fff;">
            {service_options}
          </select>
        </div>
        <div>
          <label>Your Message / Project Details</label>
          <textarea name="message" rows="4" placeholder="Briefly describe what you need help with..."></textarea>
        </div>
        <button type="submit">Submit Request →</button>
      </form>
      <!-- /wp:html -->
    </div>
    <!-- /wp:column -->
  </div>
  <!-- /wp:columns -->
</div>
<!-- /wp:group -->"""

    email_link_text = email_val or "Email Us"
    phone_link_text = phone_val or "Call Us"
    
    replacements = {
        "{primary_hex}": primary_hex,
        "{secondary_hex}": secondary_hex,
        "{light_hex}": light_hex,
        "{border_hex}": border_hex,
        "{body_text}": body_text,
        "{card_bg}": card_bg,
        "{title_text}": title_text,
        "{rating_val}": str(rating_val),
        "{review_cnt}": str(review_cnt),
        "{phone_val}": phone_val,
        "{phone_link_text}": phone_link_text,
        "{email_val}": email_val,
        "{email_link_text}": email_link_text,
        "{address_val}": address_val,
        "{biz_name}": biz_name,
        "{social_html}": social_html,
        "{service_options}": service_options,
        "{service_0_icon}": service_items[0]['icon'] if len(service_items) > 0 else "",
        "{service_0_title}": service_items[0]['title'] if len(service_items) > 0 else "",
        "{service_0_desc}": service_items[0]['desc'] if len(service_items) > 0 else "",
        "{service_1_icon}": service_items[1]['icon'] if len(service_items) > 1 else "",
        "{service_1_title}": service_items[1]['title'] if len(service_items) > 1 else "",
        "{service_1_desc}": service_items[1]['desc'] if len(service_items) > 1 else "",
        "{service_2_icon}": service_items[2]['icon'] if len(service_items) > 2 else "",
        "{service_2_title}": service_items[2]['title'] if len(service_items) > 2 else "",
        "{service_2_desc}": service_items[2]['desc'] if len(service_items) > 2 else "",
        "{service_3_icon}": service_items[3]['icon'] if len(service_items) > 3 else "",
        "{service_3_title}": service_items[3]['title'] if len(service_items) > 3 else "",
        "{service_3_desc}": service_items[3]['desc'] if len(service_items) > 3 else "",
    }
    
    for k, v in replacements.items():
        services = services.replace(k, v)
        about = about.replace(k, v)
        contact = contact.replace(k, v)

    return services, about, contact

def run_compose_command(cmd_args: List[str]) -> subprocess.CompletedProcess:
    """Run docker-compose command in builder context."""
    full_cmd = ["docker", "compose"] + cmd_args
    return subprocess.run(
        full_cmd,
        cwd=str(WP_BUILDER_DIR),
        capture_output=True,
        text=True
    )

def is_docker_running() -> bool:
    """Check if Docker daemon is active."""
    res = subprocess.run(["docker", "info"], capture_output=True)
    return res.returncode == 0

def ensure_containers_up() -> bool:
    """Ensure Docker Compose containers are running and healthy."""
    if not is_docker_running():
        print("Error: Docker is not running. Please start Docker Desktop first.")
        return False
        
    print("Checking container status...")
    res = run_compose_command(["ps", "--format", "json"])
    
    # Check if app container is already running
    if "wp_mockup_app" not in res.stdout:
        print("Starting Docker Compose services...")
        start_res = run_compose_command(["up", "-d"])
        if start_res.returncode != 0:
            print(f"Error starting containers: {start_res.stderr}")
            return False
            
    # Wait for MySQL to initialize
    print("Waiting for database connection to be ready (takes ~15-20 seconds for cold boot)...")
    max_retries = 30
    for i in range(max_retries):
        check_res = run_compose_command(["run", "--rm", "wp-cli", "mysqladmin", "ping", "-h", "db", "-u", "wordpress", "-pwordpresspassword"])
        if check_res.returncode == 0:
            print("Database connection is healthy!")
            return True
        time.sleep(1.5)
        
    print("Error: Timeout waiting for database initialization.")
    return False

def install_wordpress(title: str) -> bool:
    """Reset the database and perform a fresh WordPress installation."""
    print("Ensuring database exists...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "db", "create", "--defaults"])
    
    print("Resetting database...")
    res = run_compose_command(["run", "--rm", "wp-cli", "wp", "db", "reset", "--yes", "--defaults"])
    if res.returncode != 0:
        print(f"Failed to reset database: {res.stderr}")
        return False
        
    print(f"Installing WordPress core for '{title}'...")
    install_res = run_compose_command([
        "run", "--rm", "wp-cli", "wp", "core", "install",
        "--url=http://localhost:8080",
        f"--title={title}",
        "--admin_user=admin",
        "--admin_password=adminpassword",
        "--admin_email=admin@gilbert.studio",
        "--skip-email"
    ])
    
    if install_res.returncode != 0:
        print(f"Failed to install WordPress: {install_res.stderr}")
        return False
        
    print("WordPress installed successfully!")
    return True

def clean_default_posts():
    """Remove default sample posts and pages from fresh installation."""
    print("Cleaning default posts and pages...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "post", "delete", "1", "2", "--force"])

def create_page(title: str, slug: str, content: str) -> Optional[int]:
    """Create a page in WordPress via WP-CLI and return its page ID."""
    print(f"Creating page: {title} ({slug})...")
    res = run_compose_command([
        "run", "--rm", "wp-cli", "wp", "post", "create",
        f"--post_title={title}",
        f"--post_name={slug}",
        "--post_type=page",
        "--post_status=publish",
        f"--post_content={content}",
        "--porcelain"
    ])
    
    if res.returncode == 0:
        try:
            return int(res.stdout.strip())
        except ValueError:
            return None
    else:
        print(f"Failed to create page {title}: {res.stderr}")
        return None

def configure_site_layout(homepage_id: int, tagline: str):
    """Set static front page and site tagline."""
    print("Configuring static front page and tagline...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "show_on_front", "page"])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "page_on_front", str(homepage_id)])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "blogdescription", tagline])
    
    # Configure pretty permalinks
    run_compose_command(["run", "--rm", "wp-cli", "wp", "rewrite", "structure", "/%postname%/"])

def setup_navigation_menu(pages: List[Dict[str, Any]]):
    """Create primary navigation menu and add pages to it."""
    print("Creating primary navigation menu...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "menu", "create", "Primary Menu"])
    for p in pages:
        if p.get("wp_id"):
            run_compose_command([
                "run", "--rm", "wp-cli", "wp",
                "menu", "item", "add-post", "Primary Menu", str(p["wp_id"])
            ])
    # Assign menu to primary theme location
    run_compose_command([
        "run", "--rm", "wp-cli", "wp",
        "menu", "location", "assign", "Primary Menu", "primary"
    ])

def configure_mockup_styles(lead: Dict[str, Any], vertical: str, design_style: str = "modern_minimalist"):
    """Copy the premium styles plugin and update WordPress options for typography/contact info."""
    print("Configuring premium mockup styles and injecting contact info...")
    
    # 1. Create mu-plugins folder and copy styles file
    try:
        subprocess.run(
            ["docker", "exec", "wp_mockup_app", "mkdir", "-p", "/var/www/html/wp-content/mu-plugins"],
            capture_output=True, text=True
        )
        
        styles_src = WP_BUILDER_DIR / "premium-mockup-styles.php"
        subprocess.run(
            ["docker", "cp", str(styles_src), "wp_mockup_app:/var/www/html/wp-content/mu-plugins/premium-mockup-styles.php"],
            capture_output=True, text=True
        )
        print("Premium styles plugin copied successfully.")
    except Exception as e:
        print(f"Warning: Failed to copy styles plugin: {e}")
        
    # 2. Update options via WP-CLI
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_vertical", vertical])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_design_style", design_style])
    
    if lead.get("business_name"):
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_business_name", lead["business_name"]])
        
    if lead.get("phone"):
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_phone", lead["phone"]])
        
    if lead.get("email"):
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_email", lead["email"]])
        
    if lead.get("address"):
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_address", lead["address"]])

def install_custom_plugins_and_themes():
    """Scan local custom-plugins/ and custom-theme/ and load them into the container."""
    print("\nScanning for custom plugins and themes...")
    
    # 1. Must-use plugins (mu-plugins)
    mu_local_dir = WP_BUILDER_DIR / "custom-plugins" / "mu-plugins"
    if mu_local_dir.exists():
        files = [f for f in mu_local_dir.iterdir() if f.is_file() and f.suffix == ".php"]
        if files:
            print(f"Found {len(files)} custom mu-plugins. Copying to container...")
            subprocess.run(["docker", "exec", "wp_mockup_app", "mkdir", "-p", "/var/www/html/wp-content/mu-plugins"], capture_output=True)
            for f in files:
                subprocess.run([
                    "docker", "cp", str(f), f"wp_mockup_app:/var/www/html/wp-content/mu-plugins/{f.name}"
                ], capture_output=True)
                print(f"  ✓ Copied mu-plugin: {f.name}")
                
    # 2. Standard plugins
    plugins_local_dir = WP_BUILDER_DIR / "custom-plugins"
    if plugins_local_dir.exists():
        # List all subdirectories or php files (except mu-plugins)
        plugins = [p for p in plugins_local_dir.iterdir() if p.name != "mu-plugins" and (p.is_dir() or p.suffix == ".php")]
        if plugins:
            print(f"Found {len(plugins)} standard custom plugins/apps. Copying and activating...")
            for p in plugins:
                # Copy to wp-content/plugins/
                subprocess.run([
                    "docker", "cp", str(p), f"wp_mockup_app:/var/www/html/wp-content/plugins/{p.name}"
                ], capture_output=True)
                print(f"  ✓ Copied plugin: {p.name}")
                
                # Activate via WP-CLI
                slug = p.stem if p.is_file() else p.name
                act_res = run_compose_command(["run", "--rm", "wp-cli", "wp", "plugin", "activate", slug])
                if act_res.returncode == 0:
                    print(f"  ✓ Activated plugin: {slug}")
                else:
                    print(f"  ✗ Failed to activate plugin {slug}: {act_res.stderr.strip()}")

    # 3. Custom themes
    theme_local_dir = WP_BUILDER_DIR / "custom-theme"
    if theme_local_dir.exists():
        # Look for theme subdirectories (containing style.css)
        themes = [t for t in theme_local_dir.iterdir() if t.is_dir() and (t / "style.css").exists()]
        if themes:
            print(f"Found {len(themes)} custom theme(s). Copying and activating...")
            # We activate the first one found
            target_theme = themes[0]
            subprocess.run([
                "docker", "cp", str(target_theme), f"wp_mockup_app:/var/www/html/wp-content/themes/{target_theme.name}"
            ], capture_output=True)
            print(f"  ✓ Copied theme: {target_theme.name}")
            
            act_res = run_compose_command(["run", "--rm", "wp-cli", "wp", "theme", "activate", target_theme.name])
            if act_res.returncode == 0:
                print(f"  ✓ Activated theme: {target_theme.name}")
            else:
                print(f"  ✗ Failed to activate theme {target_theme.name}: {act_res.stderr.strip()}")

    # Set proper permissions in the container
    subprocess.run(["docker", "exec", "wp_mockup_app", "chown", "-R", "www-data:www-data", "/var/www/html/wp-content"], capture_output=True)

def export_and_package_site(slug: str) -> bool:
    """Export the database dump and zip the theme, plugins, and DB dump into dist/."""
    print("\nPackaging WordPress custom build...")
    dist_dir = WP_BUILDER_DIR / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    db_export_filename = f"wordpress_db_{slug.replace('-', '_')}.sql"
    
    # Create staging directory
    import tempfile
    import shutil
    staging_dir = Path(tempfile.mkdtemp(prefix="wp_export_staging_"))
    
    try:
        # 1. Export database SQL dump (via DB container mysqldump directly to host staging dir)
        db_name = f"wp_mockup_{slug.replace('-', '_')}"
        db_dump_dest = staging_dir / db_export_filename
        print(f"Exporting database '{db_name}' SQL dump (via db container)...")
        with open(db_dump_dest, "w") as f_out:
            dump_res = subprocess.run([
                "docker", "exec", "wp_mockup_db",
                "mysqldump", "-u", "wordpress", "-pwordpresspassword", db_name
            ], stdout=f_out, stderr=subprocess.PIPE, text=True)
            
        if dump_res.returncode != 0:
            print(f"Error: Failed to export database using mysqldump: {dump_res.stderr}")
            return False
            
        # 2. Copy wp-content from container to staging
        print("Copying wp-content directory to staging...")
        wp_content_staging = staging_dir / "wp-content"
        subprocess.run([
            "docker", "cp", "wp_mockup_app:/var/www/html/wp-content", str(wp_content_staging)
        ], capture_output=True)
        
        # 4. Generate INSTALL.md guide in staging
        install_guide = f"""# WordPress Custom Build Installation Guide: {slug}
        
This package contains a custom WordPress theme, backend configuration, and custom plugins built specifically for this site.

## Package Contents
1. `{db_export_filename}`: SQLite/MySQL database dump containing page specifications, configurations, navigation menus, and metadata.
2. `wp-content/`: Fully packaged directory containing:
   - `themes/`: Custom styles, templates, and designs.
   - `plugins/` and `mu-plugins/`: Custom plugins, apps, and helper scripts generated for this lead.
   - `uploads/`: Media and static assets.

## Deployment Instructions

### Method A: Manual Server Deployment
1. **Upload Files**: Copy the contents of the `wp-content/` directory in this package into the `wp-content/` folder of your target live WordPress site (overwriting or merging files as necessary).
2. **Import Database**: 
   - Open your hosting control panel database manager (e.g. phpMyAdmin) or connect via mysql CLI.
   - Import the `{db_export_filename}` SQL dump into your database.
   - *Note*: If the domain name changes, run a search-and-replace on the imported database to update `http://localhost:8080` to your new domain using WP-CLI:
     `wp search-replace "http://localhost:8080" "https://yourdomain.com"`

### Method B: Migration Plugins (e.g., All-in-One WP Migration)
If migrating using a standard plugin, install a clean WordPress stack, upload themes/plugins/uploads folders, and import this DB SQL dump.
"""
        with open(staging_dir / "INSTALL.md", "w") as f:
            f.write(install_guide)
            
        # 5. Zip it all up
        print("Zipping the staging directory...")
        archive_name = dist_dir / f"wp_mockup_{slug}"
        # shutil.make_archive automatically appends '.zip'
        shutil.make_archive(str(archive_name), 'zip', staging_dir)
        print(f"Success: Packaged custom theme/plugin site build at: {archive_name}.zip")
        return True
    except Exception as e:
        print(f"Error during packaging: {e}")
        return False
    finally:
        shutil.rmtree(staging_dir)

def generate_custom_calculator_plugin(slug: str, inputs: List[str]):
    """Generate the scaffolding PHP file for a custom interactive calculator plugin."""
    print("Generating custom estimator plugin scaffolding...")
    plugin_dir = WP_BUILDER_DIR / "custom-plugins"
    plugin_dir.mkdir(exist_ok=True)
    
    plugin_slug = f"custom-estimator-{slug}"
    plugin_file = plugin_dir / f"{plugin_slug}.php"
    
    # Compile form fields HTML
    fields_html = ""
    for inp in inputs:
        name_clean = inp.split(" (")[0]
        label = name_clean.replace("_", " ").replace("-", " ").capitalize()
        fields_html += f'        <div style="margin-bottom:15px;">\n            <label style="display:block;margin-bottom:5px;font-weight:bold;">{label}</label>\n            <input type="text" name="{name_clean}" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:4px;" />\n        </div>\n'
        
    plugin_code = f"""<?php
/**
 * Plugin Name: Bespoke Cost Estimator ({slug.replace('-', ' ').title()})
 * Description: Scaffolding custom calculator generated by gilbert.studio to replace legacy website calculator.
 * Version: 1.0.0
 * Author: gilbert.studio
 */

if (!defined('ABSPATH')) exit;

// 1. Register Shortcode [custom_estimator_form]
add_shortcode('custom_estimator_form', 'render_custom_estimator_form_{slug.replace("-", "_")}');

function render_custom_estimator_form_{slug.replace("-", "_")}() {{
    ob_start();
    ?>
    <div class="custom-estimator-card" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:12px;padding:32px;max-width:500px;margin:20px auto;">
        <h3 style="margin-top:0;font-size:20px;font-weight:800;">Get a Quick Ballpark Estimate</h3>
        <form id="estimator-form">
{fields_html}
            <button type="submit" style="background:#ea580c;color:#fff;font-weight:bold;border:none;padding:12px 24px;border-radius:6px;cursor:pointer;width:100%;">Calculate Ballpark Cost →</button>
        </form>
        <div id="estimator-result" style="margin-top:20px;padding:15px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;display:none;font-weight:bold;text-align:center;color:#1e293b;"></div>
    </div>
    
    <script>
    document.getElementById('estimator-form').addEventListener('submit', function(e) {{
        e.preventDefault();
        // Custom simple calculation logic
        let resultDiv = document.getElementById('estimator-result');
        resultDiv.style.display = 'block';
        resultDiv.innerText = 'Calculating ballpark quote...';
        
        setTimeout(() => {{
            resultDiv.innerHTML = '<span style="font-size:24px;color:#ea580c;">Estimated: $3,200 - $4,800</span><br/><span style="font-size:12px;color:#64748b;">(Ballpark only. We will call you to finalize.)</span>';
        }}, 800);
    }});
    </script>
    <?php
    return ob_get_clean();
}}
"""
    with open(plugin_file, "w") as f:
        f.write(plugin_code)
    print(f"✓ Custom plugin written to: {plugin_file}")

def audit_existing_site_technologies(slug: str, lead: Dict[str, Any]) -> Dict[str, Any]:
    """Audit the legacy HTML content to detect active CMS, plugins, widgets, and form endpoints.
    Outputs a markdown report and generates scaffolding for custom plugins if needed."""
    print("\nAuditing legacy site technologies and interactive elements...")
    
    html_content = lead.get("html_content", "")
    pages = lead.get("crawled_pages", [])
    
    # Combine HTML from all crawled pages for comprehensive auditing
    combined_html = html_content + "\n" + "\n".join([p.get("html_content", "") for p in pages])
    
    audit_results = {
        "cms": "Custom/Unknown",
        "technologies": [],
        "interactive_elements": [],
        "recommendations": [],
        "prd": ""
    }
    
    # 1. Detect CMS
    if any(k in combined_html for k in ["wp-content", "wp-includes", "wp-json", "xmlrpc.php"]):
        audit_results["cms"] = "WordPress"
    elif any(k in combined_html for k in ["squarespace.com", "static1.squarespace.com"]):
        audit_results["cms"] = "Squarespace"
    elif any(k in combined_html for k in ["wixstatic.com", "wixsite.com", "wix-editor"]):
        audit_results["cms"] = "Wix"
    elif any(k in combined_html for k in ["hubspot.com", "hubfs", "hs-scripts"]):
        audit_results["cms"] = "HubSpot CMS"
    elif any(k in combined_html for k in ["shopify.com", "cdn.shopify.com"]):
        audit_results["cms"] = "Shopify"

    # 2. Detect specific widgets/plugins
    # Forms
    if "js.hsforms.net" in combined_html or "forms.hsforms.com" in combined_html:
        audit_results["technologies"].append("HubSpot Lead Forms")
        audit_results["interactive_elements"].append({
            "type": "form",
            "name": "HubSpot Form",
            "details": "Dynamic HubSpot marketing form integration."
        })
        audit_results["recommendations"].append({
            "name": "HubSpot WordPress Plugin",
            "url": "https://wordpress.org/plugins/leadin/",
            "type": "existing",
            "desc": "Official HubSpot plugin. Integrates native HubSpot forms and live chat seamlessly."
        })
    if "contact-form-7" in combined_html:
        audit_results["technologies"].append("Contact Form 7")
        audit_results["recommendations"].append({
            "name": "Contact Form 7",
            "url": "https://wordpress.org/plugins/contact-form-7/",
            "type": "existing",
            "desc": "One of the most popular free forms plugins for WordPress."
        })
    if "wpforms" in combined_html:
        audit_results["technologies"].append("WPForms")
        audit_results["recommendations"].append({
            "name": "WPForms Lite",
            "url": "https://wordpress.org/plugins/wpforms-lite/",
            "type": "existing",
            "desc": "Drag-and-drop form builder for WordPress."
        })

    # Booking & Scheduling
    if "calendly.com" in combined_html:
        audit_results["technologies"].append("Calendly Scheduling")
        audit_results["interactive_elements"].append({
            "type": "booking",
            "name": "Calendly Widget",
            "details": "Embedded scheduler for appointments."
        })
        audit_results["recommendations"].append({
            "name": "Calendly for WordPress",
            "url": "https://wordpress.org/plugins/calendly/",
            "type": "existing",
            "desc": "Allows direct block or shortcode embedding of your Calendly schedules."
        })

    # Chat Widgets
    if "tawk.to" in combined_html:
        audit_results["technologies"].append("Tawk.to Live Chat")
        audit_results["recommendations"].append({
            "name": "Tawk.to Live Chat",
            "url": "https://wordpress.org/plugins/tawkto-live-chat/",
            "type": "existing",
            "desc": "Free live chat plugin to connect with website visitors."
        })

    # Analytics / Tag Managers
    if "googletagmanager.com/gtm.js" in combined_html:
        audit_results["technologies"].append("Google Tag Manager")
        audit_results["recommendations"].append({
            "name": "Site Kit by Google",
            "url": "https://wordpress.org/plugins/google-site-kit/",
            "type": "existing",
            "desc": "Official Google plugin for Analytics, Search Console, AdSense, and Speed stats."
        })
        
    # Check for custom/generic interactive elements (custom estimate form, custom calculator)
    soup = BeautifulSoup(combined_html, "html.parser")
    for form in soup.find_all("form"):
        form_id = form.get("id", "")
        form_class = str(form.get("class", ""))
        action = form.get("action", "")
        
        # Treat any detected form as an interactive lead / estimation module to migrate
        is_estimator = True
        
        if is_estimator:
            inputs = []
            for inp in form.find_all(["input", "select", "textarea"]):
                name = inp.get("name", "")
                inp_type = inp.get("type", "text")
                if name:
                    inputs.append(f"{name} ({inp_type})")
            
            elem_name = "Custom Cost Estimator Form"
            audit_results["interactive_elements"].append({
                "type": "custom_calculator",
                "name": elem_name,
                "details": f"Form fields detected: {', '.join(inputs)}"
            })
            
            # Generate a PRD for hand-rolling a custom calculator plugin
            prd_content = f"""## Product Requirement Document (PRD): Bespoke WordPress Cost Estimator Plugin

### 1. Overview
The legacy website utilizes a custom interactive form ({elem_name}) to collect project parameters and submit quote requests. We will package this functionality as a custom WordPress plugin.

### 2. Functional Requirements
*   **Gutenberg Shortcode / Widget**: Provide a shortcode `[custom_estimator_form]` that prints a responsive HTML estimate request form.
*   **Dynamic Client-Side Estimation**: Build lightweight JavaScript to calculate a ballpark price estimate based on user input (e.g. surface area, material choice).
*   **Form Submission (WP REST API)**: Securely capture inputs and submit them to a custom WordPress REST API endpoint (`/wp-json/custom-estimator/v1/submit`).
*   **Admin Notifications**: Log submission events in the WordPress options database or send an email notification to the site administrator.

### 3. Detected Form Fields (to migrate)
"""
            for inp in inputs:
                prd_content += f"*   {inp}\n"
            if not inputs:
                prd_content += "*   General query fields (name, phone, email, messages)\n"
                
            audit_results["prd"] = prd_content
            
            # Write custom plugin scaffolding file!
            generate_custom_calculator_plugin(slug, inputs)

    # 3. Compile report markdown
    report_md = f"""# Technology Audit & Integration Report: {lead.get('business_name', 'Business Mockup')}

This audit details the backend integrations, trackers, and interactive modules detected on the legacy website, alongside recommendations for WordPress alternatives or custom-built plugins.

---

## 1. Core Platform Summary
*   **Legacy CMS / Framework**: {audit_results['cms']}
*   **Detected Integration Stack**: {', '.join(audit_results['technologies']) if audit_results['technologies'] else 'None detected'}

---

## 2. Legacy Interactive Elements
{compile_interactive_elements_section(audit_results['interactive_elements'])}

---

## 3. WordPress Plugin Deployment Recommendations
{compile_recommendations_section(audit_results['recommendations'])}
"""
    if audit_results["prd"]:
        report_md += f"\n---\n\n{audit_results['prd']}"
        
    # Save Report
    dist_dir = WP_BUILDER_DIR / "dist"
    dist_dir.mkdir(exist_ok=True)
    report_dest = dist_dir / f"audit_report_{slug}.md"
    with open(report_dest, "w") as f:
        f.write(report_md)
    print(f"✓ Technology Audit Report written to: {report_dest}")
    
    return audit_results

def compile_interactive_elements_section(elements: List[Dict[str, Any]]) -> str:
    if not elements:
        return "*No complex legacy interactive forms or scheduling scripts detected on public crawls.*"
    html = ""
    for el in elements:
        html += f"### App/Widget: {el['name']} (Type: `{el['type']}`)\n*   **Details**: {el['details']}\n\n"
    return html

def compile_recommendations_section(recs: List[Dict[str, Any]]) -> str:
    if not recs:
        return "*Deploy standard contact forms and styling options. No special plugin recommendations.*"
    html = ""
    for r in recs:
        html += f"### Recommended Plugin: {r['name']}\n*   **Type**: {r['type']}\n*   **Plugin URL**: [{r['name']} ↗]({r['url']})\n*   **Description**: {r['desc']}\n\n"
    return html

def migrate_legacy_media(slug: str, lead: Dict[str, Any]) -> Dict[str, str]:
    """Extract, download, copy, and import legacy images from HTML into WordPress.
    Returns a dictionary mapping: original_image_url -> new_wordpress_media_url"""
    print("\nStarting legacy media extraction and migration...")
    
    html_content = lead.get("html_content", "")
    pages = lead.get("crawled_pages", [])
    
    # Extract images from all crawled pages
    soup_pages = [BeautifulSoup(html_content, "html.parser")]
    for p in pages:
        soup_pages.append(BeautifulSoup(p.get("html_content", ""), "html.parser"))
        
    image_urls = set()
    for soup in soup_pages:
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                # Filter out tiny tracking pixels, SVGs, spacer icons
                if any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                    # If it's a tracking pixel or tiny hubspot hs-fs image, ignore it
                    if "pixel" in src.lower() or "tracking" in src.lower() or "/hs/t" in src.lower():
                        continue
                    image_urls.add(src)
                    
    if not image_urls:
        print("No eligible image assets found on legacy site.")
        return {}
        
    print(f"Found {len(image_urls)} legacy images to migrate.")
    
    # 1. Download images locally to a staging folder
    import tempfile
    import shutil
    staging_dir = Path(tempfile.mkdtemp(prefix="wp_media_migration_"))
    
    url_mapping = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    with httpx.Client(headers=headers, follow_redirects=True, timeout=10.0) as client:
        for idx, orig_url in enumerate(image_urls):
            # Parse clean filename
            parsed_url = urllib.parse.urlparse(orig_url)
            filename = os.path.basename(parsed_url.path)
            if not filename or not any(ext in filename.lower() for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                filename = f"migrated_image_{idx}.jpg"
                
            local_dest = staging_dir / filename
            print(f"  Downloading: {orig_url} ...")
            try:
                # Resolve relative URL if any
                resolved_url = orig_url
                if lead.get("original_url") and not orig_url.startswith(("http://", "https://")):
                    resolved_url = urllib.parse.urljoin(lead["original_url"], orig_url)
                    
                resp = client.get(resolved_url)
                if resp.status_code == 200:
                    with open(local_dest, "wb") as f_out:
                        f_out.write(resp.content)
                    print(f"    ✓ Staged locally: {local_dest.name}")
                    url_mapping[orig_url] = {
                        "local_path": local_dest,
                        "filename": filename,
                        "wordpress_url": ""
                    }
                else:
                    print(f"    X Download failed (HTTP status {resp.status_code})")
            except Exception as e:
                print(f"    X Failed to download {orig_url}: {e}")
                
    if not url_mapping:
        print("Failed to download any legacy images.")
        shutil.rmtree(staging_dir)
        return {}
        
    # 2. Copy the staging directory to the container
    print("\nCopying staged media files into WordPress container...")
    container_temp_dir = "/var/www/html/wp-content/uploads/migration_temp"
    subprocess.run([
        "docker", "exec", "wp_mockup_app", "mkdir", "-p", container_temp_dir
    ], capture_output=True)
    
    # Copy files
    for orig_url, info in url_mapping.items():
        local_path = info["local_path"]
        container_dest = f"{container_temp_dir}/{info['filename']}"
        cp_res = subprocess.run([
            "docker", "cp", str(local_path), f"wp_mockup_app:{container_dest}"
        ], capture_output=True)
        if cp_res.returncode == 0:
            info["container_path"] = container_dest
        else:
            print(f"  X Failed to copy {info['filename']} to container: {cp_res.stderr.decode()}")
            
    # 3. Import images via WP-CLI inside the container
    print("\nImporting media assets into WordPress Media Library...")
    for orig_url, info in url_mapping.items():
        if "container_path" not in info:
            continue
            
        print(f"  Importing {info['filename']}...")
        import_res = run_compose_command([
            "run", "--rm", "wp-cli", "wp", "media", "import", info["container_path"], "--porcelain"
        ])
        
        if import_res.returncode == 0:
            try:
                media_id = int(import_res.stdout.strip())
                # Get the WordPress URL of the newly created attachment
                url_res = run_compose_command([
                    "run", "--rm", "wp-cli", "wp", "post", "get", str(media_id), "--field=guid"
                ])
                if url_res.returncode == 0:
                    wp_url = url_res.stdout.strip()
                    info["wordpress_url"] = wp_url
                    print(f"    ✓ WordPress URL: {wp_url}")
                else:
                    print(f"    X Failed to retrieve WordPress URL for media ID {media_id}")
            except ValueError:
                print(f"    X Failed to parse imported media ID from response: {import_res.stdout}")
        else:
            print(f"    X WP-CLI import failed: {import_res.stderr.strip()}")
            
    # 4. Clean up temp files inside container & host
    print("\nCleaning up temporary media staging files...")
    subprocess.run([
        "docker", "exec", "wp_mockup_app", "rm", "-rf", container_temp_dir
    ], capture_output=True)
    
    shutil.rmtree(staging_dir)
    
    # Return simple mapping
    result_mapping = {}
    for orig_url, info in url_mapping.items():
        if info["wordpress_url"]:
            result_mapping[orig_url] = info["wordpress_url"]
            
    print(f"✓ Media migration complete! {len(result_mapping)} assets uploaded.")
    return result_mapping

def extract_legacy_site_summary(html_content: str) -> str:
    """Parse legacy website HTML content to extract main headers, taglines, portfolio slides, and entries."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    
    summary = []
    
    # Extract title
    title_tag = soup.find("title")
    if title_tag:
        summary.append(f"Legacy Page Title: {title_tag.get_text().strip()}")
        
    # Extract tagline
    tagline_div = soup.find(id="tagline")
    if tagline_div:
        summary.append(f"Legacy Tagline/Intro: {tagline_div.get_text(separator=' ').strip()}")
        
    # Extract slide portfolios
    slides = soup.find_all(class_="slide")
    if slides:
        summary.append("\n--- LEGACY PORTFOLIO ITEMS (FROM HOME SLIDESHOW) ---")
        for idx, slide in enumerate(slides):
            title = slide.find(class_="title")
            desc = slide.find(class_="description")
            img = slide.find("img")
            
            title_text = title.get_text().strip() if title else f"Portfolio Item {idx+1}"
            desc_text = desc.get_text().strip() if desc else ""
            desc_text = " ".join(desc_text.split())
            img_src = img.get("src") if img else "No Image"
            
            summary.append(f"Portfolio {idx+1}: {title_text}")
            if img_src != "No Image":
                summary.append(f"  - Image URL: {img_src}")
            if desc_text:
                summary.append(f"  - Description: {desc_text}")
                
    # Extract entries (blog posts, featured content)
    entries = soup.find_all(class_="entry")
    if entries:
        summary.append("\n--- LEGACY BLOG POSTS / FEATURED ENTRIES ---")
        for idx, entry in enumerate(entries):
            title = entry.find(class_="title")
            desc = entry.find(class_="entry-description")
            img = entry.find("img")
            
            title_text = title.get_text().strip() if title else f"Entry {idx+1}"
            desc_text = desc.get_text().strip() if desc else ""
            desc_text = " ".join(desc_text.split())
            img_src = img.get("src") if img else "No Image"
            
            summary.append(f"Entry {idx+1}: {title_text}")
            if img_src != "No Image":
                summary.append(f"  - Image URL: {img_src}")
            if desc_text:
                summary.append(f"  - Summary: {desc_text}")

    # General headers
    headers = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        # skip slides and entries to avoid duplicates
        h_class = h.get("class", []) or []
        parent_class = h.parent.get("class", []) or [] if h.parent else []
        if any(p in h_class or p in parent_class for p in ["title", "entry"]):
            continue
        text = h.get_text().strip()
        if text and text not in headers:
            headers.append(f"- {h.name}: {text}")
    if headers:
        summary.append("\n--- LEGACY PAGE HEADINGS ---")
        summary.extend(headers[:15])

    return "\n".join(summary)

def query_claude_for_blueprint(lead: Dict[str, Any], api_key: str, vertical: str, migrated_images: Optional[Dict[str, str]] = None, design_style: str = "modern_minimalist") -> Optional[Dict[str, Any]]:
    """Query Claude to compile page specifications and Gutenberg block content."""
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
    except ImportError:
        print("Error: The 'anthropic' library is not installed. Please run: pip install anthropic")
        return None

    # Construct prompt detailing lead's requirements
    biz_name = lead.get("business_name", "Local Business")
    
    vertical_configs = {
        "home_services": {
            "name": "Local Home Services",
            "colors": "Primary Dark Charcoal (#1e293b), Secondary Slate Grey (#f8fafc), High-Contrast Amber Accent (#ea580c)",
            "primary": "#1e293b",
            "secondary": "#ea580c",
            "typography": "Outfit / Bold Sans-Serif (Rugged, Reliable, Action-Oriented)",
            "sections": "Hero Cover with Click-to-Call, Core Services Columns, 5-Star Reviews Grid, Urgent Contact Form",
            "directive": "Emphasize click-to-call links, emergency banner accents, and bold service descriptions. Use high-contrast amber (#ea580c) for buttons, icons, and actionable accents."
        },
        "health_wellness": {
            "name": "Health, Wellness & Beauty",
            "colors": "Warm Stone (#78716c), Soft Sage (#f5f5f4), Gold/Warm Amber Accent (#d97706)",
            "primary": "#78716c",
            "secondary": "#d97706",
            "typography": "Playfair Display / Serif (Elegant, Trustworthy, Restorative)",
            "sections": "Hero Banner, Treatments/Services List, Staff/About Profile, Multi-Session Booking Card",
            "directive": "Focus on generous padding, soft organic backgrounds, and high-trust testimonial cards. Accent with warm amber/gold (#d97706) for luxury, calming highlights."
        },
        "medical_professional": {
            "name": "Medical & Professional",
            "colors": "Navy Blue (#0f172a), Neutral White (#ffffff), Teal/Blue Accent (#0d9488)",
            "primary": "#0f172a",
            "secondary": "#0d9488",
            "typography": "Inter / System Sans (Clean, Modern, Trustworthy)",
            "sections": "Hero Cover, Services Grid, Accreditations & Trust Logos, Patient Booking/Contact Form",
            "directive": "A highly clean and trust-oriented medical/professional style using corporate blue tones. Use teal (#0d9488) for buttons and critical highlights."
        },
        "tech_saas": {
            "name": "Modern Tech & SaaS",
            "colors": "Midnight Black (#09090b), Deep Slate (#18181b), Electric Purple Accent (#a855f7)",
            "primary": "#09090b",
            "secondary": "#a855f7",
            "typography": "Outfit / Geometric Sans-Serif (Cutting-edge, High-tech, Bold)",
            "sections": "Interactive Hero Section, Features/SaaS Grid, Product Pricing Cards, Contact Form",
            "directive": "An electric dark layout with high contrast glowing accents for technology/modern startups. Use purple (#a855f7) for primary actions."
        },
        "restaurant_food": {
            "name": "Restaurant & Food",
            "colors": "Rich Charcoal (#18181b), Warm Terracotta (#c2410c), Olive Accent (#65a30d)",
            "primary": "#18181b",
            "secondary": "#c2410c",
            "typography": "Playfair Display / Elegant Serif (Warm, Inviting, Gourmet)",
            "sections": "Hero Banner, Gourmet Menu Grid, Restaurant Booking Card, Instagram Gallery Grid",
            "directive": "A warm and inviting template utilizing rich food tones, menu previews, and reservations. Use terracotta (#c2410c) for buttons."
        },
        "professional_services": {
            "name": "Professional & Legal",
            "colors": "Deep Navy (#1e3a8a), Ivory/Warm Neutral (#fafaf9), Muted Bronze Accent (#b45309)",
            "primary": "#1e3a8a",
            "secondary": "#b45309",
            "typography": "Playfair Display / Serif (Authoritative, Prestigious, Trustworthy)",
            "sections": "Trust-Based Hero Section, Core Practice Areas, Partner/Founder Bio Card, Consultation Form",
            "directive": "Projects high authority and reliability with structured formal sections and whitespace. Use bronze (#b45309) for highlights and primary CTA."
        }
    }

    style_configs = {
        "modern_minimalist": {
            "name": "Modern Minimalist",
            "desc": "High whitespace, sleek sans-serif typography, monochrome colors with a single subtle accent, minimal clean borders, and premium understatement.",
            "directive": "Use extensive margins/padding (e.g., clamp(3rem, 8vw, 6rem)), thin border outlines (1px solid #e2e8f0), and a clean white background. Restrict colored sections to small highlights."
        },
        "dark_sleek": {
            "name": "Dark Sleek",
            "desc": "Deep dark backgrounds, glassmorphic card borders, electric neon accents, and modern sans-serif typography.",
            "directive": "Wrap content in groups with deep dark backgrounds (#09090b or #18181b) and text in light/white. Add class 'premium-glass-card' for container cards. Accent with bright colors like purple, blue or orange."
        },
        "warm_editorial": {
            "name": "Warm Editorial",
            "desc": "Warm earth tones, serif headings, elegant editorial whitespace, and soft shadows.",
            "directive": "Use soft off-white/beige background (#fafaf9 or #fdfaf7), warm text colors, Serif headings (Playfair Display), and rounder card corners (16px)."
        },
        "corporate_tech": {
            "name": "Corporate Tech",
            "desc": "Deep blues, clean structured grids, clear sans-serif typography, and high trust signals.",
            "directive": "Use solid layout grids, trust badges, standard primary navy/slate colors, and precise solid buttons (8px border-radius)."
        },
        "bold_creative": {
            "name": "Bold Creative",
            "desc": "Huge typography, high-contrast primary colors, block borders, and high-energy diagonal elements.",
            "directive": "Use extra large font sizes (clamp(3rem, 10vw, 5rem)) for headers. Apply bold borders (2px or 3px solid) and high-contrast color blocks."
        },
        "classic_elegant": {
            "name": "Classic Elegant",
            "desc": "Centered columns, fine borders, vintage serif typography, and elegant classic colors (gold, dark emerald, deep burgundy).",
            "directive": "Center-align main headings and button blocks. Use elegant serif font, fine styling details, and rich dark accents."
        }
    }

    config = vertical_configs.get(vertical, vertical_configs["medical_professional"])
    vertical_name = config["name"]
    colors_guide = config["colors"]
    primary_hex = config["primary"]
    secondary_hex = config["secondary"]
    typography_guide = config["typography"]
    sections_guide = config["sections"]
    description_guide = config["directive"]

    style_cfg = style_configs.get(design_style, style_configs["modern_minimalist"])
    style_name = style_cfg["name"]
    style_desc = style_cfg["desc"]
    style_directive = style_cfg["directive"]

    legacy_summary = ""
    if lead.get("html_content"):
        try:
            legacy_summary = extract_legacy_site_summary(lead["html_content"])
            print(f"✓ Extracted structured legacy content summary for ingestion ({len(legacy_summary)} bytes).")
        except Exception as e:
            print(f"Warning: Failed to extract legacy site summary: {e}")

    legacy_instruction = ""
    if legacy_summary:
        legacy_instruction = (
            "\n\nLEGACY CONTENT INGESTION DIRECTIVE:\n"
            "A 'LEGACY SITE CONTENT FOR INGESTION & RE-USE' section is provided in the prompt. You MUST migrate and re-use the portfolio items, descriptions, and taglines from it. Reconstruct these projects inside modern Gutenberg blocks (e.g. Columns, Groups, Cover blocks) using the matching migrated media Attachment URLs if available. Update references/copy to represent the current year (2026), but preserve the original marketing focus.\n"
        )

    images_instruction = ""
    if migrated_images:
        images_instruction = "\n\nMIGRATED REAL IMAGES FROM THE LEGACY SITE:\n"
        for orig, wp_url in migrated_images.items():
            filename = orig.split("/")[-1].split("?")[0]
            images_instruction += f"- Original URL: {orig}\n  WordPress Attachment URL (YOU MUST USE THIS): {wp_url}\n  Context/Filename: {filename}\n"
        images_instruction += "\nCRITICAL: You MUST use the provided 'WordPress Attachment URL' as the src or background url in your Gutenberg block code to display real migrated assets (e.g. cover backgrounds, headers, portfolio images, etc.). Do not invent or use external placeholders if a matching migrated asset is provided.\n"

    system_instruction = (
        "You are an expert WordPress developer and UX designer for gilbert.studio. "
        "Your task is to generate a modern, block-based WordPress homepage mockup layout for a local business.\n"
        "Your response must be formatted using these XML-like tags, and nothing else (do NOT use JSON or wrap it inside another container):\n"
        "<tagline>A short marketing slogan for the business.</tagline>\n"
        f"<primary_color>{primary_hex}</primary_color>\n"
        f"<secondary_color>{secondary_hex}</secondary_color>\n"
        "<home_content>\n"
        "Raw Gutenberg HTML block markup for the homepage. Rebuild their legacy website into a beautiful, high-converting Gutenberg layout. Use standard block elements (e.g. <!-- wp:cover -->, <!-- wp:heading -->, <!-- wp:paragraph -->, <!-- wp:columns -->) and include optimized sales copywriting.\n"
        "</home_content>\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Do NOT wrap your output in JSON, do NOT escape double quotes as \\\", and do NOT escape newlines. Write raw HTML and block comments directly within the <home_content> tag.\n"
        "2. Output standard WordPress Gutenberg block patterns (comment tags like <!-- wp:paragraph --> followed by HTML and closed with <!-- /wp:paragraph -->) so they render correctly in the editor.\n"
        "3. Focus on 3-4 high-impact, visually stunning homepage sections (e.g., Hero cover with click-to-call, Services preview grid, Testimonial cards, and a styled estimate request form).\n"
        "4. CRITICAL: You must use the actual Phone Number, Email Address, and Physical Address provided in the user prompt in any call-to-action buttons, links (e.g., href=\"tel:...\"), and copy. Do NOT use fake or hallucinated contact details."
        f"{images_instruction}"
        f"{legacy_instruction}"
        f"\n\nSTYLING & PALETTE REQUIREMENTS FOR THIS VERTICAL ({vertical_name}):\n"
        f"- Target Colors: Primary={colors_guide}\n"
        f"- Typography Style: {typography_guide}\n"
        f"- Recommended Block Layout: {sections_guide}\n"
        f"- Design Directive: {description_guide}\n\n"
        f"STYLING PRESET & DESIGN DIRECTION ({style_name}):\n"
        f"- Description: {style_desc}\n"
        f"- Presets directive: {style_directive}\n\n"
        f"You MUST style your Gutenberg block markup referencing standard WordPress CSS custom properties: var(--wp--preset--color--primary) for brand primary, var(--wp--preset--color--secondary) for secondary accent, var(--wp--preset--color--background) for layout background, and var(--wp--preset--color--muted) for card/offset background color. DO NOT hardcode absolute hex values (like {primary_hex} or {secondary_hex}) inside block style attributes to allow site-wide customization. Use viewport-clamped typography sizes: var(--wp--preset--font-size--huge) for H1, var(--wp--preset--font-size--large) for H2, and var(--wp--preset--font-size--medium) for subheadings."
    )
    
    prompt = (
        f"Business Name: {biz_name}\n"
        f"Niche/Categories: {lead.get('categories', 'Local business')}\n"
        f"Phone Number: {lead.get('phone') or 'Not Available'}\n"
        f"Email Address: {lead.get('email') or 'Not Available'}\n"
        f"Physical Address: {lead.get('address') or 'Not Available'}\n\n"
    )
    if legacy_summary:
        prompt += f"LEGACY SITE CONTENT FOR INGESTION & RE-USE:\n{legacy_summary}\n\n"
    prompt += "Please generate the complete modern block mockup blueprint now."

    models_to_try = [
        "claude-sonnet-4-6",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229"
    ]
    
    response_text = ""
    for model in models_to_try:
        try:
            print(f"Requesting blueprint from Claude model: {model}...")
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                temperature=0.2,
                system=system_instruction,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text.strip()
            break
        except Exception as e:
            print(f"Model {model} failed: {e}. Trying next model...")
            continue
            
    if not response_text:
        print("Error: Failed to query Anthropic API with any supported model.")
        return None
        
    # Attempt XML-like tags parsing first
    if "<home_content>" in response_text or "<tagline>" in response_text:
        try:
            tagline_match = re.search(r'<tagline>(.*?)</tagline>', response_text, re.DOTALL | re.IGNORECASE)
            tagline = tagline_match.group(1).strip() if tagline_match else ""
            
            primary_match = re.search(r'<primary_color>(.*?)</primary_color>', response_text, re.DOTALL | re.IGNORECASE)
            primary_color = primary_match.group(1).strip() if primary_match else primary_hex
            
            secondary_match = re.search(r'<secondary_color>(.*?)</secondary_color>', response_text, re.DOTALL | re.IGNORECASE)
            secondary_color = secondary_match.group(1).strip() if secondary_match else secondary_hex
            
            content_match = re.search(r'<home_content>(.*?)(?:</home_content>|$)', response_text, re.DOTALL | re.IGNORECASE)
            home_content = content_match.group(1).strip() if content_match else ""
            
            if home_content or tagline:
                return {
                    "tagline": tagline,
                    "primary_color": primary_color,
                    "secondary_color": secondary_color,
                    "home_content": home_content
                }
        except Exception as e:
            print(f"XML parsing failed, trying JSON fallback: {e}")
 
    # Fallback to JSON parsing
    try:
        temp_text = response_text
        if temp_text.startswith("```json"):
            temp_text = temp_text[7:]
        if temp_text.endswith("```"):
            temp_text = temp_text[:-3]
        temp_text = temp_text.strip()
        return json.loads(temp_text)
    except Exception as e:
        print(f"Error: Failed to parse Claude response as JSON: {e}")
        debug_path = WP_BUILDER_DIR / "failed_blueprint.json"
        with open(debug_path, "w") as f:
            f.write(response_text)
        print(f"Saved raw response to {debug_path} for inspection.")
        return None

def main():
    parser = argparse.ArgumentParser(description="WordPress AI Custom Site Builder & Packager")
    
    # Generic inputs
    parser.add_argument("--requirements", "-r", help="Path to a YAML or JSON file containing business details/design requirements.")
    parser.add_argument("--blueprint", "-b", help="Path to a pre-generated JSON blueprint (bypasses Claude AI call entirely).")
    parser.add_argument("--vertical", "-v", help="Design vertical override (home_services, health_wellness, medical_professional, tech_saas, restaurant_food, professional_services)")
    parser.add_argument("--design-style", "-d", default="modern_minimalist", help="Design style preset override (modern_minimalist, dark_sleek, warm_editorial, corporate_tech, bold_creative, classic_elegant)")
    parser.add_argument("--export", "-e", action="store_true", default=True, help="Automatically package and zip the site theme, plugins, and db dump into dist/ at the end.")
    parser.add_argument("--no-export", dest="export", action="store_false", help="Disable packaging at the end.")
    parser.add_argument("--migrate", action="store_true", default=False, help="Enable legacy site content and media migration + technology audit.")
    
    # CLI-direct details overrides
    parser.add_argument("--business-name", help="Name of the business.")
    parser.add_argument("--phone", help="Business phone number.")
    parser.add_argument("--email", help="Business email address.")
    parser.add_argument("--address", help="Physical address / service area.")
    parser.add_argument("--rating", default="5.0", help="Business rating (e.g. 4.8).")
    parser.add_argument("--reviews", default="8", help="Count of customer reviews.")
    parser.add_argument("--categories", help="Niche categories (comma separated).")
    
    # Legacy DB inputs
    parser.add_argument("--lead-id", "-l", type=int, help="Fetch lead information from the main SQLite database (legacy mode).")
    parser.add_argument("--db", help="Path to SQLite database for legacy mode.", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--config", help="Path to configuration file to load Anthropic key.", default=str(DEFAULT_CONFIG_PATH))
    
    args = parser.parse_args()
    
    print("\n=======================================================")
    print("      WordPress AI Custom Site Builder & Packager")
    print("=======================================================")
    
    # 1. Resolve Lead / Business data
    lead = {}
    
    # Load from DB (Legacy mode)
    if args.lead_id:
        print(f"Running in Legacy Mode: Loading Lead {args.lead_id} from database...")
        lead = get_lead_data_from_db(args.lead_id, args.db)
        if not lead:
            print(f"Error: Lead {args.lead_id} not found in database {args.db}.")
            sys.exit(1)
    # Load from requirements file
    elif args.requirements:
        print(f"Loading business requirements from: {args.requirements}...")
        lead = load_lead_data_from_file(args.requirements)
        if not lead:
            sys.exit(1)
    # Direct CLI properties
    else:
        lead = {
            "business_name": args.business_name,
            "phone": args.phone,
            "email": args.email,
            "address": args.address,
            "rating": args.rating,
            "review_count": args.reviews,
            "categories": args.categories,
            "social_links_json": "{}"
        }
        
    # Check minimum requirements
    if not lead.get("business_name"):
        print("\nError: Business name must be provided.")
        print("Provide via --business-name CLI option, --requirements YAML/JSON file, or --lead-id legacy DB reference.")
        parser.print_help()
        sys.exit(1)
        
    print(f"Target Business Name: '{lead['business_name']}'")
    slug = slugify_name(lead["business_name"])
    
    # 2. Determine Vertical
    vertical = args.vertical or lead.get("vertical") or classify_vertical(lead.get("categories", ""))
    print(f"Target Design Vertical: {vertical}")
    
    # Set the target database name based on the business name slug
    db_name = f"wp_mockup_{slug.replace('-', '_')}"
    os.environ["WORDPRESS_DB_NAME"] = db_name
    print(f"Docker database instance: {db_name}")
    
    # 3. Spin up Docker containers (required early if migrating media or auditing via containers)
    if not ensure_containers_up():
        print("Error: Docker containers are not available.")
        sys.exit(1)
        
    # 4. Core WordPress Installation (required to import media)
    if not install_wordpress(lead["business_name"]):
        print("Error: Failed to initialize WordPress.")
        sys.exit(1)
        
    # Run technology audit and media migration if requested
    migrated_images = {}
    if args.migrate:
        # Run Audit Report
        audit_existing_site_technologies(slug, lead)
        # Run Media Migration
        migrated_images = migrate_legacy_media(slug, lead)
        
    # 5. Fetch Blueprint (Either pre-generated JSON or query Claude AI)
    blueprint = None
    if args.blueprint:
        print(f"Loading pre-generated Gutenberg block blueprint from: {args.blueprint}...")
        try:
            with open(args.blueprint, "r") as f:
                blueprint = json.load(f)
        except Exception as e:
            print(f"Error: Failed to load blueprint file: {e}")
            sys.exit(1)
    else:
        # Load API key and query Claude
        print("Resolving Anthropic API Key...")
        api_key = load_anthropic_key(args.config)
        if not api_key:
            print("Error: Anthropic API Key not found. Please provide it in config.yaml,")
            print("as ANTHROPIC_API_KEY env variable, or supply a pre-generated --blueprint JSON file.")
            sys.exit(1)
            
        print("Querying Claude AI to construct high-converting homepage blocks...")
        blueprint = query_claude_for_blueprint(lead, api_key, vertical, migrated_images, design_style=args.design_style)
        if not blueprint:
            print("Error: AI blueprint generation failed.")
            sys.exit(1)
            
    print("\n✓ Site Blueprint Loaded:")
    print(f"  - Tagline: {blueprint.get('tagline')}")
    print(f"  - Theme Colors: Primary={blueprint.get('primary_color')} | Secondary={blueprint.get('secondary_color')}")
    
    clean_default_posts()
    
    # 6. Generate Page Content
    # Home Page is loaded from blueprint, inner pages generated from clean, responsive layouts
    services_content, about_content, contact_content = get_inner_pages_content(vertical, lead)
    
    pages = [
        {
            "title": "Home",
            "slug": "home",
            "content": blueprint.get("home_content", "")
        },
        {
            "title": "Services",
            "slug": "services",
            "content": services_content
        },
        {
            "title": "About Us",
            "slug": "about-us",
            "content": about_content
        },
        {
            "title": "Contact Us",
            "slug": "contact",
            "content": contact_content
        }
    ]

    # Create WordPress pages
    created_pages = []
    homepage_id = None
    for page_spec in pages:
        wp_id = create_page(page_spec["title"], page_spec["slug"], page_spec["content"])
        if wp_id:
            page_spec["wp_id"] = wp_id
            created_pages.append(page_spec)
            if page_spec["slug"] == "home" or not homepage_id:
                homepage_id = wp_id

    # 7. Configure Site Layout and Navigation
    if homepage_id:
        configure_site_layout(homepage_id, blueprint.get("tagline", ""))
    if created_pages:
        setup_navigation_menu(created_pages)
        
    # 8. Copy Custom Premium Styles configuration
    configure_mockup_styles(lead, vertical, design_style=args.design_style)
    
    # 9. Scan and install custom user-supplied themes and plugins/apps
    install_custom_plugins_and_themes()
    
    # 10. Record active mockup in main prospects DB (if available/legacy mode)
    if args.lead_id:
        try:
            conn = sqlite3.connect(str(Path(args.db)))
            conn.execute("INSERT OR REPLACE INTO active_mockup (id, lead_id) VALUES (1, ?);", (args.lead_id,))
            conn.execute("INSERT OR REPLACE INTO generated_mockups (lead_id) VALUES (?);", (args.lead_id,))
            conn.commit()
            conn.close()
            print("✓ Updated prospects.db active/generated mockup registries.")
        except Exception as e:
            print(f"Warning: Failed to update database active_mockup registers: {e}")

    # 11. Package and Zip theme, plugins, and db dump
    if args.export:
        export_and_package_site(slug)
        
    print("\n=======================================================")
    print("✓ SUCCESS: WordPress Builder Compilation Complete!")
    print("=======================================================")
    print(f"Business: {lead['business_name']}")
    print("Mockup is live at: http://localhost:8080")
    print("WordPress Dashboard: http://localhost:8080/wp-admin")
    print("  - Username: admin")
    print("  - Password: adminpassword")
    print("=======================================================")

if __name__ == "__main__":
    main()
