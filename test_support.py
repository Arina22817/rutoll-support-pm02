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
        self.ids = {
            table: {row["name"]: row["id"] for row in self.database.fetch_all(f"SELECT id, name FROM {table}")}
            for table in ("categories", "priorities", "statuses", "lanes", "tags", "components")
        }
        self.users = {row["login"]: row["id"] for row in self.database.fetch_all("SELECT id, login FROM users")}

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _ticket(self, subject="Тестовое обращение") -> Ticket:
        return Ticket(
            id=None,
            client_id=self.users["duty.pvp46"],
            author_id=self.users["duty.pvp46"],
            assignee_id=self.users["a.ignatieva"],
            subject=subject,
            description="Проверочное описание обращения",
            category_id=self.ids["categories"]["ТП / СВП_АПД_М4"],
            priority_id=self.ids["priorities"]["Обычный"],
            status_id=self.ids["statuses"]["Новое"],
            pvp="ПВП-46 (М-1)",
            lane_id=self.ids["lanes"]["6/14"],
            tag_id=self.ids["tags"]["эксплуатация"],
            component_id=self.ids["components"]["АПП"],
            issue_type="Инцидент",
            environment="АПД М1",
        )

    def test_create_ticket(self) -> None:
        self.assertGreater(self.service.create_ticket(self._ticket()), 0)

    def test_empty_subject_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.create_ticket(self._ticket(""))

    def test_empty_pvp_is_rejected(self) -> None:
        ticket = self._ticket()
        ticket.pvp = ""
        with self.assertRaises(ValueError):
            self.service.create_ticket(ticket)

    def test_multiple_support_engineers_exist(self) -> None:
        rows = self.database.fetch_all(
            "SELECT u.full_name FROM users u JOIN roles r ON r.id=u.role_id WHERE r.name='Инженер поддержки'"
        )
        self.assertGreaterEqual(len(rows), 4)

    def test_service_desk_fields_are_saved(self) -> None:
        ticket_id = self.service.create_ticket(self._ticket())
        row = self.repository.get_ticket(ticket_id)
        self.assertEqual(row["pvp"], "ПВП-46 (М-1)")
        self.assertEqual(row["lane"], "6/14")
        self.assertEqual(row["tag"], "эксплуатация")
        self.assertEqual(row["component"], "АПП")
        self.assertEqual(row["author"], "Дежурный инженер ПВП-46")

    def test_update_ticket_card(self) -> None:
        self.service.update_ticket(
            1,
            pvp="ПВП-46 (М-1)",
            environment="АПД М4",
            affected_version="2.0.1",
            resolution="Проверка выполнена",
            assignee_id=self.users["s.morozov"],
        )
        row = self.repository.get_ticket(1)
        self.assertEqual(row["environment"], "АПД М4")
        self.assertEqual(row["affected_version"], "2.0.1")
        self.assertEqual(row["assignee"], "Сергей Морозов")

    def test_valid_status_transition(self) -> None:
        self.service.change_status(1, self.ids["statuses"]["В работе"], self.ids["statuses"]["Решено"])
        row = self.repository.get_ticket(1)
        self.assertEqual(row["status"], "Решено")

    def test_invalid_status_transition(self) -> None:
        with self.assertRaises(ValueError):
            self.service.change_status(1, self.ids["statuses"]["Закрыто"], self.ids["statuses"]["Новое"])

    def test_search_by_component_and_pvp(self) -> None:
        self.assertTrue(self.repository.list_tickets("АПП"))
        self.assertTrue(self.repository.list_tickets("ПВП-46"))

    def test_add_comment(self) -> None:
        comment_id = self.service.add_comment(1, self.users["a.ignatieva"], "Проверка комментария")
        self.assertGreater(comment_id, 0)
        self.assertTrue(any(row["text"] == "Проверка комментария" for row in self.repository.list_comments(1)))

    def test_delete_ticket_with_comments(self) -> None:
        ticket_id = self.service.create_ticket(self._ticket("Заявка для удаления"))
        self.service.add_comment(ticket_id, self.users["a.ignatieva"], "Комментарий будет удалён вместе с заявкой")
        self.assertTrue(self.repository.list_comments(ticket_id))

        self.service.delete_ticket(ticket_id)

        self.assertIsNone(self.repository.get_ticket(ticket_id))
        self.assertEqual(self.repository.list_comments(ticket_id), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
