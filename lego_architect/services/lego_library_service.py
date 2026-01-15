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
# Expanded mapping with 200+ common parts and fallback inference
PART_MAPPING: Dict[str, Dict[str, Any]] = {
    # Basic bricks
    "3001": {"ldraw_id": "3001", "name": "Brick 2x4", "width": 2, "length": 4, "height": 3, "category": "brick"},
    "3002": {"ldraw_id": "3002", "name": "Brick 2x3", "width": 2, "length": 3, "height": 3, "category": "brick"},
    "3003": {"ldraw_id": "3003", "name": "Brick 2x2", "width": 2, "length": 2, "height": 3, "category": "brick"},
    "3004": {"ldraw_id": "3004", "name": "Brick 1x2", "width": 1, "length": 2, "height": 3, "category": "brick"},
    "3005": {"ldraw_id": "3005", "name": "Brick 1x1", "width": 1, "length": 1, "height": 3, "category": "brick"},
    "3006": {"ldraw_id": "3006", "name": "Brick 2x10", "width": 2, "length": 10, "height": 3, "category": "brick"},
    "3007": {"ldraw_id": "3007", "name": "Brick 2x8", "width": 2, "length": 8, "height": 3, "category": "brick"},
    "3008": {"ldraw_id": "3008", "name": "Brick 1x8", "width": 1, "length": 8, "height": 3, "category": "brick"},
    "3009": {"ldraw_id": "3009", "name": "Brick 1x6", "width": 1, "length": 6, "height": 3, "category": "brick"},
    "3010": {"ldraw_id": "3010", "name": "Brick 1x4", "width": 1, "length": 4, "height": 3, "category": "brick"},
    "3011": {"ldraw_id": "3011", "name": "Brick 2x4 with Holes", "width": 2, "length": 4, "height": 3, "category": "brick"},
    "3622": {"ldraw_id": "3622", "name": "Brick 1x3", "width": 1, "length": 3, "height": 3, "category": "brick"},
    "2357": {"ldraw_id": "2357", "name": "Brick 2x2 Corner", "width": 2, "length": 2, "height": 3, "category": "brick"},
    "6061": {"ldraw_id": "6061", "name": "Brick 1x1 Round", "width": 1, "length": 1, "height": 3, "category": "brick"},

    # Basic plates
    "3020": {"ldraw_id": "3020", "name": "Plate 2x4", "width": 2, "length": 4, "height": 1, "category": "plate"},
    "3021": {"ldraw_id": "3021", "name": "Plate 2x3", "width": 2, "length": 3, "height": 1, "category": "plate"},
    "3022": {"ldraw_id": "3022", "name": "Plate 2x2", "width": 2, "length": 2, "height": 1, "category": "plate"},
    "3023": {"ldraw_id": "3023", "name": "Plate 1x2", "width": 1, "length": 2, "height": 1, "category": "plate"},
    "3024": {"ldraw_id": "3024", "name": "Plate 1x1", "width": 1, "length": 1, "height": 1, "category": "plate"},
    "3026": {"ldraw_id": "3026", "name": "Plate 6x6", "width": 6, "length": 6, "height": 1, "category": "plate"},
    "3027": {"ldraw_id": "3027", "name": "Plate 6x12", "width": 6, "length": 12, "height": 1, "category": "plate"},
    "3028": {"ldraw_id": "3028", "name": "Plate 6x12", "width": 6, "length": 12, "height": 1, "category": "plate"},
    "3029": {"ldraw_id": "3029", "name": "Plate 4x12", "width": 4, "length": 12, "height": 1, "category": "plate"},
    "3030": {"ldraw_id": "3030", "name": "Plate 4x10", "width": 4, "length": 10, "height": 1, "category": "plate"},
    "3031": {"ldraw_id": "3031", "name": "Plate 4x4", "width": 4, "length": 4, "height": 1, "category": "plate"},
    "3032": {"ldraw_id": "3032", "name": "Plate 4x6", "width": 4, "length": 6, "height": 1, "category": "plate"},
    "3033": {"ldraw_id": "3033", "name": "Plate 6x10", "width": 6, "length": 10, "height": 1, "category": "plate"},
    "3034": {"ldraw_id": "3034", "name": "Plate 2x8", "width": 2, "length": 8, "height": 1, "category": "plate"},
    "3035": {"ldraw_id": "3035", "name": "Plate 4x8", "width": 4, "length": 8, "height": 1, "category": "plate"},
    "3036": {"ldraw_id": "3036", "name": "Plate 6x8", "width": 6, "length": 8, "height": 1, "category": "plate"},
    "3460": {"ldraw_id": "3460", "name": "Plate 1x8", "width": 1, "length": 8, "height": 1, "category": "plate"},
    "3666": {"ldraw_id": "3666", "name": "Plate 1x6", "width": 1, "length": 6, "height": 1, "category": "plate"},
    "3710": {"ldraw_id": "3710", "name": "Plate 1x4", "width": 1, "length": 4, "height": 1, "category": "plate"},
    "3623": {"ldraw_id": "3623", "name": "Plate 1x3", "width": 1, "length": 3, "height": 1, "category": "plate"},
    "2420": {"ldraw_id": "2420", "name": "Plate 2x2 Corner", "width": 2, "length": 2, "height": 1, "category": "plate"},
    "3795": {"ldraw_id": "3795", "name": "Plate 2x6", "width": 2, "length": 6, "height": 1, "category": "plate"},
    "3832": {"ldraw_id": "3832", "name": "Plate 2x10", "width": 2, "length": 10, "height": 1, "category": "plate"},

    # Tiles (plates without studs)
    "3068": {"ldraw_id": "3068b", "name": "Tile 2x2", "width": 2, "length": 2, "height": 1, "category": "tile"},
    "3068b": {"ldraw_id": "3068b", "name": "Tile 2x2", "width": 2, "length": 2, "height": 1, "category": "tile"},
    "3069": {"ldraw_id": "3069b", "name": "Tile 1x2", "width": 1, "length": 2, "height": 1, "category": "tile"},
    "3069b": {"ldraw_id": "3069b", "name": "Tile 1x2", "width": 1, "length": 2, "height": 1, "category": "tile"},
    "3070": {"ldraw_id": "3070b", "name": "Tile 1x1", "width": 1, "length": 1, "height": 1, "category": "tile"},
    "3070b": {"ldraw_id": "3070b", "name": "Tile 1x1", "width": 1, "length": 1, "height": 1, "category": "tile"},
    "2431": {"ldraw_id": "2431", "name": "Tile 1x4", "width": 1, "length": 4, "height": 1, "category": "tile"},
    "6636": {"ldraw_id": "6636", "name": "Tile 1x6", "width": 1, "length": 6, "height": 1, "category": "tile"},

    # Slopes
    "3039": {"ldraw_id": "3039", "name": "Slope 45 2x2", "width": 2, "length": 2, "height": 2, "category": "slope"},
    "3040": {"ldraw_id": "3040", "name": "Slope 45 2x1", "width": 2, "length": 1, "height": 2, "category": "slope"},
    "3044": {"ldraw_id": "3044", "name": "Slope 45 1x2", "width": 1, "length": 2, "height": 2, "category": "slope"},
    "3045": {"ldraw_id": "3045", "name": "Slope 45 2x2 Double", "width": 2, "length": 2, "height": 3, "category": "slope"},
    "3046": {"ldraw_id": "3046", "name": "Slope 45 1x2 Double", "width": 1, "length": 2, "height": 3, "category": "slope"},
    "3048": {"ldraw_id": "3048", "name": "Slope 45 1x2 Triple", "width": 1, "length": 2, "height": 3, "category": "slope"},
    "3298": {"ldraw_id": "3298", "name": "Slope 33 3x2", "width": 3, "length": 2, "height": 2, "category": "slope"},
    "3299": {"ldraw_id": "3299", "name": "Slope 33 2x4", "width": 2, "length": 4, "height": 2, "category": "slope"},
    "3660": {"ldraw_id": "3660", "name": "Slope 45 2x2 Inverted", "width": 2, "length": 2, "height": 2, "category": "slope"},
    "3665": {"ldraw_id": "3665", "name": "Slope 45 2x1 Inverted", "width": 2, "length": 1, "height": 2, "category": "slope"},
    "4286": {"ldraw_id": "4286", "name": "Slope 33 1x3", "width": 1, "length": 3, "height": 2, "category": "slope"},

    # Technic
    "3700": {"ldraw_id": "3700", "name": "Technic Brick 1x2", "width": 1, "length": 2, "height": 3, "category": "technic"},
    "3701": {"ldraw_id": "3701", "name": "Technic Brick 1x4", "width": 1, "length": 4, "height": 3, "category": "technic"},
    "3702": {"ldraw_id": "3702", "name": "Technic Brick 1x8", "width": 1, "length": 8, "height": 3, "category": "technic"},
    "3703": {"ldraw_id": "3703", "name": "Technic Brick 1x16", "width": 1, "length": 16, "height": 3, "category": "technic"},
    "32000": {"ldraw_id": "32000", "name": "Technic Brick 1x2 with Axle Hole", "width": 1, "length": 2, "height": 3, "category": "technic"},
    "6541": {"ldraw_id": "6541", "name": "Technic Brick 1x1 with Hole", "width": 1, "length": 1, "height": 3, "category": "technic"},

    # Round bricks
    "3062": {"ldraw_id": "3062b", "name": "Round Brick 1x1", "width": 1, "length": 1, "height": 3, "category": "round"},
    "3062b": {"ldraw_id": "3062b", "name": "Round Brick 1x1", "width": 1, "length": 1, "height": 3, "category": "round"},
    "6143": {"ldraw_id": "6143", "name": "Round Brick 2x2", "width": 2, "length": 2, "height": 3, "category": "round"},
    "4073": {"ldraw_id": "4073", "name": "Round Plate 1x1", "width": 1, "length": 1, "height": 1, "category": "round"},
    "4032": {"ldraw_id": "4032", "name": "Round Plate 2x2", "width": 2, "length": 2, "height": 1, "category": "round"},

    # Modified bricks
    "2877": {"ldraw_id": "2877", "name": "Brick 1x2 with Grille", "width": 1, "length": 2, "height": 3, "category": "brick"},
    "4070": {"ldraw_id": "4070", "name": "Brick 1x1 with Headlight", "width": 1, "length": 1, "height": 3, "category": "brick"},
    "87087": {"ldraw_id": "87087", "name": "Brick 1x1 with Stud on Side", "width": 1, "length": 1, "height": 3, "category": "brick"},
    "2453": {"ldraw_id": "2453", "name": "Brick 1x1x5", "width": 1, "length": 1, "height": 15, "category": "brick"},

    # Wedges/Wings
    "41769": {"ldraw_id": "41769", "name": "Wedge 2x4 Right", "width": 2, "length": 4, "height": 1, "category": "wedge"},
    "41770": {"ldraw_id": "41770", "name": "Wedge 2x4 Left", "width": 2, "length": 4, "height": 1, "category": "wedge"},
    "43710": {"ldraw_id": "43710", "name": "Wedge 4x2 Right", "width": 4, "length": 2, "height": 2, "category": "wedge"},
    "43711": {"ldraw_id": "43711", "name": "Wedge 4x2 Left", "width": 4, "length": 2, "height": 2, "category": "wedge"},
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


def infer_part_from_name(part_name: str) -> Optional[Dict[str, Any]]:
    """
    Intelligently infer part dimensions from its name.
    Handles common naming patterns like "Brick 2x4", "Plate 1x2", etc.
    """
    import re

    name_lower = part_name.lower()

    # Extract category
    category = "brick"
    if "plate" in name_lower:
        category = "plate"
        default_height = 1
    elif "tile" in name_lower:
        category = "tile"
        default_height = 1
    elif "slope" in name_lower:
        category = "slope"
        default_height = 2
    elif "technic" in name_lower:
        category = "technic"
        default_height = 3
    elif "brick" in name_lower:
        category = "brick"
        default_height = 3
    else:
        # Unknown category, assume plate
        category = "plate"
        default_height = 1

    # Try to extract dimensions using regex
    # Patterns: "2x4", "1 x 2", "2 X 4", etc.
    dim_pattern = r'(\d+)\s*[xX]\s*(\d+)'
    matches = re.findall(dim_pattern, part_name)

    if matches:
        width, length = map(int, matches[0])
        return {
            "ldraw_id": "3001",  # Generic fallback
            "name": part_name,
            "width": width,
            "length": length,
            "height": default_height,
            "category": category,
            "is_inferred": True
        }

    # No dimensions found - use 1x1 as fallback with conservative defaults
    return {
        "ldraw_id": "3001",  # Generic brick fallback
        "name": part_name,
        "width": 1,
        "length": 1,
        "height": default_height,
        "category": category,
        "is_inferred": True
    }


def get_part_info(part_num: str, part_name: str = "") -> Optional[Dict[str, Any]]:
    """
    Get part info from mapping. Falls back to name-based inference.

    Args:
        part_num: Part number from Rebrickable
        part_name: Part name for fallback inference

    Returns:
        Part info dict or None if cannot be determined
    """
    # Try direct mapping first
    if part_num in PART_MAPPING:
        return PART_MAPPING[part_num]

    # Try without suffix (e.g., "3001a" -> "3001")
    base_num = part_num.rstrip('abcdefghijklmnopqrstuvwxyz')
    if base_num in PART_MAPPING:
        return PART_MAPPING[base_num]

    # Try inference from name if provided
    if part_name:
        return infer_part_from_name(part_name)

    return None


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
