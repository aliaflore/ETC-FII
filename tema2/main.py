from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "hobby.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    games = db.relationship("Game", back_populates="category", lazy=True)

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class Game(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    platform = db.Column(db.String(80), nullable=False)
    genre = db.Column(db.String(80), nullable=False)
    hours_played = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    category = db.relationship("Category", back_populates="games")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "platform": self.platform,
            "genre": self.genre,
            "hours_played": self.hours_played,
            "rating": self.rating,
            "completed": self.completed,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
        }


def _seed_database() -> None:
    if Category.query.first() is not None:
        return

    categories = [
        Category(name="Action"),
        Category(name="RPG"),
        Category(name="Strategy"),
        Category(name="Indie"),
    ]
    db.session.add_all(categories)
    db.session.flush()

    games = [
        Game(
            title="Hades",
            platform="PC",
            genre="Roguelike",
            hours_played=42,
            rating=9.4,
            completed=True,
            category_id=categories[3].id,
        ),
        Game(
            title="The Witcher 3",
            platform="PC",
            genre="Open World RPG",
            hours_played=110,
            rating=9.8,
            completed=True,
            category_id=categories[1].id,
        ),
        Game(
            title="Civilization VI",
            platform="PC",
            genre="Turn-Based Strategy",
            hours_played=85,
            rating=8.9,
            completed=False,
            category_id=categories[2].id,
        ),
    ]
    db.session.add_all(games)
    db.session.commit()


def initialize_database() -> None:
    db.create_all()
    _seed_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/categories")
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify([category.to_dict() for category in categories]), 200


@app.get("/api/games")
def get_games():
    query = Game.query

    completed_filter = request.args.get("completed")
    category_filter = request.args.get("category_id")

    if completed_filter is not None:
        normalized = completed_filter.strip().lower()
        if normalized in {"true", "1", "yes"}:
            query = query.filter(Game.completed.is_(True))
        elif normalized in {"false", "0", "no"}:
            query = query.filter(Game.completed.is_(False))
        else:
            return (
                jsonify({"error": "Invalid value for 'completed'. Use true or false."}),
                400,
            )

    if category_filter is not None:
        if not category_filter.isdigit():
            return (
                jsonify(
                    {"error": "Invalid value for 'category_id'. Must be an integer."}
                ),
                400,
            )
        query = query.filter(Game.category_id == int(category_filter))

    games = query.order_by(Game.id).all()
    return jsonify([game.to_dict() for game in games]), 200


@app.get("/api/games/<int:game_id>")
def get_game(game_id: int):
    game = db.session.get(Game, game_id)
    if game is None:
        return jsonify({"error": "Game not found."}), 404
    return jsonify(game.to_dict()), 200


def _validate_game_payload(
    payload: dict, *, partial: bool = False
) -> tuple[dict | None, tuple | None]:
    if payload is None:
        return None, (jsonify({"error": "Request body must be JSON."}), 400)

    required_fields = {
        "title",
        "platform",
        "genre",
        "hours_played",
        "completed",
        "category_id",
    }
    if not partial:
        missing = [field for field in required_fields if field not in payload]
        if missing:
            return None, (
                jsonify({"error": f"Missing fields: {', '.join(missing)}"}),
                400,
            )

    allowed_fields = required_fields | {"rating"}
    cleaned: dict = {}

    for key, value in payload.items():
        if key not in allowed_fields:
            return None, (jsonify({"error": f"Unknown field: {key}"}), 400)

        if key in {"title", "platform", "genre"}:
            if not isinstance(value, str) or not value.strip():
                return None, (
                    jsonify({"error": f"'{key}' must be a non-empty string."}),
                    400,
                )
            cleaned[key] = value.strip()

        elif key == "hours_played":
            if not isinstance(value, int) or value < 0:
                return None, (
                    jsonify(
                        {"error": "'hours_played' must be a non-negative integer."}
                    ),
                    400,
                )
            cleaned[key] = value

        elif key == "completed":
            if not isinstance(value, bool):
                return None, (jsonify({"error": "'completed' must be a boolean."}), 400)
            cleaned[key] = value

        elif key == "category_id":
            if not isinstance(value, int):
                return None, (
                    jsonify({"error": "'category_id' must be an integer."}),
                    400,
                )
            category = db.session.get(Category, value)
            if category is None:
                return None, (jsonify({"error": "Category not found."}), 404)
            cleaned[key] = value

        elif key == "rating":
            if value is None:
                cleaned[key] = None
            elif isinstance(value, (int, float)) and 0 <= float(value) <= 10:
                cleaned[key] = float(value)
            else:
                return None, (
                    jsonify(
                        {"error": "'rating' must be null or a number between 0 and 10."}
                    ),
                    400,
                )

    return cleaned, None


@app.post("/api/games")
def create_game():
    payload = request.get_json(silent=True)
    data, error = _validate_game_payload(payload, partial=False)
    if error:
        return error

    game = Game(**data)
    db.session.add(game)
    db.session.commit()
    return jsonify(game.to_dict()), 201


@app.put("/api/games/<int:game_id>")
def replace_game(game_id: int):
    game = db.session.get(Game, game_id)
    if game is None:
        return jsonify({"error": "Game not found."}), 404

    payload = request.get_json(silent=True)
    data, error = _validate_game_payload(payload, partial=False)
    if error:
        return error

    for key, value in data.items():
        setattr(game, key, value)

    db.session.commit()
    return jsonify(game.to_dict()), 200


@app.patch("/api/games/<int:game_id>")
def update_game(game_id: int):
    game = db.session.get(Game, game_id)
    if game is None:
        return jsonify({"error": "Game not found."}), 404

    payload = request.get_json(silent=True)
    data, error = _validate_game_payload(payload, partial=True)
    if error:
        return error

    if not data:
        return jsonify({"error": "No fields provided for update."}), 400

    for key, value in data.items():
        setattr(game, key, value)

    db.session.commit()
    return jsonify(game.to_dict()), 200


@app.delete("/api/games/<int:game_id>")
def delete_game(game_id: int):
    game = db.session.get(Game, game_id)
    if game is None:
        return jsonify({"error": "Game not found."}), 404

    db.session.delete(game)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True)
