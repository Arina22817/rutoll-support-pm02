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
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def validate(self) -> None:
        if not self.subject.strip():
            raise ValueError("Тема обращения не может быть пустой")
        if len(self.subject) > 120:
            raise ValueError("Тема обращения не должна превышать 120 символов")
        if not self.description.strip():
            raise ValueError("Описание обращения не может быть пустым")
