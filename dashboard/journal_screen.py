"""Journal screens: JournalScreen, RecordDetailScreen."""

from __future__ import annotations

import time
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Input, Markdown, OptionList, Static
from textual.widgets.option_list import Option

from orchestra.canon.project import Project
from dashboard import model
from dashboard import pager
from dashboard.display import REDRAW_SECONDS, clip, palette_from, relative_time
from dashboard.journal import (
    SEPARATOR_KEY, TYPE_LABEL, JournalItem, filter_items, journal_scope, list_markdown, load_journal,
    load_record, ordered, record_markdown,
)
from dashboard.task_detail import TaskDetailScreen


def type_cells(item: JournalItem, colors: dict[str, str]) -> Text:
    glyph, label = TYPE_LABEL.get(item.record_type, ("·", item.record_type.split(":")[-1]))
    text = Text(no_wrap=True, overflow="ellipsis")
    style = colors["warning"] if item.open else colors["muted"]
    text.append(f"{glyph} {label}", style=style)
    return text


class JournalFilterInput(Input):
    BINDINGS = [Binding("escape", "cancel", "clear", show=False)]

    def action_cancel(self) -> None:
        screen = self.screen
        if isinstance(screen, JournalScreen):
            screen.clear_filter()


class JournalTable(DataTable):
    BINDINGS = [
        Binding("enter", "select_cursor", "open", show=False),
        Binding("j", "cursor_down", "down", show=False),
        Binding("k", "cursor_up", "up", show=False),
    ]

    def __init__(self, id: str) -> None:
        super().__init__(id=id, cursor_type="row", zebra_stripes=False)
        self.items: list[JournalItem] = []
        self._keys: list[str] = []

    def fill(self, items: list[JournalItem], colors: dict[str, str], now: datetime) -> None:
        kept = None
        if self.row_count and self.cursor_row is not None and self.cursor_row < len(self._keys):
            kept = self._keys[self.cursor_row]
        open_items, rest = ordered(items)
        self.items = []
        self._keys = []
        self.clear(columns=True)
        self.add_column("type", key="type", width=14)
        self.add_column("subject", key="subject", width=16)
        self.add_column("age", key="age", width=8)
        self.add_column("text", key="text")
        for item in open_items:
            self._add_item(item, colors, now)
        if open_items and rest:
            sep = Text("─" * 12, style=colors["muted"])
            self.add_row(sep, Text(""), Text(""), Text("───", style=colors["muted"]), key=SEPARATOR_KEY)
            self._keys.append(SEPARATOR_KEY)
            self.items.append(JournalItem("", "", "", None, datetime.min.replace(tzinfo=timezone.utc), "", False))
        for item in rest:
            self._add_item(item, colors, now)
        if kept is not None and kept in self._keys and kept != SEPARATOR_KEY:
            self.move_cursor(row=self._keys.index(kept))
        elif self._keys:
            first = next((i for i, key in enumerate(self._keys) if key != SEPARATOR_KEY), 0)
            self.move_cursor(row=first)

    def _add_item(self, item: JournalItem, colors: dict[str, str], now: datetime) -> None:
        age = Text(relative_time(item.recorded_at, now), style=colors["muted"], no_wrap=True)
        subject = Text(clip(item.subject, 16), no_wrap=True, overflow="ellipsis")
        body = Text(item.text, no_wrap=True, overflow="ellipsis")
        self.add_row(type_cells(item, colors), subject, age, body, key=item.id)
        self._keys.append(item.id)
        self.items.append(item)

    def cursor_item(self) -> JournalItem | None:
        if self.cursor_row is None or self.cursor_row >= len(self._keys):
            return None
        key = self._keys[self.cursor_row]
        if key == SEPARATOR_KEY:
            return None
        return next((item for item in self.items if item.id == key), None)


