import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QToolTip, QStatusBar, QToolBar, QListWidget, QVBoxLayout, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPen, QColor, QIcon, QAction, QBrush, QPainter
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from facility.platform import Platform
from tr.linesegment import LineSegment
from buildtopology import build_topology, calc_coordinates_with_networkx
from linedata import platforms, line_segments

class HoverableGraphicsLineItem(QGraphicsLineItem):
    def __init__(self, edge, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edge = edge
        self.setAcceptHoverEvents(True)
    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor('blue'), 2))
        QToolTip.showText(event.screenPos(), f"Id: {self.edge.id} Weight: {self.edge.weight}")
        super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor('grey'), 2))
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

class HoverableGraphicsEllipseItem(QGraphicsEllipseItem):
    def __init__(self, node, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node = node
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(QColor('green'))
        QToolTip.showText(event.screenPos(), f"Id: {self.node.id} Weight: {self.node.weight}")
        super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.setBrush(QColor('lightblue'))
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent = parent
        # self.setViewport(QOpenGLWidget())  # 启用硬件加速
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        # Save the scene pos
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

        # Get the new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

class MetroWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro Topology")
        self.setGeometry(100, 100, 1500, 800)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon('logo.ico'))

        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        
        # 创建右侧的节点列表
        self.nodeList = QListWidget()
        self.nodeList.itemClicked.connect(self.onNodeClicked)

        # 创建右侧的边列表
        self.edgeList = QListWidget()
        self.edgeList.itemClicked.connect(self.onEdgeClicked)

        # 设置节点列表和边列表的宽度为窗口宽度的10%
        self.nodeList.setFixedWidth(int(self.width() * 0.1))
        self.edgeList.setFixedWidth(int(self.width() * 0.1))

        # 创建一个布局，将视图和列表添加到布局中
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.nodeList)
        layout.addWidget(self.edgeList)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建一个中央小部件，并将布局设置为中央小部件的布局
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        # 2px边距
        self.view.setStyleSheet("border: 1px solid grey; margin: 2px;")

        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 添加工具栏
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        # 添加开始按钮
        self.startAction = QAction('Start', self)
        self.toolbar.addAction(self.startAction)

        # 添加暂停按钮
        self.pauseAction = QAction('Pause', self)
        self.toolbar.addAction(self.pauseAction)

        # 添加停止按钮
        self.stopAction = QAction('Stop', self)
        self.toolbar.addAction(self.stopAction)

        # 添加缩放按钮
        self.zoomInAction = QAction('Zoom In', self)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.toolbar.addAction(self.zoomInAction)

        self.zoomOutAction = QAction('Zoom Out', self)
        self.zoomOutAction.triggered.connect(self.zoomOut)
        self.toolbar.addAction(self.zoomOutAction)

        # 设置工具栏的样式表
        self.toolbar.setStyleSheet("QToolButton { font-family: 'Times New Roman'; }")

        self.initUI()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 动态调整节点列表和边列表的宽度为窗口宽度的10%
        self.nodeList.setFixedWidth(int(self.width() * 0.1))
        self.edgeList.setFixedWidth(int(self.width() * 0.1))

    def initUI(self):
        nodes, edges = build_topology(platforms, line_segments)
        nodes = calc_coordinates_with_networkx(nodes, edges)

        # Draw the nodes and edges
        pen = QPen(QColor('grey'))
        pen.setWidth(2)  # Double the line width

        self.node_items = {}
        self.edge_items = {}

        for edge in edges:
            start_node_id = edge.start_node.id
            end_node_id = edge.end_node.id
            start_pos = QPointF(nodes[start_node_id].x * 100, nodes[start_node_id].y * 100)
            end_pos = QPointF(nodes[end_node_id].x * 100, nodes[end_node_id].y * 100)
            line = HoverableGraphicsLineItem(edge, start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            line.setPen(pen)
            self.scene.addItem(line)
            self.edge_items[edge.id] = line
            self.edgeList.addItem(f"Edge {edge.id}: {edge.start_node.weight} -> {edge.end_node.weight}")

        node_pen = QPen(QColor('grey'))
        node_brush = QColor('lightblue')

        for node_id, node in nodes.items():
            node_radius = 2
            pos = QPointF(node.x * 100, node.y * 100)
            if node.weight > 1:
                node_radius = 5
            circle = HoverableGraphicsEllipseItem(node, pos.x() - node_radius, pos.y() - node_radius, node_radius * 2, node_radius * 2)
            circle.setPen(node_pen)
            circle.setBrush(node_brush)
            self.scene.addItem(circle)
            self.node_items[node.id] = circle
            self.nodeList.addItem(f"Node {node.id}: {node.weight}")

    def onNodeClicked(self, item):
        node_id = item.text().split()[1].partition(":")[0]
        for node_id_key, circle in self.node_items.items():
            if str(node_id_key) == node_id:
                self.flashNode(circle)

    def onEdgeClicked(self, item):
        edge_id = item.text().split()[1].partition(":")[0]
        for edge_id_key, line in self.edge_items.items():
            if str(edge_id_key) == edge_id:
                self.flashEdge(line)

    def flashNode(self, node_item):
        original_brush = node_item.brush()
        flash_brush = QColor('yellow')

        def restore_brush():
            node_item.setBrush(original_brush)

        node_item.setBrush(flash_brush)
        QTimer.singleShot(500, restore_brush)

    def flashEdge(self, edge_item):
        original_pen = edge_item.pen()
        flash_pen = QPen(QColor('yellow'), 2)

        def restore_pen():
            edge_item.setPen(original_pen)

        edge_item.setPen(flash_pen)
        QTimer.singleShot(500, restore_pen)

    def zoomIn(self):
        self.view.scale(1.2, 1.2)

    def zoomOut(self):
        self.view.scale(0.8, 0.8)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetroWindow()
    window.show()
    sys.exit(app.exec())