# Vault — лабораторная работа №2 (Python)

Мини-сервис управления пользователями и OAuth-клиентами. Реализованы FastAPI, SQLAlchemy 2.x, Alembic, Ariadne (GraphQL schema-first), JWT HS256, Argon2id с pepper, zxcvbn, аудит и SPA-админка на vanilla JS. **Полноценный OAuth2/OIDC пока не реализован** — это следующий этап по методичке.

## Запуск на Windows (PowerShell, Python 3.11+)

```powershell
cd lab2_vault
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Измените в `.env` значения `JWT_SECRET` и `PASSWORD_PEPPER` на **две независимые длинные случайные строки**. Для генерации можно выполнить `python -c "import secrets; print(secrets.token_urlsafe(48))"` дважды. Не выкладывайте `.env` в Git.

```powershell
alembic upgrade head
python run.py
```

Открыть: <http://127.0.0.1:8000/admin/> — админка; <http://127.0.0.1:8000/graphql> — GraphQL explorer; <http://127.0.0.1:8000/docs> — REST Swagger; <http://127.0.0.1:8000/health> — проверка.

## Регистрация первого администратора

Зарегистрировать пользователя через `POST /auth/register` в Swagger `/docs`, например:

```json
{"email":"admin@example.com","password":"River!Sunset83?Marble#Omega"}
```

Затем **остановить сервер не требуется**, открыть вторую PowerShell в директории проекта с активированным окружением и выполнить:

```powershell
python create_admin.py admin@example.com
```

После этого авторизоваться на `/admin/` под этим аккаунтом и создавать клиентов. Обычным пользователям GraphQL `clients`, `users` и `auditEvents` недоступны.

## REST и GraphQL

REST: `POST /auth/register`, `POST /auth/login`, `GET /auth/me` (Bearer JWT). В GraphQL схемe определены `me`, `users`, `clients`, `auditEvents`, `registerUser`, `createClient`, `disableUser`; доступ ограничен директивами `@isAuthenticated` и `@isAdmin`.

Пример запроса c заголовком `Authorization: Bearer <token>`:

```graphql
query { me { id email isAdmin } }
```

Пример ожидаемого ответа:

```json
{"data":{"me":{"id":"1","email":"admin@example.com","isAdmin":true}}}
```

Мутация создания клиента (только admin):

```graphql
mutation { createClient(name:"Demo App", isConfidential:false) { clientId name redirectUris } }
```

## Тестирование

```powershell
pytest -v
```

Тесты используют отдельную SQLite-базу `test_vault.db`, которую создают и удаляют самостоятельно. Проверяются пароли, REST-аутентификация, аудит и GraphQL-ограничения доступа.

## Структура

- `app/config.py` — конфигурация через `.env`;
- `app/db/` — движок, сессии, декларативная база;
- `app/models/` — три таблицы `users`, `oauth_clients`, `audit_events`;
- `app/core/` — JWT, парольная политика, FastAPI-зависимости;
- `app/auth/` — REST-маршруты регистрации и входа;
- `app/graphql/` — SDL, резолверы, директивы, контекст;
- `app/audit/` — запись бизнес-событий;
- `app/static/` — админка HTML/JS;
- `alembic/versions/` — версионированная миграция;
- `tests/` — pytest;
- `run.py` — запуск Uvicorn;
- `create_admin.py` — назначение первого администратора вручную.

## GitHub

```powershell
git init
git add .
git commit -m "Implement Vault GraphQL lab"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/lab2_vault.git
git push -u origin main
```

Сначала создайте пустой репозиторий на GitHub и замените `YOUR_USERNAME`. `.gitignore` исключает секреты `.env`, SQLite БД, временные файлы и виртуальное окружение. Публикация на GitHub требует вашего аккаунта и выполняется отдельно.

## Примечания

- Для локальной учебной работы используется SQLite; в `.env.example` — исключительно демонстрационные секреты.
- JWT хранятся в `localStorage` только для простой учебной SPA; для production стоит рассмотреть более строгую браузерную модель защиты токенов.
- Миграции выполняются командой `alembic upgrade head`, не вызовом `Base.metadata.create_all()` из приложения.
