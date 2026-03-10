"""
设置对话框
包含快捷键设置和 AI 画图设置
"""
import json
import os

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QLabel, QLineEdit, QComboBox,
    QPushButton, QTextEdit, QKeySequenceEdit,
    QWidget, QFormLayout, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence

from ui.i18n import i18n
from ui.app_paths import SETTINGS_PATH, ensure_data_dirs
from core.ai_generator import PRESET_PROMPTS


class SettingsDialog(QDialog):
    """应用设置对话框，包含快捷键和 AI 配置。"""

    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("settings_title"))
        self.setMinimumSize(520, 480)
        self.resize(560, 520)
        self._init_ui()
        self._load_settings()
        i18n.language_changed.connect(self._retranslate)

    # ──────────── UI ────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # ═══ Tab 1: 快捷键 ═══
        hotkey_tab = QWidget()
        hk_layout = QVBoxLayout(hotkey_tab)

        self.grp_hotkeys = QGroupBox()
        form = QFormLayout()

        self.lbl_start_hotkey = QLabel()
        self.key_start = QKeySequenceEdit(QKeySequence("F5"))
        self.key_start.setMaximumWidth(160)
        form.addRow(self.lbl_start_hotkey, self.key_start)

        self.lbl_calib_start = QLabel()
        self.key_calib_start = QKeySequenceEdit(QKeySequence("F7"))
        self.key_calib_start.setMaximumWidth(160)
        form.addRow(self.lbl_calib_start, self.key_calib_start)

        self.lbl_calib_end = QLabel()
        self.key_calib_end = QKeySequenceEdit(QKeySequence("F8"))
        self.key_calib_end.setMaximumWidth(160)
        form.addRow(self.lbl_calib_end, self.key_calib_end)

        self.lbl_abort_hotkey = QLabel()
        self.key_abort = QKeySequenceEdit(QKeySequence("Esc"))
        self.key_abort.setMaximumWidth(160)
        form.addRow(self.lbl_abort_hotkey, self.key_abort)

        self.grp_hotkeys.setLayout(form)
        hk_layout.addWidget(self.grp_hotkeys)
        hk_layout.addStretch()
        self.tabs.addTab(hotkey_tab, "")

        # ═══ Tab 2: AI 画图设置 ═══
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)

        self.grp_ai = QGroupBox()
        ai_form = QFormLayout()

        self.lbl_ai_provider = QLabel()
        self.combo_ai_provider = QComboBox()
        self.combo_ai_provider.addItem(i18n.t("api_dalle"), "openai")
        self.combo_ai_provider.addItem(i18n.t("api_sd"), "sd")
        self.combo_ai_provider.addItem(i18n.t("api_custom"), "custom")
        self.combo_ai_provider.currentIndexChanged.connect(self._on_provider_changed)
        ai_form.addRow(self.lbl_ai_provider, self.combo_ai_provider)

        self.lbl_ai_url = QLabel()
        self.edit_api_url = QLineEdit()
        self.edit_api_url.setPlaceholderText(i18n.t("ai_api_url_hint_openai"))
        ai_form.addRow(self.lbl_ai_url, self.edit_api_url)

        self.lbl_ai_key = QLabel()
        self.edit_api_key = QLineEdit()
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        ai_form.addRow(self.lbl_ai_key, self.edit_api_key)

        self.grp_ai.setLayout(ai_form)
        ai_layout.addWidget(self.grp_ai)

        # 提示词
        self.grp_prompt = QGroupBox()
        prompt_layout = QVBoxLayout()

        preset_row = QHBoxLayout()
        self.lbl_preset = QLabel()
        preset_row.addWidget(self.lbl_preset)
        self.combo_preset = QComboBox()
        self.combo_preset.addItem(i18n.t("ai_select_preset"), "")
        for p in PRESET_PROMPTS:
            label = p["name_zh"] if i18n.language == "zh_CN" else p["name_en"]
            self.combo_preset.addItem(label, p["prompt"])
        self.combo_preset.currentIndexChanged.connect(self._on_preset_selected)
        preset_row.addWidget(self.combo_preset, 1)
        prompt_layout.addLayout(preset_row)

        self.lbl_prompt = QLabel()
        prompt_layout.addWidget(self.lbl_prompt)
        self.edit_prompt = QTextEdit()
        self.edit_prompt.setMinimumHeight(100)
        self.edit_prompt.setPlaceholderText(i18n.t("ai_prompt_placeholder"))
        prompt_layout.addWidget(self.edit_prompt)

        self.grp_prompt.setLayout(prompt_layout)
        ai_layout.addWidget(self.grp_prompt)
        ai_layout.addStretch()
        self.tabs.addTab(ai_tab, "")

        layout.addWidget(self.tabs)

        # ═══ 底部按钮 ═══
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save = QPushButton()
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)

        self.btn_cancel = QPushButton()
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self._retranslate()

    # ──────────── 翻译 ────────────

    def _retranslate(self, _lang=None):
        self.setWindowTitle(i18n.t("settings_title"))
        self.tabs.setTabText(0, i18n.t("settings_tab_hotkeys"))
        self.tabs.setTabText(1, i18n.t("settings_tab_ai"))

        self.grp_hotkeys.setTitle(i18n.t("group_hotkeys"))
        self.lbl_start_hotkey.setText(i18n.t("lbl_start_hotkey"))
        self.lbl_calib_start.setText(i18n.t("lbl_calib_start"))
        self.lbl_calib_end.setText(i18n.t("lbl_calib_end"))
        self.lbl_abort_hotkey.setText(i18n.t("lbl_abort_hotkey"))

        self.grp_ai.setTitle(i18n.t("settings_tab_ai"))
        self.lbl_ai_provider.setText(i18n.t("ai_provider"))
        self.lbl_ai_url.setText(i18n.t("ai_api_url"))
        self.lbl_ai_key.setText(i18n.t("ai_api_key"))

        # 重新填充 provider combo（保持选中项）
        current_data = self.combo_ai_provider.currentData()
        self.combo_ai_provider.blockSignals(True)
        self.combo_ai_provider.clear()
        self.combo_ai_provider.addItem(i18n.t("api_dalle"), "openai")
        self.combo_ai_provider.addItem(i18n.t("api_sd"), "sd")
        self.combo_ai_provider.addItem(i18n.t("api_custom"), "custom")
        idx = self.combo_ai_provider.findData(current_data)
        if idx >= 0:
            self.combo_ai_provider.setCurrentIndex(idx)
        self.combo_ai_provider.blockSignals(False)

        # 重新填充 preset combo
        current_preset_idx = self.combo_preset.currentIndex()
        self.combo_preset.blockSignals(True)
        self.combo_preset.clear()
        self.combo_preset.addItem(i18n.t("ai_select_preset"), "")
        for p in PRESET_PROMPTS:
            label = p["name_zh"] if i18n.language == "zh_CN" else p["name_en"]
            self.combo_preset.addItem(label, p["prompt"])
        self.combo_preset.setCurrentIndex(max(0, current_preset_idx))
        self.combo_preset.blockSignals(False)

        self.grp_prompt.setTitle(i18n.t("ai_prompt"))
        self.lbl_preset.setText(i18n.t("ai_preset_prompts"))
        self.lbl_prompt.setText(i18n.t("ai_prompt"))
        self.edit_prompt.setPlaceholderText(i18n.t("ai_prompt_placeholder"))

        self.btn_save.setText(i18n.t("settings_save"))
        self.btn_cancel.setText(i18n.t("settings_cancel"))

    # ──────────── 事件 ────────────

    def _on_provider_changed(self, _idx):
        provider = self.combo_ai_provider.currentData()
        hints = {
            "openai": i18n.t("ai_api_url_hint_openai"),
            "sd": i18n.t("ai_api_url_hint_sd"),
            "custom": i18n.t("ai_api_url_hint_custom"),
        }
        self.edit_api_url.setPlaceholderText(hints.get(provider, ""))

    def _on_preset_selected(self, index):
        prompt_text = self.combo_preset.currentData()
        if prompt_text:
            self.edit_prompt.setPlainText(prompt_text)

    # ──────────── 加载 / 保存 ────────────

    def _load_settings(self):
        if not os.path.isfile(SETTINGS_PATH):
            return
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            return

        # 快捷键
        hotkeys = settings.get("hotkeys", {})
        mapping = {
            "start": self.key_start,
            "calib_start": self.key_calib_start,
            "calib_end": self.key_calib_end,
            "abort": self.key_abort,
        }
        for key, editor in mapping.items():
            if key in hotkeys and hotkeys[key]:
                editor.setKeySequence(QKeySequence(hotkeys[key]))

        # AI 设置
        ai = settings.get("ai", {})
        provider = ai.get("provider", "openai")
        idx = self.combo_ai_provider.findData(provider)
        if idx >= 0:
            self.combo_ai_provider.setCurrentIndex(idx)
        self.edit_api_url.setText(ai.get("api_url", ""))
        self.edit_api_key.setText(ai.get("api_key", ""))
        self.edit_prompt.setPlainText(ai.get("prompt", ""))

    def _on_save(self):
        ensure_data_dirs()
        # 读取已有设置（防止覆盖其他字段）
        settings = {}
        if os.path.isfile(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        settings["hotkeys"] = {
            "start": self.key_start.keySequence().toString(),
            "calib_start": self.key_calib_start.keySequence().toString(),
            "calib_end": self.key_calib_end.keySequence().toString(),
            "abort": self.key_abort.keySequence().toString(),
        }
        settings["ai"] = {
            "provider": self.combo_ai_provider.currentData() or "openai",
            "api_url": self.edit_api_url.text().strip(),
            "api_key": self.edit_api_key.text().strip(),
            "prompt": self.edit_prompt.toPlainText().strip(),
        }

        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

        self.settings_saved.emit()
        self.accept()

    # ──────────── 公共接口 ────────────

    def get_hotkeys(self) -> dict:
        """返回当前快捷键配置字典。"""
        return {
            "start": self.key_start.keySequence().toString(),
            "calib_start": self.key_calib_start.keySequence().toString(),
            "calib_end": self.key_calib_end.keySequence().toString(),
            "abort": self.key_abort.keySequence().toString(),
        }

    def get_ai_settings(self) -> dict:
        """返回当前 AI 配置字典。"""
        return {
            "provider": self.combo_ai_provider.currentData() or "openai",
            "api_url": self.edit_api_url.text().strip(),
            "api_key": self.edit_api_key.text().strip(),
            "prompt": self.edit_prompt.toPlainText().strip(),
        }


def load_settings() -> dict:
    """从磁盘读取设置文件，返回 dict。"""
    if not os.path.isfile(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_settings(settings: dict):
    """将设置写入磁盘。"""
    ensure_data_dirs()
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except IOError:
        pass
