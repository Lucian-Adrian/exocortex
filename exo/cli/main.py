"""
Main CLI application for Exo.

Uses Click for command-line argument parsing.
"""

import json
import sys
from typing import Any

import click

from exo import __version__


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.version_option(version=__version__, prog_name="exo")
@click.pass_context
def app(ctx: click.Context, verbose: bool) -> None:
    """Exo - Executive OS for personal knowledge management.

    Store, search, and query your conversations, notes, and documents.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@app.command()
@click.argument("file", type=click.File("r"), default="-")
@click.option("--source-type", "-t", default="markdown", help="Source type (audio, telegram, markdown)")
@click.pass_context
def ingest(ctx: click.Context, file: Any, source_type: str) -> None:
    """Ingest content from a file or stdin.

    FILE can be a path to a file or '-' for stdin.

    Examples:

        exo ingest document.md

        echo '{"text": "Meeting notes"}' | exo ingest -

        exo ingest -t audio transcript.json
    """
    from exo.cli.ingest import run_ingest

    verbose = ctx.obj.get("verbose", False)
    content = file.read()

    try:
        result = run_ingest(content, source_type, verbose)
        click.echo(json.dumps(result, indent=2, default=str))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@app.command()
@click.argument("question")
@click.option("--top-k", "-k", default=5, help="Number of results to retrieve")
@click.option("--threshold", "-t", default=0.7, help="Similarity threshold")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def query(
    ctx: click.Context,
    question: str,
    top_k: int,
    threshold: float,
    output_json: bool,
) -> None:
    """Query your memory with a question.

    Examples:

        exo query "What did I promise John?"

        exo query "Meeting summary from last week" --top-k 10

        exo query "Project deadlines" --json
    """
    from exo.cli.query import run_query

    verbose = ctx.obj.get("verbose", False)

    try:
        result = run_query(question, top_k, threshold, verbose)

        if output_json:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            # Pretty print the answer
            click.echo("\n" + "=" * 60)
            click.echo("ANSWER:")
            click.echo("=" * 60)
            click.echo(result.get("answer", "No answer generated."))

            if result.get("sources"):
                click.echo("\n" + "-" * 60)
                click.echo("SOURCES:")
                for i, src in enumerate(result["sources"], 1):
                    click.echo(f"  [{i}] {src.get('text', '')[:100]}...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main() -> int:
    """CLI entry point."""
    try:
        app()
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
