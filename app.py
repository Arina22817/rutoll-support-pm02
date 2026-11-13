import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from database import Database
from models import Ticket
from repository import TicketRepository
from seed import seed_database
from services import TicketService


class TicketCardWindow(tk.Toplevel):
    """Карточка обращения в стиле service desk."""

    def __init__(self, app: "SupportApp", ticket_id: int) -> None:
        super().__init__(app)
        self.app = app
        self.ticket_id = ticket_id
        self.title(f"Карточка заявки RS-{48000 + ticket_id}")
        self.geometry("1180x780")
        self.minsize(1000, 680)
        self.configure(bg="#ffffff")
        self.transient(app)
        self._build()

    def _build(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        ticket = self.app.repository.get_ticket(self.ticket_id)
        if ticket is None:
            self.destroy()
            return

        root = tk.Frame(self, bg="#ffffff", padx=24, pady=18)
        root.pack(fill="both", expand=True)

        tk.Label(root, text=f"RS-{48000 + self.ticket_id}", fg="#1769c2", bg="#ffffff", font=("Arial", 10)).grid(row=0, column=0, sticky="w")
        tk.Label(root, text=ticket["subject"], fg="#1f2d4d", bg="#ffffff", font=("Arial", 18, "bold"), wraplength=800, justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(3, 12))

        actions = tk.Frame(root, bg="#ffffff")
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ttk.Button(actions, text="✎ Редактировать", command=self._edit).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="💬 Добавить комментарий", command=self._focus_comment).pack(side="left", padx=4)
        ttk.Button(actions, text="Назначить", command=self._assign).pack(side="left", padx=4)
        ttk.Button(actions, text="Еще...", command=lambda: messagebox.showinfo("Дополнительные действия", "Дополнительные действия не требуются в учебной версии.", parent=self)).pack(side="left", padx=4)

        self.status_combo = ttk.Combobox(actions, state="readonly", width=15, values=list(self.app.status_map.keys()))
        self.status_combo.set(ticket["status"])
        self.status_combo.pack(side="left", padx=(10, 0))
        self.status_combo.bind("<<ComboboxSelected>>", lambda _e: self._change_status(ticket))

        body = tk.Frame(root, bg="#ffffff")
        body.grid(row=3, column=0, columnspan=2, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        details = tk.LabelFrame(body, text=" Детали задачи ", bg="#ffffff", fg="#1f2d4d", font=("Arial", 10, "bold"), bd=0, highlightthickness=0, padx=8, pady=8)
        details.grid(row=0, column=0, sticky="nsew", padx=(0, 26))
        details.columnconfigure(1, weight=1)
        details.columnconfigure(3, weight=1)

        left_fields = [
            ("Тип", ticket["issue_type"]),
            ("Приоритет", ticket["priority"]),
            ("Затронуты версии", ticket["affected_version"]),
            ("Компоненты", ticket["component"]),
            ("Метки", ticket["tag"]),
            ("Окружение", ticket["environment"]),
            ("Категория", ticket["category"]),
            ("ПВП", ticket["pvp"]),
            ("Полоса", ticket["lane"]),
            ("Режим полосы", "Автоматизированный"),
        ]
        right_fields = [
            ("Решение", ticket["resolution"]),
            ("Исправить в версиях", ticket["fix_version"]),
            ("Организация", ticket["organization"]),
            ("Группа", ticket["group_name"]),
            ("Тип запроса", ticket["request_type"]),
            ("Канал", ticket["channel"]),
            ("Клиент", ticket["client"]),
        ]
        for index, (label, value) in enumerate(left_fields):
            self._detail_row(details, index, 0, label, value)
        for index, (label, value) in enumerate(right_fields):
            self._detail_row(details, index, 2, label, value)

        tk.Label(details, text="Описание:", bg="#ffffff", fg="#6a778b", font=("Arial", 9)).grid(row=11, column=0, sticky="nw", pady=(14, 4))
        desc = tk.Text(details, height=6, wrap="word", bd=1, relief="solid", bg="#fbfcfe", fg="#24364b")
        desc.insert("1.0", ticket["description"])
        desc.configure(state="disabled")
        desc.grid(row=11, column=1, columnspan=3, sticky="nsew", pady=(14, 4))
        details.rowconfigure(11, weight=1)

        sidebar = tk.Frame(body, bg="#ffffff")
        sidebar.grid(row=0, column=1, sticky="nsew")
        self._sidebar_block(sidebar, "SLA", [
            ("Время до решения", self._sla_resolution(ticket)),
            ("Время реакции", self._sla_response(ticket)),
        ], 0)
        self._sidebar_block(sidebar, "Люди", [
            ("Исполнитель", ticket["assignee"]),
            ("Автор", ticket["author"]),
            ("Организация", ticket["organization"]),
            ("Группа", ticket["group_name"]),
        ], 1)
        self._sidebar_block(sidebar, "Даты", [
            ("Создано", ticket["created_at"]),
            ("Обновлено", ticket["updated_at"]),
        ], 2)

        comments = tk.LabelFrame(root, text=" Комментарии ", bg="#ffffff", fg="#1f2d4d", font=("Arial", 10, "bold"), bd=0, padx=8, pady=8)
        comments.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(18, 0))
        comments.columnconfigure(0, weight=1)
        comments.rowconfigure(0, weight=1)
        self.comments_list = tk.Text(comments, height=7, wrap="word", bg="#fbfcfe", bd=1, relief="solid", state="disabled")
        self.comments_list.grid(row=0, column=0, columnspan=2, sticky="nsew")
        self.comment_entry = tk.Text(comments, height=3, wrap="word", bd=1, relief="solid")
        self.comment_entry.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(comments, text="Добавить", command=self._add_comment).grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(8, 0))
        self._refresh_comments()

        root.rowconfigure(3, weight=1)
        root.rowconfigure(4, weight=1)
        root.columnconfigure(0, weight=1)

    @staticmethod
    def _detail_row(parent, row: int, column: int, label: str, value: str) -> None:
        tk.Label(parent, text=f"{label}:", bg="#ffffff", fg="#778397", font=("Arial", 9), anchor="w").grid(row=row, column=column, sticky="nw", padx=(0, 10), pady=5)
        tk.Label(parent, text=value or "Не заполнено", bg="#ffffff", fg="#213653", font=("Arial", 9), anchor="w", justify="left", wraplength=220).grid(row=row, column=column + 1, sticky="nw", pady=5)

    @staticmethod
    def _sidebar_block(parent, title: str, rows: list[tuple[str, str]], row: int) -> None:
        frame = tk.LabelFrame(parent, text=f" {title} ", bg="#ffffff", fg="#1f2d4d", font=("Arial", 10, "bold"), bd=0, padx=8, pady=8)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        frame.columnconfigure(1, weight=1)
        for i, (label, value) in enumerate(rows):
            tk.Label(frame, text=f"{label}:", bg="#ffffff", fg="#778397", font=("Arial", 9)).grid(row=i, column=0, sticky="nw", pady=4, padx=(0, 10))
            tk.Label(frame, text=value, bg="#ffffff", fg="#213653", font=("Arial", 9), wraplength=230, justify="left").grid(row=i, column=1, sticky="nw", pady=4)

    def _sla_resolution(self, ticket) -> str:
        priority = ticket["priority"]
        targets = {"Критический": "4 ч", "Высокий": "8 ч", "Обычный": "1 д. 24 ч", "Низкий": "3 д."}
        return targets.get(priority, "1 д. 24 ч")

    def _sla_response(self, ticket) -> str:
        priority = ticket["priority"]
        targets = {"Критический": "10 мин.", "Высокий": "15 мин.", "Обычный": "20 мин.", "Низкий": "60 мин."}
        return targets.get(priority, "20 мин.")

    def _focus_comment(self) -> None:
        self.comment_entry.focus_set()

    def _refresh_comments(self) -> None:
        rows = self.app.repository.list_comments(self.ticket_id)
        self.comments_list.configure(state="normal")
        self.comments_list.delete("1.0", "end")
        if not rows:
            self.comments_list.insert("end", "Комментариев пока нет.\n")
        for row in rows:
            self.comments_list.insert("end", f"{row['author']} · {row['created_at']}\n", "author")
            self.comments_list.insert("end", f"{row['text']}\n\n")
        self.comments_list.tag_configure("author", font=("Arial", 9, "bold"), foreground="#1f4f8a")
        self.comments_list.configure(state="disabled")

    def _add_comment(self) -> None:
        text = self.comment_entry.get("1.0", "end").strip()
        try:
            self.app.service.add_comment(self.ticket_id, self.app.engineer_id, text)
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error), parent=self)
            return
        self.comment_entry.delete("1.0", "end")
        self._refresh_comments()
        self.app.refresh_tickets()

    def _assign(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Назначить инженера")
        dialog.geometry("390x170")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="Исполнитель:").pack(pady=(22, 8))
        combo = ttk.Combobox(dialog, state="readonly", width=30, values=list(self.app.engineer_map.keys()))
        combo.set(self.app.current_engineer_name)
        combo.pack()

        def save() -> None:
            self.app.repository.assign(self.ticket_id, self.app.engineer_map[combo.get()])
            dialog.destroy()
            self.app.refresh_tickets()
            self._build()

        ttk.Button(dialog, text="Назначить", command=save).pack(pady=16)

    def _change_status(self, ticket) -> None:
        new_name = self.status_combo.get()
        try:
            self.app.service.change_status(
                self.ticket_id,
                self.app.status_map[ticket["status"]],
                self.app.status_map[new_name],
            )
        except ValueError as error:
            messagebox.showerror("Ошибка", str(error), parent=self)
            self.status_combo.set(ticket["status"])
            return
        self.app.refresh_tickets()
        self._build()

    def _edit(self) -> None:
        self.app.open_edit_ticket(self.ticket_id, on_saved=self._build)


