from setuptools import setup, find_packages
setup(
    name='WsgiService',
    version='0.2.3',
    description="A lean WSGI framework for easy creation of REST services",
    author="Patrice Neff",
    url='http://github.com/pneff/wsgiservice/tree/master',
    packages=find_packages(),
    install_requires=[
        'decorator',
        'webob >= 0.9.7',
    ],
    tests_require=[
        'nose',
        'mox',
    ],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ]
)
