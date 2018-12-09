import getpass
import sys
import subprocess

from nitrocli.lib import NitroKey
from nitrocli.menu import Menu


def init(menu):
    menu.nk = NitroKey()
    menu.nk.do_connect()


def cleanup(menu):
    menu.nk.lock()
    menu.nk.logout()


def get_password(admin=False):
    hint = 'ADMIN' if admin else 'USER'
    pinentryinput = b'setdesc Enter ' + bytes(hint, 'utf-8') + b' pin\ngetpin\n'
    try:
        pr = subprocess.Popen(['pinentry'],
                              stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE).communicate(input=pinentryinput)
        if pr[0] is not None:
            replies = pr[0].decode('utf-8').split("\n")
            for reply in replies:
                if reply.startswith('D '):
                    return reply[2:]
        return None
    except FileNotFoundError:
        pass

    return getpass.getpass(f'Enter {hint} pin: ')


options = []
commands = {'quit': Menu.quit}


command = 'help'
if len(sys.argv) > 1:
    command = sys.argv[1]

if command == 'menu':
    Menu(options,
         data={'nk': None},
         init=init,
         cleanup=cleanup,
         commands=commands).run()
elif command == 'help':
    print('''These commands are available:

status    Show the status

unlock    Unlock the encrypted storage

lock      Lock the NitroKey

menu      Start an interactive menu (in development, don't use it)
''')
else:
    with NitroKey() as nk:
        if not nk.connected:
            print('NitroKey not connected')
            sys.exit(-1)

        if command == 'status':
            if nk.model == 2:
                print('With storage')

            status = nk.get_status()
            unenc_status = 'active' if status.unencrypted_volume_active == 1 else 'not active'
            enc_status = 'active' if status.encrypted_volume_active == 1 else 'not active'

            print(f'''Unencrypted volume ..... {unenc_status}
Encrypted volume ....... {enc_status}

User retry attempts .... {status.user_retry_count}
Admin retry attempts ... {status.admin_retry_count}''')
        elif command == 'lock':
            nk.lock()
        elif command == 'unlock':
            if nk.model != NitroKey.MODEL_STORAGE:
                print('No storage')
                sys.exit(-2)

            nk.unlock_encrypted_volume(get_password())

sys.exit(0)
