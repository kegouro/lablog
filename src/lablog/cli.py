"""CLI básica del engine de lablog."""

from __future__ import annotations

import argparse
import sys
from uuid import uuid4

from lablog import commands
from lablog.config import settings
from lablog.event_store import EventStore
from lablog.events import page_created
from lablog.templates import get_template, list_templates


def get_store() -> EventStore:
    return EventStore(settings.event_dir)


def cmd_create_page(args: argparse.Namespace) -> None:
    store = get_store()
    page_id = str(uuid4())
    event = page_created(page_id=page_id, title=args.title)
    store.append(event)
    print(f"Página creada: {page_id}")


def cmd_new(args: argparse.Namespace) -> None:
    """Crea una página opcionalmente desde plantilla."""
    store = get_store()
    title = args.title
    template_id = args.template
    if template_id:
        tmpl = get_template(template_id)
        if tmpl is None:
            ids = ", ".join(t.id for t in list_templates())
            print(f"Plantilla desconocida: {template_id}. Disponibles: {ids}", file=sys.stderr)
            sys.exit(1)
        title = title or tmpl.name
        page_id = commands.create_page(store, title=title)
        commands.replace_document(store, page_id, tmpl.content)
        print(f"Página creada: {page_id} (template={template_id})")
        return
    page_id = commands.create_page(store, title=title or "Sin título")
    print(f"Página creada: {page_id}")


def cmd_list_pages(_args: argparse.Namespace) -> None:
    from lablog.projections import list_page_summaries

    store = get_store()
    summaries = list_page_summaries(store)
    if not summaries:
        print("No hay páginas.")
        return
    for s in summaries:
        print(f"{s['page_id']}\t{s['title']}")


def cmd_append_text(args: argparse.Namespace) -> None:
    from lablog.projections import PageNotFoundError, assert_active

    store = get_store()
    try:
        assert_active(store, args.page_id)
    except (PageNotFoundError, ValueError) as exc:
        print(f"Página no disponible: {args.page_id} ({exc})", file=sys.stderr)
        sys.exit(1)
    commands.insert_text(
        store, page_id=args.page_id, position=args.position, text=args.text
    )
    print("Texto añadido.")


def cmd_render(args: argparse.Namespace) -> None:
    from lablog.projections import PageNotFoundError, page_detail

    store = get_store()
    try:
        detail = page_detail(store, args.page_id)
    except PageNotFoundError:
        print(f"No se encontraron eventos para la página {args.page_id}", file=sys.stderr)
        sys.exit(1)
    print(detail["latex"])


def cmd_events(args: argparse.Namespace) -> None:
    store = get_store()
    events = store.get_events(args.page_id)
    for event in events:
        print(f"{event.timestamp.isoformat()} | {event.type:30} | {event.payload}")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run("lablog.api:app", host=args.host, port=args.port, reload=args.reload)


def cmd_app(_args: argparse.Namespace) -> None:
    from lablog.desktop import run

    run()


def cmd_diagrams(args: argparse.Namespace) -> None:
    """Lista o expande presets de diagramas."""
    from lablog import diagrams

    if args.expand:
        preset = diagrams.get_preset(args.expand)
        if preset is None:
            print(f"Preset desconocido: {args.expand}", file=sys.stderr)
            sys.exit(1)
        out = diagrams.expand_preset(preset)
        print(out["latex"])
        return
    if args.sim:
        preset = diagrams.get_preset(args.sim)
        if preset is None:
            print(f"Preset desconocido: {args.sim}", file=sys.stderr)
            sys.exit(1)
        try:
            out = diagrams.expand_simulation(preset)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
        print(out["source"])
        return
    for p in diagrams.list_presets():
        sim = "sim" if p.sim_template else "viz"
        print(f"{p.preset_id:24} {p.kind:14} {sim:4}  {p.title}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lablog", description="Engine CLI de lablog")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-page", help="Crea una nueva página")
    create_parser.add_argument("--title", "-t", default="Sin título", help="Título de la página")
    create_parser.set_defaults(func=cmd_create_page)

    new_parser = subparsers.add_parser("new", help="Crea página (opcionalmente con plantilla)")
    new_parser.add_argument("--title", "-t", default=None, help="Título de la página")
    new_parser.add_argument(
        "--template",
        default=None,
        help="ID de plantilla (lab-report-physics, em-notes, experiment-diary, …)",
    )
    new_parser.set_defaults(func=cmd_new)

    list_parser = subparsers.add_parser("list-pages", help="Lista páginas existentes")
    list_parser.set_defaults(func=cmd_list_pages)

    append_parser = subparsers.add_parser("append-text", help="Añade texto a una página")
    append_parser.add_argument("page_id", help="ID de la página")
    append_parser.add_argument("text", help="Texto a insertar")
    append_parser.add_argument(
        "--position", "-p", type=int, default=-1, help="Posición de inserción"
    )
    append_parser.set_defaults(func=cmd_append_text)

    render_parser = subparsers.add_parser("render", help="Renderiza una página a LaTeX")
    render_parser.add_argument("page_id", help="ID de la página")
    render_parser.set_defaults(func=cmd_render)

    events_parser = subparsers.add_parser("events", help="Muestra eventos de una página")
    events_parser.add_argument("page_id", help="ID de la página")
    events_parser.set_defaults(func=cmd_events)

    serve_parser = subparsers.add_parser("serve", help="Inicia el servidor API")
    serve_parser.add_argument(
        "--host", default=settings.host, help="Host (por defecto LABLOG_HOST o 127.0.0.1)"
    )
    serve_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=settings.port,
        help="Puerto (por defecto LABLOG_PORT o 8000)",
    )
    serve_parser.add_argument("--reload", action="store_true", help="Recarga automática")
    serve_parser.set_defaults(func=cmd_serve)

    app_parser = subparsers.add_parser(
        "app", help="Abre lablog como app de escritorio nativa (offline)"
    )
    app_parser.set_defaults(func=cmd_app)

    diagrams_parser = subparsers.add_parser(
        "diagrams", help="Lista o expande presets de diagramas (Circuitikz/TikZ)"
    )
    diagrams_parser.add_argument(
        "--expand",
        metavar="PRESET_ID",
        default=None,
        help="Imprime el LaTeX expandido del preset",
    )
    diagrams_parser.add_argument(
        "--sim",
        metavar="PRESET_ID",
        default=None,
        help="Imprime el source Python de simulación",
    )
    diagrams_parser.set_defaults(func=cmd_diagrams)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
