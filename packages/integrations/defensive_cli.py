from __future__ import annotations

from .specs import CommandSpec, require_nonblank, require_safe_local_path


def yara_scan_command(rule_file: str, target_path: str) -> CommandSpec:
    return CommandSpec(("yara", "-r", require_safe_local_path(rule_file, "rule_file"), require_safe_local_path(target_path, "target_path")))


def volatility_command(memory_image: str, plugin: str) -> CommandSpec:
    plugin_name = require_nonblank(plugin, "plugin")
    if not all(ch.isalnum() or ch in "._-" for ch in plugin_name):
        raise ValueError("plugin contains unsupported characters")
    return CommandSpec(("vol", "-f", require_safe_local_path(memory_image, "memory_image"), plugin_name))


def zeek_offline_command(pcap_path: str) -> CommandSpec:
    return CommandSpec(("zeek", "-r", require_safe_local_path(pcap_path, "pcap_path")))


def tshark_offline_command(pcap_path: str) -> CommandSpec:
    return CommandSpec(("tshark", "-r", require_safe_local_path(pcap_path, "pcap_path"), "-T", "json"))


def osquery_local_command(sql: str) -> CommandSpec:
    query = require_nonblank(sql, "sql")
    lowered = query.lstrip().lower()
    if not lowered.startswith("select "):
        raise ValueError("osquery adapter only accepts SELECT statements")
    if ";" in query.rstrip(";"):
        raise ValueError("multiple SQL statements are not allowed")
    return CommandSpec(("osqueryi", "--json", query))


def tika_extract_command(document_path: str) -> CommandSpec:
    return CommandSpec(("tika", "--text", require_safe_local_path(document_path, "document_path")))


def qpdf_check_command(pdf_path: str) -> CommandSpec:
    return CommandSpec(("qpdf", "--check", require_safe_local_path(pdf_path, "pdf_path")))


def ffprobe_json_command(media_path: str) -> CommandSpec:
    return CommandSpec(("ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", require_safe_local_path(media_path, "media_path")))


def sleuthkit_file_list_command(image_path: str) -> CommandSpec:
    return CommandSpec(("fls", "-r", "-p", require_safe_local_path(image_path, "image_path")))


def aleapp_command(extraction_dir: str, output_dir: str) -> CommandSpec:
    return CommandSpec(("aleapp", "-t", require_safe_local_path(extraction_dir, "extraction_dir"), "-o", require_safe_local_path(output_dir, "output_dir")))


def ileapp_command(extraction_dir: str, output_dir: str) -> CommandSpec:
    return CommandSpec(("ileapp", "-t", require_safe_local_path(extraction_dir, "extraction_dir"), "-o", require_safe_local_path(output_dir, "output_dir")))


def binwalk_analysis_command(firmware_path: str) -> CommandSpec:
    return CommandSpec(("binwalk", require_safe_local_path(firmware_path, "firmware_path")))


def guestfish_ro_command(disk_image: str) -> CommandSpec:
    return CommandSpec(("guestfish", "--ro", "-a", require_safe_local_path(disk_image, "disk_image"), "-i"))


def photorec_image_command(image_path: str, output_dir: str) -> CommandSpec:
    return CommandSpec(("photorec", "/log", "/d", require_safe_local_path(output_dir, "output_dir"), require_safe_local_path(image_path, "image_path")))
