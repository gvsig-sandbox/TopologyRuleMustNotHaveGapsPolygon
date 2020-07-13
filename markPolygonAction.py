# encoding: utf-8

import gvsig
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
    gaps = None
    
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
            theDataSet = line.getDataSet1()
            if self.gaps == None:
                self.findGaps(polygon, theDataSet)
            if self.gaps != None and (polygon.intersects(self.gaps) and polygon.intersection(self.gaps).perimeter() > 0.0):
                errorsLayer = gvsig.currentView().getLayer(self.errorsLayerName)
                errorsLayer.edit()
                errorsLayer.append(GEOMETRY=polygon.intersection(self.gaps))
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
            self.gaps = None
    
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
    
def main(*args):
    pass
