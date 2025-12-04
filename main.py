# Импорт необходимых библиотек
from fastapi import FastAPI, Query
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from enum import Enum
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import json

#НАСТРОЙКА ЛОГИРОВАНИЯ
# Конфигурация логирования для отслеживания работы приложения
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#СОЗДАНИЕ ПРИЛОЖЕНИЯ FASTAPI
# Инициализация FastAPI приложения с метаданными
app = FastAPI(title="Blog Admin Panel", description="API for managing blog content")

#НАСТРОЙКА CORS
# Настройка политики CORS для взаимодействия с frontend приложениями
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],  # Разрешенные домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP методы
    allow_headers=["*"],  # Разрешить все заголовки
)

#КЛАСС ДЛЯ СЕРИАЛИЗАЦИИ JSON
# Кастомный JSON-кодер для корректной обработки ObjectId MongoDB
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)  # Преобразуем ObjectId в строку
        return json.JSONEncoder.default(self, o)

#ФУНКЦИИ ДЛЯ РАБОТЫ С ObjectId
# Рекурсивная функция для конвертации всех ObjectId в строки
def convert_objectid(data):
    if isinstance(data, list):
        return [convert_objectid(item) for item in data]
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, list):
                data[key] = convert_objectid(value)
            elif isinstance(value, dict):
                data[key] = convert_objectid(value)
    return data

#ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ MONGODB
try:
    # Создание подключения к MongoDB (локальный сервер по умолчанию)
    client = MongoClient("mongodb://localhost:27017/")
    db = client["blog_admin_db"]  # Выбор базы данных
    logger.info("Connected to MongoDB successfully")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

#МОДЕЛИ ДАННЫХ

# Enum для статусов статей (используется для валидации)
class ArticleStatus(str, Enum):
    DRAFT = "Черновик"
    MODERATION = "На модерации"
    PUBLISHED = "Опубликовано"

# Модель автора статьи
class Author(BaseModel):
    full_name: str  # Полное имя автора
    email: str  # Email автора
    registration_date: datetime = Field(default_factory=datetime.now)  # Дата регистрации (автоматически)

# Модель категории статьи
class Category(BaseModel):
    name: str  # Название категории
    description: Optional[str] = None  # Описание категории (необязательное)

# Модель статьи
class Article(BaseModel):
    title: str  # Заголовок статьи
    content: str  # Содержимое статьи
    author_id: str  # ID автора (ссылка на коллекцию авторов)
    category_id: str  # ID категории (ссылка на коллекцию категорий)
    status: ArticleStatus = ArticleStatus.DRAFT  # Статус статьи (по умолчанию "Черновик")
    created_at: datetime = Field(default_factory=datetime.now)  # Дата создания
    updated_at: datetime = Field(default_factory=datetime.now)  # Дата последнего обновления
    published_at: Optional[datetime] = None  # Дата публикации (только для опубликованных статей)
    
    # Валидатор, выполняющийся перед созданием модели
    @model_validator(mode='before')
    @classmethod
    def validate_published_at_before(cls, data):
        """Валидация даты публикации перед созданием модели"""
        if isinstance(data, dict):
            status = data.get('status')
            published_at = data.get('published_at')
            
            # Правило 1: Если статус не "Опубликовано", published_at должен быть None
            if status != ArticleStatus.PUBLISHED and published_at is not None:
                data['published_at'] = None
            
            # Правило 2: Если статус "Опубликовано" и нет даты публикации, устанавливаем текущее время
            if status == ArticleStatus.PUBLISHED and published_at is None:
                data['published_at'] = datetime.now()
        
        return data
    
    # Валидатор, выполняющийся после создания модели
    @model_validator(mode='after')
    def validate_published_at_after(self):
        """Дополнительная валидация после создания модели"""
        if self.published_at is not None and self.status != ArticleStatus.PUBLISHED:
            raise ValueError('Дата публикации может быть установлена только для опубликованных статей')
        
        if self.status == ArticleStatus.PUBLISHED and self.published_at is None:
            self.published_at = datetime.now()
        
        return self

# Модель комментария
class Comment(BaseModel):
    article_id: str  # ID статьи, к которой относится комментарий
    author_name: str  # Имя автора комментария
    content: str  # Текст комментария
    created_at: datetime = Field(default_factory=datetime.now)  # Дата создания
    is_approved: bool = False  # Флаг одобрения комментария модератором

#ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ

# Функция для рекурсивного преобразования ObjectId в строки
def to_str(data):
    if isinstance(data, list):
        return [to_str(item) for item in data]
    if isinstance(data, dict):
        return {k: str(v) if isinstance(v, ObjectId) else to_str(v) for k, v in data.items()}
    return data

#API ЭНДПОИНТЫ
#ЭНДПОИНТЫ ДЛЯ РАБОТЫ С АВТОРАМИ

