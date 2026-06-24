import json
import subprocess
from pathlib import Path
from capture.bundle import BundlePaths
from capture.models import Manifest


def _default_runner(args, input=None):
    # -T disables the pseudo-TTY so stdin piping works
    return subprocess.run(["docker", "compose", "run", "--rm", "-T", "wp-cli", *args],
                          capture_output=True, text=True, input=input)


def _default_copier(src, dst):
    subprocess.run(["docker", "cp", str(src), f"wp_mockup_app:{dst}"], check=True)
    subprocess.run(["docker", "exec", "wp_mockup_app", "chown", "-R", "www-data:www-data", dst], check=True)


class WPInstaller:
    def __init__(self, runner=_default_runner, copier=_default_copier):
        self.runner = runner
        self.copier = copier

    def _run(self, args, input=None):
        res = self.runner(args, input=input)
        if getattr(res, "returncode", 0) != 0:
            raise RuntimeError(f"wp-cli failed ({' '.join(args)}): {getattr(res, 'stderr', '')}")
        return res

    def install(self, bundle_dir: Path) -> None:
        bp = BundlePaths(bundle_dir)
        man = Manifest.from_dict(json.loads(bp.manifest.read_text()))
        self._run(["db", "reset", "--yes"])
        self._run(["core", "install", "--url=http://localhost:8080",
                   f"--title={man.site_title}", "--admin_user=admin",
                   # dev-only fixed credentials for the local mockup
                   "--admin_password=adminpassword", "--admin_email=admin@example.com"])
        self.copier(bp.theme, "/var/www/html/wp-content/themes/captured-theme")
        self._run(["theme", "activate", "captured-theme"])
        self.copier(bp.media, "/var/www/html/wp-content/uploads/captured")
        slug_to_id = {}
        for meta in man.pages:
            html = (bp.pages / f"{meta.slug}.html").read_text()
            # pipe content via stdin (wp post create reads STDIN) to avoid ARG_MAX on large pages
            res = self._run(["post", "create", "--post_type=page", "--post_status=publish",
                             f"--post_title={meta.title}", f"--post_name={meta.slug}",
                             "--porcelain"], input=html)
            slug_to_id[meta.slug] = (res.stdout or "").strip()
        front_id = slug_to_id.get(man.front_page_slug)
        if front_id:
            self._run(["option", "update", "show_on_front", "page"])
            self._run(["option", "update", "page_on_front", front_id])
        self._run(["menu", "create", "Primary"])
        for meta in man.pages:
            post_id = slug_to_id.get(meta.slug)
            if post_id:  # skip pages whose post create failed/returned no id
                self._run(["menu", "item", "add-post", "Primary", post_id])
