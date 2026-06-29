#!/usr/bin/env python3
import html
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
REPOS = [
    "Pro42good/AlloyOS",
    "Pro42good/pro42good.me",
    "polardev-ui/disband-latest",
    "rooootdev/lara",
]
SKIP_DIRS = {
    ".git",
    ".github",
    ".idea",
    "_site",
    "scripts",
}
SKIP_FILES = {
    ".DS_Store",
}
START = "<!-- PROJECT_STATUS_START -->"
END = "<!-- PROJECT_STATUS_END -->"
CHANGELOG_START = "<!-- PROJECT_CHANGELOG_START -->"
CHANGELOG_END = "<!-- PROJECT_CHANGELOG_END -->"


def copy_static_site():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for item in ROOT.iterdir():
        if item.name in SKIP_DIRS or item.name in SKIP_FILES:
            continue
        target = OUT / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)

    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def fetch_repo(repo):
    url = f"https://api.github.com/repos/{repo}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pro42good-me-pages-build",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def short_date(value):
    if not value:
        return "unknown"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value[:10]
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d")


def fallback_rows():
    return [
        {"name": "AlloyOS", "language": "Shell", "pushed_at": "fallback", "stars": "0"},
        {"name": "pro42good.me", "language": "CSS", "pushed_at": "fallback", "stars": "0"},
        {"name": "disband-latest", "language": "TypeScript", "pushed_at": "fallback", "stars": "0"},
        {"name": "lara", "language": "Swift", "pushed_at": "fallback", "stars": "1278"},
    ]


def collect_metadata():
    rows = []
    for repo in REPOS:
        data = fetch_repo(repo)
        rows.append(
            {
                "name": data.get("name") or repo,
                "language": data.get("language") or "n/a",
                "pushed_at": short_date(data.get("pushed_at")),
                "stars": str(data.get("stargazers_count", 0)),
            }
        )
    return rows


def render_status(rows, generated_note):
    body_rows = []
    for row in rows:
        body_rows.append(
            "              <tr>\n"
            f"                <th scope=\"row\">{html.escape(row['name'])}</th>\n"
            f"                <td>{html.escape(row['language'])}</td>\n"
            f"                <td>{html.escape(row['pushed_at'])}</td>\n"
            f"                <td>{html.escape(row['stars'])}</td>\n"
            "              </tr>"
        )

    return (
        f"{START}\n"
        "          <table class=\"mini-table\">\n"
        "            <thead>\n"
        "              <tr>\n"
        "                <th scope=\"col\">Repo</th>\n"
        "                <th scope=\"col\">Lang</th>\n"
        "                <th scope=\"col\">Pushed</th>\n"
        "                <th scope=\"col\">Stars</th>\n"
        "              </tr>\n"
        "            </thead>\n"
        "            <tbody>\n"
        + "\n".join(body_rows)
        + "\n"
        "            </tbody>\n"
        "          </table>\n"
        f"          <p class=\"fine-print\">{html.escape(generated_note)}</p>\n"
        f"          {END}"
    )


def render_changelog(rows, generated_note):
    body_rows = []
    for row in rows:
        body_rows.append(
            "          <tr>\n"
            f"            <th scope=\"row\">{html.escape(row['name'])}</th>\n"
            f"            <td>{html.escape(row['pushed_at'])}</td>\n"
            f"            <td>{html.escape(row['language'])}</td>\n"
            "          </tr>"
        )

    return (
        f"{CHANGELOG_START}\n"
        "      <table class=\"mini-table\">\n"
        "        <thead>\n"
        "          <tr>\n"
        "            <th scope=\"col\">Repo</th>\n"
        "            <th scope=\"col\">Last push</th>\n"
        "            <th scope=\"col\">Language</th>\n"
        "          </tr>\n"
        "        </thead>\n"
        "        <tbody>\n"
        + "\n".join(body_rows)
        + "\n"
        "        </tbody>\n"
        "      </table>\n"
        f"      <p class=\"fine-print\">{html.escape(generated_note)}</p>\n"
        f"      {CHANGELOG_END}"
    )


def replace_between(content, start, end, replacement):
    before, marker, rest = content.partition(start)
    if not marker:
        return content
    _old, marker, after = rest.partition(end)
    if not marker:
        raise RuntimeError(f"Missing end marker for {start}")
    return before + replacement + after


def inject_generated_blocks(rows, generated_note):
    status_block = render_status(rows, generated_note)
    changelog_block = render_changelog(rows, generated_note)
    for html_path in OUT.glob("*.html"):
        content = html_path.read_text(encoding="utf-8")
        content = replace_between(content, START, END, status_block)
        content = replace_between(content, CHANGELOG_START, CHANGELOG_END, changelog_block)
        html_path.write_text(content, encoding="utf-8")


def main():
    copy_static_site()
    try:
        rows = collect_metadata()
        generated_note = "Generated from public GitHub metadata during Pages deploy."
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        rows = fallback_rows()
        generated_note = f"GitHub metadata fetch failed; using fallback status. Reason: {exc}"
        print(generated_note, file=sys.stderr)
    inject_generated_blocks(rows, generated_note)
    print(f"Built {OUT}")


if __name__ == "__main__":
    main()
