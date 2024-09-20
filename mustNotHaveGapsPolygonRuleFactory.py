# encoding: utf-8

import gvsig
import sys
import locale
import os

from gvsig import uselib
uselib.use_plugin("org.gvsig.topology.app.mainplugin")

from org.gvsig.fmap.geom import Geometry
from org.gvsig.tools.util import ListBuilder
from org.gvsig.topology.lib.api import TopologyLocator
from org.gvsig.topology.lib.spi import AbstractTopologyRuleFactory
from org.gvsig.json import Json
from java.net import URL

import mustNotHaveGapsPolygonRule
reload(mustNotHaveGapsPolygonRule)

from mustNotHaveGapsPolygonRule import MustNotHaveGapsPolygonRule
from org.gvsig.json.serializers import DefaultObjectSerializer

class MustNotHaveGapsPolygonRuleSerializer(DefaultObjectSerializer):
    def __init__(self, *args):
        DefaultObjectSerializer.__init__(self,MustNotHaveGapsPolygonRule)

    def createNewObject(self):
        x = MustNotHaveGapsPolygonRule()
        return x


class MustNotHaveGapsPolygonRuleFactory(AbstractTopologyRuleFactory):
      
    def __init__(self):
        AbstractTopologyRuleFactory.__init__(
            self,
            "MustNotHaveGapsPolygon",
            "Must Not Have Gaps",
            "This rule requires adjacent polygons not to have gaps.",
            ListBuilder().add(Geometry.TYPES.SURFACE).add(Geometry.TYPES.MULTISURFACE).asList()
        )

        lcl = locale.getdefaultlocale()
        f = gvsig.getResource(__file__, lcl[0],"MustNotHaveGapsPolygon.json")
        if not os.path.exists(f):
            f = gvsig.getResource(__file__, "en","MustNotHaveGapsPolygon.json")

        url = URL("file",None,f)
        self.load_from_resource(url)\n
    
    def createRule(self, dataSet1, dataSet2, tolerance):
        rule = MustNotHaveGapsPolygonRule(self, tolerance, dataSet1)
        return rule

def selfRegister():
    try:
        manager = TopologyLocator.getTopologyManager()
        manager.addRuleFactories(MustNotHaveGapsPolygonRuleFactory())

        Json.getManager().registerSerializer2(MustNotHaveGapsPolygonRuleSerializer())

    except:
        ex = sys.exc_info()[1]
        gvsig.logger("Can't register rule. Class Name: " + ex.__class__.__name__ + ". Exception: " + str(ex), gvsig.LOGGER_ERROR)

def main(*args):
    selfRegister()
    pass
