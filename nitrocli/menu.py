"""Very basic menu"""


class Option:
    def __init__(self, title, callback=None):
        self.title = title
        self.callback = callback

    def execute(self, *args, **kwargs):
        if self.callback is None:
            raise NotImplementedError()
        self.callback(*args, **kwargs)


class Menu:
    """A generic menu"""
    def __init__(self, options, init=None, cleanup=None, info=None, commands=None, data=None):
        """Create and initialize this menu

        ``options`` is a list of options. Each option is expected to be either of class Option
        or a dict with the keys "title" and "callback".
        ``init`` is the function to call before the first run of the menu.
        ``data`` is the dictionary that's being used for storing state. It's accessible through getitem of the menu.
        ``commands`` is a dictionary with a mapping of command to callback.
        ``info`` is expected to be a callable that returns a string

        Any callback, be it ``init``, ``info``, or any option's command, will receive the menu as the first parameter.
        """
        self.options = options[:]
        self.commands = commands or dict()
        self.data = data or dict()
        self.info = info or Menu.blank
        self.init = init or Menu.blank
        self.cleanup = cleanup or Menu.blank
        self._quit = False

    def __getitem__(self, item):
        return self.data.get(item, None)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getattr__(self, item):
        if item in self.data:
            return self.data[item]
        return AttributeError(item)

    @classmethod
    def blank(cls):
        return ""

    def quit(self, *_):
        self._quit = True

    def run(self):
        self.init(self)
        try:
            while not self._quit:
                self.print_options()
                try:
                    command = input('> ')
                except (KeyboardInterrupt, EOFError):
                    self.quit()
                    continue

                if command.isdecimal():
                    pass
                elif len(command.strip()) > 0:
                    command = command.strip()
                    args = ''
                    if ' ' in command:
                        command, args = command.split(' ', 1)
                    args = args.split(' ')  # TODO, escaping and quotes

                    for cmd in sorted(self.commands.keys()):
                        if cmd.startswith(command):
                            self.commands[cmd](self, *args)
                            break
        finally:
            self.cleanup(self)

    def print_options(self):
        for idx, option in enumerate(self.options):
            print(f'{idx}: {option.title}')
        self.info()

        if len(self.commands) > 0:
            print('Available commands:', ', '.join(sorted(self.commands.keys())))
