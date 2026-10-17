from flask import Flask, jsonify, send_from_directory
from pathlib import Path
from .config import Config
from .models import db
from .api.story import bp as story_bp
from .api.character import bp as character_bp
from .api.scriptboard import bp as scriptboard_bp
from .api.director import bp as director_bp
from .api.uploads import bp as uploads_bp
from .api.art import bp as art_bp
from .api.projects import bp as projects_bp
from .api.dsh import bp as dsh_bp
from .api.receipts import bp as receipts_bp
from .api.settings import bp as settings_bp
from .api.tools import bp as tools_bp
from .api.traffic import bp as traffic_bp

def create_app():
    # 持久化真源：data/*.json（services/disk_store 原子写 + services/repo 统一读）。
    # models.db 仅 LEGACY 建表兼容保留，不承载业务。
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(story_bp)
    app.register_blueprint(character_bp)
    app.register_blueprint(scriptboard_bp)
    app.register_blueprint(director_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(art_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(dsh_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(traffic_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"code": 0, "data": {"ok": True, "blueprints": ["story", "character", "scriptboard", "director", "uploads", "art", "projects", "dsh", "receipts", "settings", "tools", "traffic"]}})

    # 兼容别名：上传接口返回的都是 /api/images/<name>，而 uploads 蓝图实际挂在 /api/v1/images 下。
    # 新老数据都用 /api/images 取图，这里补一个直达路由（与蓝图同目录）。
    @app.get("/api/images/<name>")
    def serve_images(name):
        root = Path(__file__).resolve().parents[1] / "data" / "uploads"
        return send_from_directory(root, name)

    return app
