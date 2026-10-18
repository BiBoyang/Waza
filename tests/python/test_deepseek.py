"""Unit tests for the read skill's DeepSeek tier.

The network call is replaced; these pin the opt-in contract (no key, nothing
sent), the request bodies, and the rendering of search and fetch responses.
"""

import io
import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "skills" / "read" / "scripts"))

import deepseek  # noqa: E402


def _spy(monkeypatch, response):
    sent = []

    def fake_call(endpoint, body, key):
        sent.append((endpoint, body, key))
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(deepseek, "call", fake_call)
    return sent


def test_missing_key_sends_nothing(monkeypatch, capsys):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    sent = _spy(monkeypatch, {"results": []})

    assert deepseek.main(["search", "mole"]) == 2
    assert sent == []
    assert "status=skip" in capsys.readouterr().err


def test_search_body_clamps_count_and_renders(monkeypatch, capsys):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    sent = _spy(monkeypatch, {"results": [{
        "title": "Mole", "url": "https://mole.fit/", "site_name": "Mole",
        "date": "2026-06-01T00:00:00+00:00", "authority": 2,
        "rerank_score": 2.4, "summary": "Native  Mac\nutility", "content": "",
    }]})

    assert deepseek.main(["search", "mole", "--count", "99"]) == 0
    assert sent == [("search", {"query": "mole", "count": 50}, "sk-test")]
    out = capsys.readouterr()
    assert "1. Mole\n   https://mole.fit/" in out.out
    assert "Mole · 2026-06-01 · authority 2 · score 2.40" in out.out
    assert "Native Mac utility" in out.out
    assert "status=ok" in out.err


def test_overlong_query_is_rejected_before_sending(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    sent = _spy(monkeypatch, {"results": []})

    assert deepseek.main(["search", "x" * 129]) == 2
    assert sent == []


def test_fetch_renders_title_and_source(monkeypatch, capsys):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    _spy(monkeypatch, {"title": "Page", "content": "# Page\n\nBody."})

    assert deepseek.main(["fetch", "https://example.com/a"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Page\n\nSource: https://example.com/a\n\n# Page")


def test_api_error_message_reaches_stderr(monkeypatch, capsys):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    body = json.dumps({"error": {"message": "Authentication Fails"}}).encode()
    err = urllib.error.HTTPError("u", 401, "x", {}, io.BytesIO(body))
    _spy(monkeypatch, err)

    assert deepseek.main(["fetch", "https://example.com"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert 'reason="Authentication Fails"' in captured.err
    assert "sk-test" not in captured.err
