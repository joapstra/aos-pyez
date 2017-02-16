# Copyright 2014-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/community/eula

from setuptools import setup, find_packages

# parse requirements
req_lines = [line.strip() for line in open(
    'requirements.txt').readlines()]
install_reqs = list(filter(None, req_lines))

libdir = 'pylib'
packages = find_packages(libdir)

setup(
    name="aos-pyez",
    namespace_packages=['apstra'],
    url="https://github.com/Apstra/aos-pyez",
    version="0.6.1",
    author="Jeremy Schulman",
    author_email="jeremy@apstra.com",
    description=("Python wrapper library for Apstra AOS REST API "),
    license="Apache 2.0",
    keywords="networking automation vendor-agnostic",
    package_dir={'': libdir},
    packages=packages,
    install_requires=install_reqs,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
    ],
)
