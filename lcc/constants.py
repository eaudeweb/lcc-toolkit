import datetime

LOGIN_URL = "/login/"

ROLE_CONTENT_MANAGER = "Content Manager"
ROLE_POLICY_MAKER = "Policy Maker"
ROLE_SITE_ADMIN = "Site Administrator"

USER_PROFILE_ROLES = (ROLE_SITE_ADMIN, ROLE_CONTENT_MANAGER, ROLE_POLICY_MAKER)

POST_DATA_USERNAME_KEY = "username"
POST_DATA_PASSWORD_KEY = "password"

AJAX_RETURN_SUCCESS = "success"
AJAX_RETURN_FAILURE = "failure"

DEFAULT_LANGUAGE_VALUE = 'English'
DEFAULT_LANGUAGE = ('en', DEFAULT_LANGUAGE_VALUE )

ALL_LANGUAGES = (
    DEFAULT_LANGUAGE,
    ('ar', 'Arabic'),
    ('zh', 'Chinese'),
    ('fr', 'French'),
    ('ru', 'Russian'),
    ('es-es', 'Spanish'),
    ('oth', 'Other')
)

LEGISLATION_DEFAULT_VALUE = "Law"
LEGISLATION_TYPE_DEFAULT = ("Law", LEGISLATION_DEFAULT_VALUE)
LEGISLATION_TYPE = (
    LEGISLATION_TYPE_DEFAULT,
    ("Constitution", "Constitution"),
    ("Regulation", "Regulation"),
    ('oth', 'Other')
)

LEGISLATION_DEFAULT_YEAR = None
LEGISLATION_YEAR_RANGE = range(1945, datetime.datetime.now().year + 1)

GEOGRAPHICAL_COVERAGE_DEFAULT_VALUE = "National"
GEOGRAPHICAL_COVERAGE_DEFAULT = ("nat", GEOGRAPHICAL_COVERAGE_DEFAULT_VALUE)
GEOGRAPHICAL_COVERAGE = (
    GEOGRAPHICAL_COVERAGE_DEFAULT,
    ("int-reg", "International/regional"),
    ("st-pr", "State/province"),
    ("city-mun", "City/municipality"),
    ("oth", "Other")
)

SOURCE_TYPE_DEFAULT_VALUE = 'Official'
SOURCE_TYPE_DEFAULT = ('official', SOURCE_TYPE_DEFAULT_VALUE)
SOURCE_TYPE = (
    SOURCE_TYPE_DEFAULT,
    ('unofficial', 'Unofficial'),
    ('', '----')
)
