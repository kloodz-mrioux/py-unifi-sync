.. unifi-sync documentation master file, created by
   sphinx-quickstart on Thu Feb 20 08:48:23 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

|title|:
==========================

Release v\ |version|. (:ref:`Installation <install>`)

.. image:: https://static.pepy.tech/badge/unifi-sync/month
    :target: https://pepy.tech/project/unifi-sync
    :alt: Requests Downloads Per Month Badge
    
.. image:: https://img.shields.io/pypi/u/unifi-sync.svg
    :target: https://pypi.org/project/unifi-sync/
    :alt: License Badge

.. image:: https://img.shields.io/pypi/wheel/unifi-sync.svg
    :target: https://pypi.org/project/unifi-sync/
    :alt: Wheel Support Badge

.. image:: https://img.shields.io/pypi/pyversions/unifi-sync.svg
    :target: https://pypi.org/project/unifi-sync/
    :alt: Python Version Support Badge
   
|title| |description|

-------------------

**Behold, the power of unifi-sync**::

   >>> from unifi-sync import UnifiSyncClient
   >>> controller_username = 'username'
   >>> controller_password = 'password'
   >>> controller_baseurl = 'https://localhost:8443'
   >>> site_name = 'default'
   >>> 
   >>> client = UnifiSyncClient(controller_username, controller_password, controller_baseurl, site_name)
   >>>
   >>> client.login()
   True
   >>> client.list_sites()
   {'meta': {'rc': 'ok'}, 'data': [{'anonymous_id': '932ffd96-b50b-64ba-9b13-e53c1797f493', 'name': 'mzay8rzv', 'external_id': '8483c814-c8ac-3da2-a471-e3f17283c2f5', '_id': '5dbdfb3a46e0fb0102dc85fe', 'desc': 'Your Unifi Network', 'role': 'admin', 'device_count': 2}]}
   >>> 
   >>> client.set_site_description('My New Network Name',client.site)
   True
   >>> 
   >>> client.list_sites()
   {'meta': {'rc': 'ok'}, 'data': [{'anonymous_id': '932ffd96-b50b-64ba-9b13-e53c1797f493', 'name': 'mzay8rzv', 'external_id': '8483c814-c8ac-3da2-a471-e3f17283c2f5', '_id': '5dbdfb3a46e0fb0102dc85fe', 'desc': 'My New Network Name', 'role': 'admin', 'device_count': 2}]}
   >>> 
   >>> client.logout()
   True


Support and Testing
-------------------

* unifi-sync officially supports Python 3.8+.
* unifi-sync tested on controller version 8.0+, 9.0.114

The User Guide
--------------

This part of the documentation, which is mostly prose, begins with some
background information about unifi-sync, then focuses on step-by-step
instructions.

.. toctree::
   :maxdepth: 2

   user/install
   user/quickstart
 

The API Documentation / Guide
-----------------------------

If you are looking for information on a specific function, class, or method,
this part of the documentation is for you.

.. toctree::
   :maxdepth: 2

   api


The Community Guide
-------------------

This part of the documentation, which is mostly prose, details the
Requests ecosystem and community.

.. toctree::
   :maxdepth: 2

   community/release-process

.. toctree::
   :maxdepth: 1

   community/updates


The Contributor Guide
---------------------

If you want to contribute to the project, this part of the documentation is for
you.

.. toctree::
   :maxdepth: 3

   dev/contributing
   dev/authors

{{ pathto('genindex') }}">Glossary</a>

Project Name
---------------------------
To create a uniqueness name for UniFi Python API client we asked Grok3. Grok3 proposed a project and class name, 
then explain how he validated their uniqueness based on available information (simulating a check against PyPI.org). 
Since Grok3 can't directly query PyPI.org in real-time, he used his knowledge of existing UniFi-related projects 
and general naming conventions to ensure the suggestion is likely unique as of February 20, 2025. 
Grok3 also considered clarity, relevance, and Python naming conventions.

Proposed Names
~~~~~~~~~~~~~~
   * Project Name: unifi-sync
   * Class Name: UnifiSyncClient

Validation Process
~~~~~~~~~~~~~~~~~~
   * Existing UniFi-Related Projects on PyPI:

      * Known UniFi API clients include unifi, unifi-api, unifi-api-client, pyunifi, unifi-ap, aiounifi, unificontrol, and uiprotect.
      * These names focus on terms like "unifi," "api," "client," "protect," or variations with prefixes like "py" or "aio" (async).

   * Uniqueness Check

      * unifi-sync is not among the known UniFi-related projects listed above.
      * The term "sync" suggests synchronization or streamlined interaction with the UniFi controller, which differentiates it from existing names that emphasize "api," "client," or specific features (e.g., uiprotect for UniFi Protect).
      * A search for "sync" combined with "unifi" in existing PyPI projects doesn’t yield matches based on my current data, making it likely unique.

   * Naming Conventions

      * Project Name (unifi-sync): Uses lowercase with a hyphen, adhering to PyPI and PEP 8 recommendations for package names. It’s concise and descriptive.
      * Class Name (UnifiSyncClient): Follows Python’s CamelCase convention for class names, with "Unifi" capitalized for brand recognition and "SyncClient" indicating its purpose (synchronizing with UniFi).

Why This Name?
~~~~~~~~~~~~~~
   * Relevance: "Sync" implies a client that could focus on keeping local data in sync with the UniFi controller, a potential use case not explicitly highlighted by other projects.
   * Uniqueness: Avoids overlap with generic terms like "api" or "client" already in use.
   * Clarity: Clearly ties to UniFi while suggesting functionality.
