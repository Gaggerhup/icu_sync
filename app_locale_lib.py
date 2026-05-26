from PyQt6.QtCore import QLocale


APP_NUMBER_LOCALE = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)


def configure_app_locale() -> None:
    QLocale.setDefault(APP_NUMBER_LOCALE)


def apply_widget_number_locale(widget) -> None:
    widget.setLocale(APP_NUMBER_LOCALE)
