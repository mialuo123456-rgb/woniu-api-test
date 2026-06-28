#!/usr/bin/env bash
#
# Claude Code 环境重置脚本 - 兼容 macOS 与 Linux
#

# ============================================================
# 1. Shell 检测与 re-exec（纯 POSIX 语法，避免在 ash/dash 下解析失败）
# ============================================================
if [ -z "${BASH_VERSION:-}" ]; then
    if command -v bash >/dev/null 2>&1; then
        if [ -f "$0" ] && [ -r "$0" ]; then
            exec bash "$0" "$@"
        fi
        printf '错误：此脚本需要使用 bash 运行。\n' >&2
        printf '请改用： curl -fsSL https://lycoriz.cc/clear.sh | sudo bash\n' >&2
        exit 1
    fi
    printf '错误：系统未找到 bash，请先安装 bash 3.0 或更高版本。\n' >&2
    exit 1
fi

set -euo pipefail

# ============================================================
# 2. 颜色与辅助函数
# ============================================================
c_red=$'\033[31m'
c_green=$'\033[32m'
c_yellow=$'\033[33m'
c_cyan=$'\033[36m'
c_gray=$'\033[90m'
c_reset=$'\033[0m'

say()  { printf '%s%s%s\n' "$c_cyan"   "$1" "$c_reset"; }
note() { printf '%s%s%s\n' "$c_gray"   "$1" "$c_reset"; }
ok()   { printf '%s%s%s\n' "$c_green"  "$1" "$c_reset"; }
warn() { printf '%s%s%s\n' "$c_yellow" "$1" "$c_reset"; }
err()  { printf '%s%s%s\n' "$c_red"    "$1" "$c_reset"; }

is_darwin() { [ "$(uname -s)" = "Darwin" ]; }

# 以真实调用者身份执行命令（未 sudo 时直接执行）
run_as_user() {
    if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
        sudo -u "$SUDO_USER" -H "$@"
    else
        "$@"
    fi
}

# 结束前暂停一次，双击本地运行时能看清最后的输出；
# 在 curl|sudo bash 的管道场景下 stdin 已 EOF，read 立即返回，不会卡住。
trap 'read -rp "按回车键关闭窗口..." _ 2>/dev/null || true' EXIT

# ============================================================
# 3. Root 权限检查
# ============================================================
if [ "$(id -u)" -ne 0 ]; then
    err "抱歉，这项操作需要管理员权限喵，请使用 sudo 运行此脚本喵。"
    exit 1
fi

# ============================================================
# 4. 解析真实调用者与 home 目录
# ============================================================
if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
    realUser="$SUDO_USER"
    realHome=""
    if command -v getent >/dev/null 2>&1; then
        realHome=$(getent passwd "$realUser" 2>/dev/null | cut -d: -f6 || true)
    fi
    if [ -z "$realHome" ] && command -v dscl >/dev/null 2>&1; then
        realHome=$(dscl . -read "/Users/$realUser" NFSHomeDirectory 2>/dev/null | awk '/^NFSHomeDirectory:/ {print $2}' || true)
    fi
    if [ -z "$realHome" ]; then
        # 兜底：用 shell 的 ~user 展开
        realHome=$(bash -c "printf '%s' ~$realUser" 2>/dev/null || true)
        case "$realHome" in "~$realUser") realHome="" ;; esac
    fi
    if [ -z "$realHome" ] || [ ! -d "$realHome" ]; then
        realHome="${HOME:-/root}"
    fi
else
    realUser="${USER:-$(id -un)}"
    realHome="${HOME:-/root}"
fi

# ============================================================
# 5. 首次确认
# ============================================================
echo ""
say "我们知道你已经很累了，在开始下一次航行前，请容许你自己休息休息。"
note "                                                           --林小夕"
echo ""
say "这个脚本将整体重置你的电脑系统环境，以便继续猫和老鼠的游戏。"
ok  "这不会危害你的 plugin 与 skill"

confirm=""
read -rp "这可以吗? [y/n] " confirm < /dev/tty || confirm=""
case "$confirm" in
    y|Y) ;;
    *)
        say "没关系，随时准备好了再来就好喵"
        exit 0
        ;;
esac

# ============================================================
# 6. 构造待清理路径
# ============================================================
claudeDir="$realHome/.claude"

paths=()
paths+=("$realHome/.claude.json")
paths+=("$claudeDir/history.jsonl")
paths+=("$claudeDir/session-env")
paths+=("$claudeDir/shell-snapshots")
paths+=("$claudeDir/paste-cache")
paths+=("$claudeDir/.credentials.json")
paths+=("$claudeDir/mcp-needs-auth-cache.json")
paths+=("$claudeDir/hsettings.json")
paths+=("$claudeDir/stats-cache.json")
paths+=("$claudeDir/telemetry")
paths+=("$claudeDir/tasks")
paths+=("$claudeDir/sessions")
paths+=("$claudeDir/projects")
paths+=("$claudeDir/file-history")
paths+=("$claudeDir/cache")
paths+=("$claudeDir/backups")

