from distutils.core import setup

setup(name='Insteon',
      version='1.0',
      description='Program to control an insteon interface. ',
      author='Eric Busboom',
      author_email='eric@busboom.org',
      url='http://busboom.org',
      packages=['esbinsteon'],
      package_dir={'esbinsteon':'src/esbinsteon'},
      package_data={'esbinsteon': ['config/*']},
      scripts=['scripts/insteon_schedule','scripts/insteon_switch', 'scripts/insteon_install'],
      install_requires=[
            'pyephem',
            'PyYAML'
        ],
     )