# Создание нового автора
@app.post("/authors/")
def create_author(author: Author):
    # Проверка на существующего автора
    existing_author = db.authors.find_one({
        "full_name": author.full_name,
        "email": author.email
    })
    
    if existing_author:
        return {"error": "Author already exists", "id": str(existing_author["_id"])}
    
    # Вставка нового автора в коллекцию
    result = db.authors.insert_one(author.dict())
    return {"id": str(result.inserted_id)}

# Получение списка всех авторов
@app.get("/authors/")
def get_authors():
    authors = list(db.authors.find())
    return to_str(authors)

#ЭНДПОИНТЫ ДЛЯ РАБОТЫ С КАТЕГОРИЯМИ

# Создание новой категории
@app.post("/categories/")
def create_category(category: Category):
    # Проверка на существующую категорию
    existing_category = db.categories.find_one({
        "name": category.name
    })
    
    if existing_category:
        return {"error": "Category already exists", "id": str(existing_category["_id"])}
    
    result = db.categories.insert_one(category.dict())
    return {"id": str(result.inserted_id)}

# Получение списка всех категорий
@app.get("/categories/")
def get_categories():
    categories = list(db.categories.find())
    return to_str(categories)

#ЭНДПОИНТЫ ДЛЯ РАБОТЫ СО СТАТЬЯМИ

# Создание новой статьи
@app.post("/articles/")
def create_article(article: Article):
    # Проверка на существующую статью
    existing_article = db.articles.find_one({
        "title": article.title,
        "author_id": article.author_id
    })
    
    if existing_article:
        return {"error": "Article with this title by this author already exists", "id": str(existing_article["_id"])}
    
    article_dict = article.dict()
    # Устанавливаем дату публикации только если статус "Опубликовано"
    if article.status == ArticleStatus.PUBLISHED:
        article_dict["published_at"] = datetime.now()
    else:
        article_dict["published_at"] = None
    
    result = db.articles.insert_one(article_dict)
    return {"id": str(result.inserted_id)}

# Частичное обновление статьи (только статус)
@app.put("/articles/{article_id}")
def update_article(article_id: str, article_data: dict):
    try:
        # Проверяем, существует ли статья
        existing_article = db.articles.find_one({"_id": ObjectId(article_id)})
        if not existing_article:
            return {"error": "Article not found"}
        
        # Обновляем только указанные поля
        update_data = {}
        
        if "status" in article_data:
            update_data["status"] = article_data["status"]
            update_data["updated_at"] = datetime.now()
            
            # Если статус меняется на "Опубликовано", устанавливаем дату публикации
            if article_data["status"] == "Опубликовано" and not existing_article.get("published_at"):
                update_data["published_at"] = datetime.now()
        
        # Выполняем обновление в MongoDB
        result = db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": update_data}
        )
        
        return {"success": True, "modified_count": result.modified_count}
        
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {str(e)}")
        return {"error": str(e)}

# Полное обновление статьи (все поля)
@app.put("/articles/{article_id}/full")
def update_article_full(article_id: str, article_data: dict):
    try:
        # Проверяем, существует ли статья
        existing_article = db.articles.find_one({"_id": ObjectId(article_id)})
        if not existing_article:
            return {"error": "Article not found"}
        
        # Подготовка данных для обновления
        update_data = {}
        
        # Обновляем только переданные поля (кроме _id)
        allowed_fields = ['title', 'content', 'author_id', 'category_id', 'status']
        for field in allowed_fields:
            if field in article_data:
                update_data[field] = article_data[field]
        
        # Обновляем дату изменения
        update_data["updated_at"] = datetime.now()
        
        # Обработка даты публикации в зависимости от статуса
        if 'status' in update_data and update_data['status'] == "Опубликовано":
            if not existing_article.get("published_at"):
                update_data["published_at"] = datetime.now()
        elif 'status' in update_data and existing_article.get("status") == "Опубликовано":
            update_data["published_at"] = None
        
        # Выполняем обновление
        result = db.articles.update_one(
            {"_id": ObjectId(article_id)},
            {"$set": update_data}
        )
        
        return {"success": True, "modified_count": result.modified_count}
        
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {str(e)}")
        return {"error": str(e)}

# Получение списка статей с фильтрацией
@app.get("/articles/")
def get_articles(
    status: Optional[ArticleStatus] = Query(None),  # Фильтр по статусу
    author_id: Optional[str] = Query(None),         # Фильтр по автору
    category_id: Optional[str] = Query(None)        # Фильтр по категории
):
    query = {}
    
    if status:
        query["status"] = status.value
    
    if author_id:
        query["author_id"] = author_id
    
    if category_id:
        query["category_id"] = category_id
    
    # Получаем статьи с сортировкой по дате создания (новые первыми)
    articles = list(db.articles.find(query).sort("created_at", -1))
    
    # Добавляем информацию об авторе и категории 
    for article in articles:
        # Получаем автора
        author = db.authors.find_one({"_id": ObjectId(article["author_id"])})
        article["author_name"] = author["full_name"] if author else "Неизвестно"
        
        # Получаем категорию
        category = db.categories.find_one({"_id": ObjectId(article["category_id"])})
        article["category_name"] = category["name"] if category else "Неизвестно"
    
    return to_str(articles)

