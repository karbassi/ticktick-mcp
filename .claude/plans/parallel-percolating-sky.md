# TickTick MCP Server — Implementation Plan

## Context

We're building `ticktick-mcp`, an MCP server that exposes the full TickTick task management API to LLM agents. The reference implementation is the Rust CLI at `../ticktick-cli/` — we're reimplementing its API layer in Python with direct HTTP calls via httpx, using FastMCP v3.

With ~46 tools across 9 domains, Claude Code will automatically enable Tool Search (defer_loading) when tool definitions exceed ~10% of context. No server-side config needed — just clear tool names and descriptions.

### Decisions

| Area | Choice |
|------|--------|
| Scope | Everything the CLI does (~46 tools, 4 resources) |
| Auth | Env vars: `TICKTICK_ACCESS_TOKEN`, `TICKTICK_CLIENT_ID`, `TICKTICK_CLIENT_SECRET`, `TICKTICK_V2_SESSION_TOKEN` |
| Architecture | Direct HTTP (full parity: token refresh, v2 headers, fuzzy matching, timezone handling) |
| Transport | stdio now, HTTP later (GitHub issue) |
| Stack | Python 3.12+, uv, FastMCP v3, httpx, Pydantic, python-Levenshtein |
| Structure | Domain modules (`tools/`, `resources/`) |
| API layer | Mirror CLI: v1 for tasks/projects, v2 for everything else |
| Testing | FastMCP in-process client + respx mocked HTTP |
| CI/CD | GitHub Actions → lint (ruff) + typecheck (pyright) + test + PyPI publish |

---

## Phase 0: Project Scaffolding

**Goal:** Runnable empty MCP server with CI.

### Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package config, deps, scripts |
| `src/ticktick_mcp/__init__.py` | `__version__` |
| `src/ticktick_mcp/server.py` | FastMCP instance + `main()` entry point |
| `tests/conftest.py` | Shared fixtures |
| `.github/workflows/ci.yml` | ruff + pyright + pytest |
| `.github/workflows/publish.yml` | PyPI on `v*` tags |
| `.gitignore` | Python + .temp/ + .env |

### Key Config

```toml
[project]
name = "ticktick-mcp"
requires-python = ">=3.12"
dependencies = ["fastmcp>=3.0", "httpx>=0.27", "pydantic>=2.0", "python-Levenshtein>=0.25"]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "respx>=0.22", "ruff>=0.9", "pyright>=1.1"]

[project.scripts]
ticktick-mcp = "ticktick_mcp.server:main"
```

### Verify
- `uv run ticktick-mcp` starts stdio MCP
- `uv run ruff check src/` and `uv run pyright src/` pass

---

## Phase 1: HTTP Client Layer

**Goal:** Async httpx wrapper with v1 auto-refresh, v2 session auth, device ID generation.

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/auth.py` | `ticktick-cli/src/api/auth.rs`, `mod.rs` |
| `src/ticktick_mcp/client.py` | `ticktick-cli/src/api/mod.rs`, `v2.rs` |
| `tests/test_auth.py` | |
| `tests/test_client.py` | |

### client.py — `TickTickClient`

```python
class TickTickClient:
    V1_BASE = "https://api.ticktick.com/open/v1"
    V2_BASE = "https://api.ticktick.com/api/v2"
    V3_BASE = "https://api.ticktick.com/api/v3"
    MS_BASE = "https://ms.ticktick.com"

    # v1 methods — Bearer auth, auto-refresh on 401
    async def v1_get(self, endpoint: str) -> Any
    async def v1_post(self, endpoint: str, json: Any = None) -> Any
    async def v1_post_empty(self, endpoint: str) -> Response
    async def v1_delete(self, endpoint: str) -> Response

    # v2 methods — Cookie auth, x-device header
    async def v2_get(self, endpoint: str) -> Any
    async def v2_post(self, endpoint: str, json: Any) -> Any
    async def v2_put(self, endpoint: str, json: Any) -> Any
    async def v2_delete(self, endpoint: str) -> Response

    # v3 + focus
    async def batch_check(self) -> dict  # GET /batch/check/0
    async def focus_op(self, ops: list[dict]) -> Any  # POST ms.ticktick.com
```

### Key implementation details

**Token refresh** (from `auth.rs:126-147`, `mod.rs:20-37`): On 401, POST `https://ticktick.com/oauth/token` with `grant_type=refresh_token`, `Authorization: Basic base64(client_id:client_secret)`. Update stored access_token, retry original request.

**Device ID** (from `config.rs:239-259`): `"6490" + 20 hex chars` via LCG (multiplier=`6364136223846793005`, increment=`1442695040888963407`, seed=`time.time_ns()`).

