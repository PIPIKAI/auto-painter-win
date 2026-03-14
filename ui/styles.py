"""
全局样式表
"""

GLOBAL_STYLE = """
/* 整体 */
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* 分组框 */
QGroupBox {
    font-weight: bold;
    font-size: 13px;
    border: 1px solid #ddd;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 16px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: #333;
}

/* 按钮 */
QPushButton {
    padding: 8px 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #ffffff;
    color: #333;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #e8e8e8;
    border-color: #aaa;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #f0f0f0;
    color: #aaa;
    border-color: #ddd;
}

/* 主要按钮 */
QPushButton#primaryButton {
    background-color: #4a90d9;
    color: white;
    border: none;
    font-weight: bold;
}

QPushButton#primaryButton:hover {
    background-color: #357abd;
}

QPushButton#primaryButton:pressed {
    background-color: #2a5f9e;
}

QPushButton#primaryButton:disabled {
    background-color: #a0c4e8;
}

/* 分段按钮 */
QPushButton#segButton {
    padding: 8px 14px;
    border: 1px solid #ccc;
    border-radius: 6px;
    background-color: #ffffff;
}

QPushButton#segButton:hover {
    border-color: #4a90d9;
}

QPushButton#segButton:checked {
    background-color: #4a90d9;
    color: #fff;
    border-color: #4a90d9;
    font-weight: bold;
}

/* 成功按钮 */
QPushButton#successButton {
    background-color: #2ea44f;
    color: white;
    border: none;
    font-weight: bold;
}

QPushButton#successButton:hover {
    background-color: #2c974b;
}

QPushButton#successButton:pressed {
    background-color: #268643;
}

QPushButton#successButton:disabled {
    background-color: #94d3a2;
}

/* 危险按钮 */
QPushButton#dangerButton {
    background-color: #d73a49;
    color: white;
    border: none;
    font-weight: bold;
}

QPushButton#dangerButton:hover {
    background-color: #cb2431;
}

QPushButton#dangerButton:pressed {
    background-color: #b31d28;
}

QPushButton#dangerButton:disabled {
    background-color: #f0a0a8;
}

/* 下拉框 */
QComboBox {
    padding: 6px 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #fff;
}

QComboBox:hover {
    border-color: #4a90d9;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

/* 设置选中项的背景色和文本颜色 */
QComboBox::item:selected {
    background-color: #4a90d9;  /* 设置选中项的背景色 */
    color: #fff;  /* 设置选中项的文字颜色 */
}

QComboBox::item {
    background-color: #fff;  /* 设置未选中项的背景色 */
    color: #000;  /* 设置未选中项的文字颜色 */
}

QSlider::groove:horizontal {
    border: none;
    height: 6px;
    background: #ddd;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #4a90d9;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #357abd;
}

QSlider::sub-page:horizontal {
    background: #4a90d9;
    border-radius: 3px;
}

/* 上下按钮样式 */
QSlider::up-button, QSlider::down-button {
    background-color: #4a90d9;
    border: none;
    width: 16px;
    height: 16px;
    border-radius: 8px;
}

/* 上下按钮悬停状态 */
QSlider::up-button:hover, QSlider::down-button:hover {
    background-color: #357abd;
}

/* 上下按钮的箭头图标 */
QSlider::up-button::icon, QSlider::down-button::icon {
    image: url('path/to/your/arrow_icon.png');
    width: 10px;  /* 根据需要调整图标大小 */
    height: 10px;
}

/* 进度条 */
QProgressBar {
    border: 1px solid #ddd;
    border-radius: 4px;
    text-align: center;
    height: 20px;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #2ea44f;
    border-radius: 3px;
}

/* Tab */
QTabWidget::pane {
    border: 1px solid #ddd;
    border-radius: 4px;
    background: #fff;
}

QTabBar::tab {
    padding: 8px 16px;
    border: 1px solid #ddd;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    background: #f0f0f0;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: #fff;
    border-bottom: 2px solid #4a90d9;
}

QTabBar::tab:hover:!selected {
    background: #e8e8e8;
}

/* SpinBox */
QSpinBox {
    padding: 6px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

/* 滚动条 */
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}

QScrollBar::handle:vertical {
    background: #ccc;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #aaa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 状态栏 */
QStatusBar {
    background: #fff;
    border-top: 1px solid #ddd;
    font-size: 12px;
    color: #666;
}

/* 菜单栏 */
QMenuBar {
    background: #fff;
    border-bottom: 1px solid #eee;
}

QMenuBar::item:selected {
    background: #e8e8e8;
    border-radius: 4px;
}

QMenu {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 4px;
}

QMenu::item:selected {
    background: #4a90d9;
    color: white;
    border-radius: 3px;
}
"""
