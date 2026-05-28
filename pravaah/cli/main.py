"""Pravaah CLI — developer command-line interface.

Built with Typer for a clean, auto-documented CLI experience.

Commands:
    pravaah run           Start the development server
    pravaah info          Show framework info and registry summary
    pravaah list-plugins  List discovered plugins
    pravaah list-models   List registered models
    pravaah list-hooks    List registered event hooks
    pravaah init-plugin   Scaffold a new plugin
    pravaah routes        List all registered API routes

Architecture Notes:
    - Commands that need the framework's runtime state (list-plugins,
      list-models, list-hooks) perform a lightweight "headless" boot:
      they load config, discover plugins, and call setup() without
      starting the HTTP server.
    - The ``run`` command delegates to uvicorn programmatically.
    - Rich/Typer tables are used for human-readable output.
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(
    name="pravaah",
    help="Pravaah CLI -- Everything flows.",
    no_args_is_help=True,
    add_completion=False,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headless_boot():
    """Perform a lightweight boot without starting the HTTP server.

    Loads config, discovers plugins, calls setup(), and populates the
    registry — but does NOT start uvicorn or create the FastAPI app.

    Returns:
        (config, registry, loader) tuple.
    """
    from pravaah.app.core.config import get_config, reset_config
    from pravaah.app.core.registry import registry
    from pravaah.app.plugins.loader import PluginLoader

    reset_config()
    config = get_config()

    loader = PluginLoader()
    if config.plugins.auto_discover:
        loader.discover(config.plugins.plugin_dirs)

        # Headless setup: resolve order and call setup() without FastAPI app
        try:
            ordered = loader._resolve_load_order()
        except Exception:
            ordered = list(loader._discovered.values())

        for plugin in ordered:
            try:
                plugin._do_setup(None, registry)  # type: ignore[arg-type]
            except Exception:
                pass  # Ignore setup errors in headless mode

    return config, registry, loader


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def run(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind address"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
) -> None:
    """Start the Pravaah development server."""
    console.print(
        "\n[bold cyan]Pravaah[/bold cyan] [dim]-- Everything flows.[/dim]\n"
    )

    try:
        import uvicorn
    except ImportError:
        console.print("[red]Error:[/red] uvicorn is not installed.")
        raise typer.Exit(1)

    uvicorn.run(
        "pravaah.app.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
    )


@app.command()
def info() -> None:
    """Show framework information and registry summary."""
    from pravaah import __version__

    config, registry, loader = _headless_boot()

    console.print(
        "\n[bold cyan]Pravaah[/bold cyan] [dim]-- Everything flows.[/dim]\n"
    )

    # Framework info table
    info_table = Table(title="Framework Info", show_header=False, border_style="cyan")
    info_table.add_column("Key", style="bold")
    info_table.add_column("Value")
    info_table.add_row("Version", __version__)
    info_table.add_row("Debug", str(config.app.debug))
    info_table.add_row("Host", f"{config.app.host}:{config.app.port}")
    info_table.add_row("Database", config.database.provider)
    info_table.add_row("AI Provider", config.ai.provider if config.ai.enabled else "disabled")

    console.print(info_table)
    console.print()

    # Registry summary
    summary = registry.summary()
    reg_table = Table(title="Registry Summary", show_header=False, border_style="green")
    reg_table.add_column("Component", style="bold")
    reg_table.add_column("Count", justify="right")
    reg_table.add_row("Plugins", str(len(summary["plugins"])))
    reg_table.add_row("Models", str(len(summary["models"])))
    reg_table.add_row("Hooks", str(sum(summary["hooks"].values())))
    reg_table.add_row("Routers", str(summary["routers"]))
    reg_table.add_row("Services", str(len(summary["services"])))

    console.print(reg_table)
    console.print()


@app.command("list-plugins")
def list_plugins() -> None:
    """List all discovered plugins."""
    config, registry, loader = _headless_boot()

    table = Table(title="Plugins", border_style="cyan")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Name", style="bold cyan")
    table.add_column("Version")
    table.add_column("Description")
    table.add_column("Author")
    table.add_column("Status", style="green")

    plugins = list(loader._discovered.values())
    for idx, plugin in enumerate(plugins, 1):
        m = plugin.manifest
        table.add_row(
            str(idx),
            m.name,
            m.version,
            m.description or "-",
            m.author or "-",
            "loaded" if m.enabled else "disabled",
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]{len(plugins)} plugin(s) discovered[/dim]\n")


@app.command("list-models")
def list_models() -> None:
    """List all registered models."""
    config, registry, loader = _headless_boot()

    models = registry._models
    table = Table(title="Registered Models", border_style="green")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Model", style="bold green")
    table.add_column("Plugin", style="cyan")
    table.add_column("Create Schema")
    table.add_column("Update Schema")
    table.add_column("Read Schema")

    for idx, (name, reg) in enumerate(models.items(), 1):
        table.add_row(
            str(idx),
            name,
            reg.plugin or "core",
            reg.create_schema.__name__,
            reg.update_schema.__name__,
            reg.read_schema.__name__,
        )

    console.print()
    console.print(table)
    console.print(f"\n[dim]{len(models)} model(s) registered[/dim]\n")


@app.command("list-hooks")
def list_hooks() -> None:
    """List all registered event hooks."""
    config, registry, loader = _headless_boot()

    hooks = registry._hooks
    table = Table(title="Registered Hooks", border_style="yellow")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Event", style="bold yellow")
    table.add_column("Handler", style="cyan")
    table.add_column("Plugin")
    table.add_column("Priority", justify="right")

    idx = 0
    for event_name, registrations in sorted(hooks.items()):
        for reg in sorted(registrations, key=lambda r: r.priority):
            idx += 1
            table.add_row(
                str(idx),
                event_name,
                reg.handler.__qualname__,
                reg.plugin or "core",
                str(reg.priority),
            )

    console.print()
    console.print(table)
    console.print(f"\n[dim]{idx} hook(s) registered across {len(hooks)} event(s)[/dim]\n")


@app.command()
def routes() -> None:
    """List all registered API routes."""
    from pravaah.app.main import create_app
    from pravaah.app.core.config import reset_config

    reset_config()
    fastapi_app = create_app()

    table = Table(title="API Routes", border_style="magenta")
    table.add_column("Method", style="bold magenta")
    table.add_column("Path", style="cyan")
    table.add_column("Name")
    table.add_column("Tags")

    for route in fastapi_app.routes:
        if hasattr(route, "methods"):
            methods = ", ".join(sorted(route.methods))
            tags = ", ".join(getattr(route, "tags", []) or [])
            table.add_row(
                methods,
                route.path,
                getattr(route, "name", "-"),
                tags or "-",
            )

    console.print()
    console.print(table)
    console.print()


@app.command("init-plugin")
def init_plugin(
    name: str = typer.Argument(..., help="Plugin name (lowercase, underscores)"),
    directory: str = typer.Option(
        "pravaah/plugins", "--dir", "-d", help="Plugin directory"
    ),
) -> None:
    """Scaffold a new plugin with boilerplate files."""
    import re

    # Validate name
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        console.print(
            f"[red]Error:[/red] Plugin name must be lowercase with underscores. Got: '{name}'"
        )
        raise typer.Exit(1)

    plugin_dir = Path(directory) / name
    if plugin_dir.exists():
        console.print(f"[red]Error:[/red] Directory already exists: {plugin_dir}")
        raise typer.Exit(1)

    plugin_dir.mkdir(parents=True)

    # Pre-compute template values
    class_name = name.title().replace("_", "") + "Plugin"
    description = name.replace("_", " ").title() + " plugin"

    # __init__.py
    init_content = (
        f'"""Pravaah plugin: {name}."""\n'
        f"from __future__ import annotations\n"
        f"\n"
        f"from pravaah.app.plugins.base import PravaahPlugin\n"
        f"from pravaah.app.plugins.manifest import PluginManifest\n"
        f"\n"
        f"\n"
        f"class {class_name}(PravaahPlugin):\n"
        f'    """The {name} plugin."""\n'
        f"\n"
        f"    manifest = PluginManifest(\n"
        f'        name="{name}",\n'
        f'        version="0.1.0",\n'
        f'        description="{description}",\n'
        f'        author="",\n'
        f"    )\n"
        f"\n"
        f"    def setup(self, app, registry):\n"
        f'        """Register models, routes, and hooks."""\n'
        f"        pass\n"
    )
    (plugin_dir / "__init__.py").write_text(init_content, encoding="utf-8")

    # hooks.py
    hooks_content = (
        f'"""Event hooks for the {name} plugin."""\n'
        f"from __future__ import annotations\n"
        f"\n"
        f"# from pravaah.app.events.decorators import after_create, before_create\n"
        f"# Example:\n"
        f"#\n"
        f'# @after_create("MyModel")\n'
        f"# async def on_created(ctx):\n"
        f'#     print(f"Created: {{ctx.data}}")\n'
    )
    (plugin_dir / "hooks.py").write_text(hooks_content, encoding="utf-8")

    console.print(f"\n[green]Plugin scaffolded:[/green] {plugin_dir}")
    console.print(f"  [dim]Created:[/dim] {plugin_dir / '__init__.py'}")
    console.print(f"  [dim]Created:[/dim] {plugin_dir / 'hooks.py'}")
    console.print(
        f"\n[dim]Next: implement your plugin in {plugin_dir / '__init__.py'}[/dim]\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
