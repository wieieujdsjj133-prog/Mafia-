import shutil
import subprocess


ALLOWED_APT_PACKAGES = {
    "nmap",
    "whois",
    "dnsutils",
    "jq",
    "curl",
    "openssl",
}


def install_apt(package: str):
    package = package.strip().lower()

    if package not in ALLOWED_APT_PACKAGES:
        return False, "هذه الحزمة غير موجودة في قائمة التثبيت المسموحة."

    if shutil.which("apt-get") is None:
        return False, "apt-get غير متوفر."

    try:
        result = subprocess.run(
            ["sudo", "apt-get", "install", "-y", package],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return False, result.stderr[-2000:]

        return True, f"تم تثبيت {package}."

    except Exception as exc:
        return False, str(exc)


def install_python_package(package: str):
    package = package.strip()

    if not package:
        return False, "اسم الحزمة فارغ."

    # نستخدم pip فقط للحزم التي تم التحقق منها عبر PyPI.
    try:
        result = subprocess.run(
            ["python3", "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            return False, result.stderr[-2000:]

        return True, f"تم تثبيت حزمة Python: {package}"

    except Exception as exc:
        return False, str(exc)
