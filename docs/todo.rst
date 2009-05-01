Todo
====

.. todo:: Think about how to handle 201, 200/204 methods.
.. todo:: Make downtime configurable with a file or something like that? Could then send out a 503 response with proper Retry-After header.
.. todo:: Allow easy pluggin in of a compression WSGI middleware
.. todo:: Convert to requested charset with Accept-Charset header
.. todo:: Return Allow header as response to PUT and for 405 (also 501?)
.. todo:: Implement Content-Location header
.. todo:: Log From and Referer headers
.. todo:: On 201 created provide Location header
.. todo:: Abstract away error and status code handling
.. todo:: Easy deployment using good configuration file handling
.. todo:: Create usable REST API documentation from source
.. todo:: Support OPTIONS, send out the Allow header, and some machine-readable output in the correct format. ``OPTIONS *`` can be discarded as NOOP

