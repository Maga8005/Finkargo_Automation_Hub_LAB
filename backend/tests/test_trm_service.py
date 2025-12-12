"""
Unit tests for TRM Service.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.core.servicios.trm_service import TRMService, TRM_API_URL


class TestTRMService:
    """Tests for TRMService class."""

    @pytest.fixture
    def service(self):
        """Create a fresh TRMService instance."""
        return TRMService()

    def test_get_trm_for_date_success(self, service):
        """Test successful TRM fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"valor": "4150.25", "unidad": "COP", "vigenciadesde": "2025-12-01T00:00:00.000"}
        ]

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result == 4150.25
            mock_get.assert_called_once()

    def test_get_trm_for_date_cached(self, service):
        """Test that cached values are returned without API call."""
        # Prime the cache
        service._cache["2025-12-01"] = 4150.25
        service._cache_timestamps["2025-12-01"] = datetime.now()

        with patch('requests.get') as mock_get:
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result == 4150.25
            mock_get.assert_not_called()

    def test_get_trm_for_date_cache_expired(self, service):
        """Test that expired cache triggers new API call."""
        # Prime the cache with expired timestamp
        service._cache["2025-12-01"] = 4150.25
        service._cache_timestamps["2025-12-01"] = datetime.now() - timedelta(hours=2)

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"valor": "4200.00", "unidad": "COP", "vigenciadesde": "2025-12-01T00:00:00.000"}
        ]

        with patch('requests.get', return_value=mock_response):
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result == 4200.00

    def test_get_trm_for_date_lookback_weekend(self, service):
        """Test lookback for weekend dates."""
        mock_response_empty = MagicMock()
        mock_response_empty.json.return_value = []

        mock_response_friday = MagicMock()
        mock_response_friday.json.return_value = [
            {"valor": "4100.00", "unidad": "COP", "vigenciadesde": "2025-12-05T00:00:00.000"}
        ]

        # Saturday (Dec 6) has no data, Friday (Dec 5) has data
        with patch('requests.get') as mock_get:
            mock_get.side_effect = [mock_response_empty, mock_response_friday]

            result = service.get_trm_for_date(datetime(2025, 12, 6))  # Saturday

            assert result == 4100.00
            assert mock_get.call_count == 2

    def test_get_trm_for_date_api_timeout(self, service):
        """Test graceful handling of API timeout."""
        import requests

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()

            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_get_trm_for_date_api_error(self, service):
        """Test graceful handling of API error."""
        import requests

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection error")

            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_get_trm_for_date_invalid_response(self, service):
        """Test handling of invalid response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"invalid": "data"}]  # Missing 'valor'

        with patch('requests.get', return_value=mock_response):
            # Should return None when no valid data found after lookback
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_get_trm_for_date_empty_response(self, service):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.json.return_value = []

        with patch('requests.get', return_value=mock_response):
            # Should return None when no data found after lookback
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_clear_cache(self, service):
        """Test cache clearing."""
        service._cache["2025-12-01"] = 4150.25
        service._cache_timestamps["2025-12-01"] = datetime.now()

        service.clear_cache()

        assert len(service._cache) == 0
        assert len(service._cache_timestamps) == 0

    def test_preload_cache(self, service):
        """Test batch preloading of TRM values."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"valor": "4150.25", "unidad": "COP", "vigenciadesde": "2025-12-01T00:00:00.000"}
        ]

        dates = [datetime(2025, 12, 1), datetime(2025, 12, 1), datetime(2025, 12, 2)]

        with patch('requests.get', return_value=mock_response):
            results = service.preload_cache(dates)

            assert "2025-12-01" in results
            assert "2025-12-02" in results
            # Duplicate dates should be deduplicated
            assert len(results) == 2

    def test_preload_cache_caches_values(self, service):
        """Test that preload_cache populates the internal cache."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"valor": "4000.00", "unidad": "COP", "vigenciadesde": "2025-12-01T00:00:00.000"}
        ]

        dates = [datetime(2025, 12, 1)]

        with patch('requests.get', return_value=mock_response):
            service.preload_cache(dates)

        # Subsequent call should use cache
        with patch('requests.get') as mock_get:
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result == 4000.00
            mock_get.assert_not_called()

    def test_get_trm_for_date_parses_valor_as_float(self, service):
        """Test that valor string is correctly parsed to float."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"valor": "4150.7532", "unidad": "COP", "vigenciadesde": "2025-12-01T00:00:00.000"}
        ]

        with patch('requests.get', return_value=mock_response):
            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result == pytest.approx(4150.7532, rel=1e-4)

    def test_get_trm_for_date_handles_http_error(self, service):
        """Test handling of HTTP errors."""
        import requests

        with patch('requests.get') as mock_get:
            # Raise HTTPError which is a subclass of RequestException
            mock_get.side_effect = requests.exceptions.HTTPError("HTTP Error")

            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_multiple_instances_have_separate_caches(self):
        """Test that separate service instances have independent caches."""
        service1 = TRMService()
        service2 = TRMService()

        service1._cache["2025-12-01"] = 4150.25
        service1._cache_timestamps["2025-12-01"] = datetime.now()

        assert "2025-12-01" not in service2._cache
