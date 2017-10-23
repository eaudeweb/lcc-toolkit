import datetime

LOGIN_URL = "/login/"

POST_DATA_USERNAME_KEY = "username"
POST_DATA_PASSWORD_KEY = "password"

AJAX_RETURN_SUCCESS = "success"
AJAX_RETURN_FAILURE = "failure"

DEFAULT_LANGUAGE = ('en', 'English')

ALL_LANGUAGES = (
    DEFAULT_LANGUAGE,
    ('ar', 'Arabic'),
    ('zh', 'Chinese'),
    ('fr', 'French'),
    ('ru', 'Russian'),
    ('es-es', 'Spanish'),
    ('oth', 'Other')
)

LEGISLATION_TYPE_DEFAULT = ("Law", "Law")
LEGISLATION_TYPE = (
    LEGISLATION_TYPE_DEFAULT,
    ("Constitution", "Constitution"),
    ("Regulation", "Regulation"),
    ('oth', 'Other')
)

LEGISLATION_DEFAULT_YEAR = datetime.datetime.now().year
LEGISLATION_YEAR_RANGE = range(1945, LEGISLATION_DEFAULT_YEAR + 1)

GEOGRAPHICAL_COVERAGE_DEFAULT = ("nat", "National")
GEOGRAPHICAL_COVERAGE = (
    GEOGRAPHICAL_COVERAGE_DEFAULT,
    ("int-reg", "International/regional"),
    ("st-pr", "State/province"),
    ("city-mun", "City/municipality"),
    ("oth", "Other")
)

SOURCE_TYPE_DEFAULT = ('official', 'Official')
SOURCE_TYPE = (
    SOURCE_TYPE_DEFAULT,
    ('unofficial', 'Unofficial')
)
