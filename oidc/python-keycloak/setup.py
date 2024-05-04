# -*- coding: utf-8 -*-
import os
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


package_version = open('debian/changelog').readline().split()[1][1:-1]
override_version = os.environ.get('PYTHON_PACKAGE_VERSION')


setup(
    name='python-keycloak',
    version=override_version or package_version,
    url='https://github.com/marcospereirampj/python-keycloak',
    license='The MIT License',
    author='Marcos Pereira',
    author_email='marcospereira.mpj@gmail.com',
    keywords='keycloak openid',
    description='python-keycloak is a Python package providing access to the Keycloak API.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['keycloak', 'keycloak.authorization', 'keycloak.tests'],
    install_requires=['requests>=2.20.0', 'python-jose>=1.4.0'],
    tests_require=['httmock>=1.2.5'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Utilities',
    ],
)
