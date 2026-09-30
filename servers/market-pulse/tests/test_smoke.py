"""Smoke tests for market-pulse (no network access required)."""

from market_pulse import server


def test_tools_are_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"get_quote", "get_fx_rate", "convert_currency"}


def test_stooq_symbol_normalization():
    assert server._stooq_symbol("AAPL") == "aapl.us"
    assert server._stooq_symbol("^SPX") == "^spx"
    assert server._stooq_symbol("BTCUSD") == "btcusd"
    assert server._stooq_symbol("7203.JP") == "7203.jp"


def test_get_quote_rejects_empty_symbol():
    assert "Error" in server.get_quote("  ")


def test_fx_rejects_bad_currency_codes():
    assert "Error" in server.get_fx_rate("US", "CNY")
    assert "Error" in server.convert_currency(10, "USD", "C")


def test_fx_same_currency_shortcut():
    assert "1.0000" in server.get_fx_rate("USD", "USD")


def _fail_fetch(*args, **kwargs):
    raise AssertionError("_fetch_fx must not be called on a shortcut path")


def test_convert_currency_same_currency_skips_api(monkeypatch):
    monkeypatch.setattr(server, "_fetch_fx", _fail_fetch)
    out = server.convert_currency(250, "usd", "USD")
    assert "250.00 USD = 250.00 USD" in out
    assert "1.0000" in out


def test_convert_currency_zero_amount_skips_api(monkeypatch):
    monkeypatch.setattr(server, "_fetch_fx", _fail_fetch)
    out = server.convert_currency(0, "USD", "CNY")
    assert "0.00 USD = 0.00 CNY" in out


def test_convert_currency_normal_path_still_uses_api(monkeypatch):
    calls = []

    def fake_fetch(amount, base, target):
        calls.append((amount, base, target))
        return {"rates": {target: amount * 7.2}, "date": "2026-09-30"}

    monkeypatch.setattr(server, "_fetch_fx", fake_fetch)
    out = server.convert_currency(10, "USD", "CNY")
    assert calls == [(10, "USD", "CNY")]
    assert "10.00 USD = 72.00 CNY" in out
    assert "7.2000" in out


SAMPLE_CSV = (
    "Symbol,Date,Time,Open,High,Low,Close,Volume\n"
    "AAPL.US,2026-09-30,22:00:19,271.20,276.32,269.84,272.97,49213432\n"
)


class _FakeResponse:
    text = SAMPLE_CSV

    def raise_for_status(self):
        pass


class _FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, params=None):
        return _FakeResponse()


def test_get_quote_parses_stooq_csv(monkeypatch):
    monkeypatch.setattr(server.httpx, "Client", _FakeClient)
    out = server.get_quote("AAPL")
    assert "Close: 272.97" in out
    assert "+1.77 (+0.65%)" in out
    assert "49,213,432" in out
