"""
AppConfig
"""
from django.apps import AppConfig


class SearchConfig(AppConfig):
    """
    App config for this app
    """
    name = "exams"

    def ready(self):
        """
        Ready handler. Import signals.
        """
        import exams.signals  # pylint: disable=unused-variable
