\# NoteFlow — Персональный менеджер заметок и идей



Консольное приложение для создания, организации и поиска текстовых заметок.



\## Функциональность



\- Создание, редактирование, удаление заметок

\- Сортировка и фильтрация по тегу/статусу

\- Полнотекстовый поиск (регистронезависимый)

\- Экспорт в ZIP (JSON + отдельные .md + резервная копия БД)

\- Импорт из ZIP с обработкой дубликатов

\- Резервное копирование базы данных

\- Статистика по тегам

\- Поиск старых черновиков (>30 дней)



\## Требования



\- Python 3.12+

\- Библиотеки: python-dotenv



\## Установка и запуск



```bash

git clone https://github.com/ВАШ\_ЛОГИН/NoteFlow.git

cd NoteFlow

python -m venv venv

venv\\Scripts\\activate  # Windows

\# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

python src/main.py



\##Сруктура проекта


NoteFlow/
├── src/
│   └── main.py
├── backups/
├── .env
├── .gitignore
├── requirements.txt
├── app.log
└── README.md


\##Использованные технологии


Python (процедурный/функциональный стиль, без ООП)

SQLite

JSON, Markdown, ZIP

Git (ветки, Pull Request'ы)


\##Автор
Горская Алина



