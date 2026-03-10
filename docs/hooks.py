"""
MkDocs build hook: copy skills/ into docs/skills/ before build.

On Windows, the docs/skills symlink doesn't resolve. This hook copies
the skills directory into docs/ so MkDocs can find the SKILL.md files
on all platforms.
"""
import os
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_SRC = os.path.join(REPO_ROOT, "skills")
SKILLS_DST = os.path.join(REPO_ROOT, "docs", "skills")


def on_pre_build(config):
    # Remove stale symlink or old copy
    if os.path.islink(SKILLS_DST) or os.path.isfile(SKILLS_DST):
        os.remove(SKILLS_DST)
    elif os.path.isdir(SKILLS_DST):
        shutil.rmtree(SKILLS_DST)
    shutil.copytree(SKILLS_SRC, SKILLS_DST)
