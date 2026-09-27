#!/usr/bin/env python3
"""Dispatch each product repo CI workflow (manual hub trigger only)."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse


API = "https://api.github.com"
WORKFLOW = "ci.yml"


def fail(message: str) -> None:
    print(f"::error::{message}")
    raise SystemExit(1)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def repo_slug(url: str) -> str:
    text = url.strip()
    if text.endswith(".git"):
        text = text[:-4]
    if text.startswith("git@"):
        text = text.split(":", 1)[1]
    parsed = urlparse(text)
    path = parsed.path.lstrip("/") if parsed.scheme else text
    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        fail(f"Could not parse GitHub repo from submodule URL: {url}")
    return f"{parts[-2]}/{parts[-1]}"


def submodule_repos(repo_root: Path) -> list[tuple[str, str]]:
    modules = repo_root / ".gitmodules"
    if not modules.is_file():
        fail(".gitmodules not found")
    names = git("config", "--file", str(modules), "--get-regexp", r"^submodule\..*\.path$")
    mapping: list[tuple[str, str]] = []
    for line in names.splitlines():
        if not line.strip():
            continue
        key, path = line.split(None, 1)
        name = key.split(".")[1]
        url = git("config", "--file", str(modules), "--get", f"submodule.{name}.url")
        mapping.append((path, repo_slug(url)))
    return sorted(mapping)


def token() -> str:
    value = (
        os.environ.get("HUB_DISPATCH_TOKEN", "").strip()
        or os.environ.get("GH_PAT", "").strip()
    )
    if not value:
        fail(
            "HUB_DISPATCH_TOKEN is empty. Add a GitHub token that can dispatch "
            "workflows on nuvyntralabs/NuvyntraLabs.NET.* repos (Settings → Secrets → Actions)."
        )
    return value


def http(method: str, url: str, api_token: str, data: bytes | None = None) -> tuple[int, object]:
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {api_token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "NETEssentials-dispatch-submodule-workflows",
        },
    )
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, context=context, timeout=30) as response:
            raw = response.read()
            body: object = {}
            if raw:
                body = json.loads(raw.decode("utf-8"))
            return response.getcode() or 200, body
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"message": raw}
        return exc.code, body


def dispatch(repo: str, ref: str, api_token: str) -> None:
    url = f"{API}/repos/{repo}/actions/workflows/{WORKFLOW}/dispatches"
    payload = json.dumps({"ref": ref}).encode("utf-8")
    status, body = http("POST", url, api_token, data=payload)
    if status == 204:
        print(f"Triggered {repo} CI on {ref}")
        return
    message = body.get("message") if isinstance(body, dict) else body
    fail(f"Could not dispatch {repo} CI (HTTP {status}): {message}")


def list_runs(repo: str, api_token: str) -> list[dict]:
    url = (
        f"{API}/repos/{repo}/actions/workflows/{WORKFLOW}/runs"
        f"?event=workflow_dispatch&per_page=10"
    )
    status, body = http("GET", url, api_token)
    if status != 200 or not isinstance(body, dict):
        fail(f"Could not list workflow runs for {repo} (HTTP {status})")
    return list(body.get("workflow_runs") or [])


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_run(repo: str, api_token: str, started: datetime) -> dict:
    for _ in range(12):
        for run in list_runs(repo, api_token):
            created = parse_iso(str(run.get("created_at") or "1970-01-01T00:00:00Z"))
            if created + timedelta(seconds=5) >= started:
                return run
        time.sleep(5)
    fail(f"Dispatched {repo} CI but no new workflow_dispatch run appeared")


def wait_for_run(repo: str, run_id: int, api_token: str, timeout_sec: int) -> dict:
    url = f"{API}/repos/{repo}/actions/runs/{run_id}"
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        status, body = http("GET", url, api_token)
        if status != 200 or not isinstance(body, dict):
            fail(f"Could not read {repo} run {run_id} (HTTP {status})")
        if body.get("status") == "completed":
            return body
        time.sleep(20)
    fail(f"{repo} run {run_id} did not finish within {timeout_sec}s")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--only", default="")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--wait", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--timeout-sec", type=int, default=5400)
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    os.chdir(root)
    api_token = token()
    selected = submodule_repos(root)
    only = args.only.strip()
    if only:
        selected = [item for item in selected if item[0] == only]
        if not selected:
            known = ", ".join(path for path, _ in submodule_repos(root))
            fail(f"Unknown product '{only}'. Expected one of: {known}")

    print(f"Dispatching {len(selected)} submodule pipeline(s) on {args.ref}")
    started = datetime.now(timezone.utc)
    dispatched: list[tuple[str, str, dict]] = []
    for folder, repo in selected:
        print(f"::group::{folder} → {repo}")
        dispatch(repo, args.ref, api_token)
        run = find_run(repo, api_token, started)
        print(f"{repo} run {run.get('html_url')}")
        print("::endgroup::")
        dispatched.append((folder, repo, run))

    if not args.wait:
        print("Submodule pipelines were triggered. Not waiting for results.")
        return 0

    failed: list[str] = []
    for folder, repo, run in dispatched:
        run_id = int(run["id"])
        print(f"::group::Wait {folder} ({repo})")
        finished = wait_for_run(repo, run_id, api_token, args.timeout_sec)
        conclusion = str(finished.get("conclusion") or "unknown")
        url = finished.get("html_url")
        print(f"{repo}: {conclusion} {url}")
        print("::endgroup::")
        if conclusion != "success":
            failed.append(f"{folder} ({repo}): {conclusion} {url}")

    if failed:
        fail("Submodule pipeline(s) failed:\n" + "\n".join(failed))
    print("All triggered submodule pipelines succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
