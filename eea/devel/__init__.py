""" Main product initializer
"""
# pylint: disable-msg=C0111
import string
import random
import transaction
import logging
import Zope2
logger = logging.getLogger('eea.devel')

def PASSWORD(size=16):
    # Generate random password
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))

def _create_devel_user(root):
    # Create devel user
    acl_users = getattr(root, 'acl_users', None)
    users = getattr(acl_users, 'users', None)
    roles = getattr(acl_users, 'roles', None)
    if not (users and roles):
        return 0

    password = PASSWORD()
    try:
        users.addUser('eeadevel', 'eeadevel', password)
        roles.assignRoleToPrincipal('Manager', 'eeadevel')
    except KeyError, err:
        users.updateUserPassword('eeadevel', password)
    except Exception, err:
        logger.debug(err)
        return 0

    logger.warn(
        "\n******************************************************************\n"
        "\nZOPE DEVEL MANAGER ADDED user: eeadevel password: %s\n"
        "\n******************************************************************",
        password
    )
    return 1

def _remove_devel_user(root):
    # Remove devel user
    acl_users = getattr(root, 'acl_users', None)
    users = getattr(acl_users, 'users', None)
    roles = getattr(acl_users, 'roles', None)
    if not (users and roles):
        return 0

    try:
        roles.removeRoleFromPrincipal('Manager', 'eeadevel')
        users.removeUser('eeadevel')
    except Exception, err:
        logger.debug(err)
        return 0

    logger.warn(
        "\n******************************************************************\n"
        "\nZOPE DEVEL MANAGER REMOVED. user: eeadevel\n"
        "\n******************************************************************"
    )
    return 1

def _remove_cookie_domain(root):
    # Remove cookie domain
    acl_users = getattr(root, 'acl_users', None)
    plone_session = getattr(acl_users, 'plone_session', None)
    if not plone_session:
        return 0

    cookie_domain = getattr(plone_session, 'cookie_domain', '')
    if not cookie_domain:
        return 0

    logger.warn('Remove cookie_domain: %s', cookie_domain)
    plone_session.cookie_domain = ''
    return 1

def initialize(context):
    # Initializer called when used as a Zope 2 product.

    #
    # LocalSiteHook
    #
    transaction.get().note('eea.devel: before applying development hacks')
    transaction.commit()

    changed = 0

    root = Zope2.app()
    www = getattr(root, 'www', None)
    if not www:
        logger.warn("!!! Missing Plone/EEA Site 'www'. Nothing to hack !!!")
        return

    import Globals
    if not Globals.DevelopmentMode:
        logger.warn("!!! DISABLED. Run in debug mode to enable !!!")
        changed += _remove_devel_user(root)
    else:
        # Create eeadevel user
        changed += _create_devel_user(root)

        # Remove Cookie domain from plone_session
        changed += _remove_cookie_domain(www)

    if changed:
        transaction.get().note('eea.devel: applying development hacks')
        transaction.commit()
