import setuptools


setuptools.setup(
    name='autopip',
    version='1.5.9',

    author='Max Zheng',
    author_email='maxzheng.os@gmail.com',

    description='Easily install apps from PyPI and automatically keep them updated',
    long_description=open('README.rst').read(),

    url='https://github.com/maxzheng/autopip',

    license='MIT',

    packages=setuptools.find_packages(),
    include_package_data=True,

    python_requires='>=3.6',
    setup_requires=['setuptools-git', 'wheel'],

    entry_points={
       'console_scripts': [
           'app = autopip:main',
           'autopip = autopip:main',
       ],
    },

    # Standard classifiers at https://pypi.org/classifiers/
    classifiers=[
      'Development Status :: 5 - Production/Stable',

      'Intended Audience :: Developers',
      'Topic :: Software Development :: Build Tools',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.6',
    ],

    keywords='automatically pip virtualenv auto-update apps',
)
