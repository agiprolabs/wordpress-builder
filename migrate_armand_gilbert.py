import os
import sys
import json
import sqlite3
import subprocess
import time
import re
import shutil
import urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup

# Paths
WP_DIR = Path("/Users/jonathanowens/Projects/wordpress-builder")
DB_PATH = Path("/Users/jonathanowens/Projects/prospector/prospects.db")
CRAWLED_DIR = Path("/Users/jonathanowens/Projects/prospector/scratch/crawled_pages")
IMAGES_DIR = Path("/Users/jonathanowens/Projects/prospector/scratch/imported_images/uploads/2026/06")

def run_compose_command(cmd_args):
    """Run docker-compose command in wordpress-builder context."""
    full_cmd = ["docker", "compose"] + cmd_args
    return subprocess.run(
        full_cmd,
        cwd=str(WP_DIR),
        capture_output=True,
        text=True
    )

def run_compose_command_with_input(cmd_args, input_str):
    """Run docker-compose command with stdin pipe."""
    full_cmd = ["docker", "compose"] + cmd_args
    return subprocess.run(
        full_cmd,
        cwd=str(WP_DIR),
        input=input_str,
        capture_output=True,
        text=True
    )

def find_media_url(filename, mapping):
    """Finds the best matching URL in mapping for filename, ignoring suffixes like -1, -2, etc."""
    if not filename:
        return ""
    if filename in mapping:
        return mapping[filename]
        
    # Try fuzzy matching
    base, ext = os.path.splitext(filename)
    base_escaped = re.escape(base)
    # Match base + optional -digits or -widthxheight (like -150x150) + ext
    pattern = re.compile(rf"^{base_escaped}(-\d+)?(-\d+x\d+)?{re.escape(ext)}$", re.IGNORECASE)
    for key, val in mapping.items():
        if pattern.match(key):
            return val
            
    # Try substring match
    for key, val in mapping.items():
        if base in key:
            return val
            
    return ""

def find_media_id(filename, mapping_ids):
    """Finds the best matching ID in mapping_ids for filename, ignoring suffixes like -1, -2, etc."""
    if not filename:
        return None
    if filename in mapping_ids:
        return mapping_ids[filename]
        
    base, ext = os.path.splitext(filename)
    base_escaped = re.escape(base)
    pattern = re.compile(rf"^{base_escaped}(-\d+)?(-\d+x\d+)?{re.escape(ext)}$", re.IGNORECASE)
    for key, val in mapping_ids.items():
        if pattern.match(key):
            return val
            
    for key, val in mapping_ids.items():
        if base in key:
            return val
            
    return None

def replace_original_urls(text, mapping):
    """Replaces any references to original upload URLs in the text with the mapped local URLs."""
    if not text:
        return ""
    # Pattern to match original uploads URLs (with or without www, any protocol, any year/month path)
    pattern = re.compile(r'https?://(?:www\.)?armandgilbert\.com/wp-content/uploads/\d{4}/\d{2}/([^"\')\s>]+)', re.IGNORECASE)
    
    def repl_func(match):
        fname = os.path.basename(match.group(1))
        local_url = find_media_url(fname, mapping)
        return local_url if local_url else match.group(0)
        
    return pattern.sub(repl_func, text)