class JournalScreen(Screen[None]):
    CSS = """
    #journal-bar { height: 1; padding: 0 1; background: $panel; }
    #journal-error { height: auto; padding: 0 1; background: $error 20%; color: $error; display: none; }
    #journal-filter { height: 1; margin: 1 1 0 1; padding: 0 1; border: none; background: $panel; }
    #journal-filter:focus { border: none; background: $panel; }
    #journal-table { height: 1fr; margin: 1 1; border: round $panel; border-title-color: $text-muted; }
    #journal-empty { height: 1fr; content-align: center middle; color: $text-muted; display: none; }
    """
    BINDINGS = [
        Binding("escape", "back", "back"),
        Binding("a", "toggle_scope", "scope", show=False),
        Binding("slash", "filter", "filter"),
        Binding("o", "page", "pager", show=False),
        Binding("r", "app.refresh", "refresh"),
        Binding("c", "app.copy_slug", "copy"),
    ]

    def __init__(self, target: Project, effort: str, phase: str | None) -> None:
        super().__init__()
        self.target = target
        self.effort = effort
        self.anchor_phase = phase
        self.phase = phase
        self.all_items: list[JournalItem] = []
        self.filter_text = ""
        self.loaded = False
        self.token: str | None = None
        self.loaded_at = 0.0

    def compose(self) -> ComposeResult:
        yield Static(id="journal-bar")
        yield Static(id="journal-error")
        filt = JournalFilterInput(placeholder="filter journal", id="journal-filter")
        filt.display = False
        yield filt
        table = JournalTable(id="journal-table")
        table.border_title = "Journal"
        yield table
        yield Static("No journal items", id="journal-empty")
        yield Footer()

    def on_mount(self) -> None:
        self.load()

    def action_back(self) -> None:
        self.app.pop_screen()
        self.app.call_after_refresh(self.app.focus_tasks)

    def action_toggle_scope(self) -> None:
        if self.anchor_phase is None:
            return
        self.phase = None if self.phase is not None else self.anchor_phase
        self.repaint()

    def action_filter(self) -> None:
        box = self.query_one("#journal-filter", Input)
        box.value = self.filter_text
        box.display = True
        box.focus()
        box.cursor_position = len(box.value)

    def clear_filter(self) -> None:
        self.filter_text = ""
        box = self.query_one("#journal-filter", Input)
        box.display = False
        box.value = ""
        self.repaint()
        self.query_one("#journal-table", JournalTable).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "journal-filter":
            return
        if event.input.display and event.value != self.filter_text:
            self.filter_text = event.value
            self.repaint()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "journal-filter":
            return
        event.input.display = False
        self.query_one("#journal-table", JournalTable).focus()

    def action_page(self) -> None:
        items = filter_items(journal_scope(self.all_items, self.phase), self.filter_text)
        scope = "effort" if self.phase is None else self.phase
        text = list_markdown(items, scope=scope)
        self._page(text)

    def _page(self, text: str) -> None:
        suspend = getattr(self.app, "suspend", None)
        context = suspend() if callable(suspend) else nullcontext()
        try:
            with context:
                pager.page_text(text)
        except Exception:
            pager.page_text(text)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = event.data_table
        if not isinstance(table, JournalTable):
            return
        event.stop()
        item = table.cursor_item()
        if item is None:
            return
        self.app.push_screen(RecordDetailScreen(self.target, item.id, task_id=item.task_id))

    @work(thread=True, exclusive=True, group="journal")
    def load(self) -> None:
        self.loaded_at = time.monotonic()
        try:
            self.token = model.change_token(self.target)
            items = load_journal(self.target, self.effort)
        except (OSError, model.ModelError) as exc:
            self.app.call_from_thread(self.show_error, str(exc))
            return
        self.app.call_from_thread(self.apply, items)

    def poll(self, token: str) -> None:
        if token != self.token or time.monotonic() - self.loaded_at > REDRAW_SECONDS:
            self.load()

    def show_error(self, message: str) -> None:
        if not self.is_attached:
            return
        banner = self.query_one("#journal-error", Static)
        banner.update(Text(message.splitlines()[0] if message else "error", no_wrap=True, overflow="ellipsis"))
        banner.display = True

    def apply(self, items: list[JournalItem]) -> None:
        if not self.is_attached:
            return
        self.all_items = items
        self.query_one("#journal-error", Static).display = False
        self.repaint()
        if not self.loaded:
            self.query_one("#journal-table", JournalTable).focus()
        self.loaded = True

    def repaint(self) -> None:
        colors = palette_from(self.app.get_css_variables())
        scope = "effort" if self.phase is None else self.phase
        bar = Text(no_wrap=True, overflow="ellipsis")
        bar.append("Journal", style="bold")
        bar.append(f"  {self.effort}", style=colors["muted"])
        bar.append(f"  · {scope}", style=colors["muted"])
        self.query_one("#journal-bar", Static).update(bar)
        items = filter_items(journal_scope(self.all_items, self.phase), self.filter_text)
        table = self.query_one("#journal-table", JournalTable)
        empty = self.query_one("#journal-empty", Static)
        table.display = bool(items)
        empty.display = not items
        if items:
            now = datetime.now(timezone.utc)
            table.fill(items, colors, now)
            table.border_title = f"Journal {len(items)}"


