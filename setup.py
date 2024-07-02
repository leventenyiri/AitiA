from setuptools import setup

setup(
    name='AitiA',
    version='1.0.0',
    description='Testing python code for Starling detection project',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=['example'],
    scripts=['FileShare/read.py'],
    install_requires=['netifaces',
                      'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest']
)
