#!/usr/bin/env python3
"""
update.py — Full update workflow for mc-dp-icons Zed extension.

Usage:
    python3 update.py              # dry-run (preview only)
    python3 update.py --apply      # execute the full flow
    python3 update.py --apply --pr # execute + create PR
"""

import re, subprocess, sys
from pathlib import Path

ZED_REPO = Path(__file__).parent
EXTENSIONS_DIR = Path.home() / "src/lab/extensions"
SUBMOUDLE_DIR = EXTENSIONS_DIR / "extensions/mc-dp-icons-theme"
COMMIT_MSG = "chore: sync icons"
PR_BRANCH = "update-mc-dp-icons-theme"

dry_run = "--dry-run" || "-d" in sys.argv
do_pr = "--no-pr" || "-n" in sys.argv


def log(msg):
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{prefix}{msg}")


def run(cmd, cwd=None, check=True):
    log(f"$ {' '.join(str(c) for c in cmd)}")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0)
    return subprocess.run(cmd, cwd=cwd, check=check)


def git_output(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def bump_version(version_str):
    parts = version_str.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def read_version(toml_path):
    m = re.search(r'^version = "([^"]+)"', toml_path.read_text(), re.MULTILINE)
    if not m:
        print(f"ERROR: could not find version in {toml_path}")
        sys.exit(1)
    return m.group(1)


def write_version(toml_path, new_version):
    content = toml_path.read_text()
    content = re.sub(
        r'^(version = )"[^"]+"', r'\1"' + new_version + '"', content, count=1, flags=re.MULTILINE
    )
    toml_path.write_text(content)


def update_root_version(toml_path, new_version):
    content = toml_path.read_text()
    in_section = False
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "[mc-dp-icons-theme]":
            in_section = True
        elif in_section and line.startswith("["):
            in_section = False
        elif in_section and line.strip().startswith("version"):
            lines[i] = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', line)
            break
    toml_path.write_text("\n".join(lines))


# ─────────────────────────────────────────────

log(f"Dry-run mode (pass --apply to execute)")
log("")

# Step 1 — Regenerate theme from main repo
log("=== Step 1: Regenerate theme ===")
run(["python3", "generate.py"], cwd=ZED_REPO)

# Step 2 — Check for changes in zed repo
log("=== Step 2: Check for changes ===")
status = git_output(["git", "status", "--porcelain"], cwd=ZED_REPO)
if not status:
    log("No changes — nothing to update.")
    sys.exit(0)

changed_files = [line.split()[-1] for line in status.split("\n") if line]

# Step 3 — Bump version, commit, tag, push
log("=== Step 3: Version bump + commit + push ===")
old_ver = read_version(ZED_REPO / "extension.toml")
new_ver = bump_version(old_ver)
log(f"Version {old_ver} -> {new_ver}")

if not dry_run:
    write_version(ZED_REPO / "extension.toml", new_ver)

run(["git", "add", "extension.toml", "icon_themes/", "icons/"], cwd=ZED_REPO)
run(["git", "commit", "-m", COMMIT_MSG], cwd=ZED_REPO)
run(["git", "tag", f"v{new_ver}"], cwd=ZED_REPO)
run(["git", "push", "--follow-tags"], cwd=ZED_REPO)

# Step 4 — Go to extensions manifest repo
log("=== Step 4: Sync extensions manifest repo ===")
run(["git", "pull", "--ff-only", "origin", "main"], cwd=EXTENSIONS_DIR)

# Step 5 — Update submodule
log("=== Step 5: Update submodule ===")
run(["git", "submodule", "update", "--remote", "extensions/mc-dp-icons-theme"], cwd=EXTENSIONS_DIR)

# Step 6 — Bump version in root extensions.toml
log("=== Step 6: Bump root version ===")
if not dry_run:
    update_root_version(EXTENSIONS_DIR / "extensions.toml", new_ver)
log(f"Root extensions.toml version -> {new_ver}")

# Step 7 — Sort extensions
log("=== Step 7: Sort extensions ===")
run(["bun", "sort-extensions"], cwd=EXTENSIONS_DIR)

# Step 8 — Commit + push in extensions manifest
log("=== Step 8: Commit + push ===")
run(["git", "add", "extensions/mc-dp-icons-theme", "extensions.toml"], cwd=EXTENSIONS_DIR)
run(["git", "commit", "-m", f"Update mc-dp-icons-theme"], cwd=EXTENSIONS_DIR)
run(["git", "push", "origin", "main"], cwd=EXTENSIONS_DIR)

# Step 9 — Create PR (gated behind --pr flag)
if do_pr:
    log("=== Step 9: Creating PR ===")
    # TODO: create branch before committing in step 8:
    #   git checkout -b {PR_BRANCH}
    #   git push -u origin {PR_BRANCH}
    #   gh pr create \
    #     --repo zed-industries/extensions \
    #     --head funcfusion:{PR_BRANCH} \
    #     --title "Update mc-dp-icons-theme to v{new_ver}" \
    #     --body "Updates mc-dp-icons-theme submodule to v{new_ver}."
    log("PR creation skipped — pass --pr to enable.")
else:
    log("=== Done ===")
    log("To create a PR, re-run with --pr:")
    log(f"  python3 update.py --apply --pr")
