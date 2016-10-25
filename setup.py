# Copyright 2016 Uri Laserson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

def readme():
    with open('README.md', 'r') as ip:
        return ip.read()

setup(
    name='pepsyn',
    version='0.2.0.dev0',
    description='Peptide library design',
    long_description=readme(),
    url='https://github.com/lasersonlab/pepsyn',
    author='Laserson Lab',
    license='Apache License, Version 2.0',
    classifiers=['Programming Language :: Python :: 3'],
    packages=find_packages(),
    install_requires=['click', 'biopython'],
    entry_points={'console_scripts': ['pepsyn = pepsyn.cli:cli']}
)