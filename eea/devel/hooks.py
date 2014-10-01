""" Development hooks
"""
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
        """
        return self._root

    @property
    def sites(self):
        """ Plone Sites
        """
        return self._sites

    @property
    def user(self):
        """ Zope user
        """
        return self._user

    @property
    def changed(self):
        """ Changed
        """
        return self._changed

    @property
    def devel(self):
        """ Development enabled
        """
        return self._devel

    #
    # Utils
    #
    def password(self, size=16):
        """ Generate random password
        """
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(size)).encode('utf8')

    #
    # Zope root specific methods
    #
    def add_zope_user(self):
        """ Add zope user
        """
        if not self.devel:
            return
        acl_users = getattr(self.root, 'acl_users', None)
        users = getattr(acl_users, 'users', None)
        roles = getattr(acl_users, 'roles', None)
        if not (users and roles):
            return

        password = self.password()
        try:
            users.addUser(self.user, self.user, password)
            roles.assignRoleToPrincipal('Manager', self.user)
        except KeyError, err:
            users.updateUserPassword(self.user, password)
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
            users.removeUser(self.user)
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
        return username

    def remove_plone_users(self):
        """ Remove development Plone users created by this package
        """
        site = getSite()
        mtool = getToolByName(site, 'portal_membership')
        roles = [r for r in mtool.getPortalRoles() if r != 'Owner']

        users = set()
        for role in roles:
            username = self.remove_plone_user(role)
            if not username:
                continue

            users.add(username)

        if users:
            mtool.deleteMembers(tuple(users))
            self._changed = True
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
            setSite(oldSite)

    def __call__(self):
        if not self.devel:
            return self.cleanup()
        return self.apply()
