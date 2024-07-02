from setuptools import setup

setup(
    name='AitiA',
    version='1.0.0',
    description='Testing python code for Starling detection project',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=['example'],
    scripts=['pc_client.py'],
    install_requires=['netifaces',
                      'PyYAML>=6.0',
                      'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest']
)