# Получение конкретной статьи по ID
@app.get("/articles/{article_id}")
def get_article(article_id: str):
    article = db.articles.find_one({"_id": ObjectId(article_id)})
    if not article:
        return {"error": "Article not found"}
    
    # Добавляем информацию об авторе и категории
    author = db.authors.find_one({"_id": ObjectId(article["author_id"])})
    article["author_name"] = author["full_name"] if author else "Неизвестно"
    
    category = db.categories.find_one({"_id": ObjectId(article["category_id"])})
    article["category_name"] = category["name"] if category else "Неизвестно"
    
    return to_str(article)

#ЭНДПОИНТЫ ДЛЯ РАБОТЫ С КОММЕНТАРИЯМИ
# Создание нового комментария
@app.post("/comments/")
def create_comment(comment: Comment):
    # Проверка на существующий комментарий
    existing_comment = db.comments.find_one({
        "article_id": comment.article_id,
        "author_name": comment.author_name,
        "content": comment.content
    })
    
    if existing_comment:
        return {"error": "Similar comment already exists", "id": str(existing_comment["_id"])}
    
    result = db.comments.insert_one(comment.dict())
    return {"id": str(result.inserted_id)}

# Одобрение комментария
@app.put("/comments/{comment_id}/approve")
def approve_comment(comment_id: str):
    result = db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"is_approved": True}}
    )
    return {"modified_count": result.modified_count}

# Отмена одобрения комментария
@app.put("/comments/{comment_id}/unapprove")
def unapprove_comment(comment_id: str):
    result = db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"is_approved": False}}
    )
    return {"modified_count": result.modified_count}

# Получение комментариев с фильтрацией
@app.get("/comments/")
def get_comments(
    article_id: Optional[str] = Query(None),  # Фильтр по статье
    is_approved: Optional[bool] = Query(None) # Фильтр по статусу одобрения
):
    query = {}
    
    if article_id:
        query["article_id"] = article_id
    
    if is_approved is not None:
        query["is_approved"] = is_approved
    
    comments = list(db.comments.find(query).sort("created_at", -1))
    
    # Добавляем информацию о статье для каждого комментария
    for comment in comments:
        article = db.articles.find_one({"_id": ObjectId(comment["article_id"])})
        comment["article_title"] = article["title"] if article else "Неизвестно"
    
    return to_str(comments)

# Удаление комментария
@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: str):
    try:
        # Проверяем, существует ли комментарий
        comment = db.comments.find_one({"_id": ObjectId(comment_id)})
        if not comment:
            return {"error": "Comment not found", "deleted_count": 0}
        
        # Удаляем комментарий
        result = db.comments.delete_one({"_id": ObjectId(comment_id)})
        
        if result.deleted_count > 0:
            return {"success": True, "deleted_count": result.deleted_count}
        else:
            return {"error": "Failed to delete comment", "deleted_count": 0}
            
    except Exception as e:
        logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        return {"error": str(e), "deleted_count": 0}

#СВОДНЫЕ ТАБЛИЦЫ (АНАЛИТИКА)