class SupportApp(tk.Tk):
    """Главное окно системы учёта обращений технической поддержки."""

    def __init__(self, db_path: str = "support_tickets.db") -> None:
        super().__init__()
        self.title("ООО «Рутолл» — служба технической поддержки")
        self.geometry("1380x820")
        self.minsize(1080, 640)
        self.configure(bg="#f4f6f9")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=28, font=("Arial", 9))
        style.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        self.database = Database(db_path)
        seed_database(self.database)
        self.repository = TicketRepository(self.database)
        self.service = TicketService(self.repository)
        self.status_map = self._lookup("statuses")
        self.category_map = self._lookup("categories")
        self.priority_map = self._lookup("priorities")
        self.lane_map = self._lookup("lanes")
        self.tag_map = self._lookup("tags")
        self.component_map = self._lookup("components")
        self.engineer_map = self._users_by_role("Инженер поддержки")
        self.author_map = self._all_users()
        self.client_map = self._users_by_roles(("Заявитель", "Клиент"))
        self.current_engineer_name = "Арина Игнатьева"
        self.engineer_id = self.engineer_map[self.current_engineer_name]
        self._build_ui()
        self.refresh_tickets()

    def _lookup(self, table: str) -> dict[str, int]:
        return {row["name"]: row["id"] for row in self.database.fetch_all(f"SELECT id, name FROM {table} ORDER BY id")}

    def _users_by_role(self, role: str) -> dict[str, int]:
        rows = self.database.fetch_all(
            "SELECT u.id, u.full_name FROM users u JOIN roles r ON r.id=u.role_id WHERE r.name=? ORDER BY u.full_name",
            (role,),
        )
        return {row["full_name"]: row["id"] for row in rows}

    def _users_by_roles(self, roles: tuple[str, ...]) -> dict[str, int]:
        marks = ",".join("?" for _ in roles)
        rows = self.database.fetch_all(
            f"SELECT u.id, u.full_name FROM users u JOIN roles r ON r.id=u.role_id WHERE r.name IN ({marks}) ORDER BY u.full_name",
            roles,
        )
        return {row["full_name"]: row["id"] for row in rows}

    def _all_users(self) -> dict[str, int]:
        return {row["full_name"]: row["id"] for row in self.database.fetch_all("SELECT id, full_name FROM users ORDER BY full_name")}

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#ffffff", padx=18, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Служба технической поддержки RUTOLL", bg="#ffffff", fg="#1f2d4d", font=("Arial", 17, "bold")).pack(side="left")
        tk.Label(header, text="Текущий инженер:", bg="#ffffff", fg="#66758a").pack(side="right", padx=(0, 6))
        self.engineer_combo = ttk.Combobox(header, state="readonly", width=22, values=list(self.engineer_map.keys()))
        self.engineer_combo.set(self.current_engineer_name)
        self.engineer_combo.pack(side="right")
        self.engineer_combo.bind("<<ComboboxSelected>>", self._change_engineer)

        tools = tk.Frame(self, bg="#f4f6f9", padx=18, pady=12)
        tools.pack(fill="x")
        tk.Label(tools, text="Очередь обращений", bg="#f4f6f9", fg="#1f2d4d", font=("Arial", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ttk.Entry(tools, textvariable=self.search_var, width=34).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.search_var.trace_add("write", lambda *_: self.refresh_tickets())
        self.status_filter = ttk.Combobox(tools, state="readonly", width=18, values=["Все статусы"] + list(self.status_map.keys()))
        self.status_filter.set("Все статусы")
        self.status_filter.grid(row=1, column=1, padx=8, pady=(8, 0))
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_tickets())
        ttk.Button(tools, text="Создать", command=self.open_new_ticket).grid(row=1, column=2, padx=(16, 4), pady=(8, 0))
        ttk.Button(tools, text="Открыть карточку", command=self.open_ticket_card).grid(row=1, column=3, padx=4, pady=(8, 0))
        ttk.Button(tools, text="Назначить", command=self.assign_selected).grid(row=1, column=4, padx=4, pady=(8, 0))
        tools.columnconfigure(5, weight=1)

        table_frame = tk.Frame(self, bg="#ffffff", padx=12, pady=12)
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        columns = ("key", "subject", "pvp", "lane", "component", "priority", "status", "author", "assignee", "updated")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "key": "Ключ", "subject": "Тема", "pvp": "ПВП", "lane": "Полоса",
            "component": "Компонент", "priority": "Приоритет", "status": "Статус",
            "author": "Автор", "assignee": "Исполнитель", "updated": "Обновлено",
        }
        widths = {"key": 80, "subject": 310, "pvp": 125, "lane": 70, "component": 105, "priority": 90, "status": 95, "author": 165, "assignee": 145, "updated": 140}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.bind("<Double-1>", lambda _e: self.open_ticket_card())
        y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.status_bar = ttk.Label(self, text="", anchor="w")
        self.status_bar.pack(fill="x", padx=18, pady=(0, 8))

    def _change_engineer(self, _event=None) -> None:
        self.current_engineer_name = self.engineer_combo.get()
        self.engineer_id = self.engineer_map[self.current_engineer_name]

    def refresh_tickets(self) -> None:
        status = self.status_filter.get() if hasattr(self, "status_filter") else "Все статусы"
        status_id = None if status == "Все статусы" else self.status_map[status]
        rows = self.repository.list_tickets(self.search_var.get() if hasattr(self, "search_var") else "", status_id)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", iid=str(row["id"]), values=(
                f"RS-{48000 + row['id']}", row["subject"], row["pvp"], row["lane"],
                row["component"], row["priority"], row["status"], row["author"],
                row["assignee"], row["updated_at"],
            ))
        self.status_bar.config(text=f"Обращений: {len(rows)}")

    def _selected_ticket_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор обращения", "Выберите обращение в таблице")
            return None
        return int(selected[0])

    def open_ticket_card(self) -> None:
        ticket_id = self._selected_ticket_id()
        if ticket_id is not None:
            TicketCardWindow(self, ticket_id)

    def assign_selected(self) -> None:
        ticket_id = self._selected_ticket_id()
        if ticket_id is None:
            return
        dialog = tk.Toplevel(self)
        dialog.title("Назначить")
        dialog.geometry("380x170")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text="Выберите инженера поддержки:").pack(pady=(22, 8))
        combo = ttk.Combobox(dialog, state="readonly", width=30, values=list(self.engineer_map.keys()))
        combo.set(self.current_engineer_name)
        combo.pack()
        def save() -> None:
            self.repository.assign(ticket_id, self.engineer_map[combo.get()])
            dialog.destroy()
            self.refresh_tickets()
        ttk.Button(dialog, text="Назначить", command=save).pack(pady=16)

    def open_new_ticket(self) -> None:
        self._ticket_form(None)

    def open_edit_ticket(self, ticket_id: int, on_saved=None) -> None:
        self._ticket_form(ticket_id, on_saved)

    def _ticket_form(self, ticket_id=None, on_saved=None) -> None:
        existing = self.repository.get_ticket(ticket_id) if ticket_id else None
        dialog = tk.Toplevel(self)
        dialog.title("Редактирование заявки" if existing else "Новое обращение")
        dialog.geometry("760x720")
        dialog.transient(self)
        dialog.grab_set()
        form = ttk.Frame(dialog, padding=16)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        combos = {}
        entries = {}
        selectors = [
            ("Автор", self.author_map, "author"),
            ("Исполнитель", self.engineer_map, "assignee"),
            ("Категория", self.category_map, "category"),
            ("Приоритет", self.priority_map, "priority"),
            ("Полоса", self.lane_map, "lane"),
            ("Тэг", self.tag_map, "tag"),
            ("Компонент", self.component_map, "component"),
        ]
        for idx, (label, mapping, key) in enumerate(selectors):
            r, c = divmod(idx, 2)
            c *= 2
            ttk.Label(form, text=f"{label}:").grid(row=r, column=c, sticky="w", pady=5, padx=(0, 8))
            combo = ttk.Combobox(form, state="readonly", values=list(mapping.keys()), width=28)
            combo.grid(row=r, column=c + 1, sticky="ew", pady=5, padx=(0, 16))
            if existing and existing[key] in mapping:
                combo.set(existing[key])
            else:
                combo.set(self.current_engineer_name if label == "Исполнитель" else list(mapping.keys())[0])
            combos[label] = combo

        row = 4
        text_fields = [
            ("Тип", "issue_type", "Инцидент"),
            ("ПВП", "pvp", "ПВП-46 (М-1)"),
            ("Окружение", "environment", "АПД М1"),
            ("Затронута версия", "affected_version", "Не заполнено"),
            ("Решение", "resolution", "Нет решения"),
            ("Исправить в версии", "fix_version", "Не заполнено"),
            ("Организация", "organization", "АПД (М4 и М1)"),
            ("Группа", "group_name", "АПД М1"),
            ("Тип запроса", "request_type", "Сообщить об инциденте"),
            ("Канал", "channel", "Портал"),
        ]
        for idx, (label, key, default) in enumerate(text_fields):
            r = row + idx // 2
            c = (idx % 2) * 2
            ttk.Label(form, text=f"{label}:").grid(row=r, column=c, sticky="w", pady=5, padx=(0, 8))
            entry = ttk.Entry(form)
            entry.grid(row=r, column=c + 1, sticky="ew", pady=5, padx=(0, 16))
            entry.insert(0, existing[key] if existing else default)
            entries[key] = entry

        row += 5
        ttk.Label(form, text="Тема:").grid(row=row, column=0, sticky="w", pady=5)
        subject = ttk.Entry(form)
        subject.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
        if existing:
            subject.insert(0, existing["subject"])
        row += 1
        ttk.Label(form, text="Описание:").grid(row=row, column=0, sticky="nw", pady=5)
        description = tk.Text(form, height=7, wrap="word")
        description.grid(row=row, column=1, columnspan=3, sticky="nsew", pady=5)
        if existing:
            description.insert("1.0", existing["description"])
        form.rowconfigure(row, weight=1)
        row += 1

        def save() -> None:
            fields = {
                "subject": subject.get(),
                "description": description.get("1.0", "end").strip(),
                "category_id": self.category_map[combos["Категория"].get()],
                "priority_id": self.priority_map[combos["Приоритет"].get()],
                "lane_id": self.lane_map[combos["Полоса"].get()],
                "tag_id": self.tag_map[combos["Тэг"].get()],
                "component_id": self.component_map[combos["Компонент"].get()],
                "author_id": self.author_map[combos["Автор"].get()],
                "assignee_id": self.engineer_map[combos["Исполнитель"].get()],
                **{key: widget.get() for key, widget in entries.items()},
            }
            try:
                if existing:
                    self.service.update_ticket(ticket_id, **fields)
                else:
                    ticket = Ticket(
                        id=None,
                        client_id=fields["author_id"],
                        status_id=self.status_map["Новое"],
                        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        **fields,
                    )
                    self.service.create_ticket(ticket)
            except ValueError as error:
                messagebox.showerror("Ошибка", str(error), parent=dialog)
                return
            dialog.destroy()
            self.refresh_tickets()
            if on_saved:
                on_saved()

        ttk.Button(form, text="Сохранить", command=save).grid(row=row, column=3, sticky="e", pady=(14, 0))


if __name__ == "__main__":
    SupportApp().mainloop()
