from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    full_name: str
    login: str
    role: str


@dataclass
class Ticket:
    id: Optional[int]
    client_id: int
    subject: str
    description: str
    category_id: int
    priority_id: int
    status_id: int
    assignee_id: Optional[int] = None
    author_id: Optional[int] = None
    pvp: str = ""
    lane_id: Optional[int] = None
    tag_id: Optional[int] = None
    component_id: Optional[int] = None
    issue_type: str = "Инцидент"
    affected_version: str = "Не заполнено"
    environment: str = "АПД М1"
    resolution: str = "Нет решения"
    fix_version: str = "Не заполнено"
    organization: str = "АПД (М4 и М1)"
    group_name: str = "АПД М1"
    request_type: str = "Сообщить об инциденте"
    channel: str = "Портал"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.author_id is None:
            self.author_id = self.client_id
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def validate(self) -> None:
        if not self.subject.strip():
            raise ValueError("Тема обращения не может быть пустой")
        if len(self.subject) > 160:
            raise ValueError("Тема обращения не должна превышать 160 символов")
        if not self.description.strip():
            raise ValueError("Описание обращения не может быть пустым")
        if not self.pvp.strip():
            raise ValueError("Поле ПВП должно быть заполнено")
        if not self.issue_type.strip():
            raise ValueError("Тип обращения должен быть заполнен")
