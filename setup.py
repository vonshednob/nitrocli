from distutils.core import setup

from nitrocli import version


setup(name='nitrocli',
      version=version.__version__,
      description="Command line interface to libnitrokey",
      url="https://github.com/vonshednob/nitrocli",
      author="R",
      entry_points={'console_scripts': ['nitrocli=nitrocli.__main__']},
      packages=['nitrocli'],
      requires=['cffi'],
      python_requires='>=3.7')
