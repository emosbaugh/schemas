from setuptools import setup


__version__ = "0.6.0"


setup(name='schemas',
      version=__version__,
      description='Python library for marshalling and validation',
      author='Charles Reese',
      author_email='charlespreese@gmail.com',
      url='https://github.com/creese/schemas',
      download_url=(
          'https://github.com/creese/schemas/archive/' + __version__ + '.zip'),
      packages=['schemas'],
      install_requires=['functions',
                        'pytest'],)
