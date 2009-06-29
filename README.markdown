WsgiService is a project to create a lean Python WSGI framework for very easy creation of REST services.

A REST service in this context is a HTTP service to be used by machines. So a service should output something like XML, JSON or any other machine-readable format.

## Installation ##

If you want to install the current live version of WsgiService just type the following command on the command line (you probably want to execute this inside a virtualenv):

    easy_install WsgiService

## Links ##

* Documentation: [http://packages.python.org/WsgiService/](http://packages.python.org/WsgiService/)
* Package index page: [http://pypi.python.org/pypi/WsgiService](http://pypi.python.org/pypi/WsgiService)

## Goals ##

The primary guiding principle is that the actual service should be as easy and small to write as possible. And here's what the WsgiService framework will do for the developer:

* Abstract away error and status code handling
* Make it easy to create machine readable output
* Easily validate input
* Easy deployment using good configuration file handling
* Make testing easy
* Create usable REST API documentation from source
* Content negotiation to automatically use the correct output format

Just as important as what WsgiService tries to accomplish is what it will never be:

* WsgiService is not planning to be a full-featured frontend framework. Use your existing framework of choice for that, e.g. [Pylons](http://pylonshq.com/).

## Development ##

To use the development version, check out this project somewhere on your file system and then type the following command:

    python setup.py develop

To build the documentation first install [Sphinx](http://sphinx.pocoo.org/). Then execute:

    cd docs
    make html

The documentation was built into `_build/html/index.html`.

## See also ##

* [servicegen](http://github.com/pneff/servicegen/tree/master): The predecessor to WsgiService
