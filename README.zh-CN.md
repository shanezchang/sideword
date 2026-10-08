# Sideword

在终端里学英语：先认识单词，再按时复习。离线运行，无需账号。

## 启动

macOS / Linux，Python 3.9+，无需安装第三方 Python 依赖。
克隆后直接运行：

```sh
git clone https://github.com/shanezchang/sideword.git
cd sideword
python3 app.py --page-size 10
```

- M 输入任意正整数设置每页词数，Enter 保存，Esc 取消。
- ↑↓ 选词，←→ 翻页；窗口放不下时随选中词滚动，不改变设置。
- Enter 打开完整释义和双语例句，再按返回。
- 默认自动播放选中词的英音，空格重播；A 开关自动播放，V 切换口音，X 停止。
- 1 不熟，2 记住。记住的词退出日常学习列表，但仍安排到期复习。
- R 到期复习，P 查看排程；复习时先回忆，Enter 揭晓后再自评。
- F 收藏，S 读例句，T 开关例句翻译；Tab 首页，Esc 保存退出。

每页默认 5 词，顺序随机但持久保存。看过不等于记住；拼写测验是可选项。
记住后间隔从 1 天逐步延长至 3、7、14、30、60 天，忘记则回到 10 分钟。
这是简化排程，不是不背单词的专有算法，也不代表经过验证的记忆曲线。

## 公开版与本机词库

公开版附 30 词原创示例，包含英音音标、中文解释、双语例句和搭配。
未捆绑授权尚未核清的教材词库；它不是官方雅思课程。
导入自己有权使用的本地词库见 [数据说明](data/README.md)。

进度与缓存默认在 `~/.local/share/sideword/`，遵循 XDG_DATA_HOME。
无联网请求、账号、遥测或后台通知。

发音使用 macOS 系统合成语音；Linux 目前只支持无声学习。
开发沙箱未完成真实出声验收；无声时运行 `python3 app.py --audio-check`。

## 技术与验证

Python 标准库：curses 界面、SQLite 本地数据、subprocess 发音进程。
`python3 -m unittest -v` 运行测试；测试不会修改真实学习记录。
建议终端 80×24，最低 42×15。Windows 原生终端暂不支持，可尝试 WSL。

独立代码及原创示例使用 MIT 许可证。完整说明见 [README](README.md)。
