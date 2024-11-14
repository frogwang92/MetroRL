import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QToolTip, QStatusBar, QToolBar, QListWidget, QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPen, QColor, QIcon, QAction, QBrush, QPainter
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from facility.platform import Platform
from tr.linesegment import LineSegment
from buildtopology import build_topology, calc_coordinates_with_networkx
from linedata import platforms, line_segments

class HoverableItem:
    """Mixin class for hoverable graphics items"""
    def __init__(self, tooltip_prefix=""):
        self.tooltip_prefix = tooltip_prefix
        self.setAcceptHoverEvents(True)

    def _show_tooltip(self, event, item):
        """Show tooltip for the item"""
        QToolTip.showText(
            event.screenPos(), 
            f"{self.tooltip_prefix} Id: {item.id} Weight: {item.weight}"
        )

    def _hide_tooltip(self):
        """Hide the tooltip"""
        QToolTip.hideText()

class HoverableGraphicsLineItem(QGraphicsLineItem, HoverableItem):
    def __init__(self, edge, *args, **kwargs):
        QGraphicsLineItem.__init__(self, *args, **kwargs)
        HoverableItem.__init__(self, "Edge")
        self.edge = edge
        
    def hoverEnterEvent(self, event):
        self.setPen(QPen(QColor('blue'), 2))
        self._show_tooltip(event, self.edge)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setPen(QPen(QColor('grey'), 2))
        self._hide_tooltip()
        super().hoverLeaveEvent(event)

