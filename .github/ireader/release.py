#!/usr/bin/env python3
"""Detect published upstream stable releases and write safe Actions outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
TAG = re.compile(r"v[0-9][A-Za-z0-9._+-]{0,100}\Z")


def api(route):
    request = Request(
        "https://api.github.com/" + route,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ["GH_TOKEN"],
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def plan(config, requested_tag="", get=api):
    if not isinstance(config["patch_revision"], int) or not 1 <= config["patch_revision"] <= 9999:
        raise ValueError("patch_revision must be an integer between 1 and 9999")
    if requested_tag and not TAG.fullmatch(requested_tag):
        raise ValueError("Invalid upstream tag")
    endpoint = "tags/" + quote(requested_tag, safe="") if requested_tag else "latest"
    upstream = get(f"repos/{config['upstream']}/releases/{endpoint}")
    if not upstream:
        raise ValueError("No upstream published release found")
    tag = upstream["tag_name"]
    if not TAG.fullmatch(tag):
        raise ValueError("Unsupported upstream tag")
    if upstream.get("draft") or upstream.get("prerelease") or not upstream.get("published_at"):
        raise ValueError("Only published stable upstream releases are accepted")
    release_tag = f"ireader-{tag}-p{config['patch_revision']}"
    existing = get(f"repos/{config['fork']}/releases/tags/{release_tag}")
    return {
        "needed": "false" if existing and not existing.get("draft") else "true",
        "upstream_tag": tag,
        "release_tag": release_tag,
        "patch_revision": str(config["patch_revision"]),
        "upstream_url": upstream["html_url"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((ROOT / "config.json").read_text())
    result = plan(config, args.tag)
    result["patch_sha256"] = hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted((ROOT / "patches").glob("*.patch")))
    ).hexdigest()
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            for key, value in result.items():
                if "\n" in value or "\r" in value:
                    raise ValueError("Unsafe output")
                output.write(f"{key}={value}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
