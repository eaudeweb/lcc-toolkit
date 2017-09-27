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


DEFAULT_LANGUAGE = ('en', 'English') 

ALL_LANGUAGES = (
    DEFAULT_LANGUAGE,    
    ('sq', 'Albanian'),
    ('hy', 'Armenian'),
    ('az-az', 'Azeri'),
    ('be-by', 'Belarusian'),
    ('bs-ba', 'Bosnian'),
    ('bg', 'Bulgaria'),
    ('ca', 'Catalan'),
    ('hr-hr', 'Croatian'),
    ('cs', 'Czech'),
    ('da-dk', 'Danish'),
    ('nl', 'Dutch'),
    ('et', 'Estonian'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('ka', 'Georgian'),
    ('de-lu', 'German'),
    ('el-gr', 'Greek'),
    ('hu', 'Hungarian'),
    ('is', 'Icelandic'),
    ('it-ch', 'Italian'),
    ('it-it', 'Italian'),
    ('kk', 'Kazakh'),
    ('ky', 'Kyrgyz'),
    ('lv', 'Latvian'),
    ('lt', 'Lithuanian'),
    ('mk', 'Macedonian'),
    ('mt', 'Maltese'),
    ('md', 'Moldavian'),
    ('sr', 'Montenegrin'),
    ('no', 'Norwegian'),
    ('pl', 'Polish'),
    ('pt-pt', 'Portuguese'),
    ('ro', 'Romanian'),
    ('ru', 'Russian'),
    ('se-se', 'Sami'),
    ('sr', 'Serbian'),
    ('sk', 'Slovak'),
    ('sl', 'Slovenian'),
    ('es-es', 'Spanish'),
    ('tg', 'Tajik'),
    ('tr', 'Turkish'),
    ('tk', 'Turkmen'),
    ('uk', 'Ukrainian'),
    ('uz', 'Uzbek'))

LEGISLATION_TYPE_DEFAULT = ("Constitution", "Constitution")
LEGISLATION_TYPE = (
    LEGISLATION_TYPE_DEFAULT,
    ("Legislation", "Legislation"),
    ("Miscellaneous", "Miscellaneous"),
    ("Regulation", "Regulation"),
    ("Unknown", "Unknown"),     
)

LEGISLATION_DEFAULT_YEAR = datetime.datetime.now().year 
