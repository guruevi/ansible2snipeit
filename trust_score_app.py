#!/usr/bin/env python3
"""
Device Trust Score web app.
Looks up the visitor's IP in Medigate/xDOME and returns a trust score
based on which security integrations are associated with that device.
"""
import logging
import re
import smtplib
from configparser import RawConfigParser, NoSectionError, NoOptionError
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, request, render_template, jsonify, abort
from medigate_api import DevicesApi, Configuration, ApiClient
from medigate_api.models import GetDevicesParameters
from medigate_api.rest import ApiException

CONFIG = RawConfigParser()
CONFIG.read("settings.conf")

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

medigate_apikey = CONFIG.get('medigate', 'apikey')
medigate_apiurl = CONFIG.get('medigate', 'url')


def _cfg(section, key, fallback):
    try:
        return CONFIG.get(section, key)
    except (NoSectionError, NoOptionError):
        return fallback


SMTP_HOST = _cfg('mail', 'smtp_host', 'localhost')
SMTP_PORT = int(_cfg('mail', 'smtp_port', '25'))
MAIL_FROM = _cfg('mail', 'from_address', 'noreply@rochester.edu')
MAIL_TO   = _cfg('mail', 'to_address',   'researchsupport@rochester.edu')

LOOKUP_FIELDS = [
    "device_name",
    "domains",
    "endpoint_security_names",
    "ip_list",
    "management_services",
    "manufacturer",
    "model",
    "os_name",
    "os_version",
    "serial_number",
    "site_name",
    "infected",
    "edr_last_scan_time",
    "last_scan_time",
    "os_eol_date",
    "risk_score_points",
    "collection_interfaces",
]


# ── Datetime helpers ──────────────────────────────────────────────────────────

