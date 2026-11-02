# Инструкция по деплою Link Saver (Render, Railway, Vercel)

В данном руководстве подробно проанализированы три популярные платформы хостинга — **Railway**, **Render** и **Vercel** — с учетом специфики архитектуры проекта **Link Saver** (единый multi-stage `Dockerfile`, React 19 SPA, FastAPI, PostgreSQL, Alembic, системные зависимости `ffmpeg` и `nodejs`, а также потоковый стриминг 720p YouTube видео).

---

## 1. Сравнительный анализ платформ

| Критерий / Требование | **Railway** (Рекомендуется) | **Render** | **Vercel** |
|---|---|---|---|
| **Поддержка нашего `Dockerfile`** |  **Полная** (автоматический билд из репозитория) |  **Полная** (Docker Web Service) | ❌ **Нет** (только serverless / static) |
| **База данных PostgreSQL** |  Managed PostgreSQL в 1 клик, авто-связка переменной `DATABASE_URL` |  Managed PostgreSQL (бесплатный тариф на 90 дней, далее $7/мес) | ❌ Встроенного нет (только внешние: Neon, Supabase) |
| **Системные зависимости (`ffmpeg`, `nodejs`)** |  Поддерживаются внутри контейнера |  Поддерживаются внутри контейнера | ❌ Не поддерживаются в Serverless |
| **Потоковый стриминг видео (`StreamingResponse`)** |  Прямой chunked-стриминг без буферизации |  Поддерживается (без обрыва соединений) | ⚠️ Тайм-ауты функций (10–60 сек на Hobby/Pro), обрыв стриминга |
| **Холодный старт (Cold start)** | ⚡ Мгновенный отклик (контейнер не засыпает) | ⏳ Засыпает через 15 мин неактивности на Free (старт ~50 сек) | ⚡ Быстрый для статики, но бэкенд не развернуть |
| **Сложность настройки** | 🟢 **Минимальная** (единый стек в 1 клик) | 🟡 **Средняя** (настройка Web Service + Postgres) | 🔴 **Высокая** (требует разделения на 2 разных хостинга) |

###  Итоговый вердикт:
1. **Railway — Победитель и оптимальный выбор**:
   - Автоматически собирает наш единый `Dockerfile` (React SPA + FastAPI).
   - В один клик разворачивает managed PostgreSQL и сам прокидывает `DATABASE_URL`.
   - Не обрывает долгие загрузки 720p видео (в отличие от serverless-платформ).
2. **Render — Хорошая альтернатива**:
   - Имеет бесплатный тариф для Docker Web Service и базы PostgreSQL.
   - Минус бесплатного тарифа: «засыпает» при отсутствии трафика и база истекает через 90 дней.
3. **Vercel — Не подходит для единого контейнера**:
   - Vercel ориентирован на Jamstack и serverless Next.js/React.
   - Единый Dockerfile с FastAPI, ffmpeg, nodejs и непрерывным видеостримингом запустить на Vercel напрямую невозможно. Если использовать Vercel — придётся выносить фронтенд отдельно на Vercel, а бэкенд всё равно разворачивать на Railway/Render.

---

## 2. Пошаговый деплой на Railway (Рекомендуемый путь)

Railway позволяет запустить базу данных и приложение в рамках одного проекта.

