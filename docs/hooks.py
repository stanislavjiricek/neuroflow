"""
MkDocs build hook: copy skills/ and agents/ into docs/ before build.

On Windows, symlinks don't resolve. This hook copies the skills and agents
directories into docs/ so MkDocs can find the files on all platforms.
"""
import os
import shutil

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
