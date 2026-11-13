from datetime import datetime
from typing import Optional

from database import Database
from models import Ticket


class TicketRepository:
    """Слой доступа к данным обращений."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create_ticket(self, ticket: Ticket) -> int:
        return self.database.execute(
            """
            INSERT INTO tickets (
                client_id, assignee_id, author_id, category_id, priority_id, status_id,
                subject, description, pvp, lane_id, tag_id, component_id,
                issue_type, affected_version, environment, resolution, fix_version,
                organization, group_name, request_type, channel, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket.client_id, ticket.assignee_id, ticket.author_id,
                ticket.category_id, ticket.priority_id, ticket.status_id,
                ticket.subject.strip(), ticket.description.strip(), ticket.pvp.strip(),
                ticket.lane_id, ticket.tag_id, ticket.component_id,
                ticket.issue_type.strip(), ticket.affected_version.strip(),
                ticket.environment.strip(), ticket.resolution.strip(),
                ticket.fix_version.strip(), ticket.organization.strip(),
                ticket.group_name.strip(), ticket.request_type.strip(), ticket.channel.strip(),
                ticket.created_at, ticket.updated_at,
            ),
        )

    def _base_select(self) -> str:
        return """
        SELECT
            t.*,
            c.name AS category,
            p.name AS priority,
            s.name AS status,
            cl.full_name AS client,
            COALESCE(a.full_name, 'Не назначен') AS assignee,
            COALESCE(au.full_name, cl.full_name) AS author,
            COALESCE(l.name, 'Не заполнено') AS lane,
            COALESCE(g.name, 'Не заполнено') AS tag,
            COALESCE(cp.name, 'Не заполнено') AS component
        FROM tickets t
        JOIN categories c ON c.id = t.category_id
        JOIN priorities p ON p.id = t.priority_id
        JOIN statuses s ON s.id = t.status_id
        JOIN users cl ON cl.id = t.client_id
        LEFT JOIN users a ON a.id = t.assignee_id
        LEFT JOIN users au ON au.id = t.author_id
        LEFT JOIN lanes l ON l.id = t.lane_id
        LEFT JOIN tags g ON g.id = t.tag_id
        LEFT JOIN components cp ON cp.id = t.component_id
        """

    def list_tickets(self, search: str = "", status_id: Optional[int] = None) -> list:
        query = self._base_select() + " WHERE 1 = 1"
        params: list = []
        if status_id is not None:
            query += " AND t.status_id = ?"
            params.append(status_id)
        query += " ORDER BY p.sort_order ASC, t.updated_at DESC"
        rows = self.database.fetch_all(query, tuple(params))
        needle = search.strip().casefold()
        if not needle:
            return rows
        searchable = (
            "subject", "description", "pvp", "category", "priority", "status",
            "assignee", "author", "lane", "tag", "component", "environment",
            "issue_type", "organization", "group_name"
        )
        return [
            row for row in rows
            if any(needle in str(row[key] or "").casefold() for key in searchable)
        ]

    def get_ticket(self, ticket_id: int):
        return self.database.fetch_one(self._base_select() + " WHERE t.id = ?", (ticket_id,))

    def assign(self, ticket_id: int, assignee_id: Optional[int]) -> None:
        self.database.execute(
            "UPDATE tickets SET assignee_id = ?, updated_at = ? WHERE id = ?",
            (assignee_id, self._now(), ticket_id),
        )

    def update_status(self, ticket_id: int, status_id: int) -> None:
        self.database.execute(
            "UPDATE tickets SET status_id = ?, updated_at = ? WHERE id = ?",
            (status_id, self._now(), ticket_id),
        )

    def update_ticket(self, ticket_id: int, **fields) -> None:
        allowed = {
            "subject", "description", "category_id", "priority_id", "pvp", "lane_id",
            "tag_id", "component_id", "author_id", "assignee_id", "issue_type",
            "affected_version", "environment", "resolution", "fix_version",
            "organization", "group_name", "request_type", "channel"
        }
        clean = {key: value for key, value in fields.items() if key in allowed}
        if not clean:
            return
        clean["updated_at"] = self._now()
        assignments = ", ".join(f"{key} = ?" for key in clean)
        values = tuple(clean.values()) + (ticket_id,)
        self.database.execute(f"UPDATE tickets SET {assignments} WHERE id = ?", values)

    def get_status_name(self, status_id: int) -> str:
        row = self.database.fetch_one("SELECT name FROM statuses WHERE id = ?", (status_id,))
        return row["name"] if row else ""

    def add_comment(self, ticket_id: int, author_id: int, text: str) -> int:
        comment_id = self.database.execute(
            "INSERT INTO comments(ticket_id, author_id, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author_id, text, self._now()),
        )
        self.database.execute(
            "UPDATE tickets SET updated_at = ? WHERE id = ?", (self._now(), ticket_id)
        )
        return comment_id

    def list_comments(self, ticket_id: int) -> list:
        return self.database.fetch_all(
            """
            SELECT c.id, c.text, c.created_at, u.full_name AS author
            FROM comments c
            JOIN users u ON u.id = c.author_id
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (ticket_id,),
        )

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
