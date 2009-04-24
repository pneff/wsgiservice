WsgiService is a project to create a lean Python WSGI framework for very easy creation of REST services.

A REST service in this context is a HTTP service to be used by machines. So a service should output something like XML, JSON or any other machine-readable format.

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

## Current implementation ##

The current implementation is not production ready. But much has been done already:

* Easy input validation of path parameters and POST input (validate decorator).
* Send the correct expiry headers (expiry decorator).
* Easy testing, the resources can be instantiated and tested without having to go through the WsgiService framework at all.
* Content negotiation between JSON and XML. Both using the Accept request header and file extensions.
* Almost complete test coverage.

## Open questions ##

How should query string and POST data be handled? Take the following method definition:

    def PUT(self, id, email=None, password=None):

This requires and id and optionally an email and password - either extracted from the path routing information or from query string / POST data.

There are two ways how query string and POST data could be handled. The framework could look at the method signature and see the values the developer is interested in. As a second option, the framework could just extract all passed values and hand them in.

In case #1 we'd have to rely on Python's @func_code.co_varnames@ for introspection - which breaks with decorators.

In the second case, Python would handle the validation - which would be a lot easier to implement. But if unexpected parameters get passed in that would cause an exception - something that could be fixed if wished by adding a @**kwargs@ argument to the method definition.

## See also ##

* [servicegen](http://github.com/pneff/servicegen/tree/master): The predecessor to WsgiService
