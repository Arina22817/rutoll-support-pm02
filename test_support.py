import tempfile
import unittest
from pathlib import Path

from database import Database
from models import Ticket
from repository import TicketRepository
from seed import seed_database
from services import TicketService


class TicketServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")
        self.database = Database(self.db_path)
        seed_database(self.database)
        self.repository = TicketRepository(self.database)
        self.service = TicketService(self.repository)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_create_ticket(self) -> None:
        ticket = Ticket(None, 2, "Тестовое обращение", "Описание", 1, 3, 1)
        ticket_id = self.service.create_ticket(ticket)
        self.assertGreater(ticket_id, 0)

    def test_empty_subject_is_rejected(self) -> None:
        ticket = Ticket(None, 2, "", "Описание", 1, 3, 1)
        with self.assertRaises(ValueError):
            self.service.create_ticket(ticket)

    def test_valid_status_transition(self) -> None:
        self.service.change_status(1, 2, 3)
        row = self.database.fetch_one("SELECT status_id FROM tickets WHERE id = 1")
        self.assertEqual(row["status_id"], 3)

    def test_invalid_status_transition(self) -> None:
        with self.assertRaises(ValueError):
            self.service.change_status(1, 4, 1)

    def test_search(self) -> None:
        rows = self.repository.list_tickets("платёж")
        self.assertTrue(any("Платёж" in row["subject"] for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
