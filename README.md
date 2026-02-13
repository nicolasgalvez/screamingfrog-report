# sfreport

CLI tool that automates Screaming Frog SEO Spider crawl exports into a single Excel workbook with per-page issue and accessibility breakdowns.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pre-commit install
```

## Usage

### Fresh crawl

Run Screaming Frog headlessly against a URL and generate a report:

```bash
uv run sfreport crawl https://example.com -o report.xlsx
```

Uses `config/Accessibility.seospiderconfig` by default. Override with `--config`:

```bash
uv run sfreport crawl https://example.com -c config/MyConfig.seospiderconfig
```

### From existing CSV exports

If you've already exported CSVs from Screaming Frog (via GUI or CLI), point at the folder:

```bash
uv run sfreport report ./my-exports/ -o report.xlsx
```

### From a saved crawl database

Re-export from a `.dbseospider` file (requires Screaming Frog installed):

```bash
uv run sfreport from-db db-exports/my-crawl.dbseospider -o report.xlsx
```

Add `--keep-exports` to retain the intermediate CSV files.

## Output

The generated `.xlsx` workbook contains:

| Sheet | Contents |
|---|---|
| **Issues Summary** | All issue types with priority, URL counts, descriptions, and fix guidance |
| **Accessibility Summary** | WCAG violation types with impact, % of pages affected, sample URLs |
| **Pages** | Master index of all HTML pages with accessibility/issue counts and hyperlinks to each page's sheet |
| **Per-page sheets** | Combined accessibility violations and SEO issues for each page, with a `Type` column distinguishing them |

Pages with identical issue sets are deduplicated into a single sheet listing all affected URLs. HTTP/HTTPS duplicates are normalized automatically.

## Project structure

```
sfreport/
  cli.py        # Typer CLI with crawl, report, from-db commands
  crawl.py      # Screaming Frog CLI automation (headless mode)
  report.py     # CSV parsing + Excel workbook generation
config/         # .seospiderconfig files for crawl settings
db-exports/     # Saved .dbseospider crawl databases (gitignored)
```

## SF CLI requirements

Screaming Frog SEO Spider must be installed at the default macOS location:

```
/Applications/Screaming Frog SEO Spider.app
```

Override with `--sf-binary` if installed elsewhere. The `crawl` and `from-db` commands require a valid Screaming Frog license for headless mode.

## TODO

- [ ] Use `.env` for configuration (SF binary path, default config, output directory)
- [ ] Add interactive CLI interface with Typer prompts (URL input, config selection, output options)
- [ ] Dockerize with Screaming Frog installed in the container for fully self-contained headless crawls
- [ ] Better management of export files (timestamped output dirs, automatic cleanup of old exports, list/diff past crawls)
