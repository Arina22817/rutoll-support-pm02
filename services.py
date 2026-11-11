from models import Ticket
from repository import TicketRepository


class TicketService:
    """Бизнес-логика системы учёта обращений."""

    ALLOWED_TRANSITIONS = {
        "Новое": {"В работе", "Закрыто"},
        "В работе": {"Ожидает клиента", "Закрыто"},
        "Ожидает клиента": {"В работе", "Закрыто"},
        "Закрыто": set(),
    }

    def __init__(self, repository: TicketRepository) -> None:
        self.repository = repository

    def create_ticket(self, ticket: Ticket) -> int:
        ticket.validate()
        return self.repository.create_ticket(ticket)

    def change_status(self, ticket_id: int, current_status_id: int, new_status_id: int) -> None:
        statuses = [self.repository.get_status_name(i) for i in (current_status_id, new_status_id)]
        if statuses[1] not in self.ALLOWED_TRANSITIONS.get(statuses[0], set()):
            raise ValueError("Недопустимый переход между статусами обращения")
        self.repository.update_status(ticket_id, new_status_id)

    def add_comment(self, ticket_id: int, author_id: int, text: str) -> int:
        if not text.strip():
            raise ValueError("Комментарий не может быть пустым")
        return self.repository.add_comment(ticket_id, author_id, text.strip())
