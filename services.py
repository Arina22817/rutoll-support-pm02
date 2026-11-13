from models import Ticket
from repository import TicketRepository


class TicketService:
    """Бизнес-логика service desk приложения."""

    ALLOWED_TRANSITIONS = {
        "Новое": {"В работе", "Ожидает", "Решено", "Закрыто"},
        "В работе": {"Ожидает", "Решено", "Закрыто"},
        "Ожидает": {"В работе", "Решено", "Закрыто"},
        "Решено": {"В работе", "Закрыто"},
        "Закрыто": {"В работе"},
    }

    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    def create_ticket(self, ticket: Ticket) -> int:
        ticket.validate()
        return self.repository.create_ticket(ticket)

    def change_status(self, ticket_id: int, current_status_id: int, new_status_id: int) -> None:
        current = self.repository.get_status_name(current_status_id)
        new = self.repository.get_status_name(new_status_id)
        if new == current:
            return
        if new not in self.ALLOWED_TRANSITIONS.get(current, set()):
            raise ValueError("Недопустимый переход между статусами обращения")
        self.repository.update_status(ticket_id, new_status_id)

    def update_ticket(self, ticket_id: int, **fields) -> None:
        if "subject" in fields and not str(fields["subject"]).strip():
            raise ValueError("Тема обращения не может быть пустой")
        if "description" in fields and not str(fields["description"]).strip():
            raise ValueError("Описание обращения не может быть пустым")
        if "pvp" in fields and not str(fields["pvp"]).strip():
            raise ValueError("Поле ПВП должно быть заполнено")
        self.repository.update_ticket(ticket_id, **fields)

    def add_comment(self, ticket_id: int, author_id: int, text: str) -> int:
        if not text.strip():
            raise ValueError("Комментарий не может быть пустым")
        return self.repository.add_comment(ticket_id, author_id, text.strip())
