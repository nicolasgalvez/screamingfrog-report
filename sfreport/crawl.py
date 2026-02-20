"""Run Screaming Frog SEO Spider in headless mode and export crawl data."""

import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

SF_BINARY = (
    "/Applications/Screaming Frog SEO Spider.app"
    "/Contents/MacOS/ScreamingFrogSEOSpiderLauncher"
)

EXPORTS = {
    "reports": "Issues Overview,Accessibility:Accessibility Violations Summary",
    "bulk": "Accessibility:All Violations,Issues:All",
    "tabs": "Internal:All",
}

# SF bulk-export strings for inlinks, keyed by (status, scope)
INLINK_STATUS_CODES = ("all", "2xx", "3xx", "4xx", "5xx")
INLINK_SCOPES = ("both", "internal", "external")

_STATUS_LABELS = {
    "2xx": "Success (2xx)",
    "3xx": "Redirection (3xx)",
    "4xx": "Client Error (4xx)",
    "5xx": "Server Error (5xx)",
}

_SCOPE_PREFIXES = {
    "both": "Internal & External",
    "internal": "Internal",
    "external": "External",
}


def _inlink_bulk_export(status: str, scope: str) -> str:
    """Build the SF --bulk-export string for a status/scope combo."""
    if status == "all":
        return "Links:All Inlinks"
    label = _STATUS_LABELS[status]
    prefix = _SCOPE_PREFIXES[scope]
    if scope == "both":
        return f"Response Codes:{prefix}:{label} Inlinks"
    # Internal/external variants prefix the label too
    return f"Response Codes:{prefix}:{prefix} {label} Inlinks"


def _inlink_tab_export(status: str, scope: str) -> str | None:
    """Build the SF --export-tabs string, or None for 'all'."""
    if status == "all":
        return None
    label = _STATUS_LABELS[status]
    if scope == "both":
        return f"Response Codes:{label}"
    prefix = _SCOPE_PREFIXES[scope]
    return f"Response Codes:{prefix} {label}"


def _embed_credentials(url: str, username: str, password: str) -> str:
    """Embed basic auth credentials into a URL."""
    parsed = urlparse(url)
    netloc = f"{quote(username, safe='')}:{quote(password, safe='')}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _build_export_flags(output_dir: Path) -> list[str]:
    """Common export flags shared between crawl and re-export."""
    return [
        "--headless",
        "--output-folder",
        str(output_dir),
        "--overwrite",
        "--save-report",
        EXPORTS["reports"],
        "--bulk-export",
        EXPORTS["bulk"],
        "--export-tabs",
        EXPORTS["tabs"],
    ]


def _run_sf(cmd: list[str], label: str) -> None:
    """Execute SF CLI and handle errors."""
    print(f"{label}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"SF stderr:\n{result.stderr}", file=sys.stderr)
        raise RuntimeError(f"Screaming Frog exited with code {result.returncode}")

    print("Screaming Frog finished.\n")


def run_crawl(
    url: str,
    output_dir: Path,
    config: Path | None = None,
    sf_binary: str = SF_BINARY,
    username: str | None = None,
    password: str | None = None,
) -> Path:
    """Run a headless SF crawl and export issues + accessibility data.

    Returns the output directory containing exported CSVs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    crawl_url = url
    if username and password:
        crawl_url = _embed_credentials(url, username, password)

    cmd = [sf_binary, "--crawl", crawl_url]
    cmd += _build_export_flags(output_dir)

    if config:
        cmd.extend(["--config", str(config)])

    _run_sf(cmd, f"Starting crawl of {url} → {output_dir}")
    return output_dir


def export_inlinks(
    crawl_file: Path,
    output_dir: Path,
    status: str = "all",
    scope: str = "both",
    sf_binary: str = SF_BINARY,
) -> Path:
    """Export inlinks from a saved crawl, optionally filtered by status and scope.

    Returns the output directory containing exported CSVs.
    """
    if status not in INLINK_STATUS_CODES:
        raise ValueError(
            f"Unknown status {status!r}, expected: {', '.join(INLINK_STATUS_CODES)}"
        )
    if scope not in INLINK_SCOPES:
        raise ValueError(
            f"Unknown scope {scope!r}, expected: {', '.join(INLINK_SCOPES)}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    bulk = _inlink_bulk_export(status, scope)
    tabs = _inlink_tab_export(status, scope)

    cmd = [
        sf_binary,
        "--headless",
        "--load-crawl",
        str(crawl_file),
        "--output-folder",
        str(output_dir),
        "--overwrite",
        "--bulk-export",
        bulk,
    ]
    if tabs:
        cmd.extend(["--export-tabs", tabs])

    label = f"{scope} {status}" if status != "all" else "all"
    _run_sf(cmd, f"Exporting {label} inlinks from {crawl_file.name} → {output_dir}")
    return output_dir


def export_from_crawl_file(
    crawl_file: Path,
    output_dir: Path,
    sf_binary: str = SF_BINARY,
) -> Path:
    """Load a saved .seospider/.dbseospider crawl and re-export data.

    Returns the output directory containing exported CSVs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sf_binary, "--load-crawl", str(crawl_file)]
    cmd += _build_export_flags(output_dir)

    _run_sf(cmd, f"Exporting from {crawl_file.name} → {output_dir}")
    return output_dir
