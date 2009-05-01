Philisophy
==========

WsgiService allows very easy creation of REST web services. The basic goal is to provide a great HTTP service implementation to free the service author from some tedious work in relation to HTTP. It takes advantage of HTTP by making it easy to provide cachable responses, handle conditional requests and do content negotiation to service a wide spectrum of clients.

The primary guiding principle is that the services should be as easy and small to write as possible.

WsgiService is not intended to be frontend framework. Creating full-featured frontend applications with WsgiService is quite cumbersome.

Goals
-----

* Abstract away error and status code handling
* Make it easy to create machine readable output
* Easily validate input
* Easy deployment using good configuration file handling
* Make testing easy
* Create usable REST API documentation from source
* Content negotiation to automatically use the correct output format
