from setuptools import setup, find_packages


VERSION = '0.0.1'

setup(
    name='loser',
    version=VERSION,
    description='Local simple repository server as a bridge to custom sources',
    author='Alex Lopez',
    author_email='alex.lopez.zorzano@gmail.com',
    packages=find_packages(),
    install_requires=["aiohttp", "boto3"],
    python_requires='~=3.6',
    license="MIT",
    zip_safe=False,
    keywords='',
    classifiers=[
        'License :: OSI Approved :: MIT License'
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'loser = loser.server:main'
        ],
    },
)
