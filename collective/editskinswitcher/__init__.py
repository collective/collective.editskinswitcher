import monkeypatches

from collective.editskinswitcher import permissions

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
    permissions.initialize()
