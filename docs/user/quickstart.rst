.. _quickstart:

Quickstart
==========

.. module:: unifi_sync

This page gives a good introduction in how to get started.

First, make sure that:

* unifi-sync is :ref:`installed <install>`
* unifi-sync is :ref:`up-to-date <updates>`


Let's get started with some simple examples.


Unifi Controller First Connection
---------------------------------

Establishing connection with Unifi Controller or UI web portal is very simple.

Begin by importing the unifi-sync module::

    >>> from unifi_sync import UnifiSyncClient

For this example, let's setup unifi controller information::
    >>> config = [ username := "ubnt", password := "ubnt", 
    ... baseurl := "https://localhost:8443", site_name := "default"]

Create client object using :class:`UnifiSyncClient <unifi_sync.UnifiSyncClient>` class with the controller information config::
    >>> client = UnifiSyncClient(*config)

Now, we have a :class:`UnifiSyncClient <unifi_sync.UnifiSyncClient>` object called ``client``.
We can get / set all the information we need with this object.

Now, let's try to connect on unifi controller::
    >>> client.login()
    True

Finally we will disconnect from unifi controller::
    >>> client.logout()
    True

Nice, right? That's all we need to start playing!


List device
--------------------------

Restart device
--------------------------

List network
--------------------------

Add network
--------------------------

List wlan
-------------------------

Add wlan
-------------------------

Modify wlan
-------------------------

Requests Timeouts
-----------------

As you may know unifi-sync use Requests module. to stop waiting for a response after a given number of
seconds with the ``timeout`` parameter. Nearly all production code should use
this parameter in nearly all requests. Failure to do so can cause your program
to hang indefinitely::

    >>> requests.get('https://github.com/', timeout=0.001)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    requests.exceptions.Timeout: HTTPConnectionPool(host='github.com', port=80): Request timed out. (timeout=0.001)


.. admonition:: Note

    ``timeout`` is not a time limit on the entire response download;
    rather, an exception is raised if the server has not issued a
    response for ``timeout`` seconds (more precisely, if no bytes have been
    received on the underlying socket for ``timeout`` seconds). If no timeout is specified explicitly, requests do
    not time out.


Requests Errors and Exceptions
------------------------------

In the event of a network problem (e.g. DNS failure, refused connection, etc),
Requests will raise a :exc:`~requests.exceptions.ConnectionError` exception.

:meth:`Response.raise_for_status() <requests.Response.raise_for_status>` will
raise an :exc:`~requests.exceptions.HTTPError` if the HTTP request
returned an unsuccessful status code.

If a request times out, a :exc:`~requests.exceptions.Timeout` exception is
raised.

If a request exceeds the configured number of maximum redirections, a
:exc:`~requests.exceptions.TooManyRedirects` exception is raised.

All exceptions that Requests explicitly raises inherit from
:exc:`requests.exceptions.RequestException`.

