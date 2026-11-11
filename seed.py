from datetime import datetime, timedelta

from database import Database


def seed_database(database: Database) -> None:
    database.initialize()

    with database.connect() as connection:
        for role in ("Клиент", "Инженер поддержки", "Руководитель"):
            connection.execute("INSERT OR IGNORE INTO roles(name) VALUES (?)", (role,))

        roles = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM roles")}
        users = [
            ("Арина Игнатьева", "a.ignatieva", roles["Инженер поддержки"]),
            ("Иван Петров", "i.petrov", roles["Клиент"]),
            ("Мария Соколова", "m.sokolova", roles["Клиент"]),
            ("Алексей Орлов", "a.orlov", roles["Руководитель"]),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO users(full_name, login, role_id) VALUES (?, ?, ?)",
            users,
        )

        for category in ("Доступ к системе", "Платежи", "Сбой приложения", "Консультация"):
            connection.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (category,))

        priorities = (("Критический", 1), ("Высокий", 2), ("Средний", 3), ("Низкий", 4))
        connection.executemany(
            "INSERT OR IGNORE INTO priorities(name, sort_order) VALUES (?, ?)", priorities
        )

        for status in ("Новое", "В работе", "Ожидает клиента", "Закрыто"):
            connection.execute("INSERT OR IGNORE INTO statuses(name) VALUES (?)", (status,))

        existing = connection.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()["count"]
        if existing:
            return

        user_ids = {row["login"]: row["id"] for row in connection.execute("SELECT id, login FROM users")}
        category_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM categories")}
        priority_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM priorities")}
        status_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM statuses")}

        now = datetime.now()
        demo_tickets = [
            (
                user_ids["i.petrov"], user_ids["a.ignatieva"], category_ids["Доступ к системе"],
                priority_ids["Высокий"], status_ids["В работе"],
                "Не удаётся войти в личный кабинет",
                "После ввода логина отображается сообщение об ошибке авторизации.",
                (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ),
            (
                user_ids["m.sokolova"], None, category_ids["Платежи"],
                priority_ids["Критический"], status_ids["Новое"],
                "Платёж отображается дважды",
                "В истории операций одна транзакция отображается двумя строками.",
                (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
                (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
            ),
            (
                user_ids["i.petrov"], user_ids["a.ignatieva"], category_ids["Консультация"],
                priority_ids["Низкий"], status_ids["Ожидает клиента"],
                "Уточнение по настройкам профиля",
                "Требуется объяснить порядок изменения контактных данных.",
                (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                now.strftime("%Y-%m-%d %H:%M:%S"),
            ),
        ]
        connection.executemany(
            """
            INSERT INTO tickets(
                client_id, assignee_id, category_id, priority_id, status_id,
                subject, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            demo_tickets,
        )
