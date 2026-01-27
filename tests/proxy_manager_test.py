"""Tests for proxy_manager module."""

import pytest

from proxy_manager import ProxyManager


@pytest.mark.asyncio
async def test_starts_with_direct_connection():
    """Test that manager starts with direct connection."""
    manager = ProxyManager(
        proxy_urls=[
            "socks5://proxy1.example.com:1080",
            "socks5://proxy2.example.com:1080",
        ]
    )

    await manager.initialize()

    assert manager.current_proxy is None
    assert manager.error_count == 0


@pytest.mark.asyncio
async def test_switches_to_first_proxy_on_errors():
    """Test that manager switches to first proxy after reaching error threshold."""
    manager = ProxyManager(
        proxy_urls=[
            "socks5://proxy1.example.com:1080",
            "socks5://proxy2.example.com:1080",
        ],
        error_threshold=2,
    )

    await manager.initialize()

    # Report errors until threshold
    await manager.report_error(Exception("Connection error 1"))
    await manager.report_error(Exception("Connection error 2"))

    assert manager.current_proxy == "socks5://proxy1.example.com:1080"
    assert manager.error_count == 0


@pytest.mark.asyncio
async def test_switches_through_all_proxies_to_direct():
    """Test that manager cycles through all proxies and returns to direct connection."""
    manager = ProxyManager(
        proxy_urls=[
            "socks5://proxy1.example.com:1080",
            "socks5://proxy2.example.com:1080",
        ],
        error_threshold=1,
    )

    await manager.initialize()

    # Direct -> Proxy1
    await manager.report_error(Exception("Direct connection failed"))
    assert manager.current_proxy == "socks5://proxy1.example.com:1080"

    # Proxy1 -> Proxy2
    await manager.report_error(Exception("Proxy1 failed"))
    assert manager.current_proxy == "socks5://proxy2.example.com:1080"

    # Proxy2 -> Direct
    await manager.report_error(Exception("Proxy2 failed"))
    assert manager.current_proxy is None


@pytest.mark.asyncio
async def test_infinite_cycling_through_proxies():
    """Test that manager infinitely cycles through connections."""
    manager = ProxyManager(
        proxy_urls=["socks5://proxy1.example.com:1080"],
        error_threshold=1,
    )

    await manager.initialize()

    # Direct -> Proxy1
    await manager.report_error(Exception("Direct failed"))
    assert manager.current_proxy == "socks5://proxy1.example.com:1080"

    # Proxy1 -> Direct
    await manager.report_error(Exception("Proxy1 failed"))
    assert manager.current_proxy is None

    # Direct -> Proxy1 again
    await manager.report_error(Exception("Direct failed"))
    assert manager.current_proxy == "socks5://proxy1.example.com:1080"

    # Proxy1 -> Direct again
    await manager.report_error(Exception("Proxy1 failed"))
    assert manager.current_proxy is None


@pytest.mark.asyncio
async def test_resets_error_count_on_success():
    """Test that error count resets on successful connection."""
    manager = ProxyManager(
        proxy_urls=["socks5://proxy1.example.com:1080"],
        error_threshold=3,
    )

    await manager.initialize()

    await manager.report_error(Exception("Error 1"))
    assert manager.error_count == 1

    await manager.report_success()
    assert manager.error_count == 0

    # Should not switch after threshold because errors were reset
    await manager.report_error(Exception("Error 2"))
    await manager.report_error(Exception("Error 3"))
    assert manager.current_proxy is None


@pytest.mark.asyncio
async def test_does_not_switch_before_threshold():
    """Test that manager doesn't switch before error threshold is reached."""
    manager = ProxyManager(
        proxy_urls=["socks5://proxy1.example.com:1080"],
        error_threshold=5,
    )

    await manager.initialize()

    # Report 4 errors (threshold is 5)
    for i in range(4):
        await manager.report_error(Exception(f"Error {i + 1}"))

    assert manager.current_proxy is None
    assert manager.error_count == 4


@pytest.mark.asyncio
async def test_creates_direct_connector():
    """Test that get_connector creates direct connector when no proxy is set."""
    manager = ProxyManager(proxy_urls=["socks5://proxy1.example.com:1080"])
    await manager.initialize()

    connector = await manager.get_connector()

    assert connector is not None
    assert not connector.closed


@pytest.mark.asyncio
async def test_creates_proxy_connector():
    """Test that get_connector creates proxy connector when proxy is set."""
    manager = ProxyManager(
        proxy_urls=["socks5://proxy1.example.com:1080"],
        error_threshold=1,
    )
    await manager.initialize()

    # Switch to proxy
    await manager.report_error(Exception("Direct failed"))

    connector = await manager.get_connector()

    assert connector is not None
    assert not connector.closed


@pytest.mark.asyncio
async def test_no_proxies_starts_with_direct():
    """Test that manager works correctly when no proxies are configured."""
    manager = ProxyManager(proxy_urls=[], error_threshold=2)
    await manager.initialize()

    assert manager.current_proxy is None

    # Errors should not cause switching since there are no proxies
    await manager.report_error(Exception("Error 1"))
    await manager.report_error(Exception("Error 2"))

    assert manager.current_proxy is None


@pytest.mark.asyncio
async def test_shutdown_closes_connector():
    """Test that shutdown properly closes connector."""
    manager = ProxyManager(proxy_urls=["socks5://proxy1.example.com:1080"])
    await manager.initialize()

    connector = await manager.get_connector()
    assert not connector.closed

    await manager.shutdown()

    assert manager.current_connector is None


@pytest.mark.asyncio
async def test_get_connector_reuses_existing():
    """Test that get_connector reuses existing connector."""
    manager = ProxyManager(proxy_urls=["socks5://proxy1.example.com:1080"])
    await manager.initialize()

    connector1 = await manager.get_connector()
    connector2 = await manager.get_connector()

    assert connector1 is connector2
