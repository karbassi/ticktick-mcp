from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ChecklistItem(CamelModel):
    title: str
    status: int = 0
    is_all_day: bool | None = None
    start_date: str | None = None
    sort_order: int | None = None


class Task(CamelModel):
    id: str = ""
    title: str = ""
    project_id: str | None = None
    content: str | None = None
    desc: str | None = None
    priority: int = 0
    status: int = 0
    due_date: str | None = None
    start_date: str | None = None
    completed_time: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_all_day: bool | None = None
    time_zone: str | None = None
    parent_id: str | None = None
    items: list[ChecklistItem] | None = None
    reminders: list[str] | None = None
    repeat_flag: str | None = None


class Project(CamelModel):
    id: str = ""
    name: str = ""
    color: str | None = None
    sort_order: int = 0
    closed: bool = False
    group_id: str | None = None
    view_mode: str | None = None
    kind: str | None = None


class Tag(CamelModel):
    name: str = ""
    raw_name: str | None = None
    label: str | None = None
    sort_order: int | None = None
    sort_type: str | None = None
    color: str | None = None
    etag: str | None = None
    parent: str | None = None


class Habit(CamelModel):
    id: str = ""
    name: str | None = ""
    icon_res: str | None = None
    color: str | None = None
    sort_order: int | None = None
    status: int | None = None
    encouragement: str | None = None
    total_check_ins: int | None = None
    current_streak: int | None = None
    created_time: str | None = None
    modified_time: str | None = None
    habit_type: str | None = Field(default=None, alias="type")
    goal: float | None = None
    step: float | None = None
    unit: str | None = None
    record_enable: bool | None = None
    repeat_rule: str | None = None
    reminders: list[str] | None = None
    section_id: str | None = None
    target_days: int | None = None
    target_start_date: int | None = None
    completed_cycles: int | None = None
    etag: str | None = None


class HabitCheckin(CamelModel):
    id: str = ""
    habit_id: str | None = None
    checkin_stamp: int | None = None
    checkin_time: str | None = None
    op_time: str | None = None
    value: float | None = None
    goal: float | None = None
    status: int | None = None


class HabitSection(CamelModel):
    id: str = ""
    name: str = ""
    sort_order: int | None = None


class Filter(CamelModel):
    id: str = ""
    name: str = ""
    rule: str | None = None
    sort_order: int | None = None
    sort_type: str | None = None
    etag: str | None = None


class ProjectGroup(CamelModel):
    id: str = ""
    etag: str | None = None
    name: str = ""
    show_all: bool | None = None
    sort_order: int | None = None
    sort_type: str | None = None
    view_mode: str | None = None