# 1. Управление контентом: список статей с расширенной информацией
@app.get("/content-management/")
def get_content_management():
    try:
        articles = list(db.articles.find())
        
        result = []
        for article in articles:
            # Получаем автора
            author = None
            if "author_id" in article:
                try:
                    author = db.authors.find_one({"_id": ObjectId(article["author_id"])})
                except:
                    author = None
            
            # Получаем категорию
            category = None
            if "category_id" in article:
                try:
                    category = db.categories.find_one({"_id": ObjectId(article["category_id"])})
                except:
                    category = None
            
            # Формируем запись для таблицы управления контентом
            result.append({
                "_id": str(article.get("_id", "")),
                "title": article.get("title", "Без названия"),
                "author_name": author.get("full_name", "Неизвестно") if author else "Неизвестно",
                "category_name": category.get("name", "Без категории") if category else "Без категории",
                "status": article.get("status", "Не указан"),
                "created_at": article.get("created_at"),
                "published_at": article.get("published_at")
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in content-management: {str(e)}")
        return {"error": str(e)}

# 2. Активность авторов: статистика по каждому автору
@app.get("/author-activity/")
def get_author_activity():
    try:
        # Агрегационный запрос для подсчета опубликованных статей
        articles_pipeline = [
            {"$match": {"status": ArticleStatus.PUBLISHED.value}},
            {
                "$group": {
                    "_id": "$author_id",
                    "published_articles_count": {"$sum": 1}
                }
            }
        ]
        
        # Агрегационный запрос для подсчета комментариев к статьям автора
        comments_pipeline = [
            {
                "$addFields": {
                    "article_object_id": {"$toObjectId": "$article_id"}
                }
            },
            {
                "$lookup": {
                    "from": "articles",
                    "localField": "article_object_id",
                    "foreignField": "_id",
                    "as": "article"
                }
            },
            {"$unwind": "$article"},
            {
                "$group": {
                    "_id": "$article.author_id",
                    "total_comments_count": {"$sum": 1}
                }
            }
        ]
        
        published_articles = list(db.articles.aggregate(articles_pipeline))
        comments_by_author = list(db.comments.aggregate(comments_pipeline))
        
        # Преобразуем в словари поиска
        articles_dict = {str(item["_id"]): item["published_articles_count"] for item in published_articles}
        comments_dict = {str(item["_id"]): item["total_comments_count"] for item in comments_by_author}
        
        # Получаем всех авторов
        authors = list(db.authors.find())
        
        # Формируем результат
        result = []
        for author in authors:
            author_id = str(author["_id"])
            result.append({
                "author_name": author["full_name"],
                "published_articles_count": articles_dict.get(author_id, 0),
                "total_comments_count": comments_dict.get(author_id, 0),
                "email": author.get("email", ""),
                "registration_date": author.get("registration_date")
            })
        
        return to_str(result)
        
    except Exception as e:
        logger.error(f"Error in author-activity: {str(e)}")
        return {"error": str(e)}

#СТАТИСТИКА

# Общая статистика блога
@app.get("/statistics/")
def get_statistics():
    try:
        # Подсчет основных метрик
        total_articles = db.articles.count_documents({})
        total_published = db.articles.count_documents({"status": "Опубликовано"})
        total_moderation = db.articles.count_documents({"status": "На модерации"})
        total_drafts = db.articles.count_documents({"status": "Черновик"})
        total_authors = db.authors.count_documents({})
        total_comments = db.comments.count_documents({})
        total_approved_comments = db.comments.count_documents({"is_approved": True})
        
        # Статистика по категориям
        categories_stats = []
        categories = list(db.categories.find())
        
        for category in categories:
            count = db.articles.count_documents({"category_id": str(category["_id"])})
            categories_stats.append({
                "_id": category.get("name", "Без названия"),
                "count": count
            })
        
        # Статьи без категории
        uncategorized_count = db.articles.count_documents({
            "$or": [
                {"category_id": {"$exists": False}},
                {"category_id": ""},
                {"category_id": None}
            ]
        })
        
        if uncategorized_count > 0:
            categories_stats.append({
                "_id": "Без категории",
                "count": uncategorized_count
            })
        
        # Возвращаем все собранные статистические данные
        return {
            "total_articles": total_articles,
            "total_published": total_published,
            "total_moderation": total_moderation,
            "total_drafts": total_drafts,
            "total_authors": total_authors,
            "total_comments": total_comments,
            "total_approved_comments": total_approved_comments,
            "categories_distribution": categories_stats,
            "published_percentage": round((total_published / total_articles * 100) if total_articles > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"Error in statistics: {str(e)}")
        return {"error": str(e)}

#ПОИСК

# Универсальный поиск по контенту
@app.get("/search/")
def search_content(
    query: str = Query(..., min_length=2),  # Поисковый запрос (минимум 2 символа)
    search_in: str = Query("all", regex="^(all|articles|comments)$")  # Где искать
):
    results = {}
    
    # Поиск в статьях
    if search_in in ["all", "articles"]:
        articles_query = {
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},  # Поиск в заголовке
                {"content": {"$regex": query, "$options": "i"}}  # Поиск в содержимом
            ]
        }
        articles = list(db.articles.find(articles_query).limit(10))
        
        # Добавляем информацию об авторе
        for article in articles:
            author = db.authors.find_one({"_id": ObjectId(article["author_id"])})
            article["author_name"] = author["full_name"] if author else "Неизвестно"
        
        results["articles"] = to_str(articles)
    
    # Поиск в комментариях
    if search_in in ["all", "comments"]:
        comments_query = {
            "content": {"$regex": query, "$options": "i"}
        }
        comments = list(db.comments.find(comments_query).limit(10))
        
        # Добавляем информацию о статье
        for comment in comments:
            article = db.articles.find_one({"_id": ObjectId(comment["article_id"])})
            comment["article_title"] = article["title"] if article else "Неизвестно"
        
        results["comments"] = to_str(comments)
    
    return results

#ЗАПУСК СЕРВЕРА

if __name__ == "__main__":
    # Запуск сервера Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Сервер доступен на всех сетевых интерфейсах