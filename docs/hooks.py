"""
MkDocs build hook: copy skills/ and agents/ into docs/ before build, and say when a build has no
intro video.

On Windows, symlinks don't resolve. This hook copies the skills and agents
directories into docs/ so MkDocs can find the files on all platforms.

The intro video is not in git: the docs deploy downloads it from the intro-video release into
docs/assets/video/ (docs/maintenance/automation.md). A local or pull-request build without it is
complete and its players show the poster; the hook says so at INFO, never WARNING, which would
fail strict builds.
"""
import glob
import os
import shutil

from mkdocs.plugins import get_plugin_logger

log = get_plugin_logger(__name__)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DIRS = [
    ("skills", "docs/skills"),
    ("agents", "docs/agents"),
]


def _sync_dir(src, dst):
    if os.path.islink(dst) or os.path.isfile(dst):
        os.remove(dst)
    elif os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def on_pre_build(config):
    for src_rel, dst_rel in _DIRS:
        _sync_dir(
            os.path.join(REPO_ROOT, src_rel),
            os.path.join(REPO_ROOT, dst_rel),
        )


def on_post_build(config):
    if not glob.glob(os.path.join(config["site_dir"], "assets", "video", "*.mp4")):
        log.info(
            "No intro video in this build, so its players show only the poster. The docs deploy "
            "downloads it from the intro-video release; for a local preview put the release asset "
            "into docs/assets/video/ (gitignored, see docs/maintenance/automation.md)."
        )
