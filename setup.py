from setuptools import setup, find_packages
setup(
    name='WsgiService',
    # Version number also needs to be updated in wsgiservice/__init__.py
    version='0.4.0',
    description="A lean WSGI framework for easy creation of REST services",
    long_description=open('README').read(),
    author=", ".join([
        "Patrice Neff <software@patrice.ch>",
    ]),
    url='http://github.com/pneff/wsgiservice/tree/master',
    download_url='http://pypi.python.org/pypi/WsgiService',
    packages=find_packages(),
    install_requires=[
        'decorator',
        'webob >= 1.2b2',
    ],
    tests_require=[
        'nose',
        'mox',
    ],
    test_suite='nose.collector',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ]
)
