from flask import current_app, render_template, request


def register_errors(app):
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        original = getattr(e, "original_exception", None)
        if original is not None:
            current_app.logger.error(
                "Error 500 en %s %s (%s)",
                request.method,
                request.path,
                type(original).__name__,
            )
        else:
            current_app.logger.error("Error 500 en %s %s: %s", request.method, request.path, e)
        return render_template("errors/500.html"), 500
