# AutoPainter Win

![LOGO](doc/LOGO.png)

AutoPainter Win 是一个基于 PyQt5 的桌面应用，用于将图片转换为线稿，并提供自动绘画相关的界面与核心模块。

## 功能概览

- 图片转线稿
- 多种线稿风格：
  - Pencil
  - Pen
  - Ink
  - Comic
  - Contour
  - AI（当前界面中为预留选项）
- 可调参数：
  - 线条粗细
  - 对比度
  - 阈值
  - 反色
- 原图 / 线稿对比预览
- 中英文界面切换
- 文本渲染模式，可将输入文字生成黑白路径图用于后续绘制
- 记忆化的绘画按键选择（左 / 右键），历史记录自动去重


## 示例展示
![alt text](doc/37eb39209880acd6546957dec9989e86.png)

## 当前状态

- 线稿生成功能已接入桌面界面
- 自动绘画核心 `core/auto_painter.py` 已与界面联通，可直接从左侧面板启动真实绘画流程
- UI 中支持绘画速度、左右键选择与热键校准画布

## 环境要求

- Python 3.9+
- Windows / macOS

依赖见 `requirements.txt`：

- PyQt5
- opencv-python
- numpy
- pyautogui
- pynput（macOS/Linux 用于全局热键监听）
- Pillow（作为高版本 Python 的 OpenCV 兼容降级依赖）

### Python 版本说明

- Python 3.9–3.12：默认使用 OpenCV，效果最好、速度最快。
- Python 3.13+：OpenCV 可能不可用，本项目会自动切换到纯 Python 图像处理（依赖 Pillow）。
  该模式可运行但效果和性能会略弱。

## 安装

```bash
pip install -r requirements.txt
```

## macOS 说明

- 首次运行时需要在 **系统设置 → 隐私与安全性** 中给 Python/Terminal 授权：
  - **辅助功能**（用于控制鼠标）
  - **输入监控**（用于全局热键）
- 若热键无响应，请重新打开应用或终端，让系统重新加载权限。

## 运行

```bash
python main.py
```

启动后可按以下流程使用：

1. 打开图片
2. 选择线稿风格
3. 调整线条粗细、对比度、阈值等参数
4. 生成并预览线稿
5. 如需修改快捷键或画笔按键，点击左侧面板顶部的「⚙️ 设置」或菜单中的「设置」
6. 需要时保存线稿，或切换到文字模式生成文本图像
7. 点击「开始绘画」，按提示用热键框出目标画布，等待自动绘制完成

### 自动绘画参数说明

- **绘画速度**：界面 1~100 数值线性映射到落点延迟时间，速度 1≈0.008s、速度 100≈0.0008s（数值越大越快）。
- **画笔按键**：在绘画面板中通过左右键二选一按钮切换，并自动保存，下次打开沿用。
- **热键**：默认 F7 记录画布左上角、F8 记录右下角，F5 开始绘画，ESC 可随时中断（可在界面中自定义）。

## 项目结构

```text
auto-painter-win/
├── main.py                 # 应用入口
├── core/
│   ├── sketch_generator.py # 线稿生成核心
│   ├── auto_painter.py     # 自动绘画相关逻辑
│   ├── ai_generator.py     # AI 线稿生成
│   ├── image_ops.py        # 图像处理后端（含无 OpenCV 降级）
│   ├── hotkey.py           # 跨平台热键检测
│   ├── mouseapi.py         # 跨平台鼠标控制
│   ├── deps.py             # 运行依赖检查
│   └── utils.py            # 图像读取与缩放等工具
├── ui/
│   ├── main_window.py      # 主窗口
│   ├── control_panel.py    # 左侧控制面板
│   ├── preview_panel.py    # 预览面板
│   ├── text_panel.py       # 文字模式面板
│   ├── settings_dialog.py  # 设置对话框
│   ├── styles.py           # 全局样式
│   └── i18n.py             # 中英文翻译
└── requirements.txt
```

## 说明

目前仓库中未包含现成的自动化测试或构建配置，主要通过本地运行桌面程序进行验证。
