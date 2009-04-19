WsgiService is a project to create a lean Python WSGI framework for very easy creation of REST services.

A REST service in this context is a HTTP service to be used my machines - thus working with XML, JSON and other machine-readable formats.

## Goals ##

* Abstract away error and status code handling
* Make it easy to create machine readable output
* Easily validate input
* Easy deployment using good configuration file handling
* Make testing easy
* Create usable REST API documentation from source
* Content negotiation to automatically use the correct output format

Just as important as what WsgiService tries to accomplish is what it will never be:

* WsgiService is not planning to be a full-featured frontend framework. Use your existing framework of choice for that, e.g. [Pylons](http://pylonshq.com/).

## See also ##

* [servicegen](http://github.com/pneff/servicegen/tree/master): The predecessor to WsgiService
