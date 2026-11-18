"""Download session files from the Google Drive folder DataPipe writes to. Runs locally; credentials come from
environment variables and are never printed or stored. Drive API v3: files.list and files.get?alt=media
(read-only scope)."""
import hashlib
import os
from pathlib import Path

DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DRIVE_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
FOLDER_ENV = "MINDBENCH_DRIVE_FOLDER_ID"
CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"
FOLDER_MIME = "application/vnd.google-apps.folder"


class ConfigError(RuntimeError):
    """Missing or unusable configuration. Messages name variables, never their values."""


def get_config(env=None):
    """Return (folder_id, service-account key path) from the environment."""
    env = os.environ if env is None else env
    folder = (env.get(FOLDER_ENV) or "").strip()
    cred = (env.get(CREDENTIALS_ENV) or "").strip()
    missing = [name for name, value in ((FOLDER_ENV, folder), (CREDENTIALS_ENV, cred)) if not value]
    if missing:
        raise ConfigError(f"Set the environment variable(s): {', '.join(missing)}")
    if "'" in folder:
        raise ConfigError(f"{FOLDER_ENV} must be a plain Drive folder ID")
    path = Path(cred)
    if not path.is_file():
        raise ConfigError(f"{CREDENTIALS_ENV} does not point to an existing file")
    return folder, path


def make_session(credentials_path):
    """Authorized requests session for the Drive API (read-only service-account credentials)."""
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_file(str(credentials_path), scopes=[DRIVE_SCOPE])
    return AuthorizedSession(creds)


def list_folder_files(session, folder_id):
    """All non-trashed files directly inside a Drive folder (follows nextPageToken)."""
    if "'" in folder_id:
        raise ConfigError("Folder ID must not contain quotes")
    params = {
        "q": f"'{folder_id}' in parents and trashed = false",
        "pageSize": 1000,
        "fields": "nextPageToken, files(id, name, mimeType, md5Checksum, size, modifiedTime)",
        "supportsAllDrives": True,
        "includeItemsFromAllDrives": True,
    }
    files = []
    while True:
        resp = session.get(DRIVE_FILES_URL, params=params, timeout=60)
        resp.raise_for_status()
        payload = resp.json()
        files.extend(payload.get("files", []))
        token = payload.get("nextPageToken")
        if not token:
            return files
        params = {**params, "pageToken": token}


def _md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def _safe_name(name):
    return bool(name) and name == Path(name).name and "\\" not in name and not name.startswith(".")


def download_new_files(session, folder_id, dest):
    """Download session `.json` files that are new or changed (by MD5) into `dest`.

    Skips folders and non-JSON files, `.partial.json` files (abandoned sessions), and unsafe names that could
    write outside `dest`. Files are written atomically.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    report = {"downloaded": [], "skipped_existing": [], "skipped_partial": [], "skipped_other": [], "skipped_unsafe": []}
    for f in list_folder_files(session, folder_id):
        name = f.get("name", "")
        if f.get("mimeType") == FOLDER_MIME or not name.endswith(".json"):
            report["skipped_other"].append(name)
        elif not _safe_name(name):
            report["skipped_unsafe"].append(name)
        elif name.endswith(".partial.json"):
            report["skipped_partial"].append(name)
        else:
            target = dest / name
            remote_md5 = f.get("md5Checksum")
            if target.exists() and remote_md5 and _md5(target) == remote_md5:
                report["skipped_existing"].append(name)
                continue
            resp = session.get(f"{DRIVE_FILES_URL}/{f['id']}", params={"alt": "media", "supportsAllDrives": True}, timeout=120)
            resp.raise_for_status()
            content = resp.content
            if remote_md5 and hashlib.md5(content).hexdigest() != remote_md5:
                raise OSError(f"Checksum mismatch downloading {name}")
            tmp = dest / f".{name}.tmp"
            tmp.write_bytes(content)
            os.replace(tmp, target)
            report["downloaded"].append(name)
    return report
