"""CLI entry point for sfreport."""

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import typer
from dotenv import load_dotenv

from sfreport.config import get_sf_binary
from sfreport.crawl import (
    INLINK_STATUS_CODES,
    export_from_crawl_file,
    export_inlinks,
    run_crawl,
)
from sfreport.report import generate_report

load_dotenv()

app = typer.Typer(help="Screaming Frog crawl → Excel report generator.")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DB_EXPORTS_DIR = PROJECT_ROOT / "db-exports"
EXPORTS_DIR = PROJECT_ROOT / "exports"


def _exports_dir_for_url(url: str) -> Path:
    """Create an exports subdirectory named after the domain."""
    domain = urlparse(url).hostname or "unknown"
    return EXPORTS_DIR / domain


def _exports_dir_for_crawl_file(crawl_file: Path) -> Path:
    """Create an exports subdirectory named after the crawl file."""
    return EXPORTS_DIR / crawl_file.stem


@app.command()
def crawl(
    url: str = typer.Argument(help="URL to crawl"),
    output: Path = typer.Option(
        "report.xlsx", "--output", "-o", help="Output Excel file path"
    ),
    config: Path = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to .seospiderconfig file (defaults to config/Accessibility.seospiderconfig)",
    ),
    sf_binary: str = typer.Option(
        None,
        "--sf-binary",
        help="Path to Screaming Frog binary (default: from config or platform default)",
    ),
    keep_exports: bool = typer.Option(
        False,
        "--keep-exports",
        help="Keep intermediate CSV exports (saved to exports/<domain>/)",
    ),
    user: str | None = typer.Option(
        None,
        "--user",
        "-u",
        help="Basic auth username (overrides BASIC_AUTH_USERNAME in .env)",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="Basic auth password (overrides BASIC_AUTH_PASSWORD in .env)",
    ),
) -> None:
    """Run a fresh Screaming Frog crawl and generate an Excel report."""
    # Resolve auth: CLI flags override .env values
    auth_user = user or os.getenv("BASIC_AUTH_USERNAME")
    auth_pass = password or os.getenv("BASIC_AUTH_PASSWORD")

    if auth_user and auth_pass:
        typer.echo(f"Using basic auth as {auth_user}")
    elif auth_user or auth_pass:
        typer.echo(
            "Warning: both --user and --password are required for basic auth", err=True
        )

    # Default to the bundled accessibility config
    if config is None:
        default_config = CONFIG_DIR / "Accessibility.seospiderconfig"
        if default_config.exists():
            config = default_config
            typer.echo(f"Using config: {config}")

    with tempfile.TemporaryDirectory(prefix="sfreport_") as tmp:
        export_dir = Path(tmp)
        if keep_exports:
            export_dir = _exports_dir_for_url(url)
            export_dir.mkdir(parents=True, exist_ok=True)

        run_crawl(
            url,
            export_dir,
            config=config,
            sf_binary=sf_binary or get_sf_binary(),
            username=auth_user,
            password=auth_pass,
        )
        generate_report(export_dir, output)


@app.command()
def report(
    export_dir: Path = typer.Argument(
        help="Directory containing Screaming Frog CSV exports",
    ),
    output: Path = typer.Option(
        "report.xlsx", "--output", "-o", help="Output Excel file path"
    ),
) -> None:
    """Generate an Excel report from existing CSV exports."""
    if not export_dir.is_dir():
        typer.echo(f"Error: {export_dir} is not a directory", err=True)
        raise typer.Exit(1)

    generate_report(export_dir, output)


@app.command(name="sf")
def sf(
    args: list[str] = typer.Argument(
        None, help="Arguments to pass to Screaming Frog CLI"
    ),
    sf_binary: str = typer.Option(
        None,
        "--sf-binary",
        help="Path to Screaming Frog binary (default: from config or platform default)",
    ),
) -> None:
    """Run the Screaming Frog SEO Spider CLI directly."""
    import subprocess

    cmd = [sf_binary or get_sf_binary()] + (args or [])
    typer.echo(f"Running: {' '.join(cmd)}")
    raise typer.Exit(subprocess.run(cmd).returncode)


@app.command()
def inlinks(
    crawl_file: Path = typer.Argument(
        help="Path to a .seospider or .dbseospider crawl file",
    ),
    status: str = typer.Option(
        "all",
        "--status",
        "-s",
        help=f"Filter by status code: {', '.join(INLINK_STATUS_CODES)}",
    ),
    internal: bool = typer.Option(
        False,
        "--internal",
        help="Only internal inlinks",
    ),
    external: bool = typer.Option(
        False,
        "--external",
        help="Only external inlinks",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for CSVs (default: exports/<crawl-name>/)",
    ),
    sf_binary: str = typer.Option(
        None,
        "--sf-binary",
        help="Path to Screaming Frog binary (default: from config or platform default)",
    ),
) -> None:
    """Export inlinks from a saved crawl, optionally filtered by response status."""
    if internal and external:
        typer.echo("Error: --internal and --external are mutually exclusive", err=True)
        raise typer.Exit(1)

    if status not in INLINK_STATUS_CODES:
        typer.echo(
            f"Error: unknown status {status!r}. Choose from: {', '.join(INLINK_STATUS_CODES)}",
            err=True,
        )
        raise typer.Exit(1)

    if not crawl_file.exists():
        typer.echo(f"Error: {crawl_file} not found", err=True)
        raise typer.Exit(1)

    scope = "internal" if internal else "external" if external else "both"

    if output_dir is None:
        output_dir = _exports_dir_for_crawl_file(crawl_file)
    output_dir.mkdir(parents=True, exist_ok=True)

    export_inlinks(
        crawl_file,
        output_dir,
        status=status,
        scope=scope,
        sf_binary=sf_binary or get_sf_binary(),
    )
    typer.echo(f"Inlinks exported to {output_dir}")


@app.command(name="from-db")
def from_db(
    crawl_file: Path = typer.Argument(
        help="Path to a .seospider or .dbseospider crawl file",
    ),
    output: Path = typer.Option(
        "report.xlsx", "--output", "-o", help="Output Excel file path"
    ),
    sf_binary: str = typer.Option(
        None,
        "--sf-binary",
        help="Path to Screaming Frog binary (default: from config or platform default)",
    ),
    keep_exports: bool = typer.Option(
        False,
        "--keep-exports",
        help="Keep intermediate CSV exports (saved to exports/<crawl-name>/)",
    ),
) -> None:
    """Re-export from a saved crawl database and generate an Excel report."""
    if not crawl_file.exists():
        typer.echo(f"Error: {crawl_file} not found", err=True)
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory(prefix="sfreport_") as tmp:
        export_dir = Path(tmp)
        if keep_exports:
            export_dir = _exports_dir_for_crawl_file(crawl_file)
            export_dir.mkdir(parents=True, exist_ok=True)

        export_from_crawl_file(
            crawl_file, export_dir, sf_binary=sf_binary or get_sf_binary()
        )
        generate_report(export_dir, output)
