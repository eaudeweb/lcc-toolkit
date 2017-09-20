import datetime


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
    ('cs', 'Czech'),
    ('sq-al', 'Albanian'),
    ('lt', 'Lithuanian'),
    ('hy', 'Armenian'),
    ('fr', 'French'),
    ('nl', 'Dutch'),
    ('ru', 'Russian'),
    ('tr', 'Turkish'),
    ('pl', 'Polish'),
    ('ky', 'Kyrgyz'),
    ('bg', 'Bulgaria'),
    ('de-at', 'German'),
    ('az-az', 'Azeri'),
    ('uk', 'Ukrainian'),
    ('tk', 'Turkmen'),
    ('be-by', 'Belarusian'),
    ('se-se', 'Sami'),
    ('uz', 'Uzbek'),
    ('sk', 'Slovak'),
    ('fi', 'Finnish'),
    ('no', 'Norwegian'),
    ('is', 'Icelandic'),
    ('de-de', 'German'),
    ('fr-ch', 'French'),
    ('de-ch', 'German'),
    ('it-ch', 'Italian'),
    ('ro', 'Romanian'),
    ('de-li', 'German'),
    ('hu', 'Hungarian'),
    ('bs-ba', 'Bosnian'),
    ('lv', 'Latvian'),
    ('it-it', 'Italian'),
    ('fr-mc', 'French'),
    ('sl', 'Slovenian'),
    ('ka', 'Georgian'),
    ('hr-hr', 'Croatian'),
    ('mk', 'Macedonian'),
    ('sr', 'Montenegrin'),
    ('ca', 'Catalan'),
    ('sr', 'Serbian'),
    ('sq', 'Albanian'),
    ('tg', 'Tajik'),
    ('kk', 'Kazakh'),
    ('pt-pt', 'Portuguese'),
    ('mt', 'Maltese'),
    ('et', 'Estonian'),
    ('fr-lu', 'French'),
    ('de-lu', 'German'),
    ('es-es', 'Spanish'),
    ('md', 'Moldavian'),
    ('da-dk', 'Danish'),
    ('el-gr', 'Greek'),
)

LEGISLATION_TYPE_DEFAULT = ("Constitution", "Constitution")
LEGISLATION_TYPE = (
    LEGISLATION_TYPE_DEFAULT,
    ("Legislation", "Legislation"),
    ("Miscellaneous", "Miscellaneous"),
    ("Regulation", "Regulation"),
    ("Unknown", "Unknown"),     
)

LEGISLATION_DEFAULT_YEAR = datetime.datetime.now().year 
