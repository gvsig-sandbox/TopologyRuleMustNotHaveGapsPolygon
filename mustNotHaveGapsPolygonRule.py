# encoding: utf-8

import gvsig
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
    gaps = None
    
    def __init__(self, plan, factory, dataSet1):
        AbstractTopologyRule.__init__(self, plan, factory, 0, dataSet1, dataSet1)
        self.addAction(DeletePolygonAction())
        self.addAction(MarkPolygonAction())
    
    def findGaps(self, polygon1, theDataSet2):
        polygonsUnion = polygon1
        for featureReference in theDataSet2.query(polygon1):
            feature2 = featureReference.getFeature()
            polygon2 = feature2.getDefaultGeometry()
            if not polygon1.equals(polygon2):
                polygonsUnion = polygonsUnion.union(polygon2)
        jtsPolygonsUnion = polygonsUnion.getJTS()
        if jtsPolygonsUnion.getGeometryType() == "Polygon":
            coordinates = jtsPolygonsUnion.getExteriorRing().getCoordinates()
            vertices = []
            for coordinate in coordinates:
                vertices.append(geom.createPoint2D(coordinate.x, coordinate.y))
            self.gaps = geom.createPolygon2D(vertices).difference(polygonsUnion)
    
    def hasGaps(self, polygon1, theDataSet2):
        result = [False, []]
        if theDataSet2.getSpatialIndex() != None:
            if self.gaps == None: 
                self.findGaps(polygon1, theDataSet2)
            if self.gaps != None and (polygon1.intersects(self.gaps) and polygon1.intersection(self.gaps).perimeter() > 0.0):
                result[0] = True
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
            feature2 = theDataSet2.findFirst(self.expression)
            if feature2 != None:
                result[0] = True
        return result
    
    def check(self, taskStatus, report, feature1):
        try:
            polygon1 = feature1.getDefaultGeometry()
            theDataSet2 = self.getDataSet1()
            geometryType1 = polygon1.getGeometryType()
            if geometryType1.getSubType() == geom.D2 or geometryType1.getSubType() == geom.D2M:
                if geometryType1.getType() == geom.POLYGON or geometryType1.isTypeOf(geom.POLYGON):
                    result = self.hasGaps(polygon1, theDataSet2)
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
                            result = self.hasGaps(polygon1[i], theDataSet2)
                            if result[0]:
                                report.addLine(self,
                                    self.getDataSet1(),
                                    None,
                                    polygon1,
                                    polygon1.getSurfaceAt(i),
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
