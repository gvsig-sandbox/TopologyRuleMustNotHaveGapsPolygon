# encoding: utf-8

import gvsig
import math
import statistics
import sys

from gvsig import geom
from gvsig import uselib
uselib.use_plugin("org.gvsig.topology.app.mainplugin")

from org.gvsig.expressionevaluator import ExpressionEvaluatorLocator
from org.gvsig.expressionevaluator import GeometryExpressionUtils
from org.gvsig.topology.lib.api import TopologyLocator
from org.gvsig.topology.lib.spi import AbstractTopologyRule
from org.gvsig.fmap.geom.jts.util import JTSUtils

from deletePolygonAction import DeletePolygonAction
from markPolygonAction import MarkPolygonAction

def __getTolerance(t):
    if t < 0:
        return 1
    return t

class GapsResult(object):
    def __init__(self, hasGaps, errorGeom):
        self.hasGaps = hasGaps
        self.errorGeom = errorGeom

    def getGeoms(self):
        return (self.errorGeom,)

class MustNotHaveGapsPolygonRule(AbstractTopologyRule):
    
    geomName = None
    expression = None
    expressionBuilder = None
    
    def __init__(self, factory=None, tolerance=None, dataSet1=None):
        if factory == None:
            AbstractTopologyRule.__init__(self)
        else :
            AbstractTopologyRule.__init__(self, factory, __getTolerance(tolerance), dataSet1, dataSet1)
            #self.addAction(CreatePolygonAction())
            #self.addAction(MergePolygonAction())
    
    def isGapInTolerance(self, polygon1, gap, tolerance):
        centroid = gap.centroid()
        if polygon1.distance(centroid) > tolerance:
            return False
        return True

    def validateCoverage(self, polygon1, theDataSet2, tolerance1):
        print "polygon1 = %s"%polygon1.convertToWKTQuietly()
        envelope = polygon1.getEnvelope()
        envelopeGeometry = envelope.getGeometry()
        polygons = theDataSet2.query(polygon1)

        coverage = list()
        for featureReference in polygons :
            feature2 = featureReference.getFeature()
            polygon2 = feature2.getDefaultGeometry()
            if not polygon2.intersects(envelopeGeometry) or polygon2.equals(polygon1):
              print "Salto el Id %s al obtener la cobertura "%feature2.get("ID")
              continue
            coverage.append(polygon2)
        print "Envelope = %s"%envelope
        errorGeom = polygon1.validateCoverage(coverage, tolerance1)
        if errorGeom != None:
            return GapsResult(True, errorGeom)
        return GapsResult(False, None)

    def isGap(self, gap, polygon1, theDataSet2):
        if gap == None:
            return False
        print "gap = %s"%gap.convertToWKTQuietly()
        if gap.getEnvelope().isCollapsed():
            print "collapsed"
            return False
        if not gap.intersects(polygon1):
            print "not intersects"
            return False
        polygons = theDataSet2.query(polygon1)
        intersects = False
        for featureReference in polygons:
            feature = featureReference.getFeature()
            polygon = feature.getDefaultGeometry()
            if polygon.equals(polygon1):
                continue
            if gap.intersects(polygon):
                intersects = True;
                break
        return intersects
    
    def check(self, taskStatus, report, feature1):
        try:
            print "id =%s"%feature1.get("ID")
            srs = feature1.getDefaultSRS()
            polygon1 = feature1.getDefaultGeometry()
            tolerance1 = self.getTolerance()
            theDataSet2 = self.getDataSet1()
            result = self.validateCoverage(polygon1, theDataSet2, tolerance1)
            if result.hasGaps:
                for errorGeom in result.getGeoms():
                    report.addLine(self,
                        self.getDataSet1(),
                        None,
                        polygon1,
                        errorGeom,
                        feature1.getReference(),
                        None,
                        -1,
                        -1,
                        False,
                        "The polygonal coverage is topologically wrong.",
                        ""
                    )
            result = polygon1.findGaps(tolerance1)
            if result != None: # or not result.isEmpty():
                report.addLine(self,
                    self.getDataSet1(),
                    None,
                    polygon1,
                    result,
                    feature1.getReference(),
                    None,
                    -1,
                    -1,
                    False,
                    "The polygon has gaps.",
                    ""
                )

            '''
            geometryType1 = polygon1.getGeometryType()
            if geometryType1.getSubType() == geom.D2 or geometryType1.getSubType() == geom.D2M:
                if geometryType1.getType() == geom.POLYGON or geometryType1.isTypeOf(geom.POLYGON):
                    result = self.validateCoverage(polygon1, theDataSet2, tolerance1)
                    if result.hasGaps:
                        for errorGeom in result.getGeoms():
                            report.addLine(self,
                                self.getDataSet1(),
                                None,
                                polygon1,
                                errorGeom,
                                feature1.getReference(),
                                None,
                                -1,
                                -1,
                                False,
                                "The coverage is topologically wrong.",
                                ""
                            )
                    result = polygon1
                else:
                    if geometryType1.getType() == geom.MULTIPOLYGON or geometryType1.isTypeOf(geom.MULTIPOLYGON):
                        n1 = polygon1.getPrimitivesNumber()
                        for i in range(0, n1):
                            result = self.checkGaps(polygon1.getSurfaceAt(i), theDataSet2, tolerance1, srs)
                            #print "check 205"
                            if result.hasGaps:
                                #print "check 207"
                                for errorGeom in result.getGeoms():
                                    report.addLine(self,
                                        self.getDataSet1(),
                                        None,
                                        polygon1,
                                        errorGeom,
                                        feature1.getReference(),
                                        None,
                                        -1,
                                        -1,
                                        False,
                                        "The coverage is topologically wrong.",
                                        ""
                                    )
                            result = self.checkGaps(polygon1.getSurfaceAt(i), theDataSet2, tolerance1, srs)
                            #print "check 205"
                                #print "check 221"
                            #print "check 222"
                        #print "check 223"
            else:
                report.addLine(self,
                    self.getDataSet1(),
                    None,
                    polygon1,
                    polygon1,
                    feature1.getReference(),
                    None,
                    -1,
                    -1,
                    False,
                    "Unsupported geometry subtype.",
                    ""
                )
            '''
        except:
            ex = sys.exc_info()[1]
            gvsig.logger("Can't execute rule. Class Name: " + ex.__class__.__name__ + ". Exception: " + str(ex), gvsig.LOGGER_ERROR)
    
def main(*args):
    pass
