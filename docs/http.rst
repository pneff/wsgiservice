WsgiService's implementation of HTTP 1.1
========================================

Wherever possible WsgiService follows the HTTP 1.1 standard as defined in
:rfc:`2616`. There are some features which WsgiService does not implement as
outlined in this document. Apart from that all deviations from the standard
are considered bugs and should be reported to the Author.


Missing features
----------------

The following features are not currently implemented. Usually this is because
the need was not currently here or because the web server usually implements
them.


Protocol-level details
^^^^^^^^^^^^^^^^^^^^^^

For big parts WsgiService relies on the web server which serves the
application.

This affects the following section of the RFC:

    - 10.1: Informational 1xx: Both status codes 100 and 101 are related to
      protocol level details.
    - 10.4.12: 411 Length Required
    - 10.4.14: 413 Request Entity Too Large
    - 10.4.15: 414 Request-URI Too Long
    - 10.4.18: 417 Expectation Failed
    - 10.5.6: 505 HTTP Version Not Supported


Range requests
^^^^^^^^^^^^^^

Content ranges are not currently implemented at all. This affects the following section of the RFC:

    - 3.12: Range Units
    - 10.2.7: 206 Partial Content
    - 10.4.17: 416 Requested Range Not Satisfiable


Proxy server
^^^^^^^^^^^^

Big parts of the HTTP 1.1 standard are relevant only for proxy servers or
gateways.

This affects the following section of the RFC:

    - 9.8: TRACE method not implemented as it's mostly relevant because of the
      ``Max-Forwards`` request header and it's not clear how useful that's for
      non-gateways. Implementation would be easy to do however, similar to the
      existing OPTIONS method.
    - 9.9: CONNECT
    - 10.2.4: 203 Non-Authoritative Information
    - 10.4.8: 407 Proxy Authentication Required
    - 10.4.9: 408 Request Timeout
    - 10.5.3: 502 Bad Gateway
    - 10.5.5: 504 Gateway Timeout
    - 13: Caching in HTTP. Most of the chapter is for proxies, though some
      parts are also relevant for applications and implemented in WsgiService


Open questions
--------------

The following details are still untested and undecided:

    - 100 (Continue) status: Section 8.2.3 of the RFC. Not sure if this should
      be implemented, if it is done by the server already, etc.



Possible future directions
--------------------------

Some details can't really be considered missing features but are outlined
here. They may be implemented if anybody sees a value in them.

    - 503 Service Unavailable: This status code would be ideal to communicate
      a planned downtime. Especially because it can include a ``Retry-After``
      response header containing the estimated time of the downtime. This
      could be output automatically for example after touching some file.
    - ``Accept-Charset`` request header: When the client sends this header the
      service output could be converted automatically. Currently WsgiService
      always returns UTF-8 and that's probably workable enough.
    - Authentication is not very well supported, yet. This might be made
      easier by some access checks on a resource level.
