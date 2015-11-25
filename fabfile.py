from fabric.api import *
import fabric.contrib.project as project
import os

from source import conf

PROD = 'stacktrace.org'
# Format the path using the version in the Sphinx config.
DEST_PATH = '/home/mixxx/public_html/manual/%s' % conf.version
ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
DEPLOY_PATH = os.path.join(ROOT_PATH, 'build/html')
env.user = 'mixxx'

def make_command(language):
    return 'make -e SPHINXOPTS="-D language=\'%s\'"' % language

@task
def clean():
    local('make clean')

@task
def i18n_update_source_translations():
    # Builds .pot files containing translation text from all manual pages.
    local('make gettext')

    # Updates Transifex configuration to include new chapters / source files.
    local('sphinx-intl update-txconfig-resources --pot-dir source/locale/pot '
          '--transifex-project-name mixxxdj-manual --locale-dir source/locale')

@task
def tx_push():
    # Pushes latest .pot files to Transifex.
    local('tx push -s')

@task
def tx_pull():
    # Pulls latest .po translation files for all languages from Transifex.
    local('tx pull -a')

@task
def i18n_build():
    # Re-build .mo files.
    local('sphinx-intl build')

@task
def regen():
    clean()
    html()

@task
def html(language='en'):
    local('%s html' % make_command(language))

@task
def pdf(language='en'):
    local('%s latex' % make_command(language))
    # The manual PDF build typically throws tons of errors. We should fix them
    # but for now we ignore so the build server job isn't always marked as
    # failed when a mostly-working PDF is generated.
    with settings(warn_only=True):
        with lcd('build/latex'):
            # You need to run pdflatex twice to get the TOC and references
            # right.
            local('pdflatex -interaction=nonstopmode Mixxx-Manual.tex')
            local('pdflatex -interaction=nonstopmode Mixxx-Manual.tex')

@task
@hosts(PROD)
def publish():
    regen()
    project.rsync_project(
        remote_dir=DEST_PATH,
        local_dir=DEPLOY_PATH.rstrip('/') + '/',
        delete=True
    )
