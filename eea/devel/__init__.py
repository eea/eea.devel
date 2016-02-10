""" Main product initializer
"""
import transaction
import logging
import Zope2
import Globals
from eea.devel.hooks import Setup
logger = logging.getLogger('eea.devel')


def initialize(context):
    """ Initializer called when used as a Zope 2 product.
    """
    db = getattr(Globals, 'DB', None)
    storage = getattr(db, 'storage', None)
    isReadOnly = getattr(storage, 'isReadOnly', lambda: False)
    if isReadOnly():
        logger.warn("!!! DISABLED. Database is mounted read-only !!!")
        return

    try:
        transaction.get().note('eea.devel: before applying development hacks')
        transaction.commit()
    except Exception, err:
        logger.warn(
            "\n************************************************************\n"
            "\nCan NOT apply development hacks. See error bellow.          \n"
            "\n**************************************************************"
        )
        logger.exception(err)
        transaction.abort()
        return

    devel = True if Globals.DevelopmentMode else False
    if not devel:
        logger.warn("!!! DISABLED. Run in debug mode to enable !!!")

    root = Zope2.app()
    setup = Setup(root, devel)
    setup()

    if setup.changed:
        try:
            transaction.get().note('eea.devel: applying development hacks')
            transaction.commit()
        except Exception, err:
            logger.warn(
              "\n**********************************************************\n"
              "\nCould NOT apply development hacks. See error bellow.      \n"
              "\n************************************************************"
            )
            logger.exception(err)
            transaction.abort()
            return
