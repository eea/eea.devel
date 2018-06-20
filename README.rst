=========
EEA Devel
=========
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.devel/develop
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.devel/job/develop/display/redirect
  :alt: Develop
.. image:: https://ci.eionet.europa.eu/buildStatus/icon?job=eea/eea.devel/master
  :target: https://ci.eionet.europa.eu/job/eea/job/eea.devel/job/master/display/redirect
  :alt: Master


EEA Devel is a helper package to be used with a new EEA Data.fs.


Contents
========

.. contents::


Main features
=============

1. Hooks EEA Data.fs to make it development ready
2. Creates a user with Manager roles within Zope root acl_users named **eeadevel**
3. Creates Plone users for each role within Plone Site.
4. Removes **cookie_domain** from Plone Site acl_users / plone_session in order
   to be able to login with ldap user


Install
=======

- Add eea.devel to your eggs section in your buildout and re-run buildout.
  You can download a sample buildout from
  https://github.com/eea/eea.devel/tree/master/buildouts/plone4
- Within console search for created admin user name and password
- Within console search for created Plone users by role
- Login to `ZMI`_ with user **eeadevel**


Source code
===========

- Latest source code (Plone 4 compatible):
  https://github.com/eea/eea.devel


Copyright and license
=====================
The Initial Owner of the Original Code is European Environment Agency (EEA).
All Rights Reserved.

The EEA Devel (the Original Code) is free software;
you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation;
either version 2 of the License, or (at your option) any later
version.

More details under docs/License.txt


Funding
=======

EEA_ - European Environment Agency (EU)

.. _EEA: https://www.eea.europa.eu/
.. _ZMI: http://localhost:2020/manage
