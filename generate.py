#!/usr/bin/env python3
import copy, json, shutil, subprocess, sys
from pathlib import Path

SOURCE = Path(__file__).parent.parent / "mc-dp-icons"
for i, arg in enumerate(sys.argv[1:], 1):
    if arg == "--source" and i < len(sys.argv):
        SOURCE = Path(sys.argv[i + 1])

OUT = Path(__file__).parent
THEME_TS = SOURCE / "src/data/baseTheme.ts"
THEME_JSON = OUT / "icon_themes/mc-dp-icons.json"


def extract_json(lines, start_idx):
    text = ""
    bc, brc = 0, 0
    started = False
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not started:
            eq = line.find("=")
            if eq == -1:
                continue
            js = next((p for p in range(eq, len(line)) if line[p] in "{["), -1)
            if js == -1:
                continue
            text = line[js:]
            started = True
        else:
            text += "\n" + line.rstrip()
        for ch in line:
            if ch == "{": bc += 1
            elif ch == "}": bc -= 1
            elif ch == "[": brc += 1
            elif ch == "]": brc -= 1
        if started and bc == 0 and brc == 0:
            break
    return json.loads(text)


def parse_theme(fp):
    with open(fp) as f:
        lines = f.readlines()
    return (
        extract_json(lines, next(i for i, l in enumerate(lines) if "export const baseTheme:" in l)),
        extract_json(lines, next(i for i, l in enumerate(lines) if "export const xmasIcons:" in l)),
    )


def path_zed(vsc_path):
    return vsc_path.replace("../", "./")


def build_theme(schema, name):
    closed = schema["iconDefinitions"].get(schema["folder"], {}).get("iconPath", "")
    opened = schema["iconDefinitions"].get(schema["folderExpanded"], {}).get("iconPath", "")

    default_closed = path_zed(closed) if closed else ""

    ndi = {}
    for fn, ik in schema["folderNamesExpanded"].items():
        icon = schema["iconDefinitions"].get(ik)
        if icon is None:
            continue
        ndi[fn] = {"collapsed": default_closed, "expanded": path_zed(icon["iconPath"])}
    for fn, ik in schema["folderNames"].items():
        icon = schema["iconDefinitions"].get(ik)
        if icon is None:
            continue
        if fn not in ndi:
            ndi[fn] = {"collapsed": path_zed(icon["iconPath"]), "expanded": ""}
        else:
            ndi[fn]["collapsed"] = path_zed(icon["iconPath"])

    fi = {}
    for ik, iv in schema["iconDefinitions"].items():
        if "_file" not in ik:
            continue
        fi[ik] = {"path": path_zed(iv["iconPath"])}
    default = schema["iconDefinitions"].get(schema["file"], {})
    if default:
        fi["default"] = {"path": path_zed(default["iconPath"])}

    return {
        "name": name,
        "appearance": "dark",
        "directory_icons": {
            "collapsed": path_zed(closed) if closed else "",
            "expanded": path_zed(opened) if opened else "",
        },
        "named_directory_icons": ndi,
        "file_stems": {k: v for k, v in schema["fileNames"].items() if "/" not in k},
        "file_suffixes": {k: v for k, v in schema["fileExtensions"].items() if "/" not in k},
        "file_icons": fi,
    }


def main():
    print(f"Reading icons from {SOURCE}")
    subprocess.run(["npm", "run", "generate"], cwd=SOURCE, check=True)
    base, xmas_list = parse_theme(THEME_TS)

    themes = [build_theme(base, "Datapack Icons")]
    if xmas_list:
        xmas = copy.deepcopy(base)
        for key in xmas_list:
            if key in xmas["iconDefinitions"]:
                old = xmas["iconDefinitions"][key]["iconPath"]
                xmas["iconDefinitions"][key]["iconPath"] = old.replace(".svg", "_xmas.svg")
        themes.append(build_theme(xmas, "Datapack Icons (Christmas)"))

    family = {
        "$schema": "https://zed.dev/schema/icon_themes/v0.3.0.json",
        "name": "Datapack Icons",
        "author": "funcfusion",
        "themes": themes,
    }

    (OUT / "icon_themes").mkdir(parents=True, exist_ok=True)
    THEME_JSON.write_text(json.dumps(family, indent=2))
    print(f"Wrote {THEME_JSON}")

    if (SOURCE / "icons").is_dir():
        shutil.rmtree(OUT / "icons", ignore_errors=True)
        shutil.copytree(SOURCE / "icons", OUT / "icons")
        print(f"Copied icons/")

    license_src = SOURCE / "LICENSE"
    if license_src.is_file():
        shutil.copy2(license_src, OUT / "LICENSE")
        print(f"Copied LICENSE")

    print(f"Generated — run 'git diff' to review changes before committing.")
                    


if __name__ == "__main__":
    main()
