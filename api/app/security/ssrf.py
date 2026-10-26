import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx


class SSRFBlockedError(Exception):
    """Raised when a URL is blocked due to private IP targeting, redirect abuse, or size limits."""
    pass


def validate_url_target(url: str) -> None:
    """
    Validate that a URL does not target localhost, private IPs, link-local addresses,
    cloud metadata endpoints (e.g. 169.254.169.254), or non-HTTP schemes.
    """
    parsed = urlparse(url)

    # 1. Scheme guard
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFBlockedError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError("URL is missing a valid hostname.")

    hostname_lower = hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
        raise SSRFBlockedError(f"Access to loopback or internal hostname '{hostname}' is blocked.")

    # 2. DNS resolution check for all IP families
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFBlockedError(f"Could not resolve hostname '{hostname}': {str(e)}") from e

    validated_ips = []
    for item in addr_info:
        sockaddr = item[4]
        ip_str = sockaddr[0]

        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFBlockedError(f"Invalid IP address format: '{ip_str}'")

        # 3. Check for private, loopback, link-local (cloud metadata 169.254.169.254), and reserved IPs
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise SSRFBlockedError(f"Target address '{ip}' is in a private, link-local, or restricted network range.")

        # Explicit safeguard for AWS / GCP / Azure link-local metadata IP
        if ip_str == "169.254.169.254":
            raise SSRFBlockedError("Access to cloud metadata service is strictly blocked.")

        validated_ips.append(ip_str)

    return validated_ips[0] if validated_ips else ""


async def safe_fetch_url(
    url: str,
    max_size_bytes: int = 2 * 1024 * 1024,  # 2 MB cap per plan §3.0
    max_redirects: int = 5,
    timeout_seconds: float = 8.0,
) -> bytes:
    """
    Safely fetch a URL with SSRF protection:
    - Validates target IP before opening connection
    - Re-validates target IP on every HTTP redirect
    - Enforces strict 2 MB payload cap
    """
    current_url = url
    headers = {
        "User-Agent": "Allcited-Crawler/1.0 (+https://allcited.org; document indexing)",
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
    }

    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
        for _ in range(max_redirects + 1):
            validate_url_target(current_url)

            req_headers = dict(headers)
            parsed = urlparse(current_url)
            if parsed.hostname and not parsed.hostname.replace(".", "").isdigit():
                req_headers["Host"] = parsed.netloc

            try:
                response = await client.get(current_url, headers=req_headers)
            except Exception as e:
                raise SSRFBlockedError(f"Failed to fetch URL: {str(e)}") from e

            # Handle redirects securely with re-validation
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    raise SSRFBlockedError("Redirect missing Location header.")
                next_url = urljoin(current_url, location)
                validate_url_target(next_url)
                current_url = next_url
                continue

            if response.status_code != 200:
                raise SSRFBlockedError(f"HTTP fetch returned non-200 status code: {response.status_code}")

            # Enforce 2 MB size limit via Content-Length if present
            cl_header = response.headers.get("content-length")
            if cl_header and cl_header.isdigit():
                if int(cl_header) > max_size_bytes:
                    raise SSRFBlockedError(f"Resource size ({cl_header} bytes) exceeds 2 MB cap.")

            # Read content stream enforcing byte limit
            content_bytes = response.content
            if len(content_bytes) > max_size_bytes:
                raise SSRFBlockedError(f"Downloaded content ({len(content_bytes)} bytes) exceeds 2 MB cap.")

            return content_bytes

        raise SSRFBlockedError(f"Exceeded maximum redirects ({max_redirects}).")
