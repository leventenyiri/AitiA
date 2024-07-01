from setuptools import setup, find_packages

setup(
    name='my_project',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pytest'
    ],
    entry_points={
        'console_scripts': [
            'my_script=my_script:main',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    description='A project to mount NFS and save images from an emulated camera.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/my_project',  # Update with your project's URL
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)