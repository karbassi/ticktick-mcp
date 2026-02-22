# mcp-ticktick

MCP server for [TickTick](https://ticktick.com) task management. Provides 45 tools and 4 resources covering tasks, projects, tags, folders, habits, filters, focus/pomodoro, and calendar.

## Setup

### Prerequisites

- Python 3.12+
- A TickTick account with an [OAuth app](https://developer.ticktick.com/manage) (for v1 API access)

### Install

```bash
pip install mcp-ticktick
```

Or from source:

```bash
git clone https://github.com/karbassi/mcp-ticktick.git
cd mcp-ticktick
uv sync
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TICKTICK_ACCESS_TOKEN` | Yes | OAuth access token from the [TickTick developer portal](https://developer.ticktick.com) |
| `TICKTICK_CLIENT_ID` | No | OAuth client ID (for token refresh) |
| `TICKTICK_CLIENT_SECRET` | No | OAuth client secret (for token refresh) |
| `TICKTICK_REFRESH_TOKEN` | No | OAuth refresh token |
| `TICKTICK_V2_SESSION_TOKEN` | No | Browser session cookie (`t`) for v2 API features |

The v1 API (access token) covers tasks and projects. For tags, folders, filters, habits, focus, and calendar, you also need a v2 session token — grab the `t` cookie from your browser while logged into ticktick.com.

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Tools

### Tasks (10 tools)
`list_tasks` `get_task` `add_task` `edit_task` `complete_task` `delete_task` `move_task` `set_subtask` `unparent_task` `list_trash`

### Projects (5 tools)
`list_projects` `get_project` `add_project` `edit_project` `delete_project`

### Tags (6 tools)
`list_tags` `add_tags` `delete_tags` `rename_tag` `edit_tag` `merge_tags`

### Folders (4 tools)
`list_folders` `add_folder` `delete_folders` `rename_folder`

### Habits (8 tools)
`list_habits` `add_habit` `edit_habit` `delete_habits` `checkin_habit` `habit_log` `archive_habits` `manage_habit_sections`

### Filters (4 tools)
`list_filters` `add_filter` `edit_filter` `delete_filters`

### Focus (5 tools)
`focus_status` `focus_stats` `focus_log` `focus_timeline` `focus_save`

### Calendar (3 tools)
`list_calendars` `list_events` `sync_account`

## Resources

| URI | Description |
|---|---|
| `ticktick://profile` | User profile and account status |
| `ticktick://settings` | User preferences |
| `ticktick://projects` | All projects with IDs and metadata |
| `ticktick://tags` | All tags with colors and hierarchy |

## Development

```bash
uv sync --all-extras
uv run ruff check src/ tests/
uv run pytest
```

## License

MIT
