# encoding: utf-8

import gvsig
import sys

from gvsig import uselib
uselib.use_plugin("org.gvsig.topology.app.mainplugin")

from org.gvsig.fmap.geom import Geometry
from org.gvsig.tools.util import ListBuilder
from org.gvsig.topology.lib.api import TopologyLocator
from org.gvsig.topology.lib.spi import AbstractTopologyRuleFactory

from mustNotHaveGapsPolygonRule import MustNotHaveGapsPolygonRule

class MustNotHaveGapsPolygonRuleFactory(AbstractTopologyRuleFactory):
      
    def __init__(self):
        AbstractTopologyRuleFactory.__init__(
            self,
            "MustNotHaveGapsPolygon",
            "Must Not Have Gaps",
            "This rule requires adjacent polygons not to have gaps.",
            ListBuilder().add(Geometry.TYPES.SURFACE).add(Geometry.TYPES.MULTISURFACE).asList()
        )
    
    def createRule(self, plan, dataSet1, dataSet2, tolerance):
        rule = MustNotHaveGapsPolygonRule(plan, self, dataSet1)
        return rule

def selfRegister():
    try:
        manager = TopologyLocator.getTopologyManager()
        manager.addRuleFactories(MustNotHaveGapsPolygonRuleFactory())
    except:
        ex = sys.exc_info()[1]
        gvsig.logger("Can't register rule. Class Name: " + ex.__class__.__name__ + ". Exception: " + str(ex), gvsig.LOGGER_ERROR)

def main(*args):
    pass
