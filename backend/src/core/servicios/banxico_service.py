"""
BanxicoService - Integration with Banco de México (Banxico) SIE API.

Provides USD/MXN FIX exchange rate retrieval with caching and fallback logic.
"""
import os
import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class BanxicoService:
    """
    Service for fetching USD/MXN exchange rates from Banco de México API.

    Features:
    - Fetches FIX exchange rate (series SF43718)
    - In-memory caching to reduce API calls
    - Fallback logic for weekends/holidays (up to 5 business days)
    - Token-based authentication via Bmx-Token header
    """

    BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series"
    SERIE_TC_FIX = "SF43718"  # USD/MXN FIX exchange rate series
    TIMEOUT = 30  # seconds
    MAX_FALLBACK_DAYS = 5  # Maximum days to look back for rate

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize BanxicoService.

        Args:
            api_token: Banxico API token. If not provided, reads from
                      BANXICO_API_TOKEN environment variable.
        """
        self.api_token = api_token or os.environ.get("BANXICO_API_TOKEN")
        self._cache: dict[str, Decimal] = {}

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API request including auth token."""
        headers = {
            "Accept": "application/json",
        }
        if self.api_token:
            headers["Bmx-Token"] = self.api_token
        return headers

    async def get_tipo_cambio(self, fecha: date) -> Decimal:
        """
        Get USD/MXN exchange rate for a specific date.

        Checks cache first, then fetches from API if needed.

        Args:
            fecha: Date to get exchange rate for

        Returns:
            Decimal: Exchange rate (MXN per USD)

        Raises:
            ValueError: If no rate available for date (after fallback attempts)
            RuntimeError: If API request fails
        """
        fecha_str = fecha.isoformat()

        # Check cache first
        if fecha_str in self._cache:
            logger.debug(f"Cache hit for date {fecha_str}")
            return self._cache[fecha_str]

        # Fetch from API
        rate = await self._fetch_from_api(fecha)

        # Cache the result
        self._cache[fecha_str] = rate
        logger.info(f"Cached exchange rate for {fecha_str}: {rate}")

        return rate

    async def get_tipo_cambio_actual(self) -> tuple[Decimal, date]:
        """
        Get the most recent USD/MXN exchange rate.

        Falls back to previous business days if today's rate is not available
        (weekends, holidays).

        Returns:
            tuple[Decimal, date]: Exchange rate and the date it corresponds to

        Raises:
            ValueError: If no rate available within fallback period
            RuntimeError: If API request fails
        """
        current_date = date.today()

        for days_back in range(self.MAX_FALLBACK_DAYS + 1):
            check_date = current_date - timedelta(days=days_back)
            try:
                rate = await self.get_tipo_cambio(check_date)
                return rate, check_date
            except ValueError:
                # No data for this date, try previous day
                logger.debug(f"No rate available for {check_date}, trying previous day")
                continue

        raise ValueError(
            f"No se encontró tipo de cambio disponible en los últimos "
            f"{self.MAX_FALLBACK_DAYS} días"
        )

    async def _fetch_from_api(self, fecha: date) -> Decimal:
        """
        Internal method to fetch exchange rate from Banxico API.

        Args:
            fecha: Date to fetch rate for

        Returns:
            Decimal: Exchange rate

        Raises:
            ValueError: If no data available for date
            RuntimeError: If API request fails
        """
        if not self.api_token:
            raise RuntimeError(
                "BANXICO_API_TOKEN no está configurado. "
                "Por favor configure la variable de entorno."
            )

        fecha_str = fecha.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/{self.SERIE_TC_FIX}/datos/{fecha_str}/{fecha_str}"

        logger.info(f"Fetching exchange rate from Banxico for {fecha_str}")

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, headers=self._get_headers())

                if response.status_code != 200:
                    # Check for specific error responses
                    try:
                        error_data = response.json()
                        if "error" in error_data:
                            error_msg = error_data["error"].get(
                                "mensaje", "Error desconocido"
                            )
                            raise RuntimeError(
                                f"Error de Banxico API: {error_msg}"
                            )
                    except (ValueError, KeyError):
                        pass

                    raise RuntimeError(
                        f"Error al consultar Banxico API: HTTP {response.status_code}"
                    )

                data = response.json()

        except httpx.TimeoutException:
            raise RuntimeError(
                "Timeout al consultar Banxico API. "
                "El servicio puede estar lento o no disponible."
            )
        except httpx.RequestError as e:
            raise RuntimeError(
                f"Error de red al consultar Banxico API: {str(e)}"
            )

        # Parse response
        try:
            series = data.get("bmx", {}).get("series", [])
            if not series:
                raise ValueError(f"No hay datos disponibles para la fecha {fecha_str}")

            datos = series[0].get("datos", [])
            if not datos:
                raise ValueError(f"No hay tipo de cambio publicado para {fecha_str}")

            # Extract the rate value
            # Note: Banxico returns "N/E" for dates without data
            dato_str = datos[0].get("dato", "")
            if not dato_str or dato_str == "N/E":
                raise ValueError(f"No hay tipo de cambio publicado para {fecha_str}")

            rate = Decimal(dato_str)
            logger.info(f"Successfully fetched rate for {fecha_str}: {rate}")
            return rate

        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Banxico response: {e}")
            raise RuntimeError(
                f"Error al procesar respuesta de Banxico: {str(e)}"
            )
        except InvalidOperation:
            raise RuntimeError(
                f"Valor de tipo de cambio inválido recibido de Banxico: {dato_str}"
            )

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Exchange rate cache cleared")
