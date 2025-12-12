"""
TRM (Tasa Representativa del Mercado) Service.

Fetches the official USD/COP exchange rate from Banco de la República
via the Datos Abiertos Colombia API.

API Documentation: https://www.datos.gov.co/Econom-a-y-Finanzas/TRM/ceyp-9c7c
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

# Datos Abiertos Colombia TRM API endpoint
TRM_API_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"
TRM_API_TIMEOUT = 5  # seconds
TRM_CACHE_TTL = 3600  # 1 hour cache TTL
MAX_LOOKBACK_DAYS = 5  # For weekends/holidays


class TRMService:
    """
    Service for fetching TRM (Tasa Representativa del Mercado) from
    Banco de la República via Datos Abiertos Colombia API.

    Features:
    - In-memory caching to reduce API calls during batch processing
    - Automatic lookback for weekends/holidays
    - Graceful error handling
    """

    def __init__(self):
        self._cache: Dict[str, float] = {}  # date_str -> trm_value
        self._cache_timestamps: Dict[str, datetime] = {}  # date_str -> cache_time

    def get_trm_for_date(self, date: datetime) -> Optional[float]:
        """
        Get TRM for a specific date.

        Args:
            date: The date to fetch TRM for

        Returns:
            TRM value as float, or None if not available
        """
        date_str = date.strftime("%Y-%m-%d")

        # Check cache first
        cached = self._get_from_cache(date_str)
        if cached is not None:
            return cached

        # Fetch from API with lookback for weekends/holidays
        for days_back in range(MAX_LOOKBACK_DAYS + 1):
            lookup_date = date - timedelta(days=days_back)
            trm = self._fetch_trm_from_api(lookup_date)
            if trm is not None:
                # Cache the result for the original date
                self._add_to_cache(date_str, trm)
                return trm

        logger.warning(f"Could not find TRM for date {date_str} (tried {MAX_LOOKBACK_DAYS} days back)")
        return None

    def _get_from_cache(self, date_str: str) -> Optional[float]:
        """Check cache for TRM value."""
        if date_str not in self._cache:
            return None

        cache_time = self._cache_timestamps.get(date_str)
        if cache_time and (datetime.now() - cache_time).total_seconds() > TRM_CACHE_TTL:
            # Cache expired
            del self._cache[date_str]
            del self._cache_timestamps[date_str]
            return None

        return self._cache[date_str]

    def _add_to_cache(self, date_str: str, value: float) -> None:
        """Add TRM value to cache."""
        self._cache[date_str] = value
        self._cache_timestamps[date_str] = datetime.now()

    def _fetch_trm_from_api(self, date: datetime) -> Optional[float]:
        """
        Fetch TRM from Datos Abiertos Colombia API.

        Args:
            date: Date to fetch TRM for

        Returns:
            TRM value or None if not found/error
        """
        date_str = date.strftime("%Y-%m-%d")

        try:
            # Query for exact date
            params = {
                "$where": f"vigenciadesde >= '{date_str}T00:00:00.000' AND vigenciadesde < '{date_str}T23:59:59.999'",
                "$limit": 1,
                "$order": "vigenciadesde DESC"
            }

            response = requests.get(
                TRM_API_URL,
                params=params,
                timeout=TRM_API_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                valor = data[0].get("valor")
                if valor:
                    trm = float(valor)
                    logger.debug(f"TRM for {date_str}: {trm}")
                    return trm

            logger.debug(f"No TRM data found for {date_str}")
            return None

        except requests.exceptions.Timeout:
            logger.warning(f"TRM API timeout for date {date_str}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"TRM API error for date {date_str}: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"TRM API response parsing error for {date_str}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the TRM cache."""
        self._cache.clear()
        self._cache_timestamps.clear()

    def preload_cache(self, dates: List[datetime]) -> Dict[str, Optional[float]]:
        """
        Preload TRM values for multiple dates.

        Useful for batch processing to minimize API calls.

        Args:
            dates: List of dates to preload

        Returns:
            Dict mapping date strings to TRM values
        """
        results: Dict[str, Optional[float]] = {}
        unique_dates = list(set(d.strftime("%Y-%m-%d") for d in dates))

        for date_str in unique_dates:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            trm = self.get_trm_for_date(date)
            results[date_str] = trm

        return results


# Singleton instance for use across the application
trm_service = TRMService()