if is_darwin; then
    paths+=("/Applications/Claude.app")
    paths+=("$realHome/Library/Application Support/Claude")
    paths+=("$realHome/Library/Caches/com.anthropic.claude")
    paths+=("$realHome/Library/Caches/Claude")
    paths+=("$realHome/Library/Saved Application State/com.anthropic.claude.savedState")
    paths+=("$realHome/Library/Preferences/com.anthropic.claude.plist")
    paths+=("$realHome/Library/Logs/Claude")
fi

# .claude.json.backup* 备份文件
for f in "$realHome"/.claude.json.backup*; do
    [ -e "$f" ] || continue
    paths+=("$f")
done

# 去重，保持原顺序
uniqPaths=()
for p in "${paths[@]}"; do
    dup=0
    if [ "${#uniqPaths[@]}" -gt 0 ]; then
        for q in "${uniqPaths[@]}"; do
            if [ "$p" = "$q" ]; then dup=1; break; fi
        done
    fi
    [ "$dup" -eq 0 ] && uniqPaths+=("$p")
done

echo ""
say "接下来会清理这些路径喵："
for p in "${uniqPaths[@]}"; do
    printf '%s  %s%s\n' "$c_cyan" "$p" "$c_reset"
done

# ============================================================
# 7. 执行清理
# ============================================================
say "开始为你清理文件..."
for p in "${uniqPaths[@]}"; do
    if [ -e "$p" ] || [ -L "$p" ]; then
        printf '%s正在清理：%s%s\n' "$c_gray" "$p" "$c_reset"
        rm -rf "$p"
    else
        printf '%s已经不在了：%s%s\n' "$c_gray" "$p" "$c_reset"
    fi
done
say "文件清理完成啦喵"
sleep 3

# ============================================================
# 8. 修改机器标识
# ============================================================
echo ""
if is_darwin; then
    oldId=$(ioreg -rd1 -c IOPlatformExpertDevice 2>/dev/null | awk -F'"' '/IOPlatformUUID/{print $4}' || true)
    newId=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]' || true)
    say "正在为你尝试更换系统身份标识（仅偏好写入，硬件 UUID 为只读）："
    printf '%s  旧的：%s%s\n' "$c_gray"  "$oldId" "$c_reset"
    printf '%s  新的：%s%s\n' "$c_green" "$newId" "$c_reset"
    defaults write /Library/Preferences/SystemConfiguration/com.apple.platform UUID "$newId" 2>/dev/null || true
    verifyId=$(defaults read /Library/Preferences/SystemConfiguration/com.apple.platform UUID 2>/dev/null || echo "")
    if [ "$verifyId" = "$newId" ]; then
        warn "偏好写入成功，但 macOS 的真实硬件 UUID 为只读，无法通过此方法修改喵。"
    else
        warn "写入偏好失败，macOS 硬件 UUID 为只读标识，无法修改喵。"
    fi
else
    if [ -f /etc/machine-id ]; then
        oldId=$(cat /etc/machine-id)
        if [ -r /proc/sys/kernel/random/uuid ]; then
            newId=$(tr -d '-' < /proc/sys/kernel/random/uuid)
        elif command -v uuidgen >/dev/null 2>&1; then
            newId=$(uuidgen | tr -d '-' | tr '[:upper:]' '[:lower:]')
        else
            newId=$(od -An -vtx1 -N16 /dev/urandom | tr -d ' \n')
        fi
        say "正在为你更换一个新的系统身份标识："
        printf '%s  旧的：%s%s\n' "$c_gray"  "$oldId" "$c_reset"
        printf '%s  新的：%s%s\n' "$c_green" "$newId" "$c_reset"
        echo "$newId" > /etc/machine-id
        if [ -d /var/lib/dbus ]; then
            cp /etc/machine-id /var/lib/dbus/machine-id 2>/dev/null || true
        fi
        verifyId=$(cat /etc/machine-id)
        if [ "$verifyId" = "$newId" ]; then
            ok "系统标识已焕然一新喵"
        else
            err "抱歉，系统标识修改没能成功，请检查一下权限喵。"
        fi
    else
        warn "未找到 /etc/machine-id，跳过系统标识修改喵"
    fi
fi
sleep 3

# ============================================================
# 9. 修改 Git 用户邮箱
# ============================================================
oldEmail=$(run_as_user git config --global user.email 2>/dev/null || echo "")
[ -z "$oldEmail" ] && oldEmail="(未设置)"