class HoverableGraphicsEllipseItem(QGraphicsEllipseItem, HoverableItem):
    def __init__(self, node, *args, **kwargs):
        QGraphicsEllipseItem.__init__(self, *args, **kwargs)
        HoverableItem.__init__(self, "Node")
        self.node = node

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
    def __init__(self, env):
        super().__init__()
        self.env = env
        self._init_window()
        self._init_layouts()
        self._init_toolbar()
        self._init_statusbar()
        self._init_graph()
        self._init_timeline()
        
    def _init_window(self):
        """Initialize window properties"""
        self.setWindowTitle("Metro Topology")
        self.setGeometry(100, 100, 1500, 800)
        self.setWindowIcon(QIcon('logo.ico'))

    def _init_layouts(self):
        """Initialize layout structure"""
        # Create main components
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.nodeList = self._create_node_list()
        self.edgeList = self._create_edge_list()
        
        # Create timeline components
        self.timeline_scene = QGraphicsScene()
        self.timeline_view = CustomGraphicsView(self.timeline_scene, self)
        
        # Setup layouts
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.view, stretch=1)
        graph_layout.addWidget(self.timeline_view, stretch=1)
        
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)
        
        layout = QHBoxLayout()
        layout.addWidget(graph_widget)
        layout.addWidget(self.nodeList)
        layout.addWidget(self.edgeList)
        layout.setContentsMargins(1, 1, 1, 1)
        
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def _init_toolbar(self):
        """Initialize toolbar and actions"""
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Create actions
        actions = {
            'Start': self._on_start,
            'Pause': self._on_pause,
            'Stop': self._on_stop,
            'Zoom In': self.zoomIn,
            'Zoom Out': self.zoomOut
        }
        
        for name, handler in actions.items():
            action = QAction(name, self)
            action.triggered.connect(handler)
            self.toolbar.addAction(action)
            
        # Store actions for later access
        self.actions = {name: action for name, action in zip(actions.keys(), self.toolbar.actions())}
        
        # Set toolbar style
        # self.toolbar.setStyleSheet("QToolButton { font-family: 'Times New Roman'; }")

    def _on_start(self):
        """Handle start button click"""
        self.env.start()
        
    def _on_pause(self):
        """Handle pause button click"""
        self.env.pause()
        
    def _on_stop(self):
        """Handle stop button click"""
        self.env.stop()

    def _init_statusbar(self):
        """Initialize status bar and labels"""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Create status labels
        self.status_labels = {
            'time': QLabel("Time: 0"),
            'status': QLabel("Status: Stopped"),
            'mode': QLabel(f"Mode: {self.env.mode.value}")
        }
        
        # Add labels to status bar
        for label in self.status_labels.values():
            self.statusBar.addPermanentWidget(label)
            
        # Setup update timer
        self.statusTimer = QTimer()
        self.statusTimer.timeout.connect(self._update_status)
        self.statusTimer.start(1000)  # Update every second

    def _init_graph(self):
        """Initialize graph visualization"""
        nodes, edges = self.env.nodes, self.env.edges
        
        # Initialize storage for graph items
        self.node_items = {}
        self.edge_items = {}
        
        # Draw edges first (so they appear under nodes)
        self._draw_edges(edges)
        
        # Then draw nodes
        self._draw_nodes(nodes)

    def _draw_edges(self, edges):
        """Draw edges on the graph"""
        pen = QPen(QColor('grey'))
        pen.setWidth(2)
        
        for edge in edges:
            # Calculate edge positions
            start_pos = self._get_node_position(edge.start_node)
            end_pos = self._get_node_position(edge.end_node)
            
            # Create and configure edge item
            line = HoverableGraphicsLineItem(
                edge, 
                start_pos.x(), 
                start_pos.y(), 
                end_pos.x(), 
                end_pos.y()
            )
            line.setPen(pen)
            
            # Add to scene and store reference
            self.scene.addItem(line)
            self.edge_items[edge.id] = line
            
            # Add to edge list
            self.edgeList.addItem(
                f"Edge {edge.id}: {edge.start_node.weight} -> {edge.end_node.weight}"
            )

    def _draw_nodes(self, nodes):
        """Draw nodes on the graph"""
        node_pen = QPen(QColor('grey'))
        node_brush = QColor('lightblue')
        
        for node_id, node in nodes.items():
            # Calculate node size based on weight
            node_radius = 5 if node.weight > 1 else 2
            pos = self._get_node_position(node)
            
            # Create and configure node item
            circle = HoverableGraphicsEllipseItem(
                node,
                pos.x() - node_radius,
                pos.y() - node_radius,
                node_radius * 2,
                node_radius * 2
            )
            circle.setPen(node_pen)
            circle.setBrush(node_brush)
            
            # Add to scene and store reference
            self.scene.addItem(circle)
            self.node_items[node.id] = circle
            
            # Add to node list
            self.nodeList.addItem(f"Node {node.id}: {node.weight}")

    def _init_timeline(self):
        """Initialize timeline visualization"""
        pen = QPen(QColor('black'))
        pen.setWidth(1)
        
        # Get the viewport size
        width = self.timeline_view.viewport().width()
        height = self.timeline_view.viewport().height()
        
        margin = 50  # Margin from edges
        
        # Draw axes using full width/height while respecting margins
        self.timeline_scene.addLine(margin, height-margin, width-margin, height-margin, pen)  # X axis
        self.timeline_scene.addLine(margin, margin, margin, height-margin, pen)    # Y axis
        
        # Add time labels with proper spacing
        time_width = width - (2 * margin)
        for i in range(5):
            time_text = self.timeline_scene.addText(f"{i*6}:00")
            time_text.setPos(margin + (i * time_width/4), height-margin+10)

    def _get_node_position(self, node) -> QPointF:
        """Convert node coordinates to scene coordinates"""
        return QPointF(node.x * 100, node.y * 100)

    def _create_node_list(self) -> QListWidget:
        """Create and configure node list widget"""
        node_list = QListWidget()
        node_list.setFixedWidth(int(self.width() * 0.1))
        node_list.itemClicked.connect(self.onNodeClicked)
        return node_list

    def _create_edge_list(self) -> QListWidget:
        """Create and configure edge list widget"""
        edge_list = QListWidget()
        edge_list.setFixedWidth(int(self.width() * 0.1))
        edge_list.itemClicked.connect(self.onEdgeClicked)
        return edge_list

    def _update_status(self):
        """Update status bar information"""
        self.status_labels['time'].setText(f"Time: {self.env.time}")
        self.status_labels['status'].setText(
            f"Status: {'Running' if self.env.is_running else 'Stopped'}"
        )
        self.status_labels['mode'].setText(f"Mode: {self.env.mode.value}")

    def onNodeClicked(self, item):
        """Handle node list item click event"""
        node_id = item.text().split()[1].partition(":")[0]
        for node_id_key, circle in self.node_items.items():
            if str(node_id_key) == node_id:
                self.flashNode(circle)

    def onEdgeClicked(self, item):
        """Handle edge list item click event"""
        edge_id = item.text().split()[1].partition(":")[0]
        for edge_id_key, line in self.edge_items.items():
            if str(edge_id_key) == edge_id:
                self.flashEdge(line)

    def flashNode(self, node_item):
        """Highlight a node temporarily"""
        original_brush = node_item.brush()
        flash_brush = QColor('yellow')

        def restore_brush():
            node_item.setBrush(original_brush)

        node_item.setBrush(flash_brush)
        QTimer.singleShot(500, restore_brush)

    def flashEdge(self, edge_item):
        """Highlight an edge temporarily"""
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

    def addTimelinePoint(self, time, platform):
        # Convert time and platform to coordinates
        x = 50 + (time.hour * 60 + time.minute) * (500/1440)  # 1440 minutes in a day
        y = 150 - (platform * 10)  # Adjust scaling as needed
        
        point = self.timeline_scene.addEllipse(x-2, y-2, 4, 4, 
                                             QPen(QColor('blue')), 
                                             QBrush(QColor('blue')))
        return point
