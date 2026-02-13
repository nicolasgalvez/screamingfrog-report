"""CLI entry point for sfreport."""

import tempfile
from pathlib import Path

import typer

from sfreport.crawl import SF_BINARY, export_from_crawl_file, run_crawl
from sfreport.report import generate_report

app = typer.Typer(help="Screaming Frog crawl → Excel report generator.")

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
DB_EXPORTS_DIR = Path(__file__).resolve().parent.parent / "db-exports"


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
        SF_BINARY,
        "--sf-binary",
        help="Path to Screaming Frog binary",
    ),
    keep_exports: bool = typer.Option(
        False,
        "--keep-exports",
        help="Keep intermediate CSV exports",
    ),
) -> None:
    """Run a fresh Screaming Frog crawl and generate an Excel report."""
    # Default to the bundled accessibility config
    if config is None:
        default_config = CONFIG_DIR / "Accessibility.seospiderconfig"
        if default_config.exists():
            config = default_config
            typer.echo(f"Using config: {config}")

    with tempfile.TemporaryDirectory(prefix="sfreport_") as tmp:
        export_dir = Path(tmp)
        if keep_exports:
            export_dir = output.parent / f"{output.stem}_exports"
            export_dir.mkdir(parents=True, exist_ok=True)

        run_crawl(url, export_dir, config=config, sf_binary=sf_binary)
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


@app.command(name="from-db")
def from_db(
    crawl_file: Path = typer.Argument(
        help="Path to a .seospider or .dbseospider crawl file",
    ),
    output: Path = typer.Option(
        "report.xlsx", "--output", "-o", help="Output Excel file path"
    ),
    sf_binary: str = typer.Option(
        SF_BINARY,
        "--sf-binary",
        help="Path to Screaming Frog binary",
    ),
    keep_exports: bool = typer.Option(
        False,
        "--keep-exports",
        help="Keep intermediate CSV exports",
    ),
) -> None:
    """Re-export from a saved crawl database and generate an Excel report."""
    if not crawl_file.exists():
        typer.echo(f"Error: {crawl_file} not found", err=True)
        raise typer.Exit(1)

    with tempfile.TemporaryDirectory(prefix="sfreport_") as tmp:
        export_dir = Path(tmp)
        if keep_exports:
            export_dir = output.parent / f"{output.stem}_exports"
            export_dir.mkdir(parents=True, exist_ok=True)

        export_from_crawl_file(crawl_file, export_dir, sf_binary=sf_binary)
        generate_report(export_dir, output)
