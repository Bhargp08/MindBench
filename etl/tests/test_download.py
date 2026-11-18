import hashlib

import pytest

from mindbench_etl.download import (
    DRIVE_FILES_URL,
    ConfigError,
    download_new_files,
    get_config,
    list_folder_files,
)


class FakeResponse:
    def __init__(self, payload=None, content=b"", status=200):
        self._payload = payload
        self.content = content
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeDrive:
    """Stands in for google.auth.transport.requests.AuthorizedSession (a requests.Session)."""

    def __init__(self, pages, contents):
        self.pages = pages  # list of file-list payloads
        self.contents = contents  # file id -> bytes
        self.calls = []

    def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        if url == DRIVE_FILES_URL:
            token = (params or {}).get("pageToken")
            idx = 0 if token is None else int(token)
            return FakeResponse(self.pages[idx])
        file_id = url.rsplit("/", 1)[-1]
        assert (params or {}).get("alt") == "media"
        return FakeResponse(content=self.contents[file_id])


def md5(b):
    return hashlib.md5(b).hexdigest()


def file(id_, name, content, **extra):
    return {"id": id_, "name": name, "md5Checksum": md5(content), "size": str(len(content)), **extra}


A = b'[{"a": 1}]'
B = b'[{"b": 2}]'


def make_drive(files, per_page=2):
    pages = []
    for i in range(0, len(files), per_page):
        page = {"files": files[i : i + per_page]}
        if i + per_page < len(files):
            page["nextPageToken"] = str(len(pages) + 1)
        pages.append(page)
    return FakeDrive(pages, {f["id"]: {"A1": A, "B2": B}.get(f["id"], b"[]") for f in files})


def test_list_folder_files_follows_pages_and_sends_the_documented_query():
    files = [file("A1", "K7M2QX9P_session1.json", A), file("B2", "K7M2QX9P_session2.json", B), file("C3", "K7M2QX9P_session3.json", b"[]")]
    drive = make_drive(files)
    got = list_folder_files(drive, "FOLDER123")
    assert [f["name"] for f in got] == ["K7M2QX9P_session1.json", "K7M2QX9P_session2.json", "K7M2QX9P_session3.json"]
    assert len(drive.calls) == 2
    url, params = drive.calls[0]
    assert url == "https://www.googleapis.com/drive/v3/files"
    assert "'FOLDER123' in parents" in params["q"]
    assert "trashed = false" in params["q"]
    assert params["pageSize"] == 1000
    assert "md5Checksum" in params["fields"] and "nextPageToken" in params["fields"]
    assert params["supportsAllDrives"] is True
    assert params["includeItemsFromAllDrives"] is True
    assert drive.calls[1][1]["pageToken"] == "1"


def test_downloads_new_json_files_and_skips_partials_and_other_files(tmp_path):
    files = [
        file("A1", "K7M2QX9P_session1.json", A),
        file("P9", "K7M2QX9P_session2.partial.json", b"[]"),
        file("T1", "notes.txt", b"hi"),
        file("F1", "folder", b"", mimeType="application/vnd.google-apps.folder"),
    ]
    drive = make_drive(files)
    report = download_new_files(drive, "FOLDER123", tmp_path)
    assert report["downloaded"] == ["K7M2QX9P_session1.json"]
    assert report["skipped_partial"] == ["K7M2QX9P_session2.partial.json"]
    assert sorted(report["skipped_other"]) == ["folder", "notes.txt"]
    assert (tmp_path / "K7M2QX9P_session1.json").read_bytes() == A
    assert not (tmp_path / "K7M2QX9P_session2.partial.json").exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_unchanged_files_are_not_downloaded_again_but_changed_ones_are(tmp_path):
    files = [file("A1", "K7M2QX9P_session1.json", A), file("B2", "K7M2QX9P_session2.json", B)]
    drive = make_drive(files)
    download_new_files(drive, "F", tmp_path)
    downloads_first = [c for c in drive.calls if c[0] != DRIVE_FILES_URL]
    assert len(downloads_first) == 2

    drive2 = make_drive(files)
    report = download_new_files(drive2, "F", tmp_path)
    assert report["downloaded"] == []
    assert sorted(report["skipped_existing"]) == ["K7M2QX9P_session1.json", "K7M2QX9P_session2.json"]
    assert [c for c in drive2.calls if c[0] != DRIVE_FILES_URL] == []

    (tmp_path / "K7M2QX9P_session1.json").write_bytes(b"corrupted")
    drive3 = make_drive(files)
    report = download_new_files(drive3, "F", tmp_path)
    assert report["downloaded"] == ["K7M2QX9P_session1.json"]
    assert (tmp_path / "K7M2QX9P_session1.json").read_bytes() == A


def test_unsafe_file_names_never_write_outside_the_destination(tmp_path):
    dest = tmp_path / "raw"
    dest.mkdir()
    files = [file("X1", "../evil.json", A), file("X2", "sub/dir.json", A), file("X3", ".hidden.json", A), file("A1", "K7M2QX9P_session1.json", A)]
    report = download_new_files(make_drive(files), "F", dest)
    assert report["downloaded"] == ["K7M2QX9P_session1.json"]
    assert sorted(report["skipped_unsafe"]) == ["../evil.json", ".hidden.json", "sub/dir.json"]
    assert not (tmp_path / "evil.json").exists()
    assert sorted(p.name for p in dest.iterdir()) == ["K7M2QX9P_session1.json"]


class TestConfig:
    def test_reads_folder_id_and_credentials_path_from_the_environment(self, tmp_path):
        key = tmp_path / "key.json"
        key.write_text("{}")
        folder, path = get_config({"MINDBENCH_DRIVE_FOLDER_ID": "FOLDER123", "GOOGLE_APPLICATION_CREDENTIALS": str(key)})
        assert folder == "FOLDER123"
        assert path == key

    def test_missing_variables_are_named_in_the_error(self):
        with pytest.raises(ConfigError) as e:
            get_config({})
        assert "MINDBENCH_DRIVE_FOLDER_ID" in str(e.value)
        assert "GOOGLE_APPLICATION_CREDENTIALS" in str(e.value)

    def test_errors_never_echo_values_from_the_environment(self, tmp_path):
        env = {"MINDBENCH_DRIVE_FOLDER_ID": "super-secret-folder-id", "GOOGLE_APPLICATION_CREDENTIALS": str(tmp_path / "missing" / "key.json")}
        with pytest.raises(ConfigError) as e:
            get_config(env)
        assert "super-secret-folder-id" not in str(e.value)
        assert "GOOGLE_APPLICATION_CREDENTIALS" in str(e.value)

    def test_blank_values_count_as_missing(self):
        with pytest.raises(ConfigError):
            get_config({"MINDBENCH_DRIVE_FOLDER_ID": "  ", "GOOGLE_APPLICATION_CREDENTIALS": ""})
