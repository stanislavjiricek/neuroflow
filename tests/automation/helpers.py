"""Shared helpers for the automation tests: load scripts by path, build a fixture plugin repo."""

from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUTOMATION = REPO / "scripts" / "automation"


def load(name: str):
    """Import scripts/automation/<name>.py by path (the folder is not a package)."""
    if str(AUTOMATION) not in sys.path:
        sys.path.insert(0, str(AUTOMATION))
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, AUTOMATION / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CORE = textwrap.dedent("""\
    ---
    name: neuroflow-core
    description: core rules
    ---
    # neuroflow-core

    ## Rule markers

    Markers look like `<!-- nf-rule: ID -->` and sit on the line before the rule.

    | id | rule | where |
    |---|---|---|
    | PREREG-FROZEN | Frozen preregistration files are never edited | skills |
    | MEMORY-PURITY | Memory holds only the documented structure | commands |

    ## Phase taxonomy

    **Valid `phase:` frontmatter values:** `alpha`, `utility`
    """)

COMMAND = textwrap.dedent("""\
    ---
    name: alpha
    description: Alpha command
    phase: alpha
    reads:
      - .neuroflow/project_config.md
    writes:
      - .neuroflow/alpha/
    lifecycle: full
    requires:
      - .neuroflow/alpha/plan.md
    next:
      - alpha
    ---

    # /alpha

    <!-- nf-rule: MEMORY-PURITY -->
    Write only into the documented folders.
    """)

FILES = {
    ".claude-plugin/plugin.json": '{\n  "name": "neuroflow",\n  "version": "1.2.3",\n  "description": "x"\n}\n',
    ".claude-plugin/marketplace.json": (
        '{\n  "name": "neuroflow",\n  "plugins": [\n    {\n      "name": "neuroflow",\n      "source": "./",\n'
        '      "version": "1.2.3",\n      "keywords": ["a", "b"]\n    }\n  ]\n}\n'
    ),
    "hooks/hooks.json": json.dumps({"description": "hooks", "hooks": {"PostToolUse": [
        {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "echo hi; true"}]}]}}, indent=2) + "\n",
    "mkdocs.yml": textwrap.dedent("""\
        site_name: neuroflow
        plugins:
          - search:
              version: "9.9.9"
        extra:
          version: "1.2.3"
          social:
            - icon: github
        nav:
          - Home: index.md
          - Commands:
              - "Alpha": commands/alpha.md
          - Skills:
              - "neuroflow-core": skills/neuroflow-core/SKILL.md
              - "phase-alpha": skills/phase-alpha/SKILL.md
          - Agents:
              - "helper": agents/helper.md
        """),
    ".neuroflow/project_config.md": "# neuroflow - project config\n\n**Plugin version:** 1.2.3\n**Phase:** active development\n",
    "skills/neuroflow-core/SKILL.md": CORE,
    "skills/phase-alpha/SKILL.md": (
        "---\nname: phase-alpha\ndescription: Alpha phase guidance\n---\n\n<!-- nf-rule: PREREG-FROZEN -->\n"
        "Never edit a frozen preregistration file.\n"
    ),
    "commands/alpha.md": COMMAND,
    "agents/helper.md": "---\nname: helper\ndescription: A helper agent\n---\n\n# helper\n",
    "docs/index.md": '<span class="sa-bar-version">v1.2.3</span>\n',
    "docs/changelog.md": "# Changelog\n\n## 1.2.3\n\n- x\n",
    "docs/commands/alpha.md": "# /alpha\n",
    "docs/javascripts/mind.js": 'const NODES = [\n  { id: "c-alpha", commands: ["/alpha"], desc: "the helper agent", '
                                'url: "commands/alpha/" },\n]\n',
    "README.md": textwrap.dedent("""\
        # neuroflow

        ## What's new in 1.2.3

        - [old thing](agents/removed-long-ago.md)

        ## Why neuroflow

        | Command | What |
        |---|---|
        | [`/alpha`](commands/alpha.md) | alpha |

        | Skill | What |
        |---|---|
        | [`neuroflow-core`](skills/neuroflow-core/SKILL.md) | core |
        | [`phase-alpha`](skills/phase-alpha/SKILL.md) | alpha |

        | Agent | What |
        |---|---|
        | [`helper`](agents/helper.md) | helper |
        """),
}


def write(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)


def make_repo(root: Path) -> Path:
    write(root, FILES)
    return root
