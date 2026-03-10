"""
集中管理应用数据目录。

Windows : %APPDATA%/AutoPainter/
其它    : ~/.auto_painter/
"""
import os
import sys


def _data_root() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "AutoPainter")
    return os.path.join(os.path.expanduser("~"), ".auto_painter")


DATA_DIR: str = _data_root()
SETTINGS_PATH: str = os.path.join(DATA_DIR, "settings.json")
HISTORY_DIR: str = os.path.join(DATA_DIR, "history")


def ensure_data_dirs():
    """确保数据目录存在。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)


def migrate_legacy_data():
    """
    将旧版项目根目录下的 settings.json 和 history/ 迁移到新路径。
    仅在新路径尚无数据时执行一次。
    """
    import shutil

    project_root = os.path.dirname(os.path.dirname(__file__))

    # 迁移 settings.json
    old_settings = os.path.join(project_root, "settings.json")
    if os.path.isfile(old_settings) and not os.path.isfile(SETTINGS_PATH):
        ensure_data_dirs()
        shutil.copy2(old_settings, SETTINGS_PATH)

    # 迁移 history/
    old_history = os.path.join(project_root, "history")
    if os.path.isdir(old_history) and not os.path.isdir(HISTORY_DIR):
        ensure_data_dirs()
        shutil.copytree(old_history, HISTORY_DIR)


# 应用启动时自动执行迁移
ensure_data_dirs()
migrate_legacy_data()