### Шаг 2.1: Создание проекта и подключение репозитория
1. Зарегистрируйтесь на [railway.app](https://railway.com/) через GitHub.
2. Нажмите **«+ New Project»** $\rightarrow$ выберите **«Deploy from GitHub repo»**.
3. Выберите ваш репозиторий `AslanMurzalin/Assigment1.2`.
4. Railway автоматически обнаружит корневой `Dockerfile`.

### Шаг 2.2: Добавление базы данных PostgreSQL
1. В том же проекте на панели нажмите **«+ New»** $\rightarrow$ **«Database»** $\rightarrow$ **«Add PostgreSQL»**.
2. Railway за несколько секунд поднимет контейнер PostgreSQL 16.
3. Перейдите во вкладку **Variables** базы данных и скопируйте `DATABASE_URL` (или используйте системную переменную `${{Postgres.DATABASE_URL}}`).

### Шаг 2.3: Настройка переменных окружения Web-сервиса
Перейдите в созданный сервис приложения $\rightarrow$ вкладка **Variables** $\rightarrow$ добавьте:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=generate-a-strong-random-key-at-least-32-chars
BHAPI_TOKEN=ваш_токен_если_есть
BHAPI_BASE_URL=https://bhapi.ru
```

> **Примечание**: Railway автоматически передаёт переменную `PORT` в контейнер. Благодаря настройке `uvicorn app.main:app --port ${PORT:-8000}` сервер автоматически привяжется к назначенному порту.

### Шаг 2.4: Публикация публичного домена
1. Перейдите в **Settings** сервиса приложения.
2. В секции **Networking** нажмите **«Generate Domain»** (например, `linksaver-production.up.railway.app`).
3. Приложение готово! Alembic автоматически накатит миграции при старте, и вы получите работающий сервис по вашему URL.

---

## 3. Пошаговый деплой на Render

### Шаг 3.1: Создание PostgreSQL базы данных
1. Зарегистрируйтесь на [render.com](https://render.com/).
2. В Dashboard нажмите **«New +»** $\rightarrow$ **«PostgreSQL»**.
3. Заполните поля:
   - **Name**: `linksaver-db`
   - **Database**: `linksaver`
   - **User**: `postgres`
   - **Region**: Франкфурт (EU Central) или ближайший к вам
   - **Plan**: Free (или Starter)
4. Нажмите **«Create Database»**.
5. После создания скопируйте **«Internal Database URL»** (вида `postgresql://user:pass@dpg-xxx:5432/linksaver`).

### Шаг 3.2: Создание Docker Web Service
1. В Dashboard нажмите **«New +»** $\rightarrow$ **«Web Service»**.
2. Подключите ваш GitHub репозиторий `AslanMurzalin/Assigment1.2`.
3. В настройках сервиса:
   - **Language**: `Docker`
   - **Branch**: `main`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`
   - **Plan**: Free (или Starter)
4. В секции **Environment Variables** добавьте:
   ```env
   DATABASE_URL=вставьте_Internal_Database_URL_сюда
   SECRET_KEY=сгенерируйте_надежный_ключ
   BHAPI_TOKEN=опционально
   BHAPI_BASE_URL=https://bhapi.ru
   ```
5. Нажмите **«Create Web Service»**.

### Шаг 3.3 (Опционально): Использование `render.yaml` (Blueprint)
Вы можете создать в корне репозитория файл `render.yaml` для автоматического развертывания обоих сервисов через Render Blueprints:

```yaml
services:
  - type: web
    name: linksaver-app
    runtime: docker
    plan: free
    region: frankfurt
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: linksaver-postgres
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: BHAPI_TOKEN
        value: ""

databases:
  - name: linksaver-postgres
    databaseName: linksaver
    user: postgres
    plan: free
    region: frankfurt
```

---

## 4. Развертывание с разделением (Vercel + Backend)

Если вы обязательно хотите разместить фронтенд именно на **Vercel** (например, из-за глобального Edge CDN):

```mermaid
graph LR
    User["Пользователь"] -->|"Запросы к UI"| Vercel["Vercel (React 19 SPA)"]
    Vercel -->|"API / Видеопоток"| Backend["Railway / Render (FastAPI + Docker)"]
    Backend --> DB["PostgreSQL 16"]
```

### Шаг 4.1: Деплой бэкенда
1. Разверните бэкенд на **Railway** или **Render** по инструкциям выше.
2. Получите URL бэкенда (например, `https://linksaver-api.up.railway.app`).

### Шаг 4.2: Деплой фронтенда на Vercel
1. Войдите на [vercel.com](https://vercel.com/) $\rightarrow$ **«Add New Project»**.
2. Выберите репозиторий `AslanMurzalin/Assigment1.2`.
3. В конфигурации проекта:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. В **Environment Variables** укажите:
   ```env
   VITE_API_URL=https://linksaver-api.up.railway.app
   ```
5. Нажмите **«Deploy»**.

---

## 5. Справочник переменных окружения

| Переменная | Обязательная | Описание | Пример значения |
|---|---|---|---|
| `DATABASE_URL` | **Да** | DSN подключения к PostgreSQL (с драйвером `psycopg2`) | `postgresql+psycopg2://postgres:pass@db:5432/linksaver` |
| `SECRET_KEY` | **Да** | Секретный ключ для подписи JWT-токенов | `a8f5b2c9d3e1...` (32+ символа) |
| `PORT` | Нет | Порт веб-сервера (передаётся платформой автоматически) | `8000` (дефолт) |
| `BHAPI_TOKEN` | Нет | API токен для глубокого парсинга Ozon / WB | токен с `bhapi.ru` |
| `BHAPI_BASE_URL` | Нет | Базовый адрес API парсера маркетплейсов | `https://bhapi.ru` |

---

## 6. Проверка и валидация после деплоя

После развертывания выполните чек-лист проверки работоспособности:

1. **Health Check**:
   Откройте в браузере: `https://<ваш-домен>/health`
   Ожидаемый ответ: `{"status": "ok", "version": "1.0.0"}`

2. **OpenAPI / Swagger документация**:
   Откройте: `https://<ваш-домен>/docs`
   Все эндпоинты авторизации, ссылок и стриминга должны быть доступны.

3. **Работа SPA интерфейса**:
   Откройте корень сайта `https://<ваш-домен>/`. Должна открыться страница авторизации Link Saver.

4. **Проверка авторизации и базы данных**:
   Зарегистрируйте нового пользователя. Убедитесь, что сессия сохранилась и открылся дашборд.

5. **Тест видеостриминга (720p)**:
   Добавьте ссылку на YouTube (например, `https://www.youtube.com/watch?v=dQw4w9WgXcQ`).
   Нажмите **«Download (720p Stream)»** и убедитесь, что анимированный прогресс-бар отображает передачу данных и файл успешно скачивается на устройство.
