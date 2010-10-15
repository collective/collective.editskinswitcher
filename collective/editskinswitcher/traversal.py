import logging

from zope.annotation.interfaces import IAnnotations

from collective.editskinswitcher.browser.view import ANNOTATION_KEY

from AccessControl import Unauthorized, getSecurityManager
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('editskinswitcher')


def anonymous(request=None):
    if request is None:
        # I thought I had seen this working, but under normal
        # circumstances when traversing you are always anonymous...
        anon = (getSecurityManager().getUser().getUserName() ==
                'Anonymous User')
    elif request.cookies.get('__ac'):
        anon = False
    else:
        anon = True
    logger.debug("Anonymous? %s", anon)
    return anon


def check_auth(request):
    if anonymous(request):
        raise Unauthorized('Go away')


def edit_url(request, props):
    ''' The default switch check based on a subdomain of cms, edit or manage'''
    from collective.editskinswitcher.utils import is_edit_url
    val = is_edit_url(request.getURL())
    logger.debug("Is edit url? %s", val)
    return val


def specific_domain(request, props):
    specific_domains = props.getProperty('specific_domains', ())
    if specific_domains != ():
        thisurl = request.getURL()
        if thisurl in specific_domains:
            logger.debug("This url is in a specific domain.")
            return True
    logger.debug("This url is NOT in a specific domain.")
    return False


def ssl_url(request, props):
    parts = request.getURL().split('://')
    if parts[0] == 'https':
        logger.debug("https url")
        return True
    logger.debug("normal http url")
    return False


def force_login(request, props):
    force_login_header = props.getProperty('force_login_header', None)
    if not force_login_header:
        return False
    if request.get(force_login_header, None):
        logger.debug("Login will be forced.")
        return True
    logger.debug("Login will NOT be forced.")
    return False


def admin_header(request, props):
    admin_header = props.getProperty('admin_header', 'HTTP_PLONEADMIN')
    if request.get(admin_header, None):
        logger.debug("admin header found")
        return True
    logger.debug("no admin header found")
    return False


def need_authentication(request, props):
    """This is for skin switching based on authentication only."""
    val = props.getProperty('need_authentication', False)
    logger.debug("Need authentication? %s", val)
    return val


methods = {'based on edit URL': edit_url,
           'based on specific domains': specific_domain,
           'based on SSL': ssl_url,
           'based on admin header': admin_header,
           'no URL based switching': need_authentication}


def really_switch_skin(object, request, skin_name):
    # object might be a view, for instance a KSS view.  Use the
    # context of that object then.
    try:
        changeSkin = object.changeSkin
    except AttributeError:
        changeSkin = object.context.changeSkin
    changeSkin(skin_name, request)


def switch_skin(object, event):
    """Switch to the Plone Default skin when we are editing.

    Note: when we bail out before the changeSkin call, then we show
    the normal theme, which presumably is a custom theme for this
    website.

    If we do the changeSkin call, this means we switch to the edit
    skin, which normally is the Plone Default skin.
    """
    request = event.request

    ns = IAnnotations(object).get(ANNOTATION_KEY, None)
    if ns is not None:
        skin_name = ns.get("default-skin", None)
        if skin_name is not None:
            really_switch_skin(object, request, skin_name)

    portal_props = getToolByName(object, 'portal_properties', None)
    if portal_props is None:
        return None
    editskin_props = portal_props.get('editskin_switcher')
    if editskin_props is None:
        return None

    # Okay, we have a property sheet we can use.
    edit_skin = editskin_props.getProperty('edit_skin', '')

    if force_login(request, editskin_props):
        # We have a header that forces us to be logged in; so add a
        # hook at the end of the traversal to check that we really are
        # logged in.
        request.post_traverse(check_auth, (request, ))

    # Check if we need authentication first, possibly in addition to
    # one of the other tests
    if need_authentication(request, editskin_props) and anonymous(request):
        logger.debug("need auth, but am anonymous: staying at normal skin.")
        return None

    # Try to find a reason for switching to the edit skin.  When one
    # of the selected actions returns True, we switch the skin.
    switches = editskin_props.getProperty('switch_skin_action', [])
    if not isinstance(switches, tuple):
        # Old data using a selection instead of multiple selection,
        # which returns a string instead of a tuple of strings.
        switches = (switches, )

    found = False
    for switch in switches:
        method = methods.get(switch)
        if not method:
            continue
        if method(request, editskin_props):
            found = True
            break
    if not found:
        # No switching
        logger.debug("no switching, staying at normal skin")
        return None

    logger.debug("will switch to edit skin")

    # Use to preview default skin in edit skin mode
    if request.get('mutate_skin', '') == 'default':
        return None

    # Assume that if you get here you are switching to the edit skin
    # ... flag this for the purposes of caching / kss loading etc.
    request.set('editskinswitched', 1)

    # If the edit_skin does not exist, the next call is
    # intelligent enough to use the default skin instead.
    really_switch_skin(object, request, edit_skin)
    return None
