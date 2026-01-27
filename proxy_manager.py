"""Proxy manager for automatic failover between multiple proxies and direct connection."""

import asyncio
import logging

from aiohttp import TCPConnector
from aiohttp_socks import ProxyConnector, ProxyError

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy connections with automatic failover."""

    def __init__(
        self,
        proxy_urls: list[str] | None = None,
        test_url: str = "https://api.telegram.org",
        test_timeout: float = 10.0,
        error_threshold: int = 3,
    ):
        """
        Initialize proxy manager.

        Args:
            proxy_urls: List of proxy URLs (e.g., "socks5://proxy.example.com:1080")
            test_url: URL to test proxy connectivity
            test_timeout: Timeout for proxy test in seconds
            error_threshold: Number of consecutive errors before switching
        """
        self.proxy_urls = proxy_urls or []
        self.test_url = test_url
        self.test_timeout = test_timeout
        self.error_threshold = error_threshold

        # Current proxy (None means direct connection)
        self.current_proxy: str | None = None
        # Error counter for current connection
        self.error_count = 0
        # Current connector
        self.current_connector: TCPConnector | None = None
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def get_connector(self) -> TCPConnector:
        """
        Get current connector, creating one if needed.

        Returns:
            TCPConnector or ProxyConnector instance
        """
        async with self._lock:
            if self.current_connector is None or self.current_connector.closed:
                if self.current_proxy:
                    logger.info(f"Creating proxy connector for: {self.current_proxy}")
                    self.current_connector = ProxyConnector.from_url(
                        self.current_proxy,
                        ttl_dns_cache=300,
                        limit=0,
                    )
                else:
                    logger.info("Creating direct connector (no proxy)")
                    self.current_connector = TCPConnector(
                        ttl_dns_cache=300,
                        limit=0,
                    )
        return self.current_connector

    async def report_success(self) -> None:
        """Report successful connection - reset error counter."""
        async with self._lock:
            self.error_count = 0

    async def report_error(self, error: Exception) -> None:
        """
        Report connection error and potentially switch proxy.

        Args:
            error: The exception that occurred
        """
        async with self._lock:
            self.error_count += 1
            logger.warning(
                f"Connection error #{self.error_count}/{self.error_threshold}: {error}"
            )

            if self.error_count >= self.error_threshold:
                logger.warning(
                    f"Error threshold reached, switching from "
                    f"{'proxy' if self.current_proxy else 'direct connection'}"
                )
                await self._switch_connection()

    async def _switch_connection(self) -> None:
        """Switch to next available connection in cycle: direct -> proxy1 -> proxy2 -> ... -> direct."""
        # Close current connector
        if self.current_connector and not self.current_connector.closed:
            await self.current_connector.close()

        self.error_count = 0

        # Determine next connection mode
        if self.current_proxy is None:
            # Currently on direct connection, try first proxy
            if self.proxy_urls:
                self.current_proxy = self.proxy_urls[0]
                logger.info(
                    f"Switching from direct connection to proxy: {self.current_proxy}"
                )
            else:
                logger.info("No proxies available, staying on direct connection")
        else:
            # Currently on a proxy
            current_index = self.proxy_urls.index(self.current_proxy)

            if current_index < len(self.proxy_urls) - 1:
                # Try next proxy
                self.current_proxy = self.proxy_urls[current_index + 1]
                logger.info(f"Switching to next proxy: {self.current_proxy}")
            else:
                # No more proxies, return to direct connection
                self.current_proxy = None
                logger.info("All proxies exhausted, returning to direct connection")

    async def test_proxy(self, proxy_url: str) -> bool:
        """
        Test if a proxy is working.

        Args:
            proxy_url: Proxy URL to test

        Returns:
            True if proxy works, False otherwise
        """
        try:
            connector = ProxyConnector.from_url(proxy_url, limit=1)
            async with connector:
                async with asyncio.timeout(self.test_timeout):
                    async with connector.get(self.test_url) as response:  # type: ignore[attr-defined]
                        if response.status < 500:
                            logger.info(f"Proxy {proxy_url} is working")
                            return True
        except (ProxyError, TimeoutError, Exception) as e:
            logger.warning(f"Proxy {proxy_url} test failed: {e}")
            return False
        return False

    async def find_working_proxy(self) -> str | None:
        """
        Find first working proxy from the list (manual testing only).

        Returns:
            Working proxy URL or None if none work
        """
        for proxy_url in self.proxy_urls:
            if await self.test_proxy(proxy_url):
                return proxy_url
        return None

    async def initialize(self) -> None:
        """Initialize proxy manager - starts with direct connection."""
        async with self._lock:
            self.current_proxy = None
            if self.proxy_urls:
                logger.info(
                    f"Initialized with direct connection. "
                    f"Proxies available for failover: {len(self.proxy_urls)}"
                )
            else:
                logger.info("No proxies configured, using direct connection")

    async def shutdown(self) -> None:
        """Clean up resources."""
        async with self._lock:
            if self.current_connector and not self.current_connector.closed:
                await self.current_connector.close()
                self.current_connector = None
