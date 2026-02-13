"""Run Screaming Frog SEO Spider in headless mode and export crawl data."""

import subprocess
import sys
from pathlib import Path

SF_BINARY = (
    "/Applications/Screaming Frog SEO Spider.app"
    "/Contents/MacOS/ScreamingFrogSEOSpiderLauncher"
)

EXPORTS = {
    "reports": "Issues Overview,Accessibility:Accessibility Violations Summary",
    "bulk": "Accessibility:All Violations,Issues:All",
    "tabs": "Internal:All",
}


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
) -> Path:
    """Run a headless SF crawl and export issues + accessibility data.

    Returns the output directory containing exported CSVs.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [sf_binary, "--crawl", url]
    cmd += _build_export_flags(output_dir)

    if config:
        cmd.extend(["--config", str(config)])

    _run_sf(cmd, f"Starting crawl of {url} → {output_dir}")
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
