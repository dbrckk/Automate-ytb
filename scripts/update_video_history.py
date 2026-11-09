"""Synchronize an auditable GitHub-tracked history of rendered MP4 Releases.

The canonical history is GitHub Releases (durable, append-only tags); this
generated index makes it searchable and easy to inspect from Android.
No local sandbox paths, no fabricated videos, no secrets in the catalog.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

CATALOG="docs/video-history.json"
SCHEMA=1


def catalog_from_releases(releases: list[dict]) -> dict:
    entries=[]
    seen=set()
    for release in releases:
        tag=release.get("tag_name")
        if not isinstance(tag,str) or tag in seen:
            continue
        videos=[a for a in release.get("assets",[])
                if isinstance(a.get("name"),str) and a["name"].endswith(".mp4")
                and a.get("state")=="uploaded"
                and isinstance(a.get("browser_download_url"),str)]
        if not videos:
            continue
        seen.add(tag)
        for asset in videos:
            name=asset["name"]
            topic=tag.split("-")
            if tag.startswith("science-preview-"):
                kind="science"
                subject=tag[len("science-preview-"):].rsplit("-",1)[0]
            elif tag.startswith("forest-25d-"):
                kind="animated-forest"
                subject="forest-discovery"
            else:
                kind="other"
                subject=name[:-4]
            entries.append({
                "id":f"{tag}/{name}",
                "topic":subject,
                "category":kind,
                "releaseTag":tag,
                "publishedAt":release.get("published_at"),
                "status":"technical-preview-unreviewed",
                "mp4":asset["browser_download_url"],
                "release":release.get("html_url"),
                "bytes":asset.get("size"),
                "sha256":asset.get("digest"),
            })
    entries.sort(key=lambda e:(e["publishedAt"] or "",e["id"]),reverse=True)
    return {
        "schemaVersion":SCHEMA,
        "source":"GitHub Releases, not temporary GitHub Actions artifacts",
        "publicationApproved":False,
        "count":len(entries),
        "videos":entries,
    }


def api(method: str, endpoint: str, token: str, repo: str,
        payload: dict | None = None) -> dict | list:
    body=None if payload is None else json.dumps(payload).encode("utf-8")
    request=urllib.request.Request(
        f"https://api.github.com/repos/{repo}/{endpoint}",data=body,
        method=method,headers={
            "Authorization":f"Bearer {token}",
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28",
            "User-Agent":"Automate-ytb-video-history",
            **({"Content-Type":"application/json"} if body is not None else {}),
        })
    with urllib.request.urlopen(request,timeout=45) as response:
        return json.load(response)


def sync(repo: str, token: str) -> dict:
    if not repo or not token:
        raise ValueError("Repository and GITHUB_TOKEN are required")
    releases=[]
    for page in range(1,21):
        batch=api("GET",f"releases?per_page=100&page={page}",token,repo)
        if not isinstance(batch,list):
            raise RuntimeError("GitHub Releases API returned unexpected response")
        releases.extend(batch)
        if len(batch)<100:
            break
    else:
        raise RuntimeError("Too many releases: refusing truncated history")
    catalog=catalog_from_releases(releases)
    if not catalog["videos"]:
        raise RuntimeError("Refusing to replace video history with empty list")
    data=(json.dumps(catalog,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    for attempt in range(5):
        try:
            existing=api("GET",f"contents/{CATALOG}?ref=main",token,repo)
            sha=existing["sha"]
            previous=base64.b64decode(existing["content"])
            if previous==data:
                return catalog
        except urllib.error.HTTPError as exc:
            if exc.code!=404:
                raise
            sha=None
        payload={"message":"docs(video): refresh verified GitHub Releases history",
                 "branch":"main","content":base64.b64encode(data).decode("ascii")}
        if sha:
            payload["sha"]=sha
        try:
            api("PUT",f"contents/{CATALOG}",token,repo,payload)
            return catalog
        except urllib.error.HTTPError as exc:
            if exc.code not in (409,422) or attempt==4:
                raise
            time.sleep(attempt+1)
    raise RuntimeError("Unable to persist history")


if __name__=="__main__":
    result=sync(os.environ["GITHUB_REPOSITORY"],os.environ["GH_TOKEN"])
    print(f"VIDEO_HISTORY_UPDATED={result['count']}")
