from flask import render_template, current_app as app

def register_error_handlers(app):
    @app.errorhandler(400)
    def handle_400(e):
        app.logger.error(f"400 Bad Request: {e}", exc_info=False)
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def handle_403(e):
        app.logger.error(f"403 Forbidden: {e}", exc_info=False)
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def handle_404(e):
        app.logger.error(f"404 Not Found: {e}", exc_info=False)
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def handle_429(e):
        app.logger.error(f"429 Too Many Requests: {e}", exc_info=False)
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.error(f"500 Internal Server Error: {e}", exc_info=True)
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
        return render_template("errors/500.html"), 500
