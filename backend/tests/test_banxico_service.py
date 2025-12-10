"""
Unit tests for BanxicoService - USD/MXN exchange rate integration.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

import httpx

from src.core.servicios.banxico_service import BanxicoService


class TestBanxicoService:
    """Tests for BanxicoService exchange rate functionality"""

    @pytest.fixture
    def service(self):
        """Create BanxicoService instance with test token"""
        return BanxicoService(api_token="test-token-12345")

    @pytest.fixture
    def mock_successful_response(self):
        """Mock successful Banxico API response"""
        return {
            "bmx": {
                "series": [
                    {
                        "idSerie": "SF43718",
                        "titulo": "Tipo de cambio pesos por dólar E.U.A.",
                        "datos": [
                            {
                                "fecha": "10/01/2025",
                                "dato": "20.4523"
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def mock_no_data_response(self):
        """Mock Banxico API response with N/E (no data available)"""
        return {
            "bmx": {
                "series": [
                    {
                        "idSerie": "SF43718",
                        "titulo": "Tipo de cambio pesos por dólar E.U.A.",
                        "datos": [
                            {
                                "fecha": "11/01/2025",
                                "dato": "N/E"
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def mock_empty_datos_response(self):
        """Mock Banxico API response with empty datos array"""
        return {
            "bmx": {
                "series": [
                    {
                        "idSerie": "SF43718",
                        "titulo": "Tipo de cambio pesos por dólar E.U.A.",
                        "datos": []
                    }
                ]
            }
        }

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_success(self, service, mock_successful_response):
        """Test successful exchange rate retrieval"""
        test_date = date(2025, 1, 10)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_successful_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            rate = await service.get_tipo_cambio(test_date)

            assert rate == Decimal("20.4523")
            mock_client_instance.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_no_data_ne(self, service, mock_no_data_response):
        """Test that N/E response raises ValueError"""
        test_date = date(2025, 1, 11)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_no_data_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ValueError) as exc_info:
                await service.get_tipo_cambio(test_date)

            assert "No hay tipo de cambio publicado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_empty_datos(self, service, mock_empty_datos_response):
        """Test that empty datos array raises ValueError"""
        test_date = date(2025, 1, 11)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_empty_datos_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ValueError) as exc_info:
                await service.get_tipo_cambio(test_date)

            assert "No hay tipo de cambio publicado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_cached(self, service, mock_successful_response):
        """Test that second call uses cache instead of API"""
        test_date = date(2025, 1, 10)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_successful_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            # First call - should hit API
            rate1 = await service.get_tipo_cambio(test_date)
            assert rate1 == Decimal("20.4523")
            assert mock_client_instance.get.call_count == 1

            # Second call - should use cache
            rate2 = await service.get_tipo_cambio(test_date)
            assert rate2 == Decimal("20.4523")
            # Call count should still be 1 (no additional API call)
            assert mock_client_instance.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_timeout(self, service):
        """Test timeout handling"""
        test_date = date(2025, 1, 10)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(RuntimeError) as exc_info:
                await service.get_tipo_cambio(test_date)

            assert "Timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_actual_fallback(self, service, mock_successful_response, mock_no_data_response):
        """Test that get_tipo_cambio_actual falls back to previous days"""
        today = date.today()

        with patch("httpx.AsyncClient") as mock_client:
            call_count = 0

            async def mock_get(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                mock_response = MagicMock()
                mock_response.status_code = 200
                # First 2 calls return N/E, third returns valid data
                if call_count <= 2:
                    mock_response.json.return_value = mock_no_data_response
                else:
                    mock_response.json.return_value = mock_successful_response
                return mock_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get = mock_get
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            rate, rate_date = await service.get_tipo_cambio_actual()

            assert rate == Decimal("20.4523")
            # Should have tried 3 times (today + 2 fallbacks)
            assert call_count == 3
            # Date should be 2 days before today
            assert rate_date == today - timedelta(days=2)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_no_token(self):
        """Test that missing token raises RuntimeError"""
        service = BanxicoService(api_token=None)
        # Clear env var if set
        with patch.dict("os.environ", {}, clear=True):
            service.api_token = None

            with pytest.raises(RuntimeError) as exc_info:
                await service.get_tipo_cambio(date(2025, 1, 10))

            assert "BANXICO_API_TOKEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_api_error(self, service):
        """Test API error response handling"""
        test_date = date(2025, 1, 10)

        error_response = {
            "error": {
                "url": "https://www.banxico.org.mx/SieAPIRest/service/v1/token",
                "mensaje": "Token inválido",
                "detalle": "El token enviado no es válido"
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = error_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(RuntimeError) as exc_info:
                await service.get_tipo_cambio(test_date)

            assert "Token inválido" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_network_error(self, service):
        """Test network error handling"""
        test_date = date(2025, 1, 10)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.side_effect = httpx.RequestError("Connection failed")
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(RuntimeError) as exc_info:
                await service.get_tipo_cambio(test_date)

            assert "Error de red" in str(exc_info.value)

    def test_clear_cache(self, service):
        """Test cache clearing"""
        # Pre-populate cache
        service._cache["2025-01-10"] = Decimal("20.4523")
        service._cache["2025-01-09"] = Decimal("20.3456")

        assert len(service._cache) == 2

        service.clear_cache()

        assert len(service._cache) == 0

    def test_headers_include_token(self, service):
        """Test that headers include Bmx-Token"""
        headers = service._get_headers()

        assert "Bmx-Token" in headers
        assert headers["Bmx-Token"] == "test-token-12345"
        assert headers["Accept"] == "application/json"

    def test_headers_without_token(self):
        """Test headers without token"""
        service = BanxicoService(api_token=None)
        headers = service._get_headers()

        assert "Bmx-Token" not in headers
        assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_tipo_cambio_actual_all_fallbacks_fail(self, service, mock_no_data_response):
        """Test that ValueError is raised when all fallback attempts fail"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_no_data_response

            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            with pytest.raises(ValueError) as exc_info:
                await service.get_tipo_cambio_actual()

            assert "últimos" in str(exc_info.value)
            # Should have tried MAX_FALLBACK_DAYS + 1 times
            assert mock_client_instance.get.call_count == service.MAX_FALLBACK_DAYS + 1
