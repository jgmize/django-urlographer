DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    }
}
USE_TZ = True
SITE_ID = 1
SECRET_KEY = 'keepitsecretkeepitsafe'
STATIC_URL = '/static/'

ROOT_URLCONF = 'test_app.urls'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_nose',
    'south',
    'urlographer',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ('--nocapture', )

import sys
if 'jenkins' in sys.argv:
    INSTALLED_APPS += ('django_jenkins',)
    PROJECT_APPS = ('urlographer',)
    COVERAGE_RCFILE = '.coveragerc'
    JENKINS_TASKS = (
        'django_jenkins.tasks.with_coverage',
        'django_jenkins.tasks.django_tests',
        'django_jenkins.tasks.run_pep8',
        'django_jenkins.tasks.run_pyflakes',
    )
