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

    transaction.get().note('eea.devel: before applying development hacks')
    transaction.commit()

    devel = True if Globals.DevelopmentMode else False
    if not devel:
        logger.warn("!!! DISABLED. Run in debug mode to enable !!!")

    root = Zope2.app()
    setup = Setup(root, devel)
    setup()

    if setup.changed:
        transaction.get().note('eea.devel: applying development hacks')
        transaction.commit()
