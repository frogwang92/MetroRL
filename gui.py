import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QToolTip, QStatusBar, QToolBar, QAction, QListWidget, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPointF, QTimer
from PyQt5.QtGui import QPen, QColor, QIcon
from facility.platform import Platform
from tr.linesegment import LineSegment
from buildtopology import build_topology
from linedata import platforms, line_segments

class HoverableGraphicsLineItem(QGraphicsLineItem):
    def __init__(self, edge, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edge = edge
        self.setAcceptHoverEvents(True)
    def hoverEnterEvent(self, event):
        self.setPen(QPen(Qt.blue, 2))
        QToolTip.showText(event.screenPos(), f"Weight: {self.edge.weight}")
        super().hoverEnterEvent(event)
    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.black, 2))
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

class HoverableGraphicsEllipseItem(QGraphicsEllipseItem):
    def __init__(self, node, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node = node
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setBrush(QColor(Qt.green))
        QToolTip.showText(event.screenPos(), f"Weight: {self.node.weight}")
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QColor(Qt.red))
        QToolTip.hideText()
        super().hoverLeaveEvent(event)

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent = parent

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.parent.statusBar.showMessage(f"Mouse coordinates: ({pos.x():.2f}, {pos.y():.2f})")
        super().mouseMoveEvent(event)

class MetroWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metro Topology")
        self.setGeometry(100, 100, 2200, 1400)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon('logo.ico'))

        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        
        # 创建右侧的节点列表
        self.nodeList = QListWidget()
        self.nodeList.itemClicked.connect(self.onNodeClicked)

        # 设置节点列表的宽度���窗口宽度的15%
        self.nodeList.setFixedWidth(int(self.width() * 0.15))

        # 创建一个布局，将视图和列表添加到布局中
        layout = QHBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.nodeList)
        layout.setContentsMargins(5, 5, 5, 5)

        # 创建一个中央小部件，并将布局设置为中央小部件的布局
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        # 设置灰色边框和5px边距
        self.view.setStyleSheet("border: 3px solid grey;")

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

        # 设置工具栏的样式表
        self.toolbar.setStyleSheet("QToolButton { font-family: 'Arial'; }")

        self.initUI()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 动态调整节点列表的宽度为窗口宽度的15%
        self.nodeList.setFixedWidth(int(self.width() * 0.15))

    def initUI(self):
        nodes, edges = build_topology(platforms, line_segments)
        print(nodes)

        # Draw the nodes and edges
        pen = QPen(Qt.black)
        pen.setWidth(2)  # Double the line width

        self.node_items = {}

        for edge in edges:
            start_pos = QPointF(edge.start_node.weight * 10, edge.start_node.weight * 10)
            end_pos = QPointF(edge.end_node.weight * 10, edge.end_node.weight * 10)
            line = HoverableGraphicsLineItem(edge, start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            line.setPen(pen)
            self.scene.addItem(line)

        node_radius = 5
        node_pen = QPen(Qt.black)
        node_brush = QColor(Qt.red)

        for node in nodes.values():
            pos = QPointF(node.weight * 10, node.weight * 10)
            circle = HoverableGraphicsEllipseItem(node, pos.x() - node_radius, pos.y() - node_radius, node_radius * 2, node_radius * 2)
            circle.setPen(node_pen)
            circle.setBrush(node_brush)
            self.scene.addItem(circle)
            self.node_items[node] = circle
            self.nodeList.addItem(f"Node {node.weight}")

    def onNodeClicked(self, item):
        node_weight = float(item.text().split()[1])
        for node, circle in self.node_items.items():
            if node.weight == node_weight:
                self.flashNode(circle)

    def flashNode(self, node_item):
        original_brush = node_item.brush()
        flash_brush = QColor(Qt.yellow)

        def restore_brush():
            node_item.setBrush(original_brush)

        node_item.setBrush(flash_brush)
        QTimer.singleShot(500, restore_brush)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MetroWindow()
    window.show()
    sys.exit(app.exec_())