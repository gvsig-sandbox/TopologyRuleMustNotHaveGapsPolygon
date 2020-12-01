# encoding: utf-8

import gvsig
import math
import statistics
import sys

from datetime import datetime
from gvsig import geom
from org.gvsig.app import ApplicationLocator
from org.gvsig.symbology.fmap.mapcontext.rendering.legend.impl import SingleSymbolLegend
from org.gvsig.symbology.fmap.mapcontext.rendering.symbol.line.impl import SimpleLineSymbol
from org.gvsig.topology.lib.spi import AbstractTopologyRuleAction

class MarkPolygonAction(AbstractTopologyRuleAction):
    
    selectedRowCount = 0
    linesCount = 0
    errorsLayerName = ""
    
    def __init__(self):
        AbstractTopologyRuleAction.__init__(
            self,
            "mustNotHaveGapsPolygon",
            "MarkPolygonAction",
            "Mark Polygon Action",
            "Polygons that have gaps are marked."
        )
    
    def execute(self, rule, line, parameters):
        try:
            self.checkErrorsLayerName()
            self.checkErrorsLayer(line)
            self.checkSelectedRowCount()
            
            polygon = line.getFeature1().getFeature().getDefaultGeometry()
            tolerance = rule.getTolerance()
            theDataSet = line.getDataSet1()
            errorsLayer = gvsig.currentView().getLayer(self.errorsLayerName)
            errorsLayer.edit()
            self.findGaps(polygon, theDataSet, tolerance, errorsLayer)
            errorsLayer.commit()
            
            self.linesCount += 1
            
            self.checkProcessState()
        except:
            ex = sys.exc_info()[1]
            gvsig.logger("Can't execute action. Class Name: " + ex.__class__.__name__ + ". Exception: " + str(ex), gvsig.LOGGER_ERROR)
    
    def checkErrorsLayerName(self):
        if self.errorsLayerName == "":
            self.errorsLayerName = "MustNotHaveGaps_" + datetime.now().strftime("%Y%m%d%H%M%S")
    
    def checkErrorsLayer(self, line):
        errorsLayer = gvsig.currentView().getLayer(self.errorsLayerName)
        if errorsLayer == None:
            errorsLayerSchema = gvsig.createSchema()
            errorsLayerSchema.append("GEOMETRY", "GEOMETRY")
            errorsLayerSchema.get("GEOMETRY").setGeometryType(geom.LINE, geom.D2)
            errorsLayer = gvsig.createShape(errorsLayerSchema)
            errorsLayer.setName(self.errorsLayerName)
            errorsLegend = SingleSymbolLegend()
            errorsSymbol = SimpleLineSymbol()
            errorsSymbol.setColor(gvsig.utils.getColorFromRGB(255, 0, 51)) # RGB
            errorsSymbol.setLineWidth(10)
            errorsLegend.setDefaultSymbol(errorsSymbol)
            errorsLayer.setLegend(errorsLegend)
            gvsig.currentView().addLayer(errorsLayer)
     
    def checkSelectedRowCount(self):
        if self.selectedRowCount == 0:
            applicationLocator = ApplicationLocator()
            applicationManager = applicationLocator.getManager()
            mdiManager = applicationManager.getUIManager()
            window = mdiManager.getFocusWindow() # org.gvsig.andami.ui.ToolsWindowManager.Window
            rootPane = window.getRootPane() # JRootPane
            layeredPane = rootPane.getComponent(1) # JLayeredPane
            panel = layeredPane.getComponent(0) # JPanel
            window = panel.getComponent(0) # org.gvsig.andami.ui.ToolsWindowManager.Window
            defaultJTopologyReport = window.getComponent(0) # org.gvsig.topology.swing.impl.DefaultJTopologyReport
            pane = defaultJTopologyReport.getComponent(0) # JPanel
            tabbedPane = pane.getComponent(0) # JTabbedPane
            pane = tabbedPane.getComponent(0) # JPanel
            scrollPane = pane.getComponent(0) # JScrollPane
            viewport = scrollPane.getComponent(0) # JViewport
            table = viewport.getComponent(0) # JTable
            self.selectedRowCount = table.getSelectedRowCount()
    
    def checkProcessState(self):
        if self.linesCount == self.selectedRowCount:
            self.selectedRowCount = 0
            self.linesCount = 0
            self.errorsLayerName = ""
    
    def findGaps(self, polygon1, theDataSet2, tolerance1, errorsLayer):
        for featureReference in theDataSet2.query(polygon1):
            feature2 = featureReference.getFeature()
            polygon2 = feature2.getDefaultGeometry()
        
            buffer1 = polygon1.buffer(tolerance1)
            
            if not polygon1.equals(polygon2) and buffer1.intersects(polygon2):
                
                difference1 = buffer1.union(polygon2).difference(polygon1).difference(polygon2)
                
                if difference1.getGeometryType().getType() == geom.POLYGON:
                
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
                                                try:
                                                    difference1 = intersection3.difference(intersection4)
                                                except:
                                                    difference1 = None
                                                if difference1 != None:
                                                    geometryType5 = difference1.getGeometryType()
                                                    if geometryType5.getType() == geom.LINE:
                                                        errorsLayer.append(GEOMETRY=difference1)
                            else:
                                lines1 = polygon2.toLines()
                                lines2 = intersection2.toLines()
                                for i in range(0, lines2.getPrimitivesNumber()):
                                    for j in range(0, lines1.getPrimitivesNumber()):
                                       line2 = lines2.getPrimitiveAt(i)
                                       if line2.difference(lines1.getPrimitiveAt(j)) == None:
                                          errorsLayer.append(GEOMETRY=line2)
                                          break
    
def main(*args):
    pass
