.. _install:
   
Installation of unifi-sync
==========================

This part of the documentation covers the installation of unifi-sync.
The first step to using any software package is getting it properly installed.


To install unifi-sync, simply run this simple command in your terminal of choice::

    $ python -m pip install unifi-sync

Get the Source Code
-------------------

unifi-sync is actively developed on GitHub, where the code is

You can either clone the public repository::

    $ git clone https://github.com/kloodz-mrioux/py-unifi-sync.git

Download tarball using curl::

    $ curl -OL https://github.com/kloodz-mrioux/py-unifi-sync/tarball/main

To download tarball:: https://github.com/kloodz-mrioux/py-unifi-sync/tarball/main

To download zipfile:: https://github.com/kloodz-mrioux/py-unifi-sync/archive/refs/heads/main.zip

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily::

    $ cd py-unifi-sync
    $ python -m pip install .
