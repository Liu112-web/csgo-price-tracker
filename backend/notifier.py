"""
notifier.py
当价格超过购入价时发出提醒。优先使用 Windows 原生 toast，
不可用时回退到 plyer / 控制台。
"""
import logging
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def _windows_toast(title: str, message: str) -> bool:
    """通过 Windows.UI.Notifications 发送桌面通知。"""
    # 注意：单引号 here-string 不会展开变量，所以 title/message
    # 需要在 Python 端替换好再传进去。
    title_xml = _xml_escape(title)
    message_xml = _xml_escape(message)
    # AUMID 形如 {GUID}\\PowerShell.exe，里面的 { } 是字面量，
    # 所以这里不能用 f-string（f-string 解析 { } 会失败），用普通拼接。
    ps_script = (
        "Add-Type -AssemblyName PresentationFramework\n"
        "[xml]$template = @'\n"
        "<toast duration=\"long\" launch=\"\">\n"
        "  <visual>\n"
        "    <binding template=\"ToastGeneric\">\n"
        "      <text>" + title_xml + "</text>\n"
        "      <text>" + message_xml + "</text>\n"
        "    </binding>\n"
        "  </visual>\n"
        "  <audio src=\"ms-winsoundevent:Notification.Default\"/>\n"
        "</toast>\n"
        "'@\n"
        "$toastXml = New-Object Windows.Data.XmlDocuments.XmlDocument\n"
        "$toastXml.LoadXml($template)\n"
        "$appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'\n"
        "$notify = [Windows.UI.Notifications.ToastNotificationManager]"
        "::CreateToastNotifier($appId)\n"
        "$notify.Show([Windows.UI.Notifications.ToastNotification]::new($toastXml))\n"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
        )
        if completed.returncode == 0:
            return True
        logger.warning("PowerShell toast 失败: %s", completed.stderr.strip())
    except FileNotFoundError:
        logger.warning("未找到 powershell，跳过 toast。")
    except Exception as e:
        logger.warning("调用 PowerShell 出错: %s", e)
    return False


def _xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))


def _plyer_notify(title: str, message: str) -> bool:
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            title=title,
            message=message,
            app_name="CSGO 弯刀价格监控",
            timeout=10,
        )
        return True
    except Exception as e:
        logger.warning("plyer 通知失败: %s", e)
        return False


def _win10toast_click(title: str, message: str) -> bool:
    """回退方案：win10toast（仅 Windows）。"""
    try:
        from win10toast import ToastNotifier  # type: ignore
        ToastNotifier().show_toast(
            title=title,
            msg=message,
            duration=10,
            threaded=True,
        )
        return True
    except Exception as e:
        logger.warning("win10toast 失败: %s", e)
        return False


def send_desktop_notification(title: str, message: str) -> bool:
    """按顺序尝试多种桌面通知方式。"""
    if sys.platform != "win32":
        logger.info("当前非 Windows，跳过桌面通知。")
        return False
    if _windows_toast(title, message):
        return True
    if _win10toast_click(title, message):
        return True
    if _plyer_notify(title, message):
        return True
    logger.error("所有桌面通知方式都失败了。")
    return False


def notify_price_alert(item_name: str, price: float,
                       target_price: float) -> bool:
    """当价格超过 target_price 时发送的提醒。"""
    title = "🔔 CSGO 弯刀 传说 价格提醒"
    msg = (f"{item_name}\n"
           f"当前最低在售: ¥{price:.2f}\n"
           f"已超过目标价: ¥{target_price:.2f}")
    return send_desktop_notification(title, msg)
