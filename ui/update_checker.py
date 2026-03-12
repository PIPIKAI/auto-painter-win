"""
自动检查 GitHub Release 更新
"""
import json
import urllib.request
import urllib.error
import webbrowser

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from ui.i18n import i18n
from ui.version import APP_VERSION

GITHUB_REPO = "PIPIKAI/auto-painter-win"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"


def _parse_version(tag: str) -> tuple:
    """将版本标签 (如 'v0.2.0' 或 '0.2.0') 解析为可比较的元组。"""
    tag = tag.lstrip("vV")
    parts = []
    for p in tag.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


class _UpdateWorker(QThread):
    """后台线程：查询 GitHub API 获取最新 release 信息。"""

    result = pyqtSignal(dict)   # {"tag": ..., "url": ...}
    error = pyqtSignal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github.v3+json",
                         "User-Agent": "AutoPainter-UpdateChecker"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "")
            html_url = data.get("html_url", GITHUB_RELEASES_URL)
            self.result.emit({"tag": tag, "url": html_url})
        except Exception as exc:
            self.error.emit(str(exc))


class UpdateDialog(QDialog):
    """提示用户有新版本可用的对话框。"""

    def __init__(self, latest_tag: str, download_url: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("update_title"))
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._download_url = download_url

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 图标 + 标题
        title_lbl = QLabel(f"🔔 {i18n.t('update_title')}")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(title_lbl)

        # 版本信息
        msg_lbl = QLabel(i18n.t("update_message", latest_tag, APP_VERSION))
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("font-size: 14px; color: #555; line-height: 1.5;")
        layout.addWidget(msg_lbl)

        layout.addSpacing(8)

        # 按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_skip = QPushButton(i18n.t("update_skip"))
        btn_skip.clicked.connect(self.reject)
        btn_row.addWidget(btn_skip)

        btn_download = QPushButton(i18n.t("update_download"))
        btn_download.setObjectName("primaryButton")
        btn_download.clicked.connect(self._on_download)
        btn_row.addWidget(btn_download)

        layout.addLayout(btn_row)

        i18n.language_changed.connect(self._retranslate)

    def _retranslate(self, _lang=None):
        self.setWindowTitle(i18n.t("update_title"))

    def _on_download(self):
        webbrowser.open(self._download_url)
        self.accept()


def check_for_updates(parent=None, silent: bool = True):
    """
    启动后台线程检查更新。

    silent=True 时仅在有新版本时弹窗；
    silent=False 时即便是最新版也会提示。
    """
    worker = _UpdateWorker()

    def _on_result(info: dict):
        tag = info.get("tag", "")
        url = info.get("url", GITHUB_RELEASES_URL)
        if not tag:
            return
        if _parse_version(tag) > _parse_version(APP_VERSION):
            dlg = UpdateDialog(tag.lstrip("vV"), url, parent)
            dlg.exec_()
        elif not silent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, i18n.t("update_title"),
                                    i18n.t("update_latest"))

    def _on_error(msg: str):
        if not silent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(parent, i18n.t("update_title"),
                                i18n.t("update_error", msg))

    worker.result.connect(_on_result)
    worker.error.connect(_on_error)
    worker.start()

    # 防止 worker 被垃圾回收
    if parent is not None:
        if not hasattr(parent, "_update_workers"):
            parent._update_workers = []
        parent._update_workers.append(worker)

    return worker
