from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

_PR_PATH = re.compile(r"/([\w.-]+)/([\w.-]+)/pull/([1-9][0-9]*)/?")


def pull_request_coordinates(value: str) -> tuple[str, str, str, str]:
    url = urlsplit(value)
    match = _PR_PATH.fullmatch(url.path)
    host = url.hostname
    if url.scheme != "https" or not host or url.netloc != host or match is None:
        raise ValueError("CI evidence requires a GitHub pull request URL")
    owner, repo, number = match.groups()
    return host, owner, repo, number


def branch_rules_endpoint(repository: str, branch: str) -> str:
    return f"{repository}/rules/branches/{quote(branch, safe='')}"
