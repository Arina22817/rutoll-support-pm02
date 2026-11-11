import tkinter as tk
from tkinter import messagebox, ttk

from database import Database
from models import Ticket
from repository import TicketRepository
from seed import seed_database
from services import TicketService


class SupportApp(tk.Tk):
    """Графический интерфейс системы учёта обращений технической поддержки."""

    def __init__(self, db_path: str = "support_tickets.db") -> None:
        super().__init__()
        self.title("ООО «Рутолл» — учёт обращений технической поддержки")
        self.geometry("1280x800")
        self.minsize(980, 560)

        self.database = Database(db_path)
        seed_database(self.database)
        self.repository = TicketRepository(self.database)
        self.service = TicketService(self.repository)
        self.status_map = self._load_lookup("statuses")
        self.category_map = self._load_lookup("categories")
        self.priority_map = self._load_lookup("priorities")
        self.client_map = self._load_clients()
        self.engineer_id = self.database.fetch_one(
            "SELECT id FROM users WHERE login = ?", ("a.ignatieva",)
        )["id"]

        self._build_ui()
        self.refresh_tickets()

    def _load_lookup(self, table: str) -> dict[str, int]:
        return {row["name"]: row["id"] for row in self.database.fetch_all(f"SELECT id, name FROM {table} ORDER BY id")}

    def _load_clients(self) -> dict[str, int]:
        rows = self.database.fetch_all(
            """
            SELECT u.id, u.full_name
            FROM users u JOIN roles r ON r.id = u.role_id
            WHERE r.name = 'Клиент'
            ORDER BY u.full_name
            """
        )
        return {row["full_name"]: row["id"] for row in rows}

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Система учёта обращений", font=("Arial", 18, "bold")).pack(side="left")
        ttk.Label(header, text="Инженер: Арина Игнатьева").pack(side="right")

        filters = ttk.LabelFrame(self, text="Поиск и фильтрация", padding=10)
        filters.pack(fill="x", padx=16, pady=(0, 8))

        ttk.Label(filters, text="Поиск:").grid(row=0, column=0, sticky="w")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=42)
        search_entry.grid(row=0, column=1, padx=(6, 16))
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_tickets())

        ttk.Label(filters, text="Статус:").grid(row=0, column=2, sticky="w")
        self.status_filter = ttk.Combobox(filters, state="readonly", width=22)
        self.status_filter["values"] = ["Все статусы"] + list(self.status_map.keys())
        self.status_filter.current(0)
        self.status_filter.grid(row=0, column=3, padx=6)
        self.status_filter.bind("<<ComboboxSelected>>", lambda _event: self.refresh_tickets())

        ttk.Button(filters, text="Новое обращение", command=self.open_new_ticket).grid(row=0, column=4, padx=(20, 4))
        ttk.Button(filters, text="Назначить мне", command=self.assign_selected).grid(row=0, column=5, padx=4)
        ttk.Button(filters, text="Изменить статус", command=self.change_status_selected).grid(row=0, column=6, padx=4)
        ttk.Button(filters, text="Комментарии", command=self.open_comments).grid(row=0, column=7, padx=4)

        table_frame = ttk.Frame(self, padding=(16, 0, 16, 8))
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "subject", "category", "priority", "status", "client", "assignee", "created")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        headings = {
            "id": "№",
            "subject": "Тема",
            "category": "Категория",
            "priority": "Приоритет",
            "status": "Статус",
            "client": "Клиент",
            "assignee": "Исполнитель",
            "created": "Создано",
        }
        widths = {"id": 45, "subject": 275, "category": 145, "priority": 95, "status": 115, "client": 135, "assignee": 145, "created": 140}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status_bar = ttk.Label(self, text="", relief="sunken", anchor="w", padding=(8, 4))
        self.status_bar.pack(fill="x")

    def refresh_tickets(self) -> None:
        status_name = self.status_filter.get() if hasattr(self, "status_filter") else "Все статусы"
        status_id = None if status_name == "Все статусы" else self.status_map[status_name]
        rows = self.repository.list_tickets(self.search_var.get() if hasattr(self, "search_var") else "", status_id)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in rows:
            self.tree.insert("", "end", values=(
                row["id"], row["subject"], row["category"], row["priority"], row["status"],
                row["client"], row["assignee"], row["created_at"]
            ))
        self.status_bar.config(text=f"Обращений отображено: {len(rows)}")

    def _selected_ticket(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор обращения", "Необходимо выбрать обращение в таблице")
            return None
        return self.tree.item(selected[0], "values")

    def assign_selected(self) -> None:
        values = self._selected_ticket()
        if not values:
            return
        self.repository.assign(int(values[0]), self.engineer_id)
        self.refresh_tickets()

    def change_status_selected(self) -> None:
        values = self._selected_ticket()
        if not values:
            return
        ticket_id = int(values[0])
        current_name = values[4]
        dialog = tk.Toplevel(self)
        dialog.title("Изменение статуса")
        dialog.geometry("360x160")
        dialog.transient(self)
        dialog.grab_set()
        ttk.Label(dialog, text=f"Текущий статус: {current_name}").pack(pady=(18, 8))
        combo = ttk.Combobox(dialog, state="readonly", values=list(self.status_map.keys()), width=24)
        combo.pack()
        combo.set(current_name)

        def save() -> None:
            new_name = combo.get()
            try:
                self.service.change_status(ticket_id, self.status_map[current_name], self.status_map[new_name])
            except ValueError as error:
                messagebox.showerror("Ошибка", str(error), parent=dialog)
                return
            dialog.destroy()
            self.refresh_tickets()

        ttk.Button(dialog, text="Сохранить", command=save).pack(pady=16)


    def open_comments(self) -> None:
        values = self._selected_ticket()
        if not values:
            return
        ticket_id = int(values[0])

        dialog = tk.Toplevel(self)
        dialog.title(f"Комментарии к обращению №{ticket_id}")
        dialog.geometry("700x430")
        dialog.transient(self)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding=14)
        frame.pack(fill="both", expand=True)

        columns = ("created", "author", "text")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        tree.heading("created", text="Дата")
        tree.heading("author", text="Автор")
        tree.heading("text", text="Комментарий")
        tree.column("created", width=135, anchor="w")
        tree.column("author", width=150, anchor="w")
        tree.column("text", width=360, anchor="w")
        tree.pack(fill="both", expand=True)

        ttk.Label(frame, text="Новый комментарий:").pack(anchor="w", pady=(12, 4))
        comment_text = tk.Text(frame, height=4)
        comment_text.pack(fill="x")

        def refresh_comments() -> None:
            for item in tree.get_children():
                tree.delete(item)
            for row in self.repository.list_comments(ticket_id):
                tree.insert(
                    "",
                    "end",
                    values=(row["created_at"], row["author"], row["text"]),
                )

        def add_comment() -> None:
            try:
                self.service.add_comment(
                    ticket_id,
                    self.engineer_id,
                    comment_text.get("1.0", "end").strip(),
                )
            except ValueError as error:
                messagebox.showerror("Ошибка ввода", str(error), parent=dialog)
                return
            comment_text.delete("1.0", "end")
            refresh_comments()

        ttk.Button(frame, text="Добавить комментарий", command=add_comment).pack(
            anchor="e", pady=(8, 0)
        )
        refresh_comments()

    def open_new_ticket(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Новое обращение")
        dialog.geometry("520x410")
        dialog.transient(self)
        dialog.grab_set()

        form = ttk.Frame(dialog, padding=16)
        form.pack(fill="both", expand=True)
        fields = {}
        for row, (label, values) in enumerate([
            ("Клиент", list(self.client_map.keys())),
            ("Категория", list(self.category_map.keys())),
            ("Приоритет", list(self.priority_map.keys())),
        ]):
            ttk.Label(form, text=label + ":").grid(row=row, column=0, sticky="w", pady=5)
            combo = ttk.Combobox(form, state="readonly", values=values, width=38)
            combo.grid(row=row, column=1, sticky="ew", pady=5)
            combo.current(0)
            fields[label] = combo

        ttk.Label(form, text="Тема:").grid(row=3, column=0, sticky="w", pady=5)
        subject = ttk.Entry(form, width=42)
        subject.grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Описание:").grid(row=4, column=0, sticky="nw", pady=5)
        description = tk.Text(form, height=8, width=42)
        description.grid(row=4, column=1, sticky="nsew", pady=5)
        form.columnconfigure(1, weight=1)
        form.rowconfigure(4, weight=1)

        def save() -> None:
            ticket = Ticket(
                id=None,
                client_id=self.client_map[fields["Клиент"].get()],
                subject=subject.get(),
                description=description.get("1.0", "end").strip(),
                category_id=self.category_map[fields["Категория"].get()],
                priority_id=self.priority_map[fields["Приоритет"].get()],
                status_id=self.status_map["Новое"],
            )
            try:
                self.service.create_ticket(ticket)
            except ValueError as error:
                messagebox.showerror("Ошибка ввода", str(error), parent=dialog)
                return
            dialog.destroy()
            self.refresh_tickets()

        ttk.Button(form, text="Создать обращение", command=save).grid(row=5, column=1, sticky="e", pady=(12, 0))


if __name__ == "__main__":
    SupportApp().mainloop()
