import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsLineItem, QGraphicsEllipseItem, QToolTip, QStatusBar, QToolBar, QListWidget, QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel, QTabWidget, QPlainTextEdit
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QPen, QColor, QIcon, QAction, QBrush, QPainter
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from facility.platform import Platform
from tr.linesegment import LineSegment
from buildtopology import build_topology, calc_coordinates_with_networkx
from topologyutils import node_in_segment_percentage
from linedata import platforms, line_segments, calc_platform_positions
from logger import logger, add_logger_to_gui

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
        # add_logger_to_gui(logger, self.log_view)

    def _init_window(self):
        """Initialize window properties"""
        logger.info("Initializing window")
        self.setWindowTitle("Metro RL Environment")
        self.setGeometry(100, 100, 1500, 800)
        self.setWindowIcon(QIcon('logo.ico'))

    def _init_layouts(self):
        """Initialize layout structure"""
        # Create main components
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene, self)
        self.view.setStyleSheet("border: 1px solid grey;")
        self.nodeList = self._create_node_list()
        self.edgeList = self._create_edge_list()
        self.trainList = self._create_train_list()
        
        # Create timeline components
        self.timeline_scene = QGraphicsScene()
        self.timeline_view = CustomGraphicsView(self.timeline_scene, self)
        self.timeline_view.setStyleSheet("border: 1px solid grey;")

        # Create topology components
        self.topology_scene = QGraphicsScene()
        self.topology_view = CustomGraphicsView(self.topology_scene, self)
        self.topology_view.setStyleSheet("border: 1px solid grey;")
        
        # Create log components
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.timeline_view, "Timeline")
        self.tab_widget.addTab(self.log_view, "Log")

        # Setup layouts
        toprow_layout = QHBoxLayout()
        toprow_layout.addWidget(self.view, stretch=1)
        toprow_layout.addWidget(self.topology_view, stretch=1)
        toprow_layout.addWidget(self.nodeList)
        toprow_layout.addWidget(self.edgeList)

        toprow_widget = QWidget()
        toprow_widget.setLayout(toprow_layout)

        bottomrow_layout = QHBoxLayout()
        bottomrow_layout.addWidget(self.tab_widget, stretch=1)
        bottomrow_layout.addWidget(self.trainList, stretch=1)

        bottomrow_widget = QWidget()
        bottomrow_widget.setLayout(bottomrow_layout)

        graph_layout = QVBoxLayout()
        graph_layout.addWidget(toprow_widget, stretch=1)
        graph_layout.addWidget(bottomrow_widget, stretch=1)

        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        layout = QHBoxLayout()
        layout.addWidget(graph_widget)

        layout.setContentsMargins(1, 1, 1, 1)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def _init_toolbar(self):
        """Initialize toolbar and actions"""
        logger.info("Initializing toolbar")
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

    def _init_statusbar(self):
        """Initialize status bar and labels"""
        logger.info("Initializing status bar")
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Create status labels
        self.status_labels = {
            'time': QLabel("Time: 0"),
            'status': QLabel("Status: Stopped"),
            'mode': QLabel(f"Mode: {self.env.state.mode.value}")
        }

        # Add time label to the left
        self.statusBar.setContentsMargins(5, 0, 5, 2)
        self.statusBar.addWidget(self.status_labels['time'])

        # Add status and mode labels to the right
        self.statusBar.addPermanentWidget(self.status_labels['status'])
        self.statusBar.addPermanentWidget(self.status_labels['mode'])

        # Setup update timer
        self.statusTimer = QTimer()
        self.statusTimer.timeout.connect(self._update_status)
        self.statusTimer.start(1000)  # Update every second

    def _init_graph(self):
        """Initialize graph visualization"""
        logger.info("Initializing graph")
        nodes, edges = self.env.nodes, self.env.edges

        # Initialize storage for graph items
        self.node_items = {}
        self.edge_items = {}
        self.train_items = {}

        # Get the viewport size
        self.timeline_width = self.timeline_view.viewport().width()
        self.timeline_height = self.timeline_view.viewport().height()
        
        self.maxtime = 6 * 3600
        self.timeline_margin = 40  # Margin from edges
        self.timeline_tickwidth = (self.timeline_width - 2 * self.timeline_margin) / self.maxtime
        
        self.platform_horiz_pos = {}

        # Draw edges first (so they appear under nodes)
        self._draw_edges(edges)

        # Then draw nodes
        self._draw_nodes(nodes)

        # draw platform nodes
        self._draw_platform_nodes(platforms)

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
        logger.info("Drawing nodes")
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

    def _draw_platform_nodes(self, platforms):
        """Draw platform nodes on the topology canvas"""
        logger.info("Drawing platform nodes")
        self.plat_positions = calc_platform_positions(platforms, 70, 70)
        platform_pen = QPen(QColor('grey'))
        platform_brush = QColor('lightblue')
        line_pen = QPen(QColor('grey'))
        line_pen.setWidth(2)
        for platform in platforms:
            # Calculate platform size
            platform_radius = 6
            pos = self.plat_positions[platform]

            # Create and configure platform item
            circle = HoverableGraphicsEllipseItem(
                platform,
                pos[0] - platform_radius,
                pos[1] - platform_radius,
                platform_radius * 2,
                platform_radius * 2
            )
            circle.setPen(platform_pen)
            circle.setBrush(platform_brush)

            # Add to topology scene and store reference
            self.topology_scene.addItem(circle)
            self.topology_scene.addText(f"{platform.name}").setPos(pos[0] - 10, pos[1] + 10)

            # Add to platform list
            # self.platformList.addItem(f"Platform {platform.id}")
        for seg in line_segments:
            start_pos = self.plat_positions[seg.start_platform]
            end_pos = self.plat_positions[seg.end_platform]
            line = HoverableGraphicsLineItem(
                seg, 
                start_pos[0], 
                start_pos[1], 
                end_pos[0], 
                end_pos[1]
            )
            line.setPen(line_pen)
            self.topology_scene.addItem(line)
            # self.edge_items[edge

    def _get_node_position(self, node) -> QPointF:
        """Convert node coordinates to scene coordinates"""
        return QPointF(node.x * 100, node.y * 100)

    def _get_node_positon_in_topology(self, node) -> QPointF:
        """Convert node coordinates to topology scene coordinates"""
        # find the segment that the node is in
        segment = self.env.node2segments[node.id]
        start_position = self.plat_positions[segment.start_platform]
        end_position = self.plat_positions[segment.end_platform]
        offset = node_in_segment_percentage(node, segment, self.env.segment2nodes)
        x = start_position[0] + (end_position[0] - start_position[0]) * offset
        y = start_position[1] + (end_position[1] - start_position[1]) * offset
        # logger.info(f"Node {node.id} is at {x}, {y}")
        return QPointF(x, y)

    def _create_node_list(self) -> QListWidget:
        """Create and configure node list widget"""
        logger.info("Creating node list")
        node_list = QListWidget()
        node_list.setFixedWidth(int(self.width() * 0.1))
        node_list.itemClicked.connect(self.onNodeClicked)
        return node_list

    def _create_edge_list(self) -> QListWidget:
        """Create and configure edge list widget"""
        logger.info("Creating edge list")
        edge_list = QListWidget()
        edge_list.setFixedWidth(int(self.width() * 0.1))
        edge_list.itemClicked.connect(self.onEdgeClicked)
        return edge_list

    def _create_train_list(self) -> QListWidget:
        """Create and configure train list widget"""
        logger.info("Creating train list")
        train_list = QListWidget()
        train_list.setFixedWidth(int(self.width() * 0.2) + 2)
        return train_list

    def _update_status(self):
        """Update status bar information"""
        self.status_labels['time'].setText(f"Time: {self.env.state.time}")
        self.status_labels['status'].setText(
            f"Status: {'Running' if self.env.state.is_running else 'Stopped'}"
        )
        self.status_labels['mode'].setText(f"Mode: {self.env.state.mode.value}")

    def onNodeClicked(self, item):
        """Handle node list item click event"""
        logger.info(f"Node clicked: {item.text()}")
        node_id = item.text().split()[1].partition(":")[0]
        for node_id_key, circle in self.node_items.items():
            if str(node_id_key) == node_id:
                self.flashNode(circle)

    def onEdgeClicked(self, item):
        """Handle edge list item click event"""
        logger.info(f"Edge clicked: {item.text()}")
        edge_id = item.text().split()[1].partition(":")[0]
        for edge_id_key, line in self.edge_items.items():
            if str(edge_id_key) == edge_id:
                self.flashEdge(line)

    def flashNode(self, node_item):
        """Highlight a node temporarily"""
        logger.info(f"Flashing node: {node_item}")
        original_brush = node_item.brush()
        flash_brush = QColor('yellow')

        def restore_brush():
            node_item.setBrush(original_brush)

        node_item.setBrush(flash_brush)
        QTimer.singleShot(500, restore_brush)

    def flashEdge(self, edge_item):
        """Highlight an edge temporarily"""
        logger.info(f"Flashing edge: {edge_item}")
        original_pen = edge_item.pen()
        flash_pen = QPen(QColor('yellow'), 2)

        def restore_pen():
            edge_item.setPen(original_pen)

        edge_item.setPen(flash_pen)
        QTimer.singleShot(500, restore_pen)

    def zoomIn(self):
        logger.info("Zooming in")
        self.view.scale(1.25, 1.25)

    def zoomOut(self):
        logger.info("Zooming out")
        self.view.scale(0.8, 0.8)

    def _add_timeline_point(self, x, y):
        """Add a point to the timeline visualization"""
        point = QGraphicsEllipseItem(x, y, 2, 2)
        point.setBrush(QBrush(QColor('green')))
        point.setPen(QPen(Qt.PenStyle.NoPen))  # No border
        self.timeline_scene.addItem(point)

    def resizeEvent(self, event):
        """Handle window resize event to adjust timeline graph"""
        logger.info("Window resized")
        super().resizeEvent(event)
        self._update_timeline()

    def showEvent(self, event):
        """Handle window show event to adjust timeline graph"""
        logger.info("Window shown")
        super().showEvent(event)
        self._update_timeline()

    def _update_timeline(self):
        """Update timeline visualization based on current viewport size"""
        self.timeline_scene.clear()
        pen = QPen(QColor('grey'))
        pen.setWidth(2)

        pen2 = QPen(QColor('lightgrey'))
        pen2.setWidth(1)

        # Get the viewport size
        self.timeline_width = self.timeline_view.viewport().width()
        self.timeline_height = self.timeline_view.viewport().height()
        
        self.maxtime = 6 * 3600
        self.timeline_margin = 40  # Margin from edges
        self.timeline_tickwidth = (self.timeline_width - 2 * self.timeline_margin) / self.maxtime
        
        self.platform_horiz_pos = {}

        interval = (self.timeline_height - (2 * self.timeline_margin)) / len(platforms)

        for i in range(len(platforms)):
            # Draw platform lines
            self.platform_horiz_pos[platforms[i]] = self.timeline_height-self.timeline_margin-(i*interval)
            self.timeline_scene.addLine(self.timeline_margin, self.platform_horiz_pos[platforms[i]], self.timeline_width-self.timeline_margin, self.platform_horiz_pos[platforms[i]], pen2)
            platform_text = self.timeline_scene.addText(f"{platforms[i].name}")
            platform_text_height = platform_text.boundingRect().height()
            platform_text_width = platform_text.boundingRect().width()
            platform_text.setPos(self.timeline_margin - platform_text_width / 2 - 15, self.platform_horiz_pos[platforms[i]] - platform_text_height / 2)

        # Draw axes using full width/height while respecting margins
        self.timeline_scene.addLine(self.timeline_margin, self.timeline_height-self.timeline_margin, self.timeline_width-self.timeline_margin, self.timeline_height-self.timeline_margin, pen)  # X axis
        self.timeline_scene.addLine(self.timeline_margin, self.timeline_margin, self.timeline_margin, self.timeline_height-self.timeline_margin, pen)    # Y axis
        # Add time labels with proper spacing
        # time_width = width - (2 * margin)
        # for i in range(5):
        #     time_text = self.timeline_scene.addText(f"{i*6}:00")
        #     time_text.setPos(margin + (i * time_width/4), height-margin+10)

        # Set up a timer to refresh trains every 500ms
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_trains)
        self.refresh_timer.start(500)

    def refresh_trains(self):
        self.trainList.clear()
        for train in self.env.get_all_trains().values():
            self.trainList.addItem(f"Train {train.id}: {train.state.current_node}")
            # update the node color to green to indicate the train is there
            for node_id_key, circle in self.node_items.items():
                if str(node_id_key) == str(train.state.current_node.id):
                    circle.setBrush(QBrush(QColor('green')))
                else:
                    circle.setBrush(QBrush(QColor('lightblue')))
            # now for each train, add a point
        for train in self.env.get_all_trains().values():
            # calculate the x 
            x = self.timeline_margin + self.env.state.time * self.timeline_tickwidth
            # claculate the y
            segment = self.env.node2segments[train.state.current_node.id]
            startplat = segment.start_platform
            endplat = segment.end_platform
            y = self.platform_horiz_pos[startplat] - (self.platform_horiz_pos[startplat] - self.platform_horiz_pos[endplat]) * node_in_segment_percentage(train.state.current_node, segment, self.env.segment2nodes)

            self._add_timeline_point(x, y)

            # calculate train position in graph scene

            if train in self.train_items:
                trainitem = self.train_items[train]
                self.topology_scene.removeItem(trainitem)
                # trainitem.setPos(self._get_node_positon_in_topology(train.state.current_node))
            
            trainitem = HoverableGraphicsEllipseItem(
                train.state.current_node,
                self._get_node_positon_in_topology(train.state.current_node).x() - 5,
                self._get_node_positon_in_topology(train.state.current_node).y() - 5,
                10,
                10
            )
            trainitem.setBrush(QBrush(QColor('red')))
            self.topology_scene.addItem(trainitem)
            self.train_items[train] = trainitem

    def _on_start(self):
        """Handle start button click"""
        logger.info("Start button clicked")
        self.env.start()

    def _on_pause(self):
        """Handle pause button click"""
        logger.info("Pause button clicked")
        self.env.pause()

    def _on_stop(self):
        """Handle stop button click"""
        logger.info("Stop button clicked")
        self.env.reset()
