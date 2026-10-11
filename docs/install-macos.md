# macOS 安装 / Install on macOS

Apple Silicon（M1 或更新芯片），macOS 14 或更新系统。本预览版不支持 Intel Mac。
无需安装 Python、uv、Homebrew，也不需要管理员密码。公开包附 30 词原创示例。

## 一条命令

在「终端」粘贴以下命令。它会从本项目 GitHub Release 下载安装脚本并执行；
脚本会校验程序 ZIP 的 SHA-256，再安装到当前用户目录。

```sh
curl --proto '=https' --tlsv1.2 -fsSL https://github.com/shanezchang/sideword/releases/download/v0.4.0-beta.1/install.sh | /bin/bash
```

完成后，新开终端输入 `sideword`。在当前终端立即启动则用：

```sh
~/.local/bin/sideword
```

不想直接执行远程脚本？先下载 `install.sh`，阅读后再运行 `bash install.sh`。
SHA-256 用于发现下载损坏，不替代开发者签名。只从本项目的 Release 下载。

## 下载后双击

1. 从 [Release](https://github.com/shanezchang/sideword/releases/tag/v0.4.0-beta.1)
   下载 `sideword-macos-arm64.zip`（不是 GitHub 自动生成的 Source code）。
2. 解压并双击 `Sideword/Install.command`。终端会显示安装结果。
3. 安装后按回车开始。以后可在个人 `Applications` 文件夹双击 `Sideword.command`，
   或在终端输入 `sideword`。

**这是未公证预览版。** 程序仅有本地 ad-hoc 签名，没有 Developer ID 分发签名和
Apple 公证。浏览器下载后，macOS 可能拦截脚本或程序。确认来自本仓库后，可按系统
「系统设置 → 隐私与安全性 → 仍要打开」提示单独批准；组织管控的 Mac 可能不允许。
不要关闭 Gatekeeper、不要批量移除隔离属性。若系统不允许，请使用 README 的 uv 源码安装方式。
完整的浏览器下载、首次安全批准流程尚需不同 macOS 设备验证，不承诺零提示双击安装。

## 安装位置、升级与卸载

- 程序：`~/.local/opt/sideword/versions/`；命令：`~/.local/bin/sideword`。
- 双击启动：`~/Applications/Sideword.command`。
- 默认记录、词库、音频：`~/.local/share/sideword/`，安装器不会修改这里。
- 安装器给 zsh 的 `.zshrc`（遵循 `ZDOTDIR`）或 bash 的 `.bash_profile` 添加一条 PATH；
  `bash install.sh --no-modify-path` 可跳过。其他 shell 需自行添加 `~/.local/bin`。
- 重复运行安装命令会安装这个固定版本；升级请使用新 Release 给出的命令。
  旧版程序和被替换的启动器留在 `~/.local/opt/sideword/`，方便恢复。
- 卸载时，在 Finder 按 `⌘⇧G` 前往以上路径，将 **Sideword 专属**程序目录、命令和启动器
  移到废纸篓，并移除 shell 配置中 `# Sideword PATH` 及紧随其后的 PATH 行。
  **保留 `~/.local/share/sideword/` 即可保留学习记录。** 不要删除整个 `.local`。

从 uv 安装切换过来时，旧命令链接会备份，但 uv 环境不会被删除。以后不要混用两个
安装器升级；如要回到 uv，请重新执行 README 中的 `uv tool install --force ...`。

## 配置、备份与回退 / Settings, backup and rollback

`--quiet` 仅关闭本次自动播放；`M` 保存每页词数，`V` 保存口音，`A` 保存自动播放偏好。
这些偏好、随机队列、选中位置和自评进度都在数据目录的 `progress.sqlite3`，没有单独配置文件。
数据目录优先级：`--data-dir` → `$XDG_DATA_HOME/sideword` → `~/.local/share/sideword`。
升级前退出所有 Sideword 窗口，复制**实际使用的数据目录**到自己选择的备份位置；不要只复制
正在使用中的 SQLite 主文件（可能还有 WAL）。自带 30 词样例无需另行下载。

安装结束会输出 `Previous launchers`。升级前保存该目录路径，并保留旧 `versions/` 目录。
如新版本打不开，先退出程序，将下面 `launchers.REPLACE_ME` 换成这次升级产生的备份目录，
确认它含有旧 `sideword` 和 `Sideword.command` 后，再执行：

```sh
root="$HOME/.local/opt/sideword"
backup="$root/backups/launchers.REPLACE_ME"
# 必须指向一次升级的备份，而非第一次安装的空备份。
if { [ -f "$backup/sideword" ] || [ -L "$backup/sideword" ]; } &&
   [ -f "$backup/Sideword.command" ]; then
    restore=$(mktemp -d "$root/backups/restore.XXXXXX") &&
    cp -P "$backup/sideword" "$restore/sideword" &&
    cp -P "$backup/Sideword.command" "$restore/Sideword.command" &&
    mv -f "$restore/sideword" "$HOME/.local/bin/sideword" &&
    mv -f "$restore/Sideword.command" "$HOME/Applications/Sideword.command" &&
    "$HOME/.local/bin/sideword" --version
else
    printf 'Choose an upgrade backup containing both previous launchers.\n'
fi
```

回退后启动程序，核对词库、当前词、每页词数和已有自评。不要只比较 ZIP 的校验值。
以上只恢复程序入口，不改学习数据或覆盖当前 shell 配置；若未来版本改了数据库格式，
先看该版发行说明，再决定是否恢复升级前的数据备份（恢复会丢失备份后的学习记录）。
目前只有一个公开预览版本，不宣称已经验证跨版本数据库迁移。

Uninstall removes only Sideword's program directory and launchers; keep the actual
`--data-dir` / XDG data directory to preserve progress. Before an upgrade, close all
sessions and copy that entire directory. Keep the installer's printed backup path.
The commands above restore the previous launchers, not your database or shell
settings. Open the restored app and check the current word and preferences. Do not
assume a future database migration is downgrade-compatible.

安全问题请使用 [私密报告渠道](https://github.com/shanezchang/sideword/security/advisories/new)，不要在公开 issue 上传词库或数据库。

## English quick notes

Apple Silicon, macOS 14+. Run the one-line installer above, then open a new terminal
and type `sideword`. Alternatively, download the ZIP and double-click `Install.command`.
No Python or administrator access required. This is an **unnotarized preview**;
Gatekeeper may require explicit approval. Never disable system security protections.
The installer preserves learning data, backs up existing launchers, and adds a PATH
entry for zsh/bash. Use `--no-modify-path` to opt out. Re-running installs the pinned
version, not an automatically selected latest version.