def main():
    print("=== Armand Gilbert Web Design 1:1 WordPress Migration ===")

    # 1. Verify Docker and start containers
    print("Checking container status...")
    run_compose_command(["up", "-d"])
    
    # Wait for MySQL to initialize
    print("Waiting for database connection...")
    max_retries = 30
    for i in range(max_retries):
        check_res = run_compose_command(["run", "--rm", "wp-cli", "mysqladmin", "ping", "-h", "db", "-u", "wordpress", "-pwordpresspassword"])
        if check_res.returncode == 0:
            print("Database connection is healthy!")
            break
        time.sleep(1)
    else:
        print("Error: MySQL timeout.")
        sys.exit(1)

    # 2. Reset database and run clean installation
    print("Resetting database...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "db", "reset", "--yes", "--defaults"])
    
    print("Installing WordPress core...")
    install_res = run_compose_command([
        "run", "--rm", "wp-cli", "wp", "core", "install",
        "--url=http://localhost:8080",
        "--title=Armand Gilbert Web Design IT & Marketing",
        "--admin_user=admin",
        "--admin_password=adminpassword",
        "--admin_email=me@armandgilbert.com",
        "--skip-email"
    ])
    if install_res.returncode != 0:
        print(f"Failed to install WordPress: {install_res.stderr}")
        sys.exit(1)
        
    print("Cleaning default posts and pages...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "post", "delete", "1", "2", "--force"])

    # Enable permalinks
    run_compose_command(["run", "--rm", "wp-cli", "wp", "rewrite", "structure", "/%postname%/"])

    # 3. Copy and Import Media Assets
    print("Importing media files...")
    container_temp_dir = "/var/www/html/wp-content/uploads/migration_temp"
    
    # Ensure destination parent folder starts fresh to avoid filename suffixing (e.g. -2, -3, etc.)
    subprocess.run(["docker", "exec", "wp_mockup_app", "rm", "-rf", "/var/www/html/wp-content/uploads"], capture_output=True)
    subprocess.run(["docker", "exec", "wp_mockup_app", "mkdir", "-p", "/var/www/html/wp-content/uploads"], capture_output=True)
    
    # Copy images directory to container in a single command
    print("Copying images to container...")
    subprocess.run(["docker", "cp", str(IMAGES_DIR), "wp_mockup_app:/var/www/html/wp-content/uploads/migration_temp"], capture_output=True)
    
    # Set proper permissions so the www-data user running wp-cli can write to and import files
    subprocess.run(["docker", "exec", "wp_mockup_app", "chown", "-R", "www-data:www-data", "/var/www/html/wp-content/uploads"], capture_output=True)
    
    # List files to import
    image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
    container_paths = [f"{container_temp_dir}/{fname}" for fname in image_files]
    
    # Import in chunks of 150 files to avoid potential shell line buffer issues
    print(f"Importing {len(image_files)} media files in batch...")
    chunk_size = 150
    for i in range(0, len(container_paths), chunk_size):
        chunk = container_paths[i:i + chunk_size]
        print(f"  Importing batch {i//chunk_size + 1} ({len(chunk)} files)...")
        run_compose_command(["run", "--rm", "wp-cli", "wp", "media", "import"] + chunk)
        
    # Fetch all imported attachments IDs and URLs in a single query
    print("Fetching media mappings...")
    list_res = run_compose_command([
        "run", "--rm", "wp-cli", "wp", "post", "list",
        "--post_type=attachment",
        "--fields=ID,guid",
        "--format=json",
        "--posts_per_page=1000"
    ])
    media_mapping = {}
    media_ids = {}
    if list_res.returncode == 0:
        try:
            attachments = json.loads(list_res.stdout)
            for att in attachments:
                wp_url = att["guid"]
                fname = os.path.basename(urllib.parse.urlparse(wp_url).path)
                media_mapping[fname] = wp_url
                media_ids[fname] = int(att["ID"])
        except Exception as e:
            print(f"Error parsing attachments JSON: {e}")
    else:
        print(f"Error listing attachments: {list_res.stderr}")

    # Remove temporary folder inside container
    subprocess.run(["docker", "exec", "wp_mockup_app", "rm", "-rf", container_temp_dir], capture_output=True)

    # 4. Replacement mapping handled dynamically via regex helper replace_original_urls

    def clean_text_content(soup_obj):
        """Cleans and rewrites urls in BeautifulSoup object."""
        # Replace image links
        for img in soup_obj.find_all("img"):
            src = img.get("src", "")
            fname = os.path.basename(urllib.parse.urlparse(src).path) if src else ""
            url = find_media_url(fname, media_mapping)
            if url:
                img["src"] = url
        
        # Replace page links
        for a in soup_obj.find_all("a"):
            href = a.get("href", "")
            if href:
                if href.rstrip("/") == "https://armandgilbert.com":
                    a["href"] = "/"
                elif "armandgilbert.com/about" in href:
                    a["href"] = "/about/"
                elif "armandgilbert.com/contact" in href:
                    a["href"] = "/contact-us/"
                elif "armandgilbert.com/faq" in href:
                    a["href"] = "/faq/"
                elif "armandgilbert.com/get-started" in href:
                    a["href"] = "/get-started/"
                elif "armandgilbert.com/referrals" in href:
                    a["href"] = "/referrals/"
                elif "armandgilbert.com/who-i-am" in href:
                    a["href"] = "/who-i-am/"
                elif "armandgilbert.com/category/blog" in href:
                    a["href"] = "/category/blog/"
                elif href.startswith("https://armandgilbert.com/wp-content/uploads/"):
                    fname = os.path.basename(urllib.parse.urlparse(href).path)
                    url = find_media_url(fname, media_mapping)
                    if url:
                        a["href"] = url
        return soup_obj

    # 5. Create Blog Posts
    print("Creating Blog Posts...")
    posts_data = [
        {
            "title": "Gravity Form’s CSS is Mess",
            "date": "2025-04-13 12:00:00",
            "categories": "Plugins, WordPress",
            "thumb": "GravityForms-185x185.jpg",
            "excerpt": "Why Gravity Forms Looks Messy Without Custom CSS — And What It Teaches Us About Software Design. Gravity Forms is a fantastic plugin for WordPress — arguably one of the most powerful tools available..."
        },
        {
            "title": "Armand Gilbert Web",
            "date": "2019-07-15 12:00:00",
            "categories": "Blog, Featured",
            "thumb": "ArmandGilbertWebDesign.jpg",
            "excerpt": "Welcome to AG Web Design Our company combines affordable, inventive graphic design, e-commerce development, and search engine optimization. We focus on building sites that load quickly and rank well."
        },
        {
            "title": "Parkers Perfect",
            "date": "2019-06-21 12:00:00",
            "categories": "Featured, Portfolio",
            "thumb": "parkersperfectbanner960-185x185.jpg",
            "excerpt": "Parkers Perfect new website represents a significant improvement from their current site which was a simple static site you can see here. The new site will be search engine optimized."
        },
        {
            "title": "Watkins Landmark",
            "date": "2019-06-14 12:00:00",
            "categories": "Featured, Portfolio",
            "thumb": "Watkins960-185x185.jpg",
            "excerpt": "Watkins Landmark Construction is a dynamic responsive web site we redesigned in 2016. It has JavaScript animated banners, CSS3 design elements, and a flexible responsive based layout."
        },
        {
            "title": "Rancho Tissue",
            "date": "2019-06-08 12:00:00",
            "categories": "Featured, Portfolio",
            "thumb": "RanchoTissue960-185x185.jpg",
            "excerpt": "Rancho Tissue Technologies is a highly developed plant grower specializing in plant tissue cloning of agave, succulents, aloe and bamboo. They service the needs of the horticulture industry."
        },
        {
            "title": "unRAID… The Good, The Bad,  & The Ugly.",
            "date": "2018-12-19 12:00:00",
            "categories": "Blog, NAS, Servers",
            "thumb": "unraid-185x185.jpg",
            "excerpt": "The Good. What is unRAID? unRAID is an OS, an Operating System built based on Linux, that gives you absolute control over your storage, virtual machines, and docker containers."
        },
        {
            "title": "Mozena Medical",
            "date": "2018-11-17 12:00:00",
            "categories": "Featured, Portfolio",
            "thumb": "MozenaMedical960-185x185.jpg",
            "excerpt": "Mozena Medical is a Medical Supply Company offering a small range of mobility solutions. There previous developer had failed to deliver a functional product. We rebuilt the site."
        }
    ]

    for post in posts_data:
        # Check if category exists, if not create it
        cats = [c.strip() for c in post["categories"].split(",")]
        cat_ids = []
        for cat in cats:
            check_cat = run_compose_command(["run", "--rm", "wp-cli", "wp", "term", "exists", "category", cat])
            if check_cat.returncode != 0:
                create_cat = run_compose_command(["run", "--rm", "wp-cli", "wp", "term", "create", "category", cat, "--porcelain"])
                cat_ids.append(create_cat.stdout.strip())
            else:
                # get term id
                cat_id_res = run_compose_command(["run", "--rm", "wp-cli", "wp", "term", "list", "category", f"--search={cat}", "--field=term_id"])
                cat_ids.append(cat_id_res.stdout.strip().split("\n")[0])
        
        # Build paragraph Gutenberg block content
        content_gutenberg = f"<!-- wp:paragraph -->\n<p>{post['excerpt']}</p>\n<!-- /wp:paragraph -->"
        
        # Create post
        create_res = run_compose_command([
            "run", "--rm", "wp-cli", "wp", "post", "create",
            "--post_type=post",
            f"--post_title={post['title']}",
            f"--post_date={post['date']}",
            f"--post_content={content_gutenberg}",
            f"--post_category={','.join(cat_ids)}",
            f"--post_excerpt={post['excerpt']}",
            "--post_status=publish",
            "--porcelain"
        ])
        if create_res.returncode == 0:
            post_id = int(create_res.stdout.strip())
            # Set featured image
            thumb_file = post["thumb"]
            thumb_id = find_media_id(thumb_file, media_ids)
            if thumb_id:
                run_compose_command([
                    "run", "--rm", "wp-cli", "wp", "post", "meta", "set", str(post_id), "_thumbnail_id", str(thumb_id)
                ])
                print(f"  ✓ Created post '{post['title']}' with featured image.")
        else:
            print(f"  X Failed to create post '{post['title']}': {create_res.stderr}")

    # 6. Create Pages from raw HTML
    print("Creating Pages...")
    pages_to_create = [
        {"title": "About Us", "slug": "about", "file": "about.html"},
        {"title": "Contact Us", "slug": "contact-us", "file": "contact.html"},
        {"title": "FAQ", "slug": "faq", "file": "faq.html"},
        {"title": "Get Started", "slug": "get-started", "file": "get-started.html"},
        {"title": "Referrals", "slug": "referrals", "file": "referrals.html"},
        {"title": "Who I Am", "slug": "who-i-am", "file": "who-i-am.html"}
    ]

    for p_spec in pages_to_create:
        fpath = CRAWLED_DIR / p_spec["file"]
        if not fpath.exists():
            print(f"  X Crawled file {p_spec['file']} not found!")
            continue
            
        with open(fpath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            
        left_area = soup.find(id="left-area")
        if not left_area:
            left_area = soup.find(id="content-area") or soup
            
        # Clean the inner links/images
        left_area = clean_text_content(left_area)
        
        # Serialize the children as clean Gutenberg blocks
        gutenberg_blocks = []
        for child in left_area.find_all(recursive=False):
            # Ignore headers that are redundant
            if child.name == "h1" and child.get_text().strip().lower() in [p_spec["title"].lower(), p_spec["slug"].lower()]:
                continue
            
            # Skip WordPress post-meta metadata paragraph
            if child.name == "p" and "posted in" in child.get_text().strip().lower():
                continue
                
            child_str = str(child)
            # Apply URL substitutions using regex helper
            child_str = replace_original_urls(child_str, media_mapping)
                
            if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(child.name[1])
                gutenberg_blocks.append(f'<!-- wp:heading {{"level":{level}}} -->\n{child_str}\n<!-- /wp:heading -->')
            elif child.name == "p":
                gutenberg_blocks.append(f'<!-- wp:paragraph -->\n{child_str}\n<!-- /wp:paragraph -->')
            elif child.name in ["ul", "ol"]:
                gutenberg_blocks.append(f'<!-- wp:list -->\n{child_str}\n<!-- /wp:list -->')
            elif child.name == "table":
                gutenberg_blocks.append(f'<!-- wp:table -->\n<figure class="wp-block-table">{child_str}</figure>\n<!-- /wp:table -->')
            elif child.name == "form":
                gutenberg_blocks.append(f'<!-- wp:html -->\n{child_str}\n<!-- /wp:html -->')
            else:
                # Wrap any other complex div or structure inside Classic/HTML block
                gutenberg_blocks.append(f'<!-- wp:html -->\n{child_str}\n<!-- /wp:html -->')
                
        page_content = "\n\n".join(gutenberg_blocks)
        
        # Create page via WP-CLI reading content from STDIN
        create_res = run_compose_command_with_input([
            "run", "--rm", "wp-cli", "wp", "post", "create",
            "-",
            "--post_type=page",
            f"--post_title={p_spec['title']}",
            f"--post_name={p_spec['slug']}",
            "--post_status=publish",
            "--porcelain"
        ], page_content)
        
        if create_res.returncode == 0:
            p_spec["wp_id"] = int(create_res.stdout.strip())
            print(f"  ✓ Page '{p_spec['title']}' created with ID {p_spec['wp_id']}")
        else:
            print(f"  X Failed to create page '{p_spec['title']}': {create_res.stderr}")

    # 7. Create Homepage
    print("Creating Homepage layout...")
    # Homepage uses slider + columns block containing posts list (left) and sidebar widgets    # Rebuild slider data
    slider_html = '<div class="et_cycle" id="featured"><span id="left-shadow"></span><span id="right-shadow"></span><div id="slides">'
    slides_list = [
        {"title": "Parkers Perfect", "img": "parkersperfectbanner960.jpg", "slug": "parkers-perfect", "desc": "Parkers Perfect new website represents a significant improvement from their current site which was a simple static site you can see here. The new site will be search engine optimized with jQuery based banner animations, website analytics, and onsite eCommerce. Click here for the current website."},
        {"title": "Watkins Landmark", "img": "Watkins960.jpg", "slug": "watkins-landmark", "desc": "Watkins Landmark Construction is a dynamic responsive web site we redesigned in 2016. It has JavaScript animated banners, CSS3 design elements, and a flexible responsive based layout designed to scale automatically."},
        {"title": "Rancho Tissue", "img": "RanchoTissue960.jpg", "slug": "rancho-tissue-2", "desc": "Rancho Tissue Technologies is a highly developed plant grower specializing in plant tissue cloning of agave, succulents, aloe and bamboo. They service the needs of the horticulture industry with custom tissue cultures."},
        {"title": "Mozena Medical", "img": "MozenaMedical960.jpg", "slug": "mozena-medical", "desc": "Mozena Medical is a Medical Supply Company offering a small range of mobility solutions. There previous developer had failed to deliver a functional product. We rebuilt the site for less than their original budget."},
        {"title": "American Catholic Church US", "img": "american-catholic-church-us.jpg", "slug": "american-catholic-church-us", "desc": "Christ Church in San Gabriel Valley is a diocese under the care of Bishop Robert Collier of The American Catholic Church US. I built this and a companion site for the Church community's outreach and services."},
        {"title": "SoundPros", "img": "banner-soundpros.jpg", "slug": "soundpros", "desc": "SoundPros.com is a private membership only retail eCommerce web site for high end electronic entertainment equipment. This was necessitated by the competitive nature of the market and manufacturer pricing policies."},
        {"title": "The Maxham Firm", "img": "Maxhamfirm-banner.jpg", "slug": "the-maxham-firm", "desc": "Maxhamfirm.com is a web site for the Maxham Firm. They are a San Diego based provider of legal services in the field of intellectual property, specializing primarily in patent and trademark law."},
        {"title": "Pillows And Decor", "img": "pillowsanddecor.jpg", "slug": "pillows-and-decor", "desc": "PillowsAndDecor.com is a Shopify based ecommerce site. It contains many hundreds of designer pillows in a flexible easy to search customized shopify theme that scales well from desktop to mobile screens."},
        {"title": "Social Gab", "img": "socialgab.jpg", "slug": "social-gab", "desc": "SocialGab is a social media content development company located in the Los Angeles Area. The company had no logo, branding or collateral material of any kind. They needed a dynamic web site to start marketing."},
        {"title": "Millenia SD", "img": "millenia-portfolio.jpg", "slug": "millenia-sd", "desc": "Millenia SD is a multimillion dollar mixed use development located in Otay Ranch area of South Bay San Diego. This site design was defined to the pixel by the McMillian’s design firm. We built it exactly to spec."}
    ]
    
    for idx, slide in enumerate(slides_list):
        img_url = find_media_url(slide["img"], media_mapping)
        active_class = "active" if idx == 0 else ""
        slider_html += f"""
        <div class="slide {active_class}" data-index="{idx}">
            <img alt="{slide['title']}" class="portfolio-slide-img" src="{img_url}" />
            <div class="overlay"></div>
            <div class="overlay2"></div>
            <div class="description">
                <div class="outer-content">
                    <div class="inner-content">
                        <h2 class="title"><a href="/{slide['slug']}/">{slide['title']}</a></h2>
                        <p>{slide['desc']}</p>
                        <a class="readmore" href="/{slide['slug']}/"><span>Learn More</span></a>
                        <div class="clear"></div>
                    </div>
                </div>
                <div class="bottom"></div>
            </div>
        </div>
        """
    slider_html += '</div>'
    # Add navigation dots
    slider_html += '<div id="controllers-wrapper"><div id="controllers">'
    for idx in range(len(slides_list)):
        active_class = "active" if idx == 0 else ""
        slider_html += f'<a class="{active_class}" href="#" data-index="{idx}">{idx + 1}</a>'
    slider_html += '</div></div></div>'

    # Rebuild static posts list for the homepage matching original DeepFocus class structures
    posts_list_html = '<div id="left-area">'
    for idx, post in enumerate(posts_data):
        wp_url = find_media_url(post["thumb"], media_mapping)
        post_slug = post["title"].lower().replace("’", "").replace("…", "").replace(",", "").replace(".", "").replace("  ", " ").replace(" ", "-")
        # Build category links
        cat_links = ", ".join([f'<a href="/category/{c.lower().replace(" ", "-")}/" rel="category tag">{c}</a>' for c in post["categories"].split(",")])
        
        posts_list_html += f"""
        <div class="entry clearfix">
            <div class="blog-thumb">
                <a href="/{post_slug}/">
                    <img alt="{post['title']}" height="185" src="{wp_url}" width="185" />
                    <span class="overlay"></span>
                </a>
            </div>
            <div class="entry-description">
                <h2 class="title"><a href="/{post_slug}/">{post['title']}</a></h2>
                <p class="post-meta">Posted in {cat_links}</p>
                <div class="clear"></div>
                <p>{post['excerpt']}</p>
                <a class="readmore" href="/{post_slug}/"><span>Learn More</span></a>
            </div>
        </div>
        """
    posts_list_html += '</div>'

    # Assemble Homepage block layout
    homepage_gutenberg = f"""<!-- wp:html -->
<div id="home-top"></div>
<div id="hr">
    <div id="hr-center">
        <div id="intro">
            <div class="center-highlight">
                <div class="container">
                    {slider_html}
                </div>
            </div>
        </div>
    </div>
</div>
<!-- /wp:html -->

<!-- wp:html -->
<div class="center-highlight">
    <div class="container">
        <div id="content-area" class="clearfix">
            {posts_list_html}
            <div id="sidebar">
                <div class="widget widget_block widget_search">
                    <form action="http://localhost:8080" class="wp-block-search__button-outside wp-block-search__text-button wp-block-search" method="get" role="search">
                        <label class="wp-block-search__label" for="wp-block-search__input-1">Search</label>
                        <div class="wp-block-search__inside-wrapper">
                            <input class="wp-block-search__input" id="wp-block-search__input-1" name="s" placeholder="" required="" type="search" value=""/>
                            <button aria-label="Search" class="wp-block-search__button wp-element-button" type="submit">Search</button>
                        </div>
                    </form>
                </div>
                <div class="widget widget_block">
                    <div class="wp-block-group">
                        <h4 class="wp-block-heading">Recent Posts</h4>
                        <ul class="wp-block-latest-posts__list wp-block-latest-posts">
                            <li><a class="wp-block-latest-posts__post-title" href="/gravity-forms-css-is-mess/">Gravity Form’s CSS is Mess</a></li>
                            <li><a class="wp-block-latest-posts__post-title" href="/armand-gilbert-web/">Armand Gilbert Web</a></li>
                            <li><a class="wp-block-latest-posts__post-title" href="/parkers-perfect/">Parkers Perfect</a></li>
                            <li><a class="wp-block-latest-posts__post-title" href="/watkins-landmark/">Watkins Landmark</a></li>
                            <li><a class="wp-block-latest-posts__post-title" href="/rancho-tissue/">Rancho Tissue</a></li>
                        </ul>
                    </div>
                </div>
                <div class="widget widget_block">
                    <div class="wp-block-group">
                        <h4 class="wp-block-heading">Recent Comments</h4>
                        <ul class="wp-block-latest-comments">
                            <li class="wp-block-latest-comments__comment"><span class="wp-block-latest-comments__comment-meta">No comments yet.</span></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<!-- /wp:html -->
<!-- wp:paragraph -->
<p style="display:none"></p>
<!-- /wp:paragraph -->"""

    # Create Homepage page reading content from STDIN
    home_res = run_compose_command_with_input([
        "run", "--rm", "wp-cli", "wp", "post", "create",
        "-",
        "--post_type=page",
        "--post_title=Home",
        "--post_name=home",
        "--post_status=publish",
        "--porcelain"
    ], homepage_gutenberg)
    
    if home_res.returncode == 0:
        homepage_id = int(home_res.stdout.strip())
        print(f"✓ Homepage created with ID {homepage_id}")
        
        # Configure Static Front Page
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "show_on_front", "page"])
        run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "page_on_front", str(homepage_id)])
        print("✓ Static front page configured to Home.")
    else:
        print(f"X Failed to create homepage: {home_res.stderr}")
        homepage_id = None

    # 8. Setup Primary Navigation Menu
    print("Setting up primary navigation menu...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "menu", "create", "Primary Menu"])
    
    # We want menu items in order: Home, About Us, Contact Us, FAQ, Get Started, Referrals, Who I Am
    menu_pages = [
        {"title": "Home", "wp_id": homepage_id},
        {"title": "About Us", "wp_id": [p for p in pages_to_create if p["slug"] == "about"][0].get("wp_id")},
        {"title": "Contact Us", "wp_id": [p for p in pages_to_create if p["slug"] == "contact-us"][0].get("wp_id")},
        {"title": "FAQ", "wp_id": [p for p in pages_to_create if p["slug"] == "faq"][0].get("wp_id")},
        {"title": "Get Started", "wp_id": [p for p in pages_to_create if p["slug"] == "get-started"][0].get("wp_id")},
        {"title": "Referrals", "wp_id": [p for p in pages_to_create if p["slug"] == "referrals"][0].get("wp_id")},
        {"title": "Who I Am", "wp_id": [p for p in pages_to_create if p["slug"] == "who-i-am"][0].get("wp_id")}
    ]
    
    for item in menu_pages:
        if item["wp_id"]:
            run_compose_command([
                "run", "--rm", "wp-cli", "wp", "menu", "item", "add-post", "Primary Menu", str(item["wp_id"])
            ])
            
    # Assign menu to primary location
    run_compose_command([
        "run", "--rm", "wp-cli", "wp", "menu", "location", "assign", "Primary Menu", "primary"
    ])
    print("✓ Primary Menu created and assigned.")

    # 9. Configure theme.json Dark Settings
    print("Updating theme.json configuration...")
    theme_json_path = WP_DIR / "custom-theme" / "premium-fse-theme" / "theme.json"
    with open(theme_json_path, "r") as f:
        theme_json = json.load(f)
        
    # Inject 1:1 color scheme
    theme_json["settings"]["color"]["palette"] = [
        {
            "slug": "primary",
            "color": "#bfbfbf", # Body text
            "name": "Body Text Light Gray"
        },
        {
            "slug": "secondary",
            "color": "#986c04", # Gold accents
            "name": "DeepFocus Gold"
        },
        {
            "slug": "background",
            "color": "#121212", # Dark page background
            "name": "DeepFocus Dark Background"
        },
        {
            "slug": "muted",
            "color": "#1c1c1c", # Panels background
            "name": "Panel Background"
        }
    ]
    
    # Save modified theme.json
    with open(theme_json_path, "w") as f:
        json.dump(theme_json, f, indent=2)
    print("✓ theme.json palette updated.")

    # 9b. Copy and Activate Theme
    print("Copying custom theme premium-fse-theme to container...")
    subprocess.run([
        "docker", "exec", "wp_mockup_app", "mkdir", "-p", "/var/www/html/wp-content/themes/premium-fse-theme"
    ], capture_output=True)
    
    # Copy host premium-fse-theme to container theme directory
    subprocess.run([
        "docker", "cp", "/Users/jonathanowens/Projects/wordpress-builder/custom-theme/premium-fse-theme", "wp_mockup_app:/var/www/html/wp-content/themes/"
    ], capture_output=True)
    
    # Remove stale home.html inside container if it exists
    subprocess.run([
        "docker", "exec", "wp_mockup_app", "rm", "-f", "/var/www/html/wp-content/themes/premium-fse-theme/templates/home.html"
    ], capture_output=True)
    
    # Activate theme
    run_compose_command(["run", "--rm", "wp-cli", "wp", "theme", "activate", "premium-fse-theme"])
    print("✓ Custom FSE theme premium-fse-theme activated.")

    # 9c. Write header.html and footer.html dynamically inside container
    logo_url = find_media_url("header-dual-logo3.png", media_mapping)
    header_html = f"""<div id="top">
    <div class="container">
        <div id="header">
            <a href="/"><img src="{logo_url}" alt="Armand Gilbert Web Design IT &amp; Marketing" id="logo"></a>
            <div id="menu" class="clearfix">
                <!-- wp:navigation {{"layout":{{"type":"flex","justifyContent":"right"}}}} /-->
            </div>
        </div>
    </div>
</div>"""
    
    tmp_header_file = WP_DIR / "scratch" / "tmp_header.html"
    with open(tmp_header_file, "w", encoding="utf-8") as f_hdr:
        f_hdr.write(header_html)
    subprocess.run(["docker", "cp", str(tmp_header_file), "wp_mockup_app:/var/www/html/wp-content/themes/premium-fse-theme/parts/header.html"], capture_output=True)
    os.remove(tmp_header_file)
    print("✓ Header template part written dynamically with logo URL.")

    footer_html = """<div id="footer">
    <div id="footer-wrapper">
        <div id="footer-center">
            <div class="container">
                <p id="copyright">
                    Designed by <a href="http://www.elegantthemes.com" title="Elegant Themes">Elegant Themes</a> | Powered by <a href="http://www.wordpress.org">WordPress</a>
                </p>
            </div>
        </div>
    </div>
</div>"""
    
    tmp_footer_file = WP_DIR / "scratch" / "tmp_footer.html"
    with open(tmp_footer_file, "w", encoding="utf-8") as f_ftr:
        f_ftr.write(footer_html)
    subprocess.run(["docker", "cp", str(tmp_footer_file), "wp_mockup_app:/var/www/html/wp-content/themes/premium-fse-theme/parts/footer.html"], capture_output=True)
    os.remove(tmp_footer_file)
    print("✓ Footer template part written dynamically.")


    # 9d. Copy and Activate Plugins
    print("Scanning and copying custom plugins...")
    plugins_local_dir = WP_DIR / "custom-plugins"
    if plugins_local_dir.exists():
        plugins = [p for p in plugins_local_dir.iterdir() if p.name != "mu-plugins" and (p.is_dir() or p.suffix == ".php")]
        for p in plugins:
            subprocess.run([
                "docker", "cp", str(p), f"wp_mockup_app:/var/www/html/wp-content/plugins/{p.name}"
            ], capture_output=True)
            print(f"  ✓ Copied plugin: {p.name}")
            
            slug = p.stem if p.is_file() else p.name
            act_res = run_compose_command(["run", "--rm", "wp-cli", "wp", "plugin", "activate", slug])
            if act_res.returncode == 0:
                print(f"  ✓ Activated plugin: {slug}")
            else:
                print(f"  ✗ Failed to activate plugin {slug}: {act_res.stderr.strip()}")

    # 10. Copy Stylesheet Plugin and Set Vertical
    print("Injecting Custom CSS overrides in container...")
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_vertical", "armand_gilbert"])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_business_name", "Armand Gilbert Web Design"])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_phone", "888-266-5449"])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_email", "me@armandgilbert.com"])
    run_compose_command(["run", "--rm", "wp-cli", "wp", "option", "update", "wp_mockup_address", "San Diego, CA"])

    # Overwrite the stylesheet plugin in wp_mockup_app
    # We will write custom CSS overrides for vertical-armand_gilbert in premium-mockup-styles.php!
    styles_src = WP_DIR / "premium-mockup-styles.php"
    subprocess.run([
        "docker", "cp", str(styles_src), "wp_mockup_app:/var/www/html/wp-content/mu-plugins/premium-mockup-styles.php"
    ], capture_output=True)
    print("✓ Stylesheet plugin copied to container.")

    print("\n✓ 1:1 Migration Complete! Access the site on: http://localhost:8080")

if __name__ == "__main__":
    main()
