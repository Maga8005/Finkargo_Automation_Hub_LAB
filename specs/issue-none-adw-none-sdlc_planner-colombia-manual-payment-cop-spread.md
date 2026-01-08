# Feature: Colombia Manual Payment COP Spread Calculation with TRM Integration

## Feature Description
Implement spread calculation for manual payments in COP (Colombian Pesos) in the Tesorería Colombia payment application module with full TRM (Tasa Representativa del Mercado) integration from Banco de la República via the Datos Abiertos Colombia API. Currently, spread is only calculated for "Pago en línea" payments. This feature extends the spread calculation logic to include manual payments made in COP, using a different formula that requires the TRM.

## User Story
As a **treasury analyst (operations/analyst role)**
I want to **have spread calculated automatically for manual COP payments using the official TRM rate**
So that **the NetSuite payment application template includes accurate spread values based on the official exchange rate differential, improving accuracy of financial reconciliation**

## Problem Statement
Currently, the `PaymentTemplateService` only calculates spread for "Pago en línea" payments using the formula `spread_value × total_pagado_usd`. Manual payments in COP, which represent a significant portion of payments, do not receive spread calculations. This creates incomplete data in the NetSuite template and requires manual intervention for spread assignment.

**Current behavior:**
- **Pago en línea**: Spread calculated as `spread_value × total_pagado_usd` → placed in Spread FK or Spread PA based on NT flag
- **Manual COP**: No spread calculation (spread columns remain empty)
- **Manual USD**: No spread calculation (correct - USD transactions don't have spread)

## Solution Statement
Implement spread calculation for manual COP payments using the formula:
```
Spread PA = (Tasa Fincargo - Tasa TRM) × Total Pagado USD
```

Where:
- **Tasa Fincargo**: The exchange rate from the "Tasa de cambio de FK/en línea" column
- **Tasa TRM**: The official TRM rate fetched from Datos Abiertos Colombia API
- **Total Pagado USD**: The USD payment amount from "Total pagado [USD]" column

**Key changes:**
1. Create a TRM service to fetch exchange rates from Datos Abiertos Colombia API
2. Implement in-memory caching to minimize API calls during file processing
3. Calculate spread for manual COP payments using the formula above
4. Place the calculated spread in "Spread PA" column (not FK or Supra) for manual payments
5. Manual USD payments should NOT have spread (they're pure USD transactions)
6. Handle API failures gracefully with fallback behavior

## Access Control
- Required Role(s): `operations`, `analyst`, `admin`, `mesa_control`
- Backend Protection: No changes needed - existing routes use RBAC from `tesoreria_routes.py`
- Frontend Protection: No changes needed - existing page protection applies

## Relevant Files
Use these files to implement the feature:

- `backend/src/core/servicios/payment_template_service.py` - **Primary file to modify**: Contains the `_process_row()` method where spread calculation logic needs to be extended for manual COP payments
- `backend/src/core/servicios/catalogs/payment_catalogs.py` - Reference for column mappings (COLOMBIA_OPTIONAL_COLUMNS has `medio_pago`, `exchangerate`, `total_pagado_usd`)
- `backend/tests/test_payment_template_service.py` - **Add new tests**: Extensive test file for PaymentTemplateService, needs new test cases for manual COP spread calculation

### New Files
- `backend/src/core/servicios/trm_service.py` - **New service**: TRM lookup service with caching and API integration
- `backend/tests/test_trm_service.py` - **New tests**: Unit tests for TRM service

## Pre-Implementation Verification

### Feature Category
- [ ] Document Generation (contracts, PDFs) → Complete sections A, D, E
- [x] Excel Processing (treasury, finance) → Complete sections B, D
- [ ] Data Import/Export (CSV, ZIP) → Complete sections C, D
- [x] API Integration (external services) → Complete sections D, F
- [ ] Reporting (queries, history) → Complete sections D, G
- [ ] CRUD Operations (basic data management) → Complete sections D, E

### B. Excel Column Mapping (Excel Processing only)

**Source Excel Structure (Historial de Pagos Colombia):**
| Column Name (exact) | Required | Data Type | Validation | Internal Name |
|--------------------|----------|-----------|------------|---------------|
| Médio de pago | No | String | "Manual", "Pago en línea" | `medio_pago` |
| Moneda | Yes | String | "COP", "USD" | `currency` |
| Tasa de cambio de FK/en línea | No | Float | Positive number | `exchangerate` |
| Total pagado [USD] | No | Float | Positive number | `total_pagado_usd` |
| Spread | No | Float | Rate value | `spread` |
| NT | No | String | Contains "NT" for NT routing | `nt_flag` |
| Fecha de pago | Yes | Date | Valid date | `payment_date` |

**Output Excel Structure (NetSuite Template):**
| Column Name | Source Field | Transformation |
|-------------|--------------|----------------|
| Spread PA | Calculated | For Manual COP: `(tasa_fincargo - tasa_trm) × total_pagado_usd` |
| Spread FK | Calculated | For Pago en línea non-NT: `spread_value × total_pagado_usd` |
| Spread Supra | Calculated | Reserved for future use (currently unused) |

**Catalog Dependencies:**
- [x] AR account mappings documented (not affected by this change)
- [x] Country-specific variations identified (CO only, MX not affected)

### D. Data Contract Verification (ALL features)

| Repository Method | Return Type | Access Pattern | Example |
|------------------|-------------|----------------|---------|
| N/A | N/A | N/A | No repository changes needed |

### F. External API Contract (Integration)

**Datos Abiertos Colombia TRM API:**

| Attribute | Value |
|-----------|-------|
| Endpoint | `https://www.datos.gov.co/resource/32sa-8pi3.json` |
| Method | GET |
| Auth | None required (public API) |
| Rate Limits | Fair use (no documented limit) |

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `vigenciadesde` | ISO 8601 date | Filter by validity start date | `2025-12-01T00:00:00.000` |
| `$where` | SoQL query | Advanced filtering | `vigenciadesde >= '2025-12-01'` |
| `$limit` | integer | Max records to return | `1` |
| `$order` | string | Sort order | `vigenciadesde DESC` |

**Response Format:**
```json
[
  {
    "valor": "4150.25",
    "unidad": "COP",
    "vigenciadesde": "2025-12-01T00:00:00.000",
    "vigenciahasta": "2025-12-01T00:00:00.000"
  }
]
```

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `valor` | string | Exchange rate (USD to COP) |
| `unidad` | string | Currency unit (always "COP") |
| `vigenciadesde` | ISO 8601 | Start of validity period |
| `vigenciahasta` | ISO 8601 | End of validity period |

**Error Handling Strategy:**
| Scenario | Behavior |
|----------|----------|
| API timeout (>5s) | Return None, log warning, skip spread calculation |
| HTTP 4xx/5xx | Return None, log error, skip spread calculation |
| No data for date | Try previous business day (up to 5 days back) |
| Invalid response | Return None, log error, skip spread calculation |
| Network error | Return None, log error, skip spread calculation |

### Interface Mapping (Frontend ↔ Backend)
No frontend changes required - this is a backend processing change.

| Frontend Field | Backend Field | Type | Notes |
|---------------|---------------|------|-------|
| N/A | spread_pa | float | New calculation for Manual COP |
| N/A | spread_fk | float | Existing, no change |
| N/A | tasa_trm | float | Fetched from TRM API |

## Implementation Plan

### Phase 1: Foundation - TRM Service
1. Create TRM service with API integration
   - New file: `backend/src/core/servicios/trm_service.py`
   - Implement `TRMService` class with caching
   - Method: `get_trm_for_date(date: datetime) -> Optional[float]`
   - In-memory cache with TTL for batch processing efficiency

2. Add HTTP client dependency
   - Use `httpx` for async HTTP requests (already available) or `requests` for sync

### Phase 2: Core Implementation
1. Create helper method for manual COP spread calculation in `PaymentTemplateService`
   - Method: `_calculate_manual_cop_spread(tasa_fincargo, tasa_trm, total_pagado_usd)`
   - Returns calculated spread or None if conditions not met

2. Modify `_process_row()` method in `payment_template_service.py`
   - Integrate TRM service for manual COP payments
   - Calculate spread_pa using the new formula
   - Set spread_fk = None for manual payments
   - Manual USD payments have all spread values as None

### Phase 3: Integration & Testing
1. Add logging for TRM lookups and spread calculations
2. Write unit tests for TRM service
3. Write unit tests for manual COP spread calculation
4. Integration testing with real API (manual verification)

## Step by Step Tasks

### Step 1: Create TRM Service
Create new file `backend/src/core/servicios/trm_service.py`:

```python
"""
TRM (Tasa Representativa del Mercado) Service.

Fetches the official USD/COP exchange rate from Banco de la República
via the Datos Abiertos Colombia API.

API Documentation: https://www.datos.gov.co/Econom-a-y-Finanzas/TRM/ceyp-9c7c
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
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

    def preload_cache(self, dates: list[datetime]) -> Dict[str, Optional[float]]:
        """
        Preload TRM values for multiple dates.

        Useful for batch processing to minimize API calls.

        Args:
            dates: List of dates to preload

        Returns:
            Dict mapping date strings to TRM values
        """
        results = {}
        unique_dates = list(set(d.strftime("%Y-%m-%d") for d in dates))

        for date_str in unique_dates:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            trm = self.get_trm_for_date(date)
            results[date_str] = trm

        return results


# Singleton instance for use across the application
trm_service = TRMService()
```

### Step 2: Add Helper Method to PaymentTemplateService
Add to `backend/src/core/servicios/payment_template_service.py`:

- Import TRM service at top of file:
  ```python
  from src.core.servicios.trm_service import trm_service
  ```

- Add helper method to class:
  ```python
  def _calculate_manual_cop_spread(
      self,
      tasa_fincargo: Optional[float],
      tasa_trm: Optional[float],
      total_pagado_usd: Optional[float]
  ) -> Optional[float]:
      """
      Calculate spread for manual COP payments.

      Formula: (Tasa Fincargo - Tasa TRM) × Total Pagado USD

      Args:
          tasa_fincargo: Fincargo exchange rate from source file
          tasa_trm: Official TRM rate from Banco de la República
          total_pagado_usd: Payment amount in USD

      Returns:
          Calculated spread amount, or None if inputs missing
      """
      if tasa_fincargo is None or tasa_trm is None or total_pagado_usd is None:
          return None

      if total_pagado_usd <= 0:
          return None

      spread = (tasa_fincargo - tasa_trm) * total_pagado_usd
      return round(spread, 2)
  ```

### Step 3: Modify `_process_row()` Spread Logic
Locate the spread calculation section in `_process_row()` (around line 510-535).

After extracting `medio_pago`, `currency`, `spread_value`, `total_pagado_usd`, add new logic block:

```python
# Manual payment spread handling (Colombia only)
if country.lower() == "colombia" and is_manual:
    if currency.upper() == "COP":
        # Manual COP: Calculate spread using (Tasa Fincargo - TRM) formula
        # Parse payment date for TRM lookup
        payment_date_parsed = None
        if payment_date_raw:
            try:
                if isinstance(payment_date_raw, datetime):
                    payment_date_parsed = payment_date_raw
                elif hasattr(payment_date_raw, 'to_pydatetime'):
                    payment_date_parsed = payment_date_raw.to_pydatetime()
                else:
                    # Try common date formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                        try:
                            payment_date_parsed = datetime.strptime(str(payment_date_raw).split()[0], fmt)
                            break
                        except ValueError:
                            continue
            except Exception as e:
                logger.warning(f"Could not parse payment date for TRM lookup: {e}")

        tasa_trm = None
        if payment_date_parsed:
            tasa_trm = trm_service.get_trm_for_date(payment_date_parsed)

        manual_spread = self._calculate_manual_cop_spread(
            tasa_fincargo=original_exchangerate,
            tasa_trm=tasa_trm,
            total_pagado_usd=total_pagado_usd
        )

        if manual_spread is not None:
            spread_pa = manual_spread
            spread_fk = None
            spread_supra = None
            logger.info(
                f"Manual COP spread calculated: customer={customer_external_id}, "
                f"tasa_fincargo={original_exchangerate}, tasa_trm={tasa_trm}, "
                f"total_pagado_usd={total_pagado_usd}, spread_pa={spread_pa}"
            )
        else:
            logger.debug(
                f"Manual COP spread skipped (missing data): customer={customer_external_id}, "
                f"tasa_fincargo={original_exchangerate}, tasa_trm={tasa_trm}, "
                f"total_pagado_usd={total_pagado_usd}"
            )
    else:
        # Manual USD: No spread calculation
        spread_pa = None
        spread_fk = None
        spread_supra = None
        logger.debug(f"Manual USD payment - no spread: customer={customer_external_id}")
```

### Step 4: Add TRM Cache Preloading (Optional Optimization)
In `convert_to_netsuite_template()`, add optional cache preloading:

```python
# Optional: Preload TRM cache for all unique payment dates
# This reduces API calls when processing large files with manual COP payments
if country.lower() == "colombia":
    payment_dates = []
    date_col = df_columns_normalized.get("fecha de pago")
    if date_col and date_col in df.columns:
        for date_val in df[date_col].dropna().unique():
            try:
                if isinstance(date_val, datetime):
                    payment_dates.append(date_val)
                elif hasattr(date_val, 'to_pydatetime'):
                    payment_dates.append(date_val.to_pydatetime())
            except:
                pass

    if payment_dates:
        from src.core.servicios.trm_service import trm_service
        trm_service.preload_cache(payment_dates)
        logger.info(f"Preloaded TRM cache for {len(payment_dates)} unique dates")
```

### Step 5: Write Unit Tests for TRM Service
Create new file `backend/tests/test_trm_service.py`:

```python
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
        with patch('requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.Timeout()

            result = service.get_trm_for_date(datetime(2025, 12, 1))

            assert result is None

    def test_get_trm_for_date_api_error(self, service):
        """Test graceful handling of API error."""
        with patch('requests.get') as mock_get:
            import requests
            mock_get.side_effect = requests.exceptions.RequestException("Connection error")

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
```

### Step 6: Write Unit Tests for Manual COP Spread
Add new test class to `backend/tests/test_payment_template_service.py`:

```python
# ==================== Tests for Manual COP Spread Calculation ====================

class TestManualCOPSpreadCalculation:
    """Tests for manual COP payment spread calculation with TRM integration."""

    def test_calculate_manual_cop_spread_valid_inputs(self, service):
        """Test spread calculation with valid inputs."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )

        # Expected: (4200.00 - 4150.25) × 1000 = 49750.00
        assert result == 49750.00

    def test_calculate_manual_cop_spread_none_tasa_fincargo(self, service):
        """Test spread calculation with missing tasa_fincargo."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=None,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )
        assert result is None

    def test_calculate_manual_cop_spread_none_tasa_trm(self, service):
        """Test spread calculation with missing tasa_trm."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=None,
            total_pagado_usd=1000.00
        )
        assert result is None

    def test_calculate_manual_cop_spread_none_total_usd(self, service):
        """Test spread calculation with missing total_pagado_usd."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=None
        )
        assert result is None

    def test_calculate_manual_cop_spread_zero_total_usd(self, service):
        """Test spread calculation with zero total_pagado_usd."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.00,
            tasa_trm=4150.25,
            total_pagado_usd=0.0
        )
        assert result is None

    def test_calculate_manual_cop_spread_negative_spread(self, service):
        """Test spread calculation when TRM > Fincargo rate (negative spread)."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4100.00,
            tasa_trm=4150.25,
            total_pagado_usd=1000.00
        )

        # Expected: (4100.00 - 4150.25) × 1000 = -50250.00
        assert result == -50250.00

    def test_calculate_manual_cop_spread_rounding(self, service):
        """Test spread calculation rounds to 2 decimal places."""
        result = service._calculate_manual_cop_spread(
            tasa_fincargo=4200.12345,
            tasa_trm=4150.98765,
            total_pagado_usd=100.00
        )

        # Expected: (4200.12345 - 4150.98765) × 100 = 4913.58 (rounded)
        assert result == 4913.58


class TestManualCOPSpreadIntegration:
    """Integration tests for manual COP spread with TRM service."""

    def test_manual_cop_payment_with_trm_calculates_spread(self, service):
        """Manual COP payment with TRM available calculates spread_pa."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:30:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,  # Fincargo rate
            "Spread": 10,  # Not used for manual
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Mock TRM service to return a fixed rate
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = 4150.25

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # Spread PA should be calculated: (4200.00 - 4150.25) × 1000 = 49750.00
        assert capital_row["Spread PA"] == 49750.00
        assert capital_row["Spread FK"] is None

    def test_manual_cop_payment_trm_unavailable_no_spread(self, service):
        """Manual COP payment with TRM unavailable skips spread."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:31:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 5000000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # Mock TRM service to return None (API error or no data)
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            mock_trm.get_trm_for_date.return_value = None

            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

        assert len(result) >= 1
        capital_row = result[0]

        # No spread when TRM unavailable
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_manual_usd_payment_no_spread(self, service):
        """Manual USD payment should have no spread regardless of TRM."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:32:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "USD",  # USD payment
            "Capital": 1000.00,
            "Banco remitente": "Test Bank",
            "Médio de pago": "Manual",
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 0,
            "Cuenta Remitente": "60100001091",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        result = service._process_row(
            row=row,
            country="colombia",
            required_columns=required_columns,
            concept_columns=concept_columns,
            optional_columns=optional_columns,
            df_columns_normalized=df_columns_normalized,
            is_first_row_in_group=True
        )

        assert len(result) >= 1
        capital_row = result[0]

        # No spread for USD payments
        assert capital_row["Spread PA"] is None
        assert capital_row["Spread FK"] is None

    def test_pago_en_linea_unchanged_with_trm_integration(self, service):
        """Pago en línea payments should still use original spread logic."""
        from src.core.servicios.catalogs.payment_catalogs import (
            get_required_columns,
            get_concept_columns,
            get_optional_columns,
        )

        required_columns = get_required_columns("colombia")
        concept_columns = get_concept_columns("colombia")
        optional_columns = get_optional_columns("colombia")

        row_data = {
            "Cliente": "Test Client",
            "Identificación del cliente": "123456789",
            "Código de desembolso": "CO:900759388:1:33:PAG",
            "Código de recaudo": "REC-001",
            "Fecha de pago": "2025-12-01",
            "Moneda": "COP",
            "Capital": 0,  # Only INTERESES
            "Banco remitente": "Test Bank",
            "Médio de pago": "Pago en línea",  # Online payment
            "Tasa de cambio de FK/en línea": 4200.00,
            "Spread": 10,  # Spread rate for online payments
            "Total pagado [USD]": 1000.00,
            "NT": "",
            "4x1000": 0,
            "Fondo de garantías": 0,
            "IVA Fondo de garantías": 0,
            "Seguro + IVA": 0,
            "Intereses Corrientes": 500.00,  # Has interest
            "Cuenta Remitente": "",
        }

        row = pd.Series(row_data)
        df_columns_normalized = {col.lower().strip(): col for col in row_data.keys()}

        # TRM service should NOT be called for Pago en línea
        with patch('src.core.servicios.payment_template_service.trm_service') as mock_trm:
            result = service._process_row(
                row=row,
                country="colombia",
                required_columns=required_columns,
                concept_columns=concept_columns,
                optional_columns=optional_columns,
                df_columns_normalized=df_columns_normalized,
                is_first_row_in_group=True
            )

            # TRM should not be called for Pago en línea
            mock_trm.get_trm_for_date.assert_not_called()

        assert len(result) >= 1
        intereses_row = result[0]

        # Pago en línea uses Spread FK with original formula
        assert intereses_row["Spread FK"] == 10000.00  # 10 × 1000
        assert intereses_row["Spread PA"] is None
```

### Step 7: Run Validation Commands
Execute validation commands to ensure no regressions.

## Testing Strategy

### Unit Tests
- Test `TRMService.get_trm_for_date()` with various scenarios (success, cache hit, API error, timeout)
- Test `TRMService.preload_cache()` for batch operations
- Test `_calculate_manual_cop_spread()` helper method with various inputs
- Test `_process_row()` with manual COP payments generates correct spread_pa
- Test `_process_row()` with manual USD payments has no spread
- Test existing Pago en línea behavior is unchanged

### Integration Tests
- Test TRM API integration with real endpoint (manual verification)
- Test cache behavior across multiple file conversions

### Edge Cases
1. Manual COP payment with missing `Tasa de cambio de FK/en línea` → No spread (need tasa_fincargo)
2. Manual COP payment with missing `Total pagado [USD]` → No spread
3. Manual COP payment with TRM API failure → No spread, log warning
4. Manual COP payment on weekend/holiday → Use previous business day TRM
5. Manual payment with mixed case "MANUAL", "manual", "Manual" → All should work
6. Empty currency field defaulting to "COP" → Should calculate spread
7. Group with mix of Manual and Pago en línea → Each type processes correctly
8. Large file with many dates → Cache reduces API calls
9. Negative spread (TRM > Fincargo rate) → Should calculate correctly

## Acceptance Criteria
1. Manual COP payments have spread calculated and placed in "Spread PA" column
2. Spread formula for manual COP: `(Tasa Fincargo - Tasa TRM) × Total Pagado USD`
3. TRM is fetched from Datos Abiertos Colombia API for the payment date
4. TRM values are cached to minimize API calls during batch processing
5. Manual USD payments have all spread columns as None
6. Pago en línea payments behavior unchanged (existing spread logic preserved)
7. API failures are handled gracefully (spread skipped, warning logged)
8. Weekend/holiday dates use previous business day TRM (up to 5 days lookback)
9. All new unit tests pass
10. All existing unit tests pass (no regressions)
11. Backend linting passes (`ruff check`)

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Run TRM service tests
cd backend && python -m pytest tests/test_trm_service.py -v

# Run payment template tests with verbose output
cd backend && python -m pytest tests/test_payment_template_service.py -v

# Run all backend tests to check for regressions
cd backend && python -m pytest

# Run backend linting
cd backend && ruff check src/

# Run frontend linting (no frontend changes, but verify no impact)
cd frontend && npm run lint

# Run TypeScript type check (no frontend changes, but verify no impact)
cd frontend && npx tsc --noEmit

# Run frontend build to validate production compilation
cd frontend && npm run build

# Manual verification: Test TRM API endpoint
curl "https://www.datos.gov.co/resource/32sa-8pi3.json?\$limit=1&\$order=vigenciadesde%20DESC"
```

## Notes

### TRM API Details
- **Source**: [Datos Abiertos Colombia - TRM](https://www.datos.gov.co/Econom-a-y-Finanzas/TRM/ceyp-9c7c)
- **Endpoint**: `https://www.datos.gov.co/resource/32sa-8pi3.json`
- **Documentation**: Uses Socrata Open Data API (SODA)
- **Rate**: Official TRM calculated and certified by Superintendencia Financiera de Colombia
- **Update Frequency**: Daily (weekdays only, weekends/holidays use previous business day)

### Design Decisions
1. **Spread PA for Manual**: Manual payments use "Spread PA" column because PA (Pago Anticipado) is the appropriate category for non-online payments
2. **No Spread for USD**: USD payments are pure currency transactions without exchange rate impact
3. **In-Memory Cache**: Using simple dict cache is sufficient for batch processing; no need for Redis/external cache
4. **5-Day Lookback**: Covers typical long weekends/holidays; adjust if longer gaps exist
5. **Graceful Degradation**: API failures don't break processing - spread is simply skipped

### Formula Clarification
- **Current "Pago en línea" formula**: `spread_value × total_pagado_usd`
  - `spread_value` comes from the "Spread" column in source file
  - This represents a spread rate that gets multiplied by USD amount

- **New Manual COP formula**: `(tasa_fincargo - tasa_trm) × total_pagado_usd`
  - This calculates the actual monetary spread from rate differential
  - `tasa_fincargo` is the rate from "Tasa de cambio de FK/en línea" column
  - `tasa_trm` is the official TRM rate from Banco de la República

### Dependencies
- `requests` library for HTTP calls (already in requirements.txt)
- No new pip packages required

## Plan Quality Checklist
Before finalizing the plan, verify all items are complete:

### General Completeness (ALL features)
- [x] Feature category identified in Pre-Implementation Verification
- [x] All new files listed in "New Files" section
- [x] All database migrations identified and tasks created (none needed)
- [ ] E2E test file task included (if UI feature) - N/A, backend only
- [x] All external dependencies (npm/pip packages) listed in Notes (none new needed)

### Category-Specific Completeness
**Excel Processing:**
- [x] Source Excel columns documented with exact names
- [x] Output Excel structure documented
- [x] Data transformation rules specified (formula for Manual COP spread)
- [x] Catalog/lookup dependencies identified (none new)

**API Integration:**
- [x] External API contract documented
- [x] Auth method specified (none required)
- [x] Error/retry strategy defined

### Consistency (ALL features)
- [x] Data types match between frontend and backend (N/A)
- [x] Field naming conventions use snake_case consistently
- [x] Access patterns verified for existing methods
- [x] Country-specific variations handled (CO only)

### Testing
- [x] Validation commands test all new functionality
- [x] Edge cases documented in Testing Strategy
- [ ] E2E test covers happy path with screenshots (if UI feature) - N/A
