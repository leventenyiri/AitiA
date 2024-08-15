from setuptools import setup, find_packages

setup(
    name='sentinel_mrhat_cam',
    version='0.3.3',
    description='Testing python code for Starling detection project',
    author='Ferenc Nandor Janky, Attila Gombos, Nyiri Levente, Nyitrai Bence',
    author_email='info@effective-range.com',
    packages=find_packages(),
    package_dir={'': 'sentinel_mrhat_cam'},
    scripts=['scripts/sentinel_mrhat_cam.sh'],
    install_requires=['pytest',
                      'PyYAML>=6.0',
                      'pillow',
                      'pytz',
                      'paho-mqtt',
                      'numpy',
                      'pybase64',
                      'pdocs']
)
