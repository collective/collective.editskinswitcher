from zope.publisher.browser import TestRequest as baseTestRequest
from Products.CMFCore.utils import getToolByName
from Products.Five import zcml
from Products.CMFCore.exportimport.skins import importSkinsTool
from Products.GenericSetup.tests.common import DummyImportContext
import collective.editskinswitcher.tests

SKINCONFIG = """\
<?xml version="1.0"?>
<!-- This file adds in the Monty Python test skins layer with a test template -->

<object name="portal_skins" allow_any="False" cookie_persistence="False" default_skin="Monty Python Skin">

 <object name="editskinswitcher_tests"
    meta_type="Filesystem Directory View"
    directory="collective.editskinswitcher.tests:skins/editskinswitcher_tests"/>

 <skin-path name="Monty Python Skin" based-on="Plone Default">
  <layer name="editskinswitcher_tests"
     insert-after="custom"/>
 </skin-path>

</object>
"""

def _hold(self, object):
    """Hold a reference to an object to delay it's destruction until mine

    Taken from ZPublisher/BaseRequest.py
    Needed by CMFCore/Skinnable.py(142)changeSkin()
    """
    if self._held is not None:
        self._held=self._held+(object, )


class TestRequest(baseTestRequest):
    """ This just adds the set, get methods of the real REQUEST object """

    def set(self,key,value):
        self.form[key] = value
        
TestRequest._hold = _hold
                                                                        
def new_default_skin(portal):
    """ Register test skins folder with extra test template - zcml
        then make new default skin based on Plone Default with test skin - xml
    """
    sk_tool = getToolByName(portal, 'portal_skins')
    zcml.load_config('skins.zcml', collective.editskinswitcher.tests)
    context = DummyImportContext(portal, False)
    context._files['skins.xml'] = SKINCONFIG
    importSkinsTool(context)


class FakeTraversalEvent(object):

    def __init__(self, object, request):
        self.object = object
        self.request = request