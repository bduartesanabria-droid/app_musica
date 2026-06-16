from datetime import datetime, timezone


def register_filters(app):

    @app.template_filter("timeago")
    def timeago(dt):
        if not dt:
            return "Nunca"
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        s = delta.total_seconds()
        if s < 60:
            return "hace un momento"
        if s < 3600:
            return f"hace {int(s // 60)} min"
        if s < 86400:
            return f"hace {int(s // 3600)} h"
        return f"hace {int(s // 86400)} días"

    @app.template_filter("duration")
    def duration(seconds):
        if not seconds:
            return "0 s"
        if seconds < 60:
            return f"{round(seconds, 1)} s"
        return f"{round(seconds / 60, 1)} min"

    @app.template_filter("accuracy_color")
    def accuracy_color(pct):
        if pct >= 90:
            return "text-green-600"
        if pct >= 70:
            return "text-blue-600"
        if pct >= 50:
            return "text-yellow-600"
        return "text-red-500"

    @app.template_filter("mode_label")
    def mode_label(mode):
        labels = {
            "notas":            "Notas",
            "intervalos":       "Intervalos",
            "escalas":          "Escalas",
            "dictado_melodico": "Dictado Melódico",
            "patrones_andinos": "Patrones Andinos",
            "guabina":          "Guabina",
            "tiple":            "Tiple",
            "requinto":         "Requinto",
            "bandola":          "Bandola",
        }
        return labels.get(mode, mode.replace("_", " ").title())