class RecordDetailScreen(Screen[None]):
    CSS = """
    #record-bar { height: 1; padding: 0 1; background: $panel; }
    #record-error { height: auto; padding: 0 1; background: $error 20%; color: $error; display: none; }
    #record-detail { padding: 0 1; scrollbar-gutter: stable; }
    #record-title { margin-top: 1; text-style: bold; }
    .record-panel { height: auto; margin-top: 1; border: round $panel; border-title-color: $text-muted; padding: 0 1; }
    .record-panel Markdown { margin: 0; padding: 0; background: transparent; }
    .record-panel Markdown > MarkdownBlock { margin: 1 0 0 0; }
    .record-panel Markdown > MarkdownHeader { margin: 0; }
    .record-panel Markdown > MarkdownBlock:first-child { margin-top: 0; }
    #record-links { height: auto; max-height: 8; margin-top: 1; border: round $panel; border-title-color: $text-muted; padding: 0 1; }
    """
    BINDINGS = [
        Binding("escape", "back", "back"),
        Binding("o", "page", "pager", show=False),
        Binding("r", "app.refresh", "refresh"),
        Binding("c", "app.copy_slug", "copy"),
        Binding("l", "focus_links", "links", show=False),
    ]

    def __init__(self, target: Project, record_id: str, task_id: str = "") -> None:
        super().__init__()
        self.target = target
        self.record_id = record_id
        self.task_id = task_id
        self.record: dict[str, Any] | None = None
        self.loaded = False
        self.token: str | None = None
        self.loaded_at = 0.0

    def compose(self) -> ComposeResult:
        yield Static(id="record-bar")
        yield Static(id="record-error")
        with VerticalScroll(id="record-detail"):
            yield Static("Loading…", id="record-loading")
            with Vertical(id="record-content"):
                yield Static(id="record-title")
                yield Static(id="record-chips")
                payload = Vertical(Markdown(), id="record-payload", classes="record-panel")
                payload.border_title = "Payload"
                yield payload
                body = Vertical(Markdown(), id="record-body", classes="record-panel")
                body.border_title = "Body"
                yield body
                links = OptionList(id="record-links")
                links.border_title = "Links"
                links.display = False
                yield links
        yield Footer()

    def on_mount(self) -> None:
        self.load()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_focus_links(self) -> None:
        links = self.query_one("#record-links", OptionList)
        if not links.display or not links.option_count:
            return
        if links.highlighted is None:
            links.highlighted = 0
        links.focus()

    def action_page(self) -> None:
        if self.record is None:
            return
        text = record_markdown(self.record)
        suspend = getattr(self.app, "suspend", None)
        context = suspend() if callable(suspend) else nullcontext()
        try:
            with context:
                pager.page_text(text)
        except Exception:
            pager.page_text(text)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "record-links":
            return
        event.stop()
        key = event.option.id or ""
        if key.startswith("task:"):
            self.app.push_screen(TaskDetailScreen(self.target, key[len("task:"):]))

    @work(thread=True, exclusive=True, group="record-detail")
    def load(self) -> None:
        self.loaded_at = time.monotonic()
        try:
            self.token = model.change_token(self.target)
            record = load_record(self.target, self.record_id)
        except (OSError, model.ModelError) as exc:
            self.app.call_from_thread(self.show_error, str(exc))
            return
        self.app.call_from_thread(self.apply, record)

    def poll(self, token: str) -> None:
        if token != self.token or time.monotonic() - self.loaded_at > REDRAW_SECONDS:
            self.load()

    def show_error(self, message: str) -> None:
        if not self.is_attached:
            return
        banner = self.query_one("#record-error", Static)
        banner.update(Text(message.splitlines()[0] if message else "error", no_wrap=True, overflow="ellipsis"))
        banner.display = True

    async def apply(self, record: dict[str, Any]) -> None:
        if not self.is_attached:
            return
        colors = palette_from(self.app.get_css_variables())
        self.record = record
        self.query_one("#record-error", Static).display = False
        self.query_one("#record-loading", Static).display = False
        self.query_one("#record-content").display = True
        bar = Text(no_wrap=True, overflow="ellipsis")
        bar.append(record.get("subject") or record["id"], style="bold")
        bar.append(f"  {record.get('record_type', '')}", style=colors["muted"])
        self.query_one("#record-bar", Static).update(bar)
        self.query_one("#record-title", Static).update(Text(record.get("subject") or "", style="bold"))
        chips = Text.assemble(
            (record.get("record_type") or "", colors["primary"]),
            "  ",
            (record.get("lifecycle_state") or "", colors["muted"]),
        )
        self.query_one("#record-chips", Static).update(chips)
        payload = model._payload(record)
        payload_md = "\n".join(f"- **{key}:** {value}" for key, value in payload.items()) if payload else ""
        payload_panel = self.query_one("#record-payload")
        payload_panel.display = bool(payload_md)
        await self.query_one("#record-payload Markdown", Markdown).update(payload_md)
        body = (record.get("body") or "").strip()
        body_panel = self.query_one("#record-body")
        body_panel.display = bool(body)
        await self.query_one("#record-body Markdown", Markdown).update(body)
        links = self.query_one("#record-links", OptionList)
        links.clear_options()
        if self.task_id:
            links.add_option(Option(Text(f"Task: {record.get('subject', self.task_id)}"), id=f"task:{self.task_id}"))
            links.display = True
            links.highlighted = 0
        else:
            links.display = False
        self.loaded = True