# 使用 bash 内置 $RANDOM 生成随机字符串，避免 /dev/urandom + tr 的 SIGPIPE 问题
gen_username() {
    local chars="abcdefghijklmnopqrstuvwxyz0123456789"
    local len=${#chars}
    local out=""
    local i=0
    while [ "$i" -lt 10 ]; do
        out="${out}${chars:$((RANDOM % len)):1}"
        i=$((i + 1))
    done
    printf '%s' "$out"
}

case "$oldEmail" in
    *@gmail.com)
        newEmail="$(gen_username)@gmail.com"
        ;;
    *@*)
        username="${oldEmail%@*}"
        newEmail="${username}@gmail.com"
        ;;
    *)
        newEmail="$(gen_username)@gmail.com"
        ;;
esac

echo ""
say "我们即将重置你的 git 邮箱。下面是该方法对您的影响："
echo ""
ok "无影响的方面："
note "  - 代码内容、文件、提交历史完全不受影响"
note "  - 仓库功能正常，clone/push/pull 都没问题"
note "  - 分支、合并、rebase 等操作照常"
echo ""
warn "唯一影响的方面："
note "  - GitHub/GitLab 等平台上，提交记录的头像会显示为默认灰色图标（无法关联到账号）"
note "  - 贡献统计不会计入你的账号（Contributions graph 不会亮绿格子）"
echo ""
ok "但是相应的，重置之后下次使用会更加稳定"
echo ""
printf '%s  旧的：%s%s\n' "$c_gray"  "$oldEmail" "$c_reset"
printf '%s  新的：%s%s\n' "$c_green" "$newEmail" "$c_reset"

emailConfirm=""
read -rp "确认重置吗? [y/n] " emailConfirm < /dev/tty || emailConfirm=""
case "$emailConfirm" in
    y|Y)
        if run_as_user git config --global user.email "$newEmail"; then
            verifyEmail=$(run_as_user git config --global user.email 2>/dev/null || echo "")
            if [ "$verifyEmail" = "$newEmail" ]; then
                ok "Git 邮箱已经换好啦喵"
            else
                err "抱歉，Git 邮箱修改没能成功。"
            fi
        else
            err "抱歉，Git 邮箱修改没能成功。"
        fi
        ;;
    *)
        say "已跳过 Git 邮箱重置喵"
        ;;
esac
sleep 3

# ============================================================
# 10. 修正 shell 配置文件中的 Claude 相关环境变量
# ============================================================
echo ""
say "正在检查并修正 Claude 的遥测与网络环境变量喵..."

envVarsToDisable=(
    "DISABLE_TELEMETRY"
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"
    "CLAUDE_CODE_USE_BEDROCK"
    "CLAUDE_CODE_USE_VERTEX"
)

profileFiles=(
    "$realHome/.bashrc"
    "$realHome/.bash_profile"
    "$realHome/.profile"
    "$realHome/.zshrc"
)
if is_darwin; then
    profileFiles+=("$realHome/.zprofile")
fi

for varName in "${envVarsToDisable[@]}"; do
    found=0
    for pf in "${profileFiles[@]}"; do
        [ -f "$pf" ] || continue
        if grep -Eq "^[[:space:]]*export[[:space:]]+${varName}=" "$pf" 2>/dev/null; then
            # sed -i.bak 同时适配 GNU sed 和 BSD sed（macOS）
            sed -i.bak -E "s#^[[:space:]]*export[[:space:]]+${varName}=.*#export ${varName}=0#" "$pf"
            rm -f "${pf}.bak"
            found=1
        elif grep -Eq "^[[:space:]]*${varName}=" "$pf" 2>/dev/null; then
            sed -i.bak -E "s#^[[:space:]]*${varName}=.*#${varName}=0#" "$pf"
            rm -f "${pf}.bak"
            found=1
        fi
    done
    if [ "$found" -eq 1 ]; then
        printf '%s  %s 已在 shell 配置文件里设为 0 喵~%s\n' "$c_green" "$varName" "$c_reset"
    else
        note "  $varName 没有在任何 shell 配置文件里显式声明，跳过喵。"
    fi
done
say "环境变量检查完毕喵！"

# ============================================================
# 11. 时区检测
# ============================================================
offset=$(date +%z 2>/dev/null || echo "")
case "$offset" in
    +0800|+08)
        echo ""
        warn "小提示：还没有检测到时区修改喵，记得让时区和你的代理在同一地点，这样更安全喵。"
        ;;
esac

# ============================================================
# 12. 语言检测
# ============================================================
lang="${LANG:-${LC_ALL:-${LC_MESSAGES:-}}}"
case "$lang" in
    en*|C|C.*|POSIX) ;;
    *)
        warn "小提示：当前系统语言不是英文，如果方便的话，换成英文会更不容易暴露喵"
        ;;
esac

# ============================================================
# 13. 收尾
# ============================================================
echo ""
say "一切都准备好啦喵，祝你下一次航行顺利"
echo ""
warn "TIP：带有 git 的项目存在泄露 hash 的危险。"
warn "通俗来说就是如果你账号A使用在这个项目开发，封号后换到账号B，该 hash 会将AB视为同一人使用，即有概率会连坐。"
warn "建议方法：项目不要使用 git，并删除 .git 目录。"
