from setuptools import setup
import schemas

setup(name='schemas',
      version=schemas.__version__,
      description='Python library for marshalling and validation',
      author='Charles Reese',
      author_email='charlespreese@gmail.com',
      url='https://github.com/creese/schemas',
      download_url=('https://github.com/creese/schemas/archive/' +
                    schemas.__version__ + '.zip'),
      packages=['schemas'],
      install_requires=['functions==0.2.0'],)