**x-device header** (from `v2.rs:9-13`): `{"platform":"web","os":"macOS 10.15.7","device":"Chrome 130.0.0.0","name":"","version":6490,"id":"{device_id}","channel":"website","campaign":"","websocket":""}`

**v2 headers**: `User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...`, `Cookie: t={session_token}`

### Lifespan in server.py

```python
@asynccontextmanager
async def lifespan(server):
    client = TickTickClient(
        access_token=os.environ["TICKTICK_ACCESS_TOKEN"],
        client_id=os.environ.get("TICKTICK_CLIENT_ID"),
        client_secret=os.environ.get("TICKTICK_CLIENT_SECRET"),
        session_token=os.environ.get("TICKTICK_V2_SESSION_TOKEN"),
    )
    async with client:
        yield {"client": client}
```

Tools access client via `ctx.request_context.lifespan_context["client"]`.

### Verify
- respx mocks for all 4 API bases
- Test 401 → refresh → retry flow
- Test device ID format (24 chars, starts with "6490", hex suffix)

---

## Phase 2: Models and Utilities

**Goal:** Pydantic models, date/time parsing, fuzzy matching.

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/models.py` | All `api/*.rs` struct defs |
| `src/ticktick_mcp/dates.py` | `api/task.rs:105-530` |
| `src/ticktick_mcp/resolve.py` | `api/project.rs:114-180` |
| `tests/test_dates.py` | |
| `tests/test_resolve.py` | |

### models.py

All models: `ConfigDict(populate_by_name=True, alias_generator=to_camel)` for camelCase JSON.

- **Task** — id, title, project_id, content, desc, priority (0/1/3/5), status (0/2), due_date, start_date, tags[], is_all_day, time_zone, parent_id, items[], reminders[]
- **Project** — id, name, color, sort_order, closed, group_id, view_mode, kind
- **Tag** — name (PK), raw_name, label, color, parent, sort_order, sort_type
- **Habit** — id, name, color, status (0/1), type (Boolean/Real), goal, unit, repeat_rule, section_id
- **HabitCheckin** — id, habit_id, checkin_stamp (YYYYMMDD int), value, goal, status
- **HabitSection** — id, name, sort_order
- **Filter** — id, name, rule (JSON string), sort_type, sort_order
- **ProjectGroup** — id, name, sort_order, show_all, sort_type, view_mode

### dates.py

Use `zoneinfo.ZoneInfo` (stdlib) instead of CLI's libc `setenv`/`tzset` hack.

- `parse_datetime(input)` — "today", "tomorrow", "YYYY-MM-DD", "YYYY-MM-DDTHH:MM"
- `parse_duration(input)` — "1h", "30m", "1h30m" → `timedelta`
- `to_api_string(dt, tz_name)` — `"2026-02-16T14:30:00.000-0600"` with correct offset
- `date_to_stamp(input)` — "YYYY-MM-DD" / "today" → `20260216` int
- `date_to_epoch_ms(input)` — for focus log queries

### resolve.py

Generic resolver reused by projects, folders, filters, habits, habit sections:

```python
def resolve_name(query, items, get_name, get_id, entity_type="item") -> str:
    # 1. hex ID check (>=20 hex chars) → return as-is
    # 2. exact match (case-insensitive)
    # 3. contains match (single match only)
    # 4. Levenshtein (threshold ≤ 3) → "Did you mean 'X'?"
    # 5. multiple matches → "Ambiguous: A, B, C"
```

### Verify
- Model round-trips: `Task(**json_data).model_dump(by_alias=True)` preserves camelCase
- `parse_datetime("today")`, `"2026-02-16"`, `"2026-02-16T14:30"`
- `parse_duration("1h30m")` → `timedelta(hours=1, minutes=30)`
- `resolve_name("shop", [...])` → exact, contains, fuzzy, ambiguous cases

---

## Phase 3: Tasks + Projects (Core Tools)

**Goal:** The 15 most-used tools.

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/tools/__init__.py` | Registers all tool modules |
| `src/ticktick_mcp/tools/tasks.py` | `api/task.rs` |
| `src/ticktick_mcp/tools/projects.py` | `api/project.rs` |
| `tests/test_tools/test_tasks.py` | |
| `tests/test_tools/test_projects.py` | |

### Task Tools (10)

| Tool | Annotations | API |
|------|-------------|-----|
| `list_tasks` | readOnly | v1 GET `/project/{id}/data`, v2 GET `/project/{id}/completed`, v2 GET `/project/all/completedInAll/` |
| `get_task` | readOnly | v1 GET `/project/{pid}/task/{tid}` |
| `add_task` | openWorld | v1 POST `/task` |
| `edit_task` | openWorld | v1 POST `/task/{tid}` |
| `complete_task` | openWorld, idempotent | v1 POST `/project/{pid}/task/{tid}/complete` (empty body) |
| `delete_task` | destructive, openWorld | v1 DELETE `/project/{pid}/task/{tid}` |
| `move_task` | openWorld | v2 POST `/batch/taskProject` |
| `set_subtask` | openWorld | v2 POST `/batch/taskParent` |
| `unparent_task` | openWorld | v1 POST `/task/{tid}` (clear parentId) |
| `list_trash` | readOnly | v2 GET `/project/all/trash/page` |

`add_task` parameters: title, project (fuzzy), due, start, duration, priority (none/low/medium/high), tags[], content, desc, items[] (checklist), all_day, timezone.

### Project Tools (5)

| Tool | Annotations | API |
|------|-------------|-----|
| `list_projects` | readOnly | v1 GET `/project` |
| `get_project` | readOnly | v1 GET `/project/{id}` (fuzzy resolved) |
| `add_project` | openWorld | v1 POST `/project` |
| `edit_project` | openWorld | v1 POST `/project/{id}` |
| `delete_project` | destructive, openWorld | v1 DELETE `/project/{id}` |

### Inbox Discovery

From `project.rs:85-109`: create temp task (no projectId) → read returned projectId → delete temp → cache in server state.

### Verify
- `add_task` with date/duration/priority builds correct v1 POST body
- `list_tasks` with project name resolves via fuzzy match then calls correct endpoint
- Inbox probe creates + deletes temp task

---

## Phase 4: Resources

**Goal:** Read-only MCP resources.

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/resources/__init__.py` | |
| `src/ticktick_mcp/resources/profile.py` | `api/v2.rs` |
| `src/ticktick_mcp/resources/settings.py` | `api/v2.rs` |
| `src/ticktick_mcp/resources/lists.py` | |
| `tests/test_resources/` | |

### Resources (4)

| URI | API |
|-----|-----|
| `ticktick://profile` | v2 GET `/user/profile` + `/user/status` (merged) |
| `ticktick://settings` | v2 GET `/user/preferences/settings?includeWeb=true` |
| `ticktick://projects` | v1 GET `/project` |
| `ticktick://tags` | v2 GET `/tags` |

### Verify
- Each resource returns valid JSON
- Profile merges profile + status

---

## Phase 5: Tags + Folders

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/tools/tags.py` | `api/tag.rs` |
| `src/ticktick_mcp/tools/folders.py` | `api/project_group.rs` |
| `tests/test_tools/test_tags.py` | |
| `tests/test_tools/test_folders.py` | |

### Tag Tools (6)

| Tool | Annotations | API |
|------|-------------|-----|
| `list_tags` | readOnly | v2 GET `/tags` |
| `add_tags` | openWorld | v2 POST `/batch/tag` `{add: [...]}` |
| `delete_tags` | destructive | v2 DELETE `/tag?name={encoded}` (per tag) |
| `rename_tag` | openWorld | v2 PUT `/tag/rename` |
| `edit_tag` | openWorld | v2 POST `/batch/tag` `{update: [...]}` |
| `merge_tags` | destructive | v2 PUT `/tag/merge` |

### Folder Tools (4)

| Tool | Annotations | API |
|------|-------------|-----|
| `list_folders` | readOnly | v3 `/batch/check/0` → `projectGroups` |
| `add_folder` | openWorld | v2 POST `/batch/projectGroup` `{add: [...]}` |
| `delete_folders` | destructive | v2 POST `/batch/projectGroup` `{delete: [...]}` |
| `rename_folder` | openWorld | v2 POST `/batch/projectGroup` `{update: [...]}` |

---

## Phase 6: Habits

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/tools/habits.py` | `api/habit.rs` |
| `tests/test_tools/test_habits.py` | |

### Habit Tools (8)

| Tool | Annotations | API |
|------|-------------|-----|
| `list_habits` | readOnly | v2 GET `/habits` |
| `add_habit` | openWorld | v2 POST `/habits/batch` `{add: [...]}` |
| `edit_habit` | openWorld | v2 POST `/habits/batch` `{update: [...]}` |
| `delete_habits` | destructive | v2 POST `/habits/batch` `{delete: [...]}` |
| `checkin_habit` | openWorld | v2 POST `/habitCheckins/batch` `{add: [...]}` |
| `habit_log` | readOnly | v2 POST `/habitCheckins/query` |
| `archive_habits` | openWorld | v2 POST `/habits/batch` `{update: [{status: 1}]}` |
| `manage_habit_sections` | varies | v2 GET `/habitSections`, POST `/habitSections/batch` |

`manage_habit_sections` takes `action` param: list/add/delete/rename. Consolidates 4 operations into 1 tool since sections are a sub-entity.

---

## Phase 7: Filters + Focus + Calendar + Sync

### Files

| File | Reference |
|------|-----------|
| `src/ticktick_mcp/tools/filters.py` | `api/filter.rs` |
| `src/ticktick_mcp/tools/focus.py` | `api/focus.rs` |
| `src/ticktick_mcp/tools/calendar.py` | `api/calendar.rs` |
| `tests/test_tools/test_filters.py` | |
| `tests/test_tools/test_focus.py` | |
| `tests/test_tools/test_calendar.py` | |

### Filter Tools (4)

| Tool | API |
|------|-----|
| `list_filters` | v3 `/batch/check/0` → `filters` |
| `add_filter` | v2 POST `/batch/filter` `{add: [...]}` |
| `edit_filter` | v2 POST `/batch/filter` `{update: [...]}` |
| `delete_filters` | v2 POST `/batch/filter` `{delete: [...]}` |

### Focus Tools (6)

| Tool | API |
|------|-----|
| `focus_status` | v2 GET `/timer` |
| `focus_stats` | v2 GET `/pomodoros/statistics/generalForDesktop` |
| `focus_log` | v2 GET `/pomodoros?from={ms}&to={ms}` |
| `focus_timeline` | v2 GET `/pomodoros/timeline` |
| `focus_start` | POST `ms.ticktick.com/focus/batch/focusOp` |
| `focus_control` | POST `ms.ticktick.com/focus/batch/focusOp` (pause/resume/stop) |

### Calendar Tools (2) + Sync (1)

| Tool | API |
|------|-----|
| `list_calendars` | v2 GET `/calendar/third/accounts` |
| `list_events` | v2 POST `/calendar/bind/events/all` |
| `sync_account` | v3 GET `/batch/check/0` |

---

## Phase 8: CI/CD + Publishing

### ci.yml
Triggers on push/PR: `uv sync --all-extras` → `ruff check` → `ruff format --check` → `pyright` → `pytest`

### publish.yml
Triggers on `v*` tags: `uv build` → `pypa/gh-action-pypi-publish` with trusted publisher (OIDC)

---

## GitHub Issues to Create

| Issue | Priority |
|-------|----------|
| HTTP/SSE transport support | P1 |
| OAuth browser login flow (like CLI `login`) | P2 |
| Incremental sync (checkpoint-based) | P3 |

---

## Project Structure (Final)

```
ticktick-mcp/
├── pyproject.toml
├── src/ticktick_mcp/
│   ├── __init__.py
│   ├── server.py           # FastMCP instance, lifespan, main()
│   ├── auth.py             # Token refresh, credential loading
│   ├── client.py           # httpx wrapper (v1/v2/v3/ms APIs)
│   ├── models.py           # Pydantic models (Task, Project, Tag, ...)
│   ├── dates.py            # Date/time/duration/timezone parsing
│   ├── resolve.py          # Generic fuzzy name resolution
│   ├── tools/
│   │   ├── __init__.py     # Imports all tool modules
│   │   ├── tasks.py        # 10 tools
│   │   ├── projects.py     # 5 tools
│   │   ├── tags.py         # 6 tools
│   │   ├── folders.py      # 4 tools
│   │   ├── habits.py       # 8 tools
│   │   ├── filters.py      # 4 tools
│   │   ├── focus.py        # 6 tools
│   │   └── calendar.py     # 3 tools (incl. sync)
│   └── resources/
│       ├── __init__.py
│       ├── profile.py
│       ├── settings.py
│       └── lists.py        # projects + tags
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_dates.py
│   ├── test_resolve.py
│   ├── test_tools/
│   │   ├── test_tasks.py
│   │   ├── test_projects.py
│   │   └── ...
│   └── test_resources/
│       └── ...
├── .github/workflows/
│   ├── ci.yml
│   └── publish.yml
└── .gitignore
```

## Verification (End-to-End)

After all phases:
1. `uv run ticktick-mcp` — starts stdio server
2. `uv run pytest` — all tests pass (mocked HTTP, no credentials needed)
3. `npx @modelcontextprotocol/inspector` — lists all 46 tools, 4 resources
4. Add to Claude Code: `claude mcp add ticktick-mcp -- uv run ticktick-mcp` with env vars
5. Test: "List my projects", "Add a task to Shopping", "Start a 25min focus session"
