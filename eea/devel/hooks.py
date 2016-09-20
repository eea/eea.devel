""" Development hooks

    >>> from plone import api
    >>> portal = layer['portal']

"""
import os
import string
import random
import logging
from zope.component.hooks import setSite, getSite
from plone import api
from eea.devel.config import ZOPEUSER
from Products.CMFCore.utils import getToolByName
logger = logging.getLogger('eea.devel')


class Setup(object):
    """ Setup development environment

        >>> from eea.devel.hooks import Setup
        >>> root = portal.getParentNode()
        >>> setup = Setup(root, devel=True)
        >>> setup
        <eea.devel.hooks.Setup object at ...>

    """
    def __init__(self, root, devel=True):
        self._root = root
        self._sites = root.objectValues('Plone Site')
        self._user = ZOPEUSER
        self._devel = devel
        self._changed = False

    #
    # Read-only
    #
    @property
    def root(self):
        """ Zope root

            >>> setup.root
            <Application at >

        """
        return self._root

    @property
    def sites(self):
        """ Plone Sites

            >>> setup.sites
            [<PloneSite at /plone>]

        """
        return self._sites

    @property
    def user(self):
        """ Zope user

            >>> setup.user
            'eeadevel'

        """
        return self._user

    @property
    def changed(self):
        """ Changed

            >>> setup.changed
            False

        """
        return self._changed

    @property
    def devel(self):
        """ Development enabled

            >>> setup.devel
            True

        """
        return self._devel

    #
    # Utils
    #
    def password(self, size=16):
        """ Generate random password

            >>> setup.password()
            '...'

        """
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size)).encode('utf8')

    #
    # Zope root specific methods
    #
    def add_zope_user(self):
        """ Add zope user
        """
        acl_users = getattr(self.root, 'acl_users', None)
        users = getattr(acl_users, 'users', None)
        roles = getattr(acl_users, 'roles', None)
        if not (users and roles):
            return

        password = self.password()
        try:
            users.addUser(self.user, self.user, password)
        except KeyError, err:
            users.updateUserPassword(self.user, password)
        except Exception, err:
            logger.exception(err)
            return

        try:
            roles.assignRoleToPrincipal('Manager', self.user)
        except Exception, err:
            logger.exception(err)
            return

        logger.warn(
            "\n**************************************************************\n"
            "\nZOPE DEVEL MANAGER ADDED user: %s password: %s\n"
            "\n***************************************************************",
            self.user,
            password
        )
        self._changed = True

    def remove_zope_user(self):
        """ Remove zope user
        """
        acl_users = getattr(self.root, 'acl_users', None)
        users = getattr(acl_users, 'users', None)
        roles = getattr(acl_users, 'roles', None)
        if not (users and roles):
            return

        try:
            roles.removeRoleFromPrincipal('Manager', self.user)
        except Exception, err:
            logger.exception(err)
            return

        logger.warn(
            "\n**************************************************************\n"
            "\nZOPE DEVEL MANAGER REMOVED. user: %s\n"
            "\n***************************************************************",
            self.user
        )
        self._changed = True

    #
    # Plone specific methods
    #
    def remove_cookie_domain(self):
        """ Remove cookie domain
        """

        site = getSite()
        acl_users = getattr(site, 'acl_users', None)
        plone_session = getattr(acl_users, 'plone_session', None)
        if not plone_session:
            return None

        cookie_domain = getattr(plone_session, 'cookie_domain', '')
        if not cookie_domain:
            return None

        logger.warn('Remove cookie_domain: %s', cookie_domain)
        plone_session.cookie_domain = ''
        self._changed = True

    def add_plone_user(self, role):
        """ Create plone users for main roles
        """
        username = ("eeaDevel%s" % role.replace(' ', '')).encode('utf8')
        user = api.user.get(username)
        password = self.password()

        if not user:
            useremail = "%s@example.com" % username
            api.user.create(
                email=useremail,
                username=username,
                password=password,
                properties={
                    'fullname': ('EEA Devel %s' % role).encode('utf8')
                }
            )
            if role != 'Member':
                api.user.grant_roles(username=username, roles=[role])
        else:
            user.setSecurityProfile(password=password)

        logger.warn(
            "\n**************************************************************\n"
            "\nPLONE DEVEL USER WITH ROLE %s ADDED user: %s password: %s\n"
            "\n***************************************************************",
            role, username, password
        )
        self._changed = True


    def add_plone_users(self):
        """ Add development Plone users for each role
        """
        site = getSite()
        mtool = getToolByName(site, 'portal_membership')
        roles = [r for r in mtool.getPortalRoles() if r != 'Owner']
        for role in roles:
            try:
                self.add_plone_user(role)
            except Exception, err:
                logger.exception(err)

    def remove_plone_user(self, role):
        """ Remove development Plone user by role
        """
        username = ("eeaDevel%s" % role.replace(' ', '')).encode('utf8')
        user = api.user.get(username)
        if not user:
            return

        api.user.revoke_roles(username=username, roles=[role, 'Member'])
        return username

    def remove_plone_users(self):
        """ Remove development Plone users created by this package
        """
        site = getSite()
        mtool = getToolByName(site, 'portal_membership')
        roles = [r for r in mtool.getPortalRoles() if r != 'Owner']

        for role in roles:
            username = self.remove_plone_user(role)
            if username:
                self._changed = True

    def update_memcached_host(self):
        """ Update memcached host to localhost
        """
        servers = os.environ.get("MEMCACHE_SERVER", None)
        if not servers:
            logger.warn("MEMCACHE_SERVER environment not set. Nothing to do.")
            return

        site = getSite()
        servers = tuple(servers.split(','))
        memcached_managers = site.objectValues('Memcached Manager')
        for obj in memcached_managers:
            current = obj._settings.get('settings', ())
            if current == servers:
                continue
            obj._settings['servers'] = servers
            obj._p_changed = True
            self._changed = True

        logger.warn(
            'Memcached domain set to %s for all "Memcached Manage" objects.',
            servers)

    #
    # API
    #
    def cleanup(self):
        """ Cleanup development hooks
        """
        # Zope
        self.remove_zope_user()

        # Plone
        for site in self.sites:
            oldSite = getSite()
            setSite(site)
            self.remove_plone_users()
            setSite(oldSite)

    def apply(self):
        """ Apply development hooks
        """
        # Zope
        self.add_zope_user()

        # Plone
        for site in self.sites:
            oldSite = getSite()
            setSite(site)
            self.remove_cookie_domain()
            self.add_plone_users()
            self.update_memcached_host()
            setSite(oldSite)

    def __call__(self):
        """ Run development setup

        This setup is called on zope startup. Let's check if everything was set

        Zope admin user:

            >>> setup.root.acl_users.users.getUserIdForLogin('eeadevel')
            'eeadevel'

            >>> setup.root.acl_users.roles.listAssignedPrincipals('Manager')
            [...'eeadevel'...]

        Plone users for each role:

            >>> api.user.get('eeaDevelManager')
            <MemberData at /plone/portal_memberdata/eeaDevelManager ...>

            >>> api.user.get_roles('eeaDevelManager')
            ['Member', 'Manager', 'Authenticated']

            >>> api.user.get('eeaDevelReviewer')
            <MemberData at /plone/portal_memberdata/eeaDevelReviewer ...>

            >>> api.user.get_roles('eeaDevelReviewer')
            ['Member', 'Reviewer', 'Authenticated']

        Zope restart (fg):

            >>> setup()

        Cleanup is called when Zope is started normally (not fg)

            >>> setup._devel = False
            >>> setup()

        Zope user shouldn't have Manager role anymore

            >>> setup.root.acl_users.roles.listAssignedPrincipals('Manager')
            [('admin', 'admin')]


        Neither Plone users

            >>> api.user.get_roles('eeaDevelManager')
            ['Authenticated']

            >>> api.user.get_roles('eeaDevelReviewer')
            ['Authenticated']

        Second Zope restart normally:

            >>> setup()

        """
        if not self.devel:
            return self.cleanup()
        return self.apply()
