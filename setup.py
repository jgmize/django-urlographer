#!/usr/bin/env python
#
# Copyright 2013 Consumers Unified LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from setuptools import setup


setup(
    name='django-urlographer',
    version='0.8.9',
    author='Josh Mize',
    author_email='jmize@consumeraffairs.com',
    description='URL mapper for django',
    license='Apache License 2.0',
    url='https://github.com/ConsumerAffairs/django-urlographer',
    packages=['urlographer', 'urlographer.migrations'],
    install_requires=['Django>=1.3', 'django-extensions>=0.9'],
    long_description='A URL mapper for the django web framework',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
