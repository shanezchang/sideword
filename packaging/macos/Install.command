#!/bin/bash
set -eu
bundle_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
if /bin/bash "$bundle_dir/install.sh" --local "$bundle_dir"; then
    printf '\n安装完成。按回车开始学习 / Press Return to start learning.\n'
    read -r
    exec "$HOME/.local/bin/sideword"
else
    printf '\n安装未完成。按回车关闭 / Installation failed. Press Return to close.\n'
    read -r
    exit 1
fi
