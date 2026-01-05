"""
LEGO Library Service - Rebrickable API integration.

Provides access to official LEGO set data including:
- Set search with filters
- Set details and metadata
- Parts inventory
- Building instructions URLs
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx

from lego_architect.config import Config


# Exceptions
class LibraryServiceError(Exception):
    """Base exception for library service errors."""
    pass


class APIKeyMissingError(LibraryServiceError):
    """Raised when API key is not configured."""
    pass


class SetNotFoundError(LibraryServiceError):
    """Raised when set is not found."""
    pass


class RateLimitError(LibraryServiceError):
    """Raised when API rate limit is exceeded."""
    pass


# Data classes for API responses
@dataclass
class SetInfo:
    """Basic set information for search results."""
    set_num: str
    name: str
    year: int
    theme_id: int
    theme_name: str
    num_parts: int
    img_url: Optional[str] = None
    set_url: Optional[str] = None


@dataclass
class SetDetail:
    """Detailed set information."""
    set_num: str
    name: str
    year: int
    theme_id: int
    theme_name: str
    num_parts: int
    img_url: Optional[str] = None
    set_url: Optional[str] = None
    instructions_count: int = 0


@dataclass
class PartEntry:
    """Part entry from inventory."""
    part_num: str
    part_name: str
    color_id: int
    color_name: str
    color_rgb: str
    quantity: int
    img_url: Optional[str] = None
    is_spare: bool = False


@dataclass
class SetInventory:
    """Set parts inventory."""
    set_num: str
    parts: List[PartEntry] = field(default_factory=list)
    total_parts: int = 0
    unique_parts: int = 0


@dataclass
class ThemeInfo:
    """Theme information."""
    id: int
    name: str
    parent_id: Optional[int] = None


# Part mapping: Rebrickable part_num -> LDraw part_id
# Most common parts have the same IDs
PART_MAPPING: Dict[str, Dict[str, Any]] = {
    # Basic bricks
    "3001": {"ldraw_id": "3001", "name": "Brick 2x4", "width": 2, "length": 4, "height": 3},
    "3002": {"ldraw_id": "3002", "name": "Brick 2x3", "width": 2, "length": 3, "height": 3},
    "3003": {"ldraw_id": "3003", "name": "Brick 2x2", "width": 2, "length": 2, "height": 3},
    "3004": {"ldraw_id": "3004", "name": "Brick 1x2", "width": 1, "length": 2, "height": 3},
    "3005": {"ldraw_id": "3005", "name": "Brick 1x1", "width": 1, "length": 1, "height": 3},
    "3008": {"ldraw_id": "3008", "name": "Brick 1x8", "width": 1, "length": 8, "height": 3},
    "3009": {"ldraw_id": "3009", "name": "Brick 1x6", "width": 1, "length": 6, "height": 3},
    "3010": {"ldraw_id": "3010", "name": "Brick 1x4", "width": 1, "length": 4, "height": 3},
    "3622": {"ldraw_id": "3622", "name": "Brick 1x3", "width": 1, "length": 3, "height": 3},
    # Basic plates
    "3020": {"ldraw_id": "3020", "name": "Plate 2x4", "width": 2, "length": 4, "height": 1},
    "3021": {"ldraw_id": "3021", "name": "Plate 2x3", "width": 2, "length": 3, "height": 1},
    "3022": {"ldraw_id": "3022", "name": "Plate 2x2", "width": 2, "length": 2, "height": 1},
    "3023": {"ldraw_id": "3023", "name": "Plate 1x2", "width": 1, "length": 2, "height": 1},
    "3024": {"ldraw_id": "3024", "name": "Plate 1x1", "width": 1, "length": 1, "height": 1},
    "3029": {"ldraw_id": "3029", "name": "Plate 4x12", "width": 4, "length": 12, "height": 1},
    "3030": {"ldraw_id": "3030", "name": "Plate 4x10", "width": 4, "length": 10, "height": 1},
    "3031": {"ldraw_id": "3031", "name": "Plate 4x4", "width": 4, "length": 4, "height": 1},
    "3032": {"ldraw_id": "3032", "name": "Plate 4x6", "width": 4, "length": 6, "height": 1},
    "3033": {"ldraw_id": "3033", "name": "Plate 6x10", "width": 6, "length": 10, "height": 1},
    "3034": {"ldraw_id": "3034", "name": "Plate 2x8", "width": 2, "length": 8, "height": 1},
    "3035": {"ldraw_id": "3035", "name": "Plate 4x8", "width": 4, "length": 8, "height": 1},
    "3036": {"ldraw_id": "3036", "name": "Plate 6x8", "width": 6, "length": 8, "height": 1},
    "3460": {"ldraw_id": "3460", "name": "Plate 1x8", "width": 1, "length": 8, "height": 1},
    "3666": {"ldraw_id": "3666", "name": "Plate 1x6", "width": 1, "length": 6, "height": 1},
    "3710": {"ldraw_id": "3710", "name": "Plate 1x4", "width": 1, "length": 4, "height": 1},
    "3623": {"ldraw_id": "3623", "name": "Plate 1x3", "width": 1, "length": 3, "height": 1},
    # Tiles (plates without studs)
    "3068b": {"ldraw_id": "3068b", "name": "Tile 2x2", "width": 2, "length": 2, "height": 1},
    "3069b": {"ldraw_id": "3069b", "name": "Tile 1x2", "width": 1, "length": 2, "height": 1},
    "3070b": {"ldraw_id": "3070b", "name": "Tile 1x1", "width": 1, "length": 1, "height": 1},
    # Slopes
    "3039": {"ldraw_id": "3039", "name": "Slope 45 2x2", "width": 2, "length": 2, "height": 2},
    "3040": {"ldraw_id": "3040", "name": "Slope 45 2x1", "width": 2, "length": 1, "height": 2},
    "3298": {"ldraw_id": "3298", "name": "Slope 33 3x2", "width": 3, "length": 2, "height": 2},
    # Technic
    "3700": {"ldraw_id": "3700", "name": "Technic Brick 1x2", "width": 1, "length": 2, "height": 3},
    "3701": {"ldraw_id": "3701", "name": "Technic Brick 1x4", "width": 1, "length": 4, "height": 3},
    # Round bricks
    "3062b": {"ldraw_id": "3062b", "name": "Round Brick 1x1", "width": 1, "length": 1, "height": 3},
    "6143": {"ldraw_id": "6143", "name": "Round Brick 2x2", "width": 2, "length": 2, "height": 3},
}

# Color mapping: Rebrickable color_id -> LDraw color_id
# Most IDs are the same between systems
COLOR_MAPPING: Dict[int, int] = {
    0: 0,      # Black
    1: 1,      # Blue
    2: 2,      # Green
    3: 10,     # Dark Turquoise
    4: 4,      # Red
    5: 5,      # Dark Pink
    6: 6,      # Brown
    7: 7,      # Light Gray
    8: 8,      # Dark Gray
    9: 9,      # Light Blue
    10: 10,    # Bright Green
    11: 11,    # Light Turquoise
    12: 12,    # Salmon
    13: 13,    # Pink
    14: 14,    # Yellow
    15: 15,    # White
    17: 17,    # Light Green
    18: 18,    # Light Yellow
    19: 19,    # Tan
    20: 20,    # Light Violet
    22: 22,    # Purple
    23: 23,    # Dark Blue-Violet
    25: 25,    # Orange
    26: 26,    # Magenta
    27: 27,    # Lime
    28: 28,    # Dark Tan
    29: 29,    # Bright Pink
    36: 36,    # Trans-Red
    70: 70,    # Reddish Brown
    71: 71,    # Light Bluish Gray
    72: 72,    # Dark Bluish Gray
    73: 73,    # Medium Blue
    85: 85,    # Dark Bluish Gray
    # Add more as needed
}


def get_part_info(part_num: str) -> Optional[Dict[str, Any]]:
    """Get part info from mapping, returns None if unknown."""
    return PART_MAPPING.get(part_num)


def map_color(rebrickable_color: int) -> int:
    """Map Rebrickable color to LDraw color."""
    return COLOR_MAPPING.get(rebrickable_color, rebrickable_color)


# Simple in-memory cache
_cache: Dict[str, Tuple[Any, float]] = {}
_cache_ttl = 300  # 5 minutes


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            return value
        del _cache[key]
    return None


def cache_set(key: str, value: Any) -> None:
    """Set value in cache."""
    _cache[key] = (value, time.time())


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[datetime] = []

    async def acquire(self) -> None:
        """Wait if necessary to stay within rate limit."""
        now = datetime.now()
        # Remove requests older than 1 minute
        self.request_times = [
            t for t in self.request_times
            if now - t < timedelta(minutes=1)
        ]

        if len(self.request_times) >= self.requests_per_minute:
            # Wait until oldest request is more than 1 minute old
            oldest = self.request_times[0]
            wait_time = (oldest + timedelta(minutes=1) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.request_times.append(now)


class LegoLibraryService:
    """
    Service for querying the Rebrickable LEGO database.

    Provides methods to search sets, get details, and fetch inventories.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize library service."""
        self.api_key = api_key or Config.REBRICKABLE_API_KEY
        self.base_url = Config.REBRICKABLE_BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limiter = RateLimiter(requests_per_minute=60)

    def _check_availability(self) -> None:
        """Raise error if service not available."""
        if not self.api_key:
            raise APIKeyMissingError(
                "REBRICKABLE_API_KEY not configured. "
                "Add it to your .env file to use library features."
            )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"key {self.api_key}"},
                timeout=30.0,
            )
        return self._client

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with rate limiting."""
        self._check_availability()
        await self._rate_limiter.acquire()

        client = await self._get_client()

        try:
            response = await client.request(method, endpoint, params=params)

            if response.status_code == 404:
                raise SetNotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded. Please wait and try again.")
            elif response.status_code != 200:
                raise LibraryServiceError(
                    f"API error {response.status_code}: {response.text}"
                )

            return response.json()

        except httpx.TimeoutException:
            raise LibraryServiceError("Request timed out. Please try again.")
        except httpx.RequestError as e:
            raise LibraryServiceError(f"Request failed: {str(e)}")

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search_sets(
        self,
        search: Optional[str] = None,
        theme_id: Optional[int] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        min_parts: Optional[int] = None,
        max_parts: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SetInfo], int]:
        """
        Search LEGO sets with filters.

        Returns tuple of (results, total_count).
        """
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "ordering": "-year",  # Most recent first
        }

        if search:
            params["search"] = search
        if theme_id:
            params["theme_id"] = theme_id
        if min_year:
            params["min_year"] = min_year
        if max_year:
            params["max_year"] = max_year
        if min_parts:
            params["min_parts"] = min_parts
        if max_parts:
            params["max_parts"] = max_parts

        data = await self._request("GET", "/lego/sets/", params=params)

        sets = []
        for item in data.get("results", []):
            sets.append(SetInfo(
                set_num=item.get("set_num", ""),
                name=item.get("name", ""),
                year=item.get("year", 0),
                theme_id=item.get("theme_id", 0),
                theme_name="",  # Will be populated separately if needed
                num_parts=item.get("num_parts", 0),
                img_url=item.get("set_img_url"),
                set_url=item.get("set_url"),
            ))

        return sets, data.get("count", 0)

    async def get_set_details(self, set_num: str) -> SetDetail:
        """Get detailed information for a specific set."""
        cache_key = f"set_detail:{set_num}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        data = await self._request("GET", f"/lego/sets/{set_num}/")

        detail = SetDetail(
            set_num=data.get("set_num", ""),
            name=data.get("name", ""),
            year=data.get("year", 0),
            theme_id=data.get("theme_id", 0),
            theme_name="",
            num_parts=data.get("num_parts", 0),
            img_url=data.get("set_img_url"),
            set_url=data.get("set_url"),
        )

        cache_set(cache_key, detail)
        return detail

    async def get_set_inventory(self, set_num: str) -> SetInventory:
        """Get parts inventory for a set."""
        cache_key = f"inventory:{set_num}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # Fetch all pages of parts
        all_parts: List[PartEntry] = []
        page = 1
        total_parts = 0

        while True:
            data = await self._request(
                "GET",
                f"/lego/sets/{set_num}/parts/",
                params={"page": page, "page_size": 100},
            )

            for item in data.get("results", []):
                part_data = item.get("part", {})
                color_data = item.get("color", {})

                all_parts.append(PartEntry(
                    part_num=part_data.get("part_num", ""),
                    part_name=part_data.get("name", ""),
                    color_id=color_data.get("id", 0),
                    color_name=color_data.get("name", "Unknown"),
                    color_rgb=color_data.get("rgb", "888888"),
                    quantity=item.get("quantity", 1),
                    img_url=part_data.get("part_img_url"),
                    is_spare=item.get("is_spare", False),
                ))
                total_parts += item.get("quantity", 1)

            # Check if there are more pages
            if not data.get("next"):
                break
            page += 1

        inventory = SetInventory(
            set_num=set_num,
            parts=all_parts,
            total_parts=total_parts,
            unique_parts=len(all_parts),
        )

        cache_set(cache_key, inventory)
        return inventory

    async def get_themes(self) -> List[ThemeInfo]:
        """Get list of LEGO themes."""
        cache_key = "themes"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # Fetch all themes (paginated)
        all_themes: List[ThemeInfo] = []
        page = 1

        while True:
            data = await self._request(
                "GET",
                "/lego/themes/",
                params={"page": page, "page_size": 100},
            )

            for item in data.get("results", []):
                all_themes.append(ThemeInfo(
                    id=item.get("id", 0),
                    name=item.get("name", ""),
                    parent_id=item.get("parent_id"),
                ))

            if not data.get("next"):
                break
            page += 1

        # Sort by name
        all_themes.sort(key=lambda t: t.name)

        cache_set(cache_key, all_themes)
        return all_themes

    async def get_set_instructions(self, set_num: str) -> List[str]:
        """Get instruction PDF URLs for a set."""
        try:
            data = await self._request("GET", f"/lego/sets/{set_num}/")
            # Rebrickable doesn't directly provide instruction URLs in the API
            # The set_url links to a page that may have instructions
            return [data.get("set_url", "")] if data.get("set_url") else []
        except SetNotFoundError:
            return []
