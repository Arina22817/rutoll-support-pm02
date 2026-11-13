PRAGMA foreign_keys = ON;

CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE priorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sort_order INTEGER NOT NULL UNIQUE
);

CREATE TABLE statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE lanes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    assignee_id INTEGER,
    author_id INTEGER,
    category_id INTEGER NOT NULL,
    priority_id INTEGER NOT NULL,
    status_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    description TEXT NOT NULL,
    pvp TEXT NOT NULL,
    lane_id INTEGER,
    tag_id INTEGER,
    component_id INTEGER,
    issue_type TEXT NOT NULL DEFAULT 'Инцидент',
    affected_version TEXT NOT NULL DEFAULT 'Не заполнено',
    environment TEXT NOT NULL DEFAULT '',
    resolution TEXT NOT NULL DEFAULT 'Нет решения',
    fix_version TEXT NOT NULL DEFAULT 'Не заполнено',
    organization TEXT NOT NULL DEFAULT '',
    group_name TEXT NOT NULL DEFAULT '',
    request_type TEXT NOT NULL DEFAULT 'Сообщить об инциденте',
    channel TEXT NOT NULL DEFAULT 'Портал',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES users(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (author_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (priority_id) REFERENCES priorities(id),
    FOREIGN KEY (status_id) REFERENCES statuses(id),
    FOREIGN KEY (lane_id) REFERENCES lanes(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    FOREIGN KEY (component_id) REFERENCES components(id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE INDEX idx_tickets_status ON tickets(status_id);
CREATE INDEX idx_tickets_assignee ON tickets(assignee_id);
CREATE INDEX idx_tickets_component ON tickets(component_id);
CREATE INDEX idx_tickets_pvp ON tickets(pvp);
CREATE INDEX idx_comments_ticket ON comments(ticket_id);
