# encoding: utf-8

import gvsig
import math
import statistics
import sys

from gvsig import geom
from gvsig import uselib
uselib.use_plugin("org.gvsig.topology.app.mainplugin")

from org.gvsig.expressionevaluator import ExpressionEvaluatorLocator
# from org.gvsig.expressionevaluator import GeometryExpressionEvaluatorLocator
from org.gvsig.topology.lib.api import TopologyLocator
from org.gvsig.topology.lib.spi import AbstractTopologyRule

from deletePolygonAction import DeletePolygonAction
from markPolygonAction import MarkPolygonAction

class MustNotHaveGapsPolygonRule(AbstractTopologyRule):
    
    geomName = None
    expression = None
    expressionBuilder = None
    hasGaps = False
    
    def __init__(self, plan, factory, tolerance, dataSet1):
        AbstractTopologyRule.__init__(self, plan, factory, tolerance, dataSet1, dataSet1)
        self.addAction(DeletePolygonAction())
        self.addAction(MarkPolygonAction())
    
    def findGaps(self, polygon1, theDataSet2, tolerance1):
        for featureReference in theDataSet2.query(polygon1):
            feature2 = featureReference.getFeature()
            polygon2 = feature2.getDefaultGeometry()
        
            buffer1 = polygon1.buffer(tolerance1)
            
            if not polygon1.equals(polygon2) and buffer1.intersects(polygon2):
                
                try:
                    difference1 = buffer1.union(polygon2).difference(polygon1).difference(polygon2)
                except:
                    difference1 = None
                if difference1 != None and (difference1.getGeometryType().getType() == geom.POLYGON  or difference1.getGeometryType().isTypeOf(geom.POLYGON)):
                    
                    # Difference cleaning begins
                    
                    numVertices = difference1.getNumVertices()
                    xCentroid, yCentroid = difference1.centroid().getX(), difference1.centroid().getY()
                    distances = []
                    for i in range(0, numVertices):
                        distances.append(math.sqrt(math.pow(difference1.getVertex(i).getX() - xCentroid, 2) + math.pow(difference1.getVertex(i).getY() - yCentroid, 2)))
                    
                    distancesMean = statistics.mean(distances)
                    distancesStDev = statistics.stdev(distances)
                    removableVertices = []
                    for i in range(0, numVertices):
                        if abs(distances[i] - distancesMean) > 2 * distancesStDev:
                            removableVertices.append(difference1.getVertex(i))
                    
                    for i in range(0, len(removableVertices)):
                        for j in range(0, difference1.getNumVertices()):
                            if difference1.getVertex(j).equals(removableVertices[i]):
                                difference1.removeVertex(j)
                                break
                    
                    # Difference cleaning ends
                    
                    try:
                        intersection1 = difference1.intersection(polygon1)
                        intersection2 = difference1.intersection(polygon2)
                    except:
                        intersection1 = None
                        intersection2 = None
                    if intersection1 != None and intersection2 != None:
                        geometryType1 = intersection1.getGeometryType()
                        geometryType2 = intersection2.getGeometryType()
                        if geometryType1.getType() in (geom.LINE, geom.MULTILINE) and geometryType2.getType() in (geom.LINE, geom.MULTILINE):
                            try:
                                intersection3 = intersection1.intersection(intersection2)
                            except:
                                intersection3 = None
                            if intersection3 != None:
                                geometryType3 = intersection3.getGeometryType()
                                if geometryType3.getType() in (geom.LINE, geom.MULTILINE):
                                    try:
                                        intersection4 = polygon1.intersection(polygon2)
                                    except:
                                        intersection4 = None
                                    if intersection4 != None:
                                        geometryType4 = intersection4.getGeometryType()
                                        if geometryType4.getType() in (geom.LINE, geom.MULTILINE):
                                            if not intersection3.equals(intersection4):
                                                self.hasGaps = True
                            else:
                                self.hasGaps = True
                                break
            if self.hasGaps:
                break
    
    def checkGaps(self, polygon1, theDataSet2, tolerance1):
        result = [False, []]
        if theDataSet2.getSpatialIndex() != None:
            if not self.hasGaps: 
                self.findGaps(polygon1, theDataSet2, tolerance1)
            if self.hasGaps:
                result[0] = True
                self.hasGaps = False
        else:
            if self.expression == None:
                self.expression = ExpressionEvaluatorLocator.getManager().createExpression()
                self.expressionBuilder = ExpressionEvaluatorLocator.getManager().createExpressionBuilder()
                # self.expressionBuilder = GeometryExpressionEvaluatorLocator.getManager().createExpressionBuilder()
                store2 = theDataSet2.getFeatureStore()
                self.geomName = store2.getDefaultFeatureType().getDefaultGeometryAttributeName()
            self.expression.setPhrase(
                self.expressionBuilder.ifnull(
                    self.expressionBuilder.column(self.geomName),
                    self.expressionBuilder.constant(False),
                    self.expressionBuilder.and(
                        self.expressionBuilder.ST_Intersects(
                            self.expressionBuilder.geometry(polygon1),
                            self.expressionBuilder.ST_Difference(
                                self.expressionBuilder.ST_MakePolygon(
                                    self.expressionBuilder.ST_ExteriorRing(
                                        self.expressionBuilder.ST_Union(
                                            self.expressionBuilder.geometry(polygon1),
                                            self.expressionBuilder.column(self.geomName)
                                        )
                                    )
                                ),
                                self.expressionBuilder.ST_Union(
                                    self.expressionBuilder.geometry(polygon1),
                                    self.expressionBuilder.column(self.geomName)
                                )
                            )
                        ),
                        self.expressionBuilder.gt(
                            self.expressionBuilder.ST_Length(
                                self.expressionBuilder.ST_Intersection(
                                    self.expressionBuilder.geometry(polygon1),
                                        self.expressionBuilder.ST_Difference(
                                            self.expressionBuilder.ST_MakePolygon(
                                                self.expressionBuilder.ST_ExteriorRing(
                                                    self.expressionBuilder.ST_Union(
                                                        self.expressionBuilder.geometry(polygon1),
                                                        self.expressionBuilder.column(self.geomName)
                                                    )
                                                )
                                            ),
                                            self.expressionBuilder.ST_Union(
                                                self.expressionBuilder.geometry(polygon1),
                                                self.expressionBuilder.column(self.geomName)
                                            )
                                        )
                                )
                            ),
                            self.expressionBuilder.constant(0.0)
                        )
                    )
                ).toString()
            )
            if theDataSet2.findFirst(self.expression) != None:
                result[0] = True
        return result
    
    def check(self, taskStatus, report, feature1):
        try:
            polygon1 = feature1.getDefaultGeometry()
            tolerance1 = self.getTolerance()
            theDataSet2 = self.getDataSet1()
            geometryType1 = polygon1.getGeometryType()
            if geometryType1.getSubType() == geom.D2 or geometryType1.getSubType() == geom.D2M:
                if geometryType1.getType() == geom.POLYGON or geometryType1.isTypeOf(geom.POLYGON):
                    result = self.checkGaps(polygon1, theDataSet2, tolerance1)
                    if result[0]:
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
                            "The polygon has gaps.",
                            ""
                        )
                else:
                    if geometryType1.getType() == geom.MULTIPOLYGON or geometryType1.isTypeOf(geom.MULTIPOLYGON):
                        n1 = polygon1.getPrimitivesNumber()
                        for i in range(0, n1 + 1):
                            result = self.checkGaps(polygon1.getSurfaceAt(i), theDataSet2, tolerance1)
                            if result[0]:
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
                                    "The polygon has gaps.",
                                    ""
                                )
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
        except:
            ex = sys.exc_info()[1]
            gvsig.logger("Can't execute rule. Class Name: " + ex.__class__.__name__ + ". Exception: " + str(ex), gvsig.LOGGER_ERROR)
    
def main(*args):
    pass
