"""CLI básica del engine de lablog."""

from __future__ import annotations

import argparse
import sys
from uuid import uuid4

from lablog.config import settings
from lablog.event_store import EventStore
from lablog.events import page_created, text_inserted
from lablog.latex_ast import serialize_ast
from lablog.projector import project


def get_store() -> EventStore:
    return EventStore(settings.event_dir)


def cmd_create_page(args: argparse.Namespace) -> None:
    store = get_store()
    page_id = str(uuid4())
    event = page_created(page_id=page_id, title=args.title)
    store.append(event)
    print(f"Página creada: {page_id}")


def cmd_list_pages(_args: argparse.Namespace) -> None:
    store = get_store()
    pages = store.list_pages()
    if not pages:
        print("No hay páginas.")
        return
    for page_id in pages:
        print(page_id)


def cmd_append_text(args: argparse.Namespace) -> None:
    store = get_store()
    event = text_inserted(page_id=args.page_id, position=args.position, text=args.text)
    store.append(event)
    print("Texto añadido.")


def cmd_render(args: argparse.Namespace) -> None:
    store = get_store()
    events = store.get_events(args.page_id)
    if not events:
        print(f"No se encontraron eventos para la página {args.page_id}", file=sys.stderr)
        sys.exit(1)

    projection = project(args.page_id, events)
    latex = serialize_ast(projection.ast)
    print(latex)


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lablog", description="Engine CLI de lablog")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-page", help="Crea una nueva página")
    create_parser.add_argument("--title", "-t", default="Sin título", help="Título de la página")
    create_parser.set_defaults(func=cmd_create_page)

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

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