def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _days_since(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    return (datetime.now(timezone.utc) - dt).days


# ── Detection helpers ─────────────────────────────────────────────────────────
# Signature: (device: dict, ctx: dict) -> bool
# ctx is a pre-lowercased view of the common list fields.

def _ctx(device: dict) -> dict:
    return {
        "mgmt":       [s.lower() for s in (device.get("management_services")     or [])],
        "edr":        [s.lower() for s in (device.get("endpoint_security_names") or [])],
        "domains":    [d.lower() for d in (device.get("domains")                 or [])],
        "interfaces": [i.lower() for i in (device.get("collection_interfaces")   or [])],
    }

def _detect_ad(device, ctx):
    return any(d in ("ur.rochester.edu", "urmc-sh.rochester.edu") for d in ctx["domains"])

def _detect_crowdstrike(device, ctx):
    return any("crowdstrike falcon" in e for e in ctx["edr"])

def _detect_tenable(device, ctx):
    in_inventory = (
        any("tenable" in i for i in ctx["interfaces"])
        or any("tenable" in s for s in ctx["mgmt"] + ctx["edr"])
    )
    if in_inventory:
        return True
    days = _days_since(_parse_dt(device.get("last_scan_time")))
    return days is not None and days <= 90

def _detect_mdm(device, ctx):
    return any(
        kw in s for s in ctx["mgmt"]
        for kw in ("mdm", "jamf", "intune")
    ) or any(s == 'mdop mbam' for s in ctx["edr"])

def _detect_infected(device, ctx):
    return bool(device.get("infected"))

def _detect_eol(device, ctx):
    eol_dt = _parse_dt(device.get("os_eol_date"))
    return bool(eol_dt and eol_dt < datetime.now(timezone.utc))

def _describe_eol(device):
    eol_dt = _parse_dt(device.get("os_eol_date"))
    return (
        f"This OS reached end-of-life on {eol_dt.strftime('%B %d, %Y')} "
        "and no longer receives security patches."
    )


# ── Unified source + penalty registry ────────────────────────────────────────
# Sources  (points > 0): contribute positive points to the trust score.
#   Optional stale_* keys enable partial scoring when a scan is overdue.
# Penalties (points < 0): deduct from the score when their condition is met.
#   description may be a callable(device) -> str for dynamic text.

DATA_SOURCES = {
    "Active Directory": {
        "points":  25,
        "detect":  _detect_ad,
        "description": "Your device is authenticating to Active Directory and your identity has been established.",
        "how_to_improve": (
            "Join this device to the University domain. Contact the IT Help Desk "
            "to request domain enrollment for your device."
        ),
    },
    "CrowdStrike EDR": {
        "points":        25,
        "points_stale":  12,
        "stale_field":   "edr_last_scan_time",
        "stale_days":    7,
        "stale_warning": "Last scan was {days} ago — agent may be unhealthy.",
        "detect":  _detect_crowdstrike,
        "description": "CrowdStrike Falcon endpoint detection and response agent is installed and scanning.",
        "how_to_improve": (
            "Install the CrowdStrike Falcon sensor. Submit a request via the IT portal "
            "or contact your departmental IT support to get the installer."
        ),
    },
    "Tenable": {
        "points":        25,
        "points_stale":  12,
        "stale_field":   "last_scan_time",
        "stale_days":    90,
        "stale_warning": "Last scan was {days} ago — device may be out of scan range.",
        "detect":  _detect_tenable,
        "description": "Your device is enrolled in the Tenable vulnerability management program.",
        "how_to_improve": (
            "Ensure your device is reachable by the Tenable scanner on the UR network. "
            "Contact the Information Security Office to have your device added to scan scope."
        ),
    },
    "SCCM / JAMF": {
        "points": 25,
        "detect": _detect_mdm,
        "description": "Your device is managed by SCCM (Windows) or JAMF (macOS/iOS).",
        "how_to_improve": (
            "Enroll your device in the University endpoint management platform. "
            "Windows users: contact the Help Desk for SCCM enrollment. "
            "Mac users: contact the Help Desk for JAMF enrollment."
        ),
    },
    "Device Infected": {
        "points": -100,
        "detect": _detect_infected,
        "description": "This device has been flagged as infected. Immediate remediation is required.",
        "how_to_improve": (
            "Contact the Information Security Office immediately. "
            "Do not use this device on the University network until it has been cleared."
        ),
    },
    "End-of-Life Operating System": {
        "points": -10,
        "detect": _detect_eol,
        "description": _describe_eol,   # callable(device) -> str
        "how_to_improve": (
            "Upgrade to a supported operating system version. "
            "Contact the Help Desk for assistance."
        ),
    },
}

CATEGORIES = [
    {
        "number": 1, "name": "Fully Managed Device", "min_score": 75,
        "color": "#2e7d32", "badge": "✔ Category 1",
        "summary": (
            "Your device meets all security requirements. "
            "You have full access to University network resources."
        ),
    },
    {
        "number": 2, "name": "Limited Access \u2013 Full Internal Resources", "min_score": 50,
        "color": "#f57f17", "badge": "\u26a0 Category 2",
        "summary": (
            "Your device meets most requirements. "
            "You have full access to internal resources but some restrictions apply."
        ),
    },
    {
        "number": 3, "name": "Limited Access \u2013 Basic Access Only", "min_score": 25,
        "color": "#e65100", "badge": "\u26a0 Category 3",
        "summary": (
            "Your device is missing several security integrations. "
            "Access is restricted to basic internal services only."
        ),
    },
    {
        "number": 4, "name": "Fully Isolated", "min_score": 0,
        "color": "#b71c1c", "badge": "\u2716 Category 4",
        "summary": (
            "Your device is not recognised by University security systems. "
            "Network access is fully restricted."
        ),
    },
]

app = Flask(__name__)


def get_client_ip() -> str:
    override = request.args.get("ip")
    if override:
        # Validate IP address format (IPv4 or IPv6)
        if not re.match(r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", override.strip()):
            abort(400, "Invalid IP address format")
        return override.strip()
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.remote_addr


def lookup_device(ip: str) -> dict | None:
    mg_api = DevicesApi(ApiClient(Configuration(access_token=medigate_apikey)))
    parameters = GetDevicesParameters.from_dict({
        "filter_by": {
            "operation": "and",
            "operands": [
                {"field": "ip_list",  "operation": "in", "value": [ip]},
                {"field": "retired",  "operation": "in", "value": [False]},
            ],
        },
        "offset": 0,
        "limit": 1,
        "fields": LOOKUP_FIELDS,
        "include_count": True,
    })
    try:
        response = mg_api.get_devices(parameters)
    except ApiException as exc:
        log.error("Medigate API error for IP %s: %s", ip, exc)
        return None
    if not response.devices:
        return None
    return response.devices[0]


def detect_data_sources(device: dict) -> tuple[list[dict], list[dict]]:
    """Iterate DATA_SOURCES and return (sources, penalties) based on device state."""
    ctx = _ctx(device)
    sources: list[dict] = []
    penalties: list[dict] = []

    for name, cfg in DATA_SOURCES.items():
        present = cfg["detect"](device, ctx)
        pts = cfg["points"]

        if pts > 0:
            # Source entry
            if not present:
                earned, warning = 0, None
            elif "stale_field" in cfg:
                days = _days_since(_parse_dt(device.get(cfg["stale_field"])))
                if days is not None and days > cfg["stale_days"]:
                    days_str = f"{days} day{'s' if days != 1 else ''}"
                    earned  = cfg["points_stale"]
                    warning = cfg["stale_warning"].format(days=days_str)
                else:
                    earned, warning = pts, None
            else:
                earned, warning = pts, None

            sources.append({
                "name":           name,
                "status":         "full" if earned >= pts else ("partial" if earned > 0 else "absent"),
                "points_earned":  earned,
                "points_max":     pts,
                "description":    cfg["description"],
                "warning":        warning,
                "how_to_improve": cfg["how_to_improve"],
            })

        elif present:
            # Penalty — only emit when condition is met
            desc = cfg["description"](device) if callable(cfg["description"]) else cfg["description"]
            penalties.append({
                "name":           name,
                "points":         pts,
                "description":    desc,
                "how_to_improve": cfg["how_to_improve"],
            })

    return sources, penalties


def calculate_score(sources: list[dict], penalties: list[dict]) -> int:
    base       = sum(s["points_earned"] for s in sources)
    deductions = sum(p["points"] for p in penalties)
    return max(0, base + deductions)


def get_category(score: int) -> dict:
    for cat in CATEGORIES:
        if score >= cat["min_score"]:
            return cat
    return CATEGORIES[-1]


def send_help_email(
    requester_name: str,
    requester_email: str,
    message: str,
    client_ip: str,
    device: dict | None,
    sources: list[dict],
    penalties: list[dict],
    score: int,
    category: dict,
) -> None:
    subject = f"Device Trust Score Help Request \u2013 {requester_name or requester_email or client_ip}"
    msg = MIMEMultipart("alternative")
    msg["Subject"]  = subject
    msg["From"]     = MAIL_FROM
    msg["To"]       = MAIL_TO
    if requester_email:
        msg["Reply-To"] = requester_email

    lines = [
        "=== Help Request ===",
        f"From    : {requester_name or '(not provided)'}",
        f"Email   : {requester_email or '(not provided)'}",
        "",
        "Message:",
        message or "(no message provided)",
        "",
        "=== Device Details ===",
        f"IP Address     : {client_ip}",
    ]
    if device:
        if device.get("device_name"):    lines.append(f"Hostname       : {device['device_name']}")
        if device.get("serial_number"):  lines.append(f"Serial No.     : {device['serial_number']}")
        os_str = " ".join(filter(None, [device.get("os_name"), device.get("os_version")]))
        if os_str:                       lines.append(f"OS             : {os_str}")
        hw_str = " ".join(filter(None, [device.get("manufacturer"), device.get("model")]))
        if hw_str:                       lines.append(f"Hardware       : {hw_str}")
        if device.get("site_name"):      lines.append(f"Location       : {device['site_name']}")
        mgmt = device.get("management_services") or []
        if mgmt:   lines.append(f"Management     : {', '.join(mgmt)}")
        edr = device.get("endpoint_security_names") or []
        if edr:    lines.append(f"EDR            : {', '.join(edr)}")
        ifaces = device.get("collection_interfaces") or []
        if ifaces: lines.append(f"Interfaces     : {', '.join(ifaces)}")
        if device.get("infected"):           lines.append("Infected       : YES")
        if device.get("os_eol_date"):        lines.append(f"OS EOL Date    : {device['os_eol_date']}")
        if device.get("edr_last_scan_time"): lines.append(f"EDR Last Scan  : {device['edr_last_scan_time']}")
        if device.get("last_scan_time"):     lines.append(f"Vuln Last Scan : {device['last_scan_time']}")

    lines += [
        "",
        "=== Trust Score ===",
        f"Score    : {score} / 100",
        f"Category : {category['name']}",
        "",
        "Integrations:",
    ]
    for s in sources:
        tick = {"full": "OK", "partial": "~~", "absent": "NO"}[s["status"]]
        warn = f"  [{s['warning']}]" if s.get("warning") else ""
        lines.append(f"  [{tick}] {s['name']}: {s['points_earned']}/{s['points_max']} pts{warn}")

    if penalties:
        lines.append("")
        lines.append("Penalties:")
        for p in penalties:
            lines.append(f"  [!!] {p['name']}: {p['points']} pts")

    missing = [s["name"] for s in sources if s["status"] == "absent"]
    if missing:
        lines += ["", f"Missing integrations: {', '.join(missing)}"]

    msg.attach(MIMEText("\n".join(lines), "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
        smtp.sendmail(MAIL_FROM, [MAIL_TO], msg.as_string())
    log.info("Help email sent for %s to %s", client_ip, MAIL_TO)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/score")
def api_score():
    client_ip = get_client_ip()
    log.info("Trust score request from %s", client_ip)

    device = lookup_device(client_ip)
    if device is None:
        return jsonify({"found": False, "client_ip": client_ip})

    log.debug("Device: %s", device)

    sources, penalties = detect_data_sources(device)
    score    = calculate_score(sources, penalties)
    category = get_category(score)

    return jsonify({
        "found":         True,
        "client_ip":     client_ip,
        "device_name":   device.get("device_name", ""),
        "serial_number": device.get("serial_number", ""),
        "os_name":       device.get("os_name", ""),
        "os_version":    device.get("os_version", ""),
        "manufacturer":  device.get("manufacturer", ""),
        "model":         device.get("model", ""),
        "site_name":     device.get("site_name", ""),
        "score":         score,
        "category":      category,
        "sources":       sources,
        "penalties":     penalties,
    })


@app.route("/api/help", methods=["POST"])
def api_help():
    data            = request.get_json(silent=True) or {}
    requester_name  = (data.get("name")      or "").strip()
    requester_email = (data.get("email")     or "").strip()
    message         = (data.get("message")   or "").strip()
    client_ip       = (data.get("client_ip") or "").strip() or get_client_ip()

    device = lookup_device(client_ip)
    if device:
        sources, penalties = detect_data_sources(device)
        score    = calculate_score(sources, penalties)
        category = get_category(score)
    else:
        sources, penalties, score, category = [], [], 0, get_category(0)

    try:
        send_help_email(
            requester_name, requester_email, message,
            client_ip, device, sources, penalties, score, category,
        )
    except Exception as exc:
        log.error("Failed to send help email: %s", exc)
        return jsonify({"ok": False, "error": "Failed to send email. Please try again later."}), 500

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
