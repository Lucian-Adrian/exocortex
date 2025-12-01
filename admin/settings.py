"""
Django settings for Exo Admin.

Full-featured admin interface for Exocortex personal knowledge management.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment from parent .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Security
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "exo-admin-dev-key-change-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    # Unfold admin theme (must be before django.contrib.admin)
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.import_export",
    "unfold.contrib.guardian",
    "unfold.contrib.simple_history",
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Third-party
    "import_export",
    "django_filters",
    "simple_history",
    # Our apps
    "admin.apps.core",
    "admin.apps.memories",
    "admin.apps.ingest",
    "admin.apps.query",
    "admin.apps.commitments",
    "admin.apps.logs",
    "admin.apps.integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "admin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "admin" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "admin.apps.core.context_processors.exo_context",
            ],
        },
    },
]

WSGI_APPLICATION = "admin.wsgi.application"

# Database - SQLite for admin metadata, Supabase for memories
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "admin" / "db.sqlite3",
    }
}

# Supabase connection (used by our apps)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "admin" / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "admin" / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (for uploads)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "admin" / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# UNFOLD ADMIN THEME CONFIGURATION
# =============================================================================
UNFOLD = {
    "SITE_TITLE": "Exo Admin",
    "SITE_HEADER": "Exocortex",
    "SITE_SUBHEADER": "Personal Knowledge Management",
    "SITE_SYMBOL": "neurology",
    "SITE_FAVICON": lambda request: "/static/favicon.ico",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "ENVIRONMENT": "admin.apps.core.utils.environment_callback",
    "DASHBOARD_CALLBACK": "admin.apps.core.views.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {
                        "title": "Home",
                        "icon": "home",
                        "link": lambda request: "/",
                    },
                    {
                        "title": "Analytics",
                        "icon": "monitoring",
                        "link": lambda request: "/analytics/",
                    },
                ],
            },
            {
                "title": "Knowledge Base",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Memories",
                        "icon": "psychology",
                        "link": lambda request: "/memories/",
                        "badge": "admin.apps.memories.utils.memory_count_badge",
                    },
                    {
                        "title": "Ingest Content",
                        "icon": "upload_file",
                        "link": lambda request: "/ingest/",
                    },
                    {
                        "title": "Query & Search",
                        "icon": "search",
                        "link": lambda request: "/query/",
                    },
                ],
            },
            {
                "title": "Task Tracking",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Commitments",
                        "icon": "task_alt",
                        "link": lambda request: "/commitments/",
                        "badge": "admin.apps.commitments.utils.open_commitments_badge",
                    },
                    {
                        "title": "Overdue",
                        "icon": "warning",
                        "link": lambda request: "/commitments/?status=overdue",
                    },
                ],
            },
            {
                "title": "System",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Activity Logs",
                        "icon": "history",
                        "link": lambda request: "/logs/",
                    },
                    {
                        "title": "Errors",
                        "icon": "error",
                        "link": lambda request: "/errors/",
                    },
                    {
                        "title": "Settings",
                        "icon": "settings",
                        "link": lambda request: "/settings/",
                    },
                ],
            },
            {
                "title": "Admin",
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": "Users",
                        "icon": "people",
                        "link": lambda request: "/admin/auth/user/",
                    },
                    {
                        "title": "Django Admin",
                        "icon": "admin_panel_settings",
                        "link": lambda request: "/admin/",
                    },
                ],
            },
        ],
    },
    "TABS": [
        {
            "models": ["memories.memory"],
            "items": [
                {
                    "title": "All Memories",
                    "link": lambda request: "/memories/",
                },
                {
                    "title": "Recent",
                    "link": lambda request: "/memories/?ordering=-created_at",
                },
                {
                    "title": "With Commitments",
                    "link": lambda request: "/memories/?has_commitments=true",
                },
            ],
        },
    ],
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "admin" / "logs" / "exo_admin.log",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "db": {
            "level": "INFO",
            "class": "admin.apps.logs.handlers.DatabaseLogHandler",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "exo": {
            "handlers": ["console", "file", "db"],
            "level": "DEBUG",
            "propagate": False,
        },
        "admin": {
            "handlers": ["console", "file", "db"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / "admin" / "logs").mkdir(parents=True, exist_ok=True)
