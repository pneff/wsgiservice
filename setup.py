from setuptools import setup, find_packages
import wsgiservice
setup(
    name='WsgiService',
    version=wsgiservice.__version__,
    description="A lean WSGI framework for easy creation of REST services",
    long_description=open('README').read(),
    author=", ".join(wsgiservice.__author__),
    url='http://github.com/pneff/wsgiservice/tree/master',
    download_url='http://pypi.python.org/pypi/WsgiService',
    packages=find_packages(),
    install_requires=[
        'decorator',
        'webob >= 0.9.7',
    ],
    tests_require=[
        'nose',
        'mox',
    ],
    setup_requires=['Sphinx-PyPI-upload'],
    test_suite='nose.collector',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ]
)
