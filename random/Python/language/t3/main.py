import gettext
def main():
    lang = input("Choose language from English [en] or Spanish (Español) [es]: ")
    # set current language
    lang_translations = gettext.translation('base', localedir='locales', languages=[lang.strip()])
    lang_translations.install()
	# define _ shortcut for translations
    _ = lang_translations.gettext

    # mark a string translatable
    print(_("Hello World"))

if __name__ == "__main__":
    main()

