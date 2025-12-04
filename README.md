# OnlyBAP — Админ-панель блога

**OnlyBAP (Blog Admin Panel)** — это веб‑приложение для ведения статей, управления авторами, категориями, комментариями и базовой статистикой активности. Backend написан на **Python 3.10** с использованием **FastAPI**, а в качестве базы данных используется **MongoDB**. Веб‑интерфейс (frontend) состоит из HTML‑страниц.

---

## Возможности

### Веб‑интерфейс (папка `frontend/`)
- Просмотр списка статей
- Просмотр активности конкретного автора
- Просмотр и модерация комментариев
- Управление контентом
- Просмотр статистики публикаций

### API (Swagger UI)
Ниже перечислены основные доступные эндпоинты.

#### **Статьи**
- `GET /articles` — получить список всех статей
- `POST /articles` — создать новую статью
- `PUT /articles/{article_id}` — обновить статью (только id)
- `PUT /articles/{article_id}/full` — обновить статью

#### **Авторы**
- `GET /authors` — получить список авторов
- `POST /authors` — создать автора
- `GET /author-activity/` — получить активность авторов

#### **Категории**
- `GET /categories` — получить список категорий
- `POST /categories` — создать категорию

#### **Комментарии**
- `GET /comments` — получить все комментарии
- `POST /comments` — добавить комментарий к статье
- `PUT /comments/approve/{comment_id}` — одобрить комментарий
- `PUT /comments/unapprove/{comment_id}` — вернуть комментарий на модерацию
- `DELETE /comments/{comment_id}` — удалить комментарий

#### **Статистика**
- `GET /statistics/` — получить общую статистику

---

## Сборка и запуск

1. Установите и запустите **MongoDB**.
2. Склонируйте или распакуйте проект в удобную директорию.
3. Установите необходимые зависимости Python:
   ```bash
   pip install fastapi uvicorn pymongo pydantic
   ```
4. Запустите MongoDB, если он ещё не запущен.
5. Для запуска backend откройте консоль и последовательно введите:
   ```bash
   cd <путь к папке, где находиться файл main.py>
   python main.py

   Пример:
   cd C:\bap
   python main.py
   ```
6. Для запуска frontend откройте консоль в новом окне (консоль с backend НЕ закрывать!) и последовательно введите:
   ```bash
   cd <путь к папке, где находяться файлы фронтенда>
   python -m http.server 8080

   Пример:
   cd C:\bap\frontend
   python -m http.server 8080
   ```
7. Не закрывая консоли, откройте в браузере:
   - Веб-интерфейс: `http://localhost:8080/index.html`
   - Swagger UI: `http://localhost:8000/docs`
---

## Требования
- **ОС:** Windows или любая система, поддерживающая Python
- **Язык:** Python 3.10
- **База данных:** MongoDB
- **Необходимые библиотеки:** fastapi, uvicorn, pymongo, pydantic
- Все файлы проекта должны находиться в одной директории

---

## Структура проекта
```
├── main.py             # Backend
├── frontend/           # Frontend
│   ├── index.html
│   ├── articles.html
│   ├── comments.html
│   ├── author-activity.html
│   ├── statistics.html
│   ├── content-management.html
│   ├── style.css
│   ├── warhammer.jpg
│   └── script.js
```
