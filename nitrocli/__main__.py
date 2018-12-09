from nitrocli.lib import NitroKey
from nitrocli.menu import Menu


def init(menu):
    menu.nk = NitroKey()
    menu.nk.do_connect()


def cleanup(menu):
    menu.nk.lock()
    menu.nk.logout()


options = []
commands = {'quit': Menu.quit}


Menu(options,
     data={'nk': None},
     init=init,
     cleanup=cleanup,
     commands=commands).run()
