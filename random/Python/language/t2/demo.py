import gettext

locale = input("Please enter the preferred locale (en, fr, lv):")

appname = 'lokalise'
localedir = './locales'

translations = gettext.translation(appname, localedir, fallback=True, languages=[locale.strip()])

translations.install()

print(gettext.gettext("Hello World"))

print(gettext.gettext("Learn Python i18n"))