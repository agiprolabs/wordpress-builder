import json, subprocess
from pathlib import Path
from capture.bundle import BundlePaths
from capture.models import Manifest

def _default_runner(args):
    return subprocess.run(["docker", "compose", "run", "--rm", "wp-cli", *args],
                          capture_output=True, text=True)

def _default_copier(src, dst):
    subprocess.run(["docker", "cp", str(src), f"wp_mockup_app:{dst}"], check=True)
    subprocess.run(["docker", "exec", "wp_mockup_app", "chown", "-R", "www-data:www-data", dst], check=True)

class WPInstaller:
    def __init__(self, runner=_default_runner, copier=_default_copier):
        self.runner = runner
        self.copier = copier

    def install(self, bundle_dir: Path) -> None:
        bp = BundlePaths(bundle_dir)
        man = Manifest.from_dict(json.loads(bp.manifest.read_text()))
        self.runner(["db", "reset", "--yes"])
        self.runner(["core", "install", f"--url=http://localhost:8080",
                     f"--title={man.site_title}", "--admin_user=admin",
                     "--admin_password=adminpassword", "--admin_email=admin@example.com"])
        self.copier(bp.theme, "/var/www/html/wp-content/themes/captured-theme")
        self.runner(["theme", "activate", "captured-theme"])
        self.copier(bp.media, "/var/www/html/wp-content/uploads/captured")
        slug_to_id = {}
        for meta in man.pages:
            html = (bp.pages / f"{meta.slug}.html").read_text()
            res = self.runner(["post", "create", "--post_type=page", "--post_status=publish",
                               f"--post_title={meta.title}", f"--post_name={meta.slug}",
                               "--porcelain", f"--post_content={html}"])
            slug_to_id[meta.slug] = (res.stdout or "").strip()
        front_id = slug_to_id.get(man.front_page_slug)
        if front_id:
            self.runner(["option", "update", "show_on_front", "page"])
            self.runner(["option", "update", "page_on_front", front_id])
        self.runner(["menu", "create", "Primary"])
        for meta in man.pages:
            self.runner(["menu", "item", "add-post", "Primary", slug_to_id.get(meta.slug, "")])
