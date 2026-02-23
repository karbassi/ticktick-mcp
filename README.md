# mcp-ticktick

A [Model Context Protocol](https://modelcontextprotocol.io/) server that gives LLMs full access to [TickTick](https://ticktick.com) — tasks, projects, habits, focus timers, and more.

45 tools. 4 resources. Covers every TickTick feature.

## Features

- **Tasks** — create, edit, complete, delete, move, nest subtasks, view trash
- **Projects** — CRUD, fuzzy name matching
- **Tags** — create, rename, merge, organize hierarchically
- **Folders** — group projects into folders
- **Habits** — track habits, check in, view streaks, manage sections
- **Filters** — saved custom filters
- **Focus** — save pomodoro records, view stats and session history
- **Calendar** — list connected calendars and events
- **Resources** — read-only access to profile, settings, projects, and tags

## Requirements

- Python 3.12+
- A TickTick account
- An [OAuth app](https://developer.ticktick.com/manage) (free to create)

## Install

```bash
pip install mcp-ticktick
```

Or from source:

```bash
git clone https://github.com/karbassi/ticktick-mcp.git
cd ticktick-mcp
uv sync
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TICKTICK_ACCESS_TOKEN` | Yes | OAuth access token from the [developer portal](https://developer.ticktick.com) |
| `TICKTICK_CLIENT_ID` | No | OAuth client ID (for token refresh) |
| `TICKTICK_CLIENT_SECRET` | No | OAuth client secret (for token refresh) |
| `TICKTICK_REFRESH_TOKEN` | No | OAuth refresh token |
| `TICKTICK_V2_SESSION_TOKEN` | No | Browser `t` cookie for v2 API features |

> **v1 vs v2:** The access token covers tasks and projects. For tags, folders, filters, habits, focus, and calendar, you also need a v2 session token — grab the `t` cookie from your browser while logged into ticktick.com.

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ticktick": {
      "command": "mcp-ticktick",
      "env": {
        "TICKTICK_ACCESS_TOKEN": "your-access-token",
        "TICKTICK_V2_SESSION_TOKEN": "your-session-cookie"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add mcp-ticktick -- mcp-ticktick
```

Then set the environment variables in your shell.

## Tools

### Tasks (10)

| Tool | Description |
|---|---|
| `list_tasks` | List tasks from a project or all projects |
| `get_task` | Get a single task by ID |
| `add_task` | Create a task with due date, priority, tags, checklist |
| `edit_task` | Update task fields |
| `complete_task` | Mark a task complete |
| `delete_task` | Delete a task |
| `move_task` | Move a task between projects |
| `set_subtask` | Make a task a subtask of another |
| `unparent_task` | Remove a task from its parent |
| `list_trash` | List deleted tasks |

### Projects (5)

| Tool | Description |
|---|---|
| `list_projects` | List all projects |
| `get_project` | Get a project by name or ID (fuzzy match) |
| `add_project` | Create a new project |
| `edit_project` | Update project properties |
| `delete_project` | Delete a project and its tasks |

### Tags (6)

| Tool | Description |
|---|---|
| `list_tags` | List all tags |
| `add_tags` | Create one or more tags |
| `delete_tags` | Delete tags |
| `rename_tag` | Rename a tag (updates all tasks) |
| `edit_tag` | Update tag color, parent, sort |
| `merge_tags` | Merge one tag into another |

### Folders (4)

| Tool | Description |
|---|---|
| `list_folders` | List all project folders |
| `add_folder` | Create a folder |
| `delete_folders` | Delete folders |
| `rename_folder` | Rename a folder |

### Habits (8)

| Tool | Description |
|---|---|
| `list_habits` | List all habits |
| `add_habit` | Create a boolean or numeric habit |
| `edit_habit` | Update habit properties |
| `delete_habits` | Delete habits |
| `checkin_habit` | Record a habit check-in |
| `habit_log` | Query check-in history |
| `archive_habits` | Archive habits (hide, keep data) |
| `manage_habit_sections` | List, add, delete, rename sections |

### Filters (4)

| Tool | Description |
|---|---|
| `list_filters` | List saved filters |
| `add_filter` | Create a filter |
| `edit_filter` | Update a filter |
| `delete_filters` | Delete filters |

### Focus (5)

| Tool | Description |
|---|---|
| `focus_status` | Current timer status |
| `focus_stats` | Daily and total focus statistics |
| `focus_log` | Focus sessions for a date range |
| `focus_timeline` | Full session history |
| `focus_save` | Save a completed pomodoro record |

### Calendar (3)

| Tool | Description |
|---|---|
| `list_calendars` | List connected calendar accounts |
| `list_events` | Query events for a date range |
| `sync_account` | Full account sync |

## Resources

| URI | Description |
|---|---|
| `ticktick://profile` | User profile and account status |
| `ticktick://settings` | User preferences |
| `ticktick://projects` | All projects with IDs and metadata |
| `ticktick://tags` | All tags with colors and hierarchy |

## Development

```bash
git clone https://github.com/karbassi/ticktick-mcp.git
cd ticktick-mcp
uv sync --all-extras

# Lint & type check
uv run ruff check src/ tests/
uv run pyright src/

# Test
uv run pytest
```

## License

[MIT](LICENSE)
