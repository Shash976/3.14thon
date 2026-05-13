# Import gettext module
import gettext

# Set the local directory
appname = 'lokalise'
localedir = './locales'

# Set up Gettext
en_i18n = gettext.translation(appname, localedir, fallback=True, languages=['en'])

# Create the "magic" function
en_i18n.install()

# Translate message
print(gettext.gettext("Hello World"))
print(gettext.gettext("Learn Python i18n"))