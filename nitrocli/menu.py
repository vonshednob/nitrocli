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
    def __init__(self, options):
        self.options = options[:]
        self._quit = False

    def quit(self):
        self._quit = True

    def run(self):
        while not self._quit:
            self.print_options()
            try:
                command = input('> ')
            except (KeyboardInterrupt, EOFError):
                self.quit()

    def print_options(self):
        for idx, option in enumerate(self.options):
            print(f'{idx}: {option.title}')


def main():
    Menu([]).run()
