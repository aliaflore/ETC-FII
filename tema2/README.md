# Gaming Library Tracker (Flask + REST API)

Homework project for building a RESTful API and a web interface that consumes the same API.

## 1. Project Description

This application tracks video games from a personal library. It supports:
- viewing games and categories,
- adding games,
- updating complete game records,
- updating partial fields,
- deleting games.

Domain choice: personal hobby (gaming).

## 2. Architecture

The project has a simple 3-layer structure:
- **Presentation layer**: server-rendered HTML (`templates/index.html`) + JavaScript client (`static/app.js`) + CSS (`static/styles.css`).
- **API layer**: Flask routes under `/api/...` in `main.py`.
- **Data layer**: SQLite database (`hobby.db`) using SQLAlchemy models (`Game`, `Category`).

Flow:
1. Browser loads `/`.
2. Frontend JS calls REST endpoints (`/api/categories`, `/api/games`, etc.).
3. Flask validates data and reads/writes SQLite.
4. API returns JSON + proper HTTP status codes.

## 3. Database Structure

### Table: `categories`
- `id` (INTEGER, PK)
- `name` (VARCHAR(80), UNIQUE, NOT NULL)

### Table: `games`
- `id` (INTEGER, PK)
- `title` (VARCHAR(120), NOT NULL)
- `platform` (VARCHAR(80), NOT NULL)
- `genre` (VARCHAR(80), NOT NULL)
- `hours_played` (INTEGER, NOT NULL, default 0)
- `rating` (FLOAT, NULL, range 0..10 in API validation)
- `completed` (BOOLEAN, NOT NULL, default false)
- `category_id` (INTEGER, FK -> `categories.id`, NOT NULL)

Initial seeded data is inserted automatically on first run.

## 4. API Endpoints

Base URL: `http://127.0.0.1:5000`

### Categories
- `GET /api/categories`
	- Description: list all categories
	- Status: `200 OK`

### Games
- `GET /api/games`
	- Description: list all games
	- Query params:
		- `completed=true|false`
		- `category_id=<int>`
	- Status: `200 OK`, `400 Bad Request`

- `GET /api/games/<id>`
	- Description: get one game by ID
	- Status: `200 OK`, `404 Not Found`

- `POST /api/games`
	- Description: create a game
	- Required JSON fields:
		- `title` (string)
		- `platform` (string)
		- `genre` (string)
		- `hours_played` (int >= 0)
		- `completed` (bool)
		- `category_id` (int, existing category)
	- Optional JSON field:
		- `rating` (null or number 0..10)
	- Status: `201 Created`, `400 Bad Request`, `404 Not Found`

- `PUT /api/games/<id>`
	- Description: replace full game resource
	- Body: same structure as POST (all required)
	- Status: `200 OK`, `400 Bad Request`, `404 Not Found`

- `PATCH /api/games/<id>`
	- Description: partial update
	- Body: one or more valid fields from game resource
	- Status: `200 OK`, `400 Bad Request`, `404 Not Found`

- `DELETE /api/games/<id>`
	- Description: delete a game
	- Status: `204 No Content`, `404 Not Found`

## 5. Postman Testing

In Postman, create a collection named `Gaming Library Tracker` and add one request per endpoint:

1. `GET /api/categories`
2. `GET /api/games`
3. `GET /api/games/1`
4. `POST /api/games`
5. `PUT /api/games/1`
6. `PATCH /api/games/1`
7. `DELETE /api/games/<newly_created_id>`

Recommended for presentation:
- include screenshot(s) from Postman for each request,
- include at least one error-case test (e.g. invalid `category_id`, invalid body).

A ready-to-import collection is included in `postman_collection.json`.

## 6. How To Run (using `uv`)

From the `tema2` folder:

```powershell
uv sync
uv run python main.py
```

Open:
- Web UI: `http://127.0.0.1:5000/`
- API base: `http://127.0.0.1:5000/api`

### Optional quick API check from terminal

```powershell
curl http://127.0.0.1:5000/api/games
```

## Project Files

- `main.py`: Flask app, models, DB init/seed, API routes
- `templates/index.html`: web interface
- `static/app.js`: frontend logic (API calls + CRUD operations)
- `static/styles.css`: styles
- `pyproject.toml`: project metadata and dependencies (managed by `uv`)
- `postman_collection.json`: Postman collection with requests for all endpoints
