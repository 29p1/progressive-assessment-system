from flask import Flask, render_template, session

from .config import Config
from .db import get_db, init_db
from .services.user_service import get_user_by_id


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    init_db(app)

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.context_processor
    def inject_current_user():
        user = None
        if session.get("user_id"):
            user = get_user_by_id(get_db(app), session["user_id"])
        return {"current_user": user}

    return app
