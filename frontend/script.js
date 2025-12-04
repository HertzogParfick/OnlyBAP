// Базовый URL API
const API_BASE_URL = 'http://localhost:8000';

// Общие функции для работы с данными
async function fetchData(endpoint, params = {}) {
    try {
        let url = `${API_BASE_URL}${endpoint}`;
        
        // Добавляем параметры, если они есть
        const queryParams = new URLSearchParams(params).toString();
        if (queryParams) {
            url += `?${queryParams}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching data:', error);
        throw error;
    }
}

// Функция для отображения сообщений об ошибках
function showError(message, elementId = 'errorMessage') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'block';
        errorElement.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
    } else {
        alert(message);
    }
}

// Функция для скрытия ошибок
function hideError(elementId = 'errorMessage') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.style.display = 'none';
    }
}

// Функция для форматирования даты
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Функция для получения статуса статьи с цветом
function getStatusBadge(status) {
    let badgeClass = '';
    let badgeText = status;
    
    switch(status) {
        case 'Черновик':
            badgeClass = 'badge bg-secondary';
            break;
        case 'На модерации':
            badgeClass = 'badge bg-warning text-dark';
            break;
        case 'Опубликовано':
            badgeClass = 'badge bg-success';
            break;
        default:
            badgeClass = 'badge bg-light text-dark';
    }
    
    return `<span class="${badgeClass}">${badgeText}</span>`;
}

// Функция для получения цвета активности
function getActivityLevel(articlesCount, commentsCount) {
    const score = articlesCount + (commentsCount / 10);
    
    if (score >= 20) return { level: 'Высокая', class: 'badge bg-success' };
    if (score >= 10) return { level: 'Средняя', class: 'badge bg-primary' };
    if (score >= 5) return { level: 'Низкая', class: 'badge bg-warning text-dark' };
    return { level: 'Минимальная', class: 'badge bg-secondary' };
}

// Функция для обрезки длинного текста
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Функция для создания элемента таблицы
function createTableCell(content, className = '') {
    const td = document.createElement('td');
    td.innerHTML = content;
    if (className) td.className = className;
    return td;
}

// Функция для создания строки таблицы
function createTableRow(cells) {
    const tr = document.createElement('tr');
    cells.forEach(cell => {
        if (typeof cell === 'string') {
            tr.appendChild(createTableCell(cell));
        } else {
            tr.appendChild(cell);
        }
    });
    return tr;
}

// Функция для загрузки авторов
let authorsCache = null;
async function loadAuthors() {
    if (authorsCache) return authorsCache;
    
    try {
        const authors = await fetchData('/authors/');
        authorsCache = authors;
        return authors;
    } catch (error) {
        console.error('Error loading authors:', error);
        return [];
    }
}

// Функция для загрузки категорий
let categoriesCache = null;
async function loadCategories() {
    if (categoriesCache) return categoriesCache;
    
    try {
        const categories = await fetchData('/categories/');
        categoriesCache = categories;
        return categories;
    } catch (error) {
        console.error('Error loading categories:', error);
        return [];
    }
}

// Функция для загрузки статей
let articlesCache = null;
async function loadArticles() {
    if (articlesCache) return articlesCache;
    
    try {
        const articles = await fetchData('/articles/');
        articlesCache = articles;
        return articles;
    } catch (error) {
        console.error('Error loading articles:', error);
        return [];
    }
}

// Инициализация страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчик для всех ссылок с подтверждением
    const links = document.querySelectorAll('a[data-confirm]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
    
    // Добавляем обработчик для всех кнопок с подтверждением
    const buttons = document.querySelectorAll('button[data-confirm]');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
                return false;
            }
        });
    });
});