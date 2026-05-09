# FEATURE: Поиск и фильтрация с использованием замыканий и lambda
import sqlite3
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import zipfile
import shutil
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "notes.db")

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            tags TEXT,
            created_date TEXT,
            status TEXT CHECK(status IN ('draft', 'final'))
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("База данных инициализирована")


def create_note():
    print("\n--- СОЗДАНИЕ ЗАМЕТКИ ---")
    title = input("Заголовок: ").strip()
    if not title:
        print("Ошибка: заголовок не может быть пустым")
        return
    
    print("Текст (для завершения введите пустую строку):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    content = "\n".join(lines)
    
    tags = input("Теги (через запятую): ").strip()
    status = input("Статус (draft/final): ").strip().lower()
    while status not in ("draft", "final"):
        print("Ошибка: статус должен быть draft или final")
        status = input("Статус (draft/final): ").strip().lower()
    
    created_date = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (title, content, tags, created_date, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, content, tags, created_date, status))
    conn.commit()
    note_id = cursor.lastrowid
    conn.close()
    
    logging.info(f"Создана заметка id={note_id}")
    print(f"\n✅ Заметка создана! ID: {note_id}")


def list_all_notes():
    sort_by = input("Сортировать по (date/title): ").strip().lower()
    if sort_by == "title":
        order = "ORDER BY title"
    else:
        order = "ORDER BY created_date DESC"
    
    filter_tag = input("Фильтр по тегу (Enter - пропустить): ").strip()
    filter_status = input("Фильтр по статусу (draft/final/Enter - пропустить): ").strip().lower()
    
    query = "SELECT id, title, created_date, status, tags FROM notes"
    conditions = []
    params = []
    
    if filter_tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{filter_tag}%")
    if filter_status in ("draft", "final"):
        conditions.append("status = ?")
        params.append(filter_status)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " " + order
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    notes = cursor.fetchall()
    conn.close()
    
    if not notes:
        print("\n📭 Нет заметок")
        return
    
    print("\n" + "="*60)
    print("СПИСОК ЗАМЕТОК")
    print("="*60)
    for note in notes:
        print(f"ID: {note[0]} | {note[1]}")
        print(f"    Дата: {note[2]} | Статус: {note[3]}")
        print(f"    Теги: {note[4]}")
        print("-"*40)


def view_note():
    note_id = input("\nВведите ID заметки: ").strip()
    if not note_id.isdigit():
        print("Ошибка: ID должен быть числом")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()
    conn.close()
    
    if not note:
        print("Заметка не найдена")
        return
    
    print("\n" + "="*50)
    print(f"ЗАГОЛОВОК: {note[1]}")
    print(f"Дата: {note[4]} | Статус: {note[5]}")
    print(f"Теги: {note[3]}")
    print("-"*50)
    print("ТЕКСТ:")
    print(note[2])
    print("="*50)


def edit_note():
    note_id = input("\nВведите ID заметки для редактирования: ").strip()
    if not note_id.isdigit():
        print("Ошибка: ID должен быть числом")
        return
    
    print("Оставьте поле пустым, чтобы не менять")
    new_title = input("Новый заголовок: ").strip()
    new_tags = input("Новые теги: ").strip()
    new_status = input("Новый статус (draft/final): ").strip().lower()
    
    updates = []
    params = []
    
    if new_title:
        updates.append("title = ?")
        params.append(new_title)
    if new_tags:
        updates.append("tags = ?")
        params.append(new_tags)
    if new_status in ("draft", "final"):
        updates.append("status = ?")
        params.append(new_status)
    
    if not updates:
        print("Ничего не изменено")
        return
    
    params.append(note_id)
    query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()
    
    logging.info(f"Отредактирована заметка id={note_id}")
    print("✅ Заметка обновлена")


def delete_note():
    note_id = input("\nВведите ID заметки для удаления: ").strip()
    if not note_id.isdigit():
        print("Ошибка: ID должен быть числом")
        return
    
    confirm = input(f"Удалить заметку {note_id}? (да/нет): ").strip().lower()
    if confirm != "да":
        print("Отменено")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    
    logging.info(f"Удалена заметка id={note_id}")
    print("✅ Заметка удалена")


def create_text_search_filter(query):
    return lambda note: query.lower() in note[1].lower() or query.lower() in note[2].lower()


def search_notes():
    keyword = input("\nВведите слово для поиска: ").strip().lower()
    if not keyword:
        print("Ошибка: пустой поисковый запрос")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM notes")
    all_notes = cursor.fetchall()
    conn.close()
    
    search_filter = create_text_search_filter(keyword)
    results = list(filter(search_filter, all_notes))
    
    if not results:
        print(f"\n🔍 Ничего не найдено по запросу '{keyword}'")
        return
    
    print(f"\n🔍 НАЙДЕНО {len(results)} ЗАМЕТОК:")
    print("="*50)
    for note in results:
        print(f"ID: {note[0]} | {note[1]}")
        preview = " ".join(note[2].split()[:10]) + "..."
        print(f"    {preview}")
        print("-"*40)
    
    export = input("\nЭкспортировать результаты в Markdown? (да/нет): ").strip().lower()
    if export == "да":
        export_search_results(results, keyword)


def export_search_results(results, keyword):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{keyword}_{timestamp}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Результаты поиска: '{keyword}'\n\n")
        f.write(f"Найдено заметок: {len(results)}\n\n")
        f.write("---\n\n")
        for note in results:
            f.write(f"## {note[1]}\n")
            f.write(f"**ID:** {note[0]}\n\n")
            f.write(f"{note[2]}\n\n")
            f.write("---\n\n")
    
    print(f"✅ Экспортировано в {filename}")
    logging.info(f"Экспорт поиска '{keyword}' в {filename}")


def get_unique_tags():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tags FROM notes WHERE tags != ''")
    all_tags = cursor.fetchall()
    conn.close()
    
    tag_count = {}
    for (tags_str,) in all_tags:
        for tag in tags_str.split(','):
            tag = tag.strip()
            if tag:
                tag_count[tag] = tag_count.get(tag, 0) + 1
    
    if not tag_count:
        print("\n📭 Нет тегов")
        return
    
    print("\n" + "="*40)
    print("УНИКАЛЬНЫЕ ТЕГИ")
    print("="*40)
    for tag, count in sorted(tag_count.items(), key=lambda x: x[1], reverse=True):
        print(f"{tag}: {count} заметок")


def find_old_drafts():
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, created_date FROM notes 
        WHERE status = 'draft' AND created_date < ?
    """, (thirty_days_ago,))
    drafts = cursor.fetchall()
    conn.close()
    
    if not drafts:
        print("\n📭 Старых черновиков нет")
        return
    
    print("\n" + "="*50)
    print(f"СТАРЫЕ ЧЕРНОВИКИ (старше 30 дней)")
    print("="*50)
    for draft in drafts:
        print(f"ID: {draft[0]} | {draft[1]} | Дата: {draft[2]}")
    
    export = input("\nЭкспортировать в Markdown? (да/нет): ").strip().lower()
    if export == "да":
        with open("old_drafts.md", "w", encoding="utf-8") as f:
            f.write("# Старые черновики\n\n")
            for draft in drafts:
                f.write(f"## {draft[1]}\n")
                f.write(f"ID: {draft[0]} | Дата: {draft[2]}\n\n")
        print("✅ Экспортировано в old_drafts.md")


def backup_db():
    Path("backups").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backups/backup_{timestamp}.sqlite"
    
    shutil.copy2(DB_PATH, backup_name)
    print(f"✅ Резервная копия создана: {backup_name}")
    logging.info(f"Создана резервная копия {backup_name}")


def export_to_zip():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"notes_export_{timestamp}.zip"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notes")
    all_notes = cursor.fetchall()
    conn.close()
    
    notes_list = []
    for note in all_notes:
        notes_list.append({
            "id": note[0],
            "title": note[1],
            "content": note[2],
            "tags": note[3],
            "created_date": note[4],
            "status": note[5]
        })
    
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        json_content = json.dumps(notes_list, ensure_ascii=False, indent=2)
        zipf.writestr("all_notes.json", json_content)
        
        for note in all_notes:
            safe_title = "".join(c for c in note[1] if c.isalnum() or c in ' _-')[:50]
            md_content = f"# {note[1]}\n\n"
            md_content += f"**Дата:** {note[4]}\n"
            md_content += f"**Статус:** {note[5]}\n"
            md_content += f"**Теги:** {note[3]}\n\n"
            md_content += f"## Содержание\n\n{note[2]}\n"
            zipf.writestr(f"{safe_title}.md", md_content)
        
        zipf.write(DB_PATH, "backup.sqlite")
    
    print(f"✅ Экспортировано в {zip_name}")
    logging.info(f"Экспорт в ZIP: {zip_name}")


def import_from_zip():
    zip_name = input("Введите имя ZIP файла для импорта: ").strip()
    if not Path(zip_name).exists():
        print("Файл не найден")
        return
    
    with zipfile.ZipFile(zip_name, 'r') as zipf:
        if "all_notes.json" not in [f.filename for f in zipf.filelist]:
            print("Неверный формат: нет all_notes.json")
            return
        
        json_content = zipf.read("all_notes.json").decode('utf-8')
        notes_list = json.loads(json_content)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        imported = 0
        skipped = 0
        
        for note in notes_list:
            cursor.execute("""
                SELECT id FROM notes WHERE title = ? AND created_date = ?
            """, (note['title'], note['created_date']))
            if cursor.fetchone():
                skipped += 1
                continue
            
            cursor.execute("""
                INSERT INTO notes (title, content, tags, created_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (note['title'], note['content'], note['tags'], 
                  note['created_date'], note['status']))
            imported += 1
        
        conn.commit()
        conn.close()
    
    print(f"✅ Импортировано: {imported}, пропущено (дубликаты): {skipped}")
    logging.info(f"Импорт из {zip_name}: {imported} добавлено, {skipped} пропущено")


def main_menu():
    while True:
        print("\n" + "="*50)
        print("              NOTE FLOW")
        print("="*50)
        print("1.  Создать заметку")
        print("2.  Список заметок (сортировка/фильтр)")
        print("3.  Просмотреть заметку")
        print("4.  Редактировать заметку")
        print("5.  Удалить заметку")
        print("6.  Поиск по заметкам")
        print("7.  Все теги и статистика")
        print("8.  Старые черновики")
        print("9.  Резервное копирование")
        print("10. Экспорт в ZIP")
        print("11. Импорт из ZIP")
        print("0.  Выход")
        print("-"*50)
        
        choice = input("Ваш выбор: ").strip()
        
        if choice == "1":
            create_note()
        elif choice == "2":
            list_all_notes()
        elif choice == "3":
            view_note()
        elif choice == "4":
            edit_note()
        elif choice == "5":
            delete_note()
        elif choice == "6":
            search_notes()
        elif choice == "7":
            get_unique_tags()
        elif choice == "8":
            find_old_drafts()
        elif choice == "9":
            backup_db()
        elif choice == "10":
            export_to_zip()
        elif choice == "11":
            import_from_zip()
        elif choice == "0":
            print("\nДо свидания!")
            logging.info("Приложение завершено")
            break
        else:
            print("Неверный ввод")


if __name__ == "__main__":
    init_db()
    main_menu()