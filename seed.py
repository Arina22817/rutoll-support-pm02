from datetime import datetime, timedelta

from database import Database


def seed_database(database: Database) -> None:
    database.initialize()

    with database.connect() as connection:
        for role in ("Заявитель", "Инженер поддержки", "Руководитель"):
            connection.execute("INSERT OR IGNORE INTO roles(name) VALUES (?)", (role,))
        roles = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM roles")}

        users = [
            ("Арина Игнатьева", "a.ignatieva", roles["Инженер поддержки"]),
            ("Дмитрий Кузнецов", "d.kuznetsov", roles["Инженер поддержки"]),
            ("Елена Волкова", "e.volkova", roles["Инженер поддержки"]),
            ("Сергей Морозов", "s.morozov", roles["Инженер поддержки"]),
            ("Дежурный инженер ПВП-46", "duty.pvp46", roles["Заявитель"]),
            ("Дежурный инженер ПВП-12", "duty.pvp12", roles["Заявитель"]),
            ("Иван Петров", "i.petrov", roles["Заявитель"]),
            ("Мария Соколова", "m.sokolova", roles["Заявитель"]),
            ("Алексей Орлов", "a.orlov", roles["Руководитель"]),
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO users(full_name, login, role_id) VALUES (?, ?, ?)", users
        )

        for category in ("ТП / СВП_АПД_М4", "ТП / СВП_АПД_М1", "Доступ к системе", "Платежи", "Консультация"):
            connection.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (category,))
        connection.executemany(
            "INSERT OR IGNORE INTO priorities(name, sort_order) VALUES (?, ?)",
            (("Критический", 1), ("Высокий", 2), ("Обычный", 3), ("Низкий", 4)),
        )
        for status in ("Новое", "В работе", "Ожидает", "Решено", "Закрыто"):
            connection.execute("INSERT OR IGNORE INTO statuses(name) VALUES (?)", (status,))
        for lane in ("6/14", "5/13", "4/12", "3/11", "Не указано"):
            connection.execute("INSERT OR IGNORE INTO lanes(name) VALUES (?)", (lane,))
        for tag in ("эксплуатация", "авторизация", "платёж", "ошибка", "консультация"):
            connection.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (tag,))
        for component in ("АПП", "API", "Личный кабинет", "Платёжный модуль", "Мобильное приложение"):
            connection.execute("INSERT OR IGNORE INTO components(name) VALUES (?)", (component,))

        user_ids = {row["login"]: row["id"] for row in connection.execute("SELECT id, login FROM users")}
        category_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM categories")}
        priority_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM priorities")}
        status_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM statuses")}
        lane_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM lanes")}
        tag_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM tags")}
        component_ids = {row["name"]: row["id"] for row in connection.execute("SELECT * FROM components")}

        existing = connection.execute("SELECT COUNT(*) AS count FROM tickets").fetchone()["count"]
        if not existing:
            now = datetime.now()
            rows = [
                (
                    user_ids["duty.pvp46"], user_ids["a.ignatieva"], user_ids["duty.pvp46"],
                    category_ids["ТП / СВП_АПД_М4"], priority_ids["Обычный"], status_ids["В работе"],
                    "ПВП М1-46 км полоса 6/14. Некорректно отображается АПП",
                    "На ПВП М1-46 км на полосе 6/14 некорректно отображается состояние АПП. Требуется проверить данные и восстановить корректное отображение.",
                    "ПВП-46 (М-1)", lane_ids["6/14"], tag_ids["эксплуатация"], component_ids["АПП"],
                    "Инцидент", "Не заполнено", "АПД М1", "Нет решения", "Не заполнено",
                    "АПД (М4 и М1)", "АПД М1", "Сообщить об инциденте", "Портал",
                    (now - timedelta(hours=43, minutes=22)).strftime("%Y-%m-%d %H:%M:%S"),
                    (now - timedelta(minutes=18)).strftime("%Y-%m-%d %H:%M:%S"),
                ),
                (
                    user_ids["duty.pvp12"], user_ids["d.kuznetsov"], user_ids["duty.pvp12"],
                    category_ids["ТП / СВП_АПД_М1"], priority_ids["Высокий"], status_ids["Новое"],
                    "ПВП М1-12. Ошибка передачи статуса оборудования",
                    "В рабочем интерфейсе отсутствует актуальный статус оборудования после обновления данных.",
                    "ПВП-12 (М-1)", lane_ids["5/13"], tag_ids["ошибка"], component_ids["API"],
                    "Инцидент", "1.8.4", "АПД М1", "Нет решения", "Не заполнено",
                    "АПД (М4 и М1)", "АПД М1", "Сообщить об инциденте", "Портал",
                    (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                    (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                ),
                (
                    user_ids["i.petrov"], user_ids["e.volkova"], user_ids["i.petrov"],
                    category_ids["Доступ к системе"], priority_ids["Низкий"], status_ids["Ожидает"],
                    "Не удаётся войти в личный кабинет",
                    "После ввода логина отображается сообщение об ошибке авторизации.",
                    "ПВП-08 (М-4)", lane_ids["Не указано"], tag_ids["авторизация"], component_ids["Личный кабинет"],
                    "Запрос", "Не заполнено", "Веб-портал", "Нет решения", "Не заполнено",
                    "Служба эксплуатации", "Поддержка пользователей", "Запрос на обслуживание", "Портал",
                    (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                    now.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            ]
            connection.executemany(
                """
                INSERT INTO tickets(
                    client_id, assignee_id, author_id, category_id, priority_id, status_id,
                    subject, description, pvp, lane_id, tag_id, component_id,
                    issue_type, affected_version, environment, resolution, fix_version,
                    organization, group_name, request_type, channel, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            first_ticket = connection.execute("SELECT MIN(id) AS id FROM tickets").fetchone()["id"]
            connection.executemany(
                "INSERT INTO comments(ticket_id, author_id, text, created_at) VALUES (?, ?, ?, ?)",
                [
                    (first_ticket, user_ids["duty.pvp46"], "Проблема воспроизводится на рабочем месте. Скриншот приложен к обращению.", (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")),
                    (first_ticket, user_ids["a.ignatieva"], "Заявка принята в работу, выполняется проверка данных по компоненту АПП.", (now - timedelta(minutes=18)).strftime("%Y-%m-%d %H:%M:%S")),
                ],
            )
        else:
            connection.execute(
                """
                UPDATE tickets
                SET issue_type = COALESCE(NULLIF(issue_type, ''), 'Инцидент'),
                    affected_version = COALESCE(NULLIF(affected_version, ''), 'Не заполнено'),
                    environment = COALESCE(NULLIF(environment, ''), 'АПД М1'),
                    resolution = COALESCE(NULLIF(resolution, ''), 'Нет решения'),
                    fix_version = COALESCE(NULLIF(fix_version, ''), 'Не заполнено'),
                    organization = COALESCE(NULLIF(organization, ''), 'АПД (М4 и М1)'),
                    group_name = COALESCE(NULLIF(group_name, ''), 'АПД М1'),
                    request_type = COALESCE(NULLIF(request_type, ''), 'Сообщить об инциденте'),
                    channel = COALESCE(NULLIF(channel, ''), 'Портал'),
                    author_id = COALESCE(author_id, client_id)
                """
            )
