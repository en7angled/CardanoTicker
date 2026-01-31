"""
Portfolio Data Fetcher - connects to portfolio-tracker-web API
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import requests

logging.basicConfig(level=logging.INFO)


@dataclass
class PortfolioHolding:
    """Represents a single asset holding in the portfolio"""
    asset: str
    quantity: float
    current_price: float
    current_value: float
    cost_basis: float
    pnl: float
    pnl_percent: float
    color: str


@dataclass
class PortfolioSummary:
    """Summary of the entire portfolio"""
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_percent: float
    holdings: List[PortfolioHolding]


# E-ink 7-color palette - EXACT RGB values from Waveshare 4.01" display driver
# These exact values ensure proper color mapping on the display
EINK_BLACK = '#464646'    # RGB(70, 70, 70)
EINK_WHITE = '#ffffff'    # RGB(255, 255, 255)
EINK_GREEN = '#00ff00'    # RGB(0, 255, 0)
EINK_BLUE = '#0000ff'     # RGB(0, 0, 255)
EINK_RED = '#ff0000'      # RGB(255, 0, 0)
EINK_ORANGE = '#ff8000'   # RGB(255, 128, 0)
EINK_YELLOW = '#ffff00'   # RGB(255, 255, 0)

# Map assets to e-ink colors for optimal display
ASSET_COLORS = {
    # Major cryptos
    'BTC': EINK_ORANGE,   # Orange
    'ETH': EINK_BLUE,     # Blue
    'ADA': EINK_BLUE,     # Blue
    'SOL': EINK_GREEN,    # Green
    'DOT': EINK_RED,      # Red
    'AVAX': EINK_RED,     # Red
    'MATIC': EINK_BLUE,   # Blue
    'LINK': EINK_BLUE,    # Blue
    'UNI': EINK_RED,      # Red
    'ATOM': EINK_BLACK,   # Black
    'XRP': EINK_BLACK,    # Black
    'DOGE': EINK_YELLOW,  # Yellow
    'SHIB': EINK_ORANGE,  # Orange
    'LTC': EINK_BLACK,    # Black
    'BNB': EINK_YELLOW,   # Yellow
    # Stablecoins - Green
    'USDT': EINK_GREEN,   # Green
    'USDC': EINK_GREEN,   # Green
    'USD': EINK_GREEN,    # Green
    'EUR': EINK_GREEN,    # Green
    'CASH': EINK_GREEN,   # Green
    # Other
    'NIGHT': EINK_BLACK,  # Black
}

DEFAULT_COLOR = EINK_BLACK  # Black for unknown assets


def get_asset_color(asset: str) -> str:
    """Get the color for an asset"""
    return ASSET_COLORS.get(asset.upper(), DEFAULT_COLOR)


class PortfolioDataFetcher:
    """
    Fetches portfolio data from portfolio-tracker-web API.
    Can also work with manually provided data.
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        portfolio_id: int = 1,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None  # Deprecated: userId is now derived from API key
    ):
        """
        Initialize the portfolio data fetcher.

        Args:
            api_base_url: Base URL for the portfolio-tracker API (e.g., "http://localhost:3000")
                         If None, only manual data can be used.
            portfolio_id: The portfolio ID to fetch data for
            api_key: API key for authentication (required for API access)
            user_id: Deprecated - userId is now derived from the API key on the server
        """
        self.api_base_url = api_base_url.rstrip('/') if api_base_url else None
        self.portfolio_id = portfolio_id
        self.api_key = api_key
        self._cached_holdings: Optional[List[PortfolioHolding]] = None
        self._cached_prices: Dict[str, float] = {}
        self._cached_btc_price: float = 0

    def set_manual_holdings(self, holdings: List[Dict]) -> None:
        """
        Set holdings manually without API.

        Args:
            holdings: List of dicts with keys: asset, quantity, cost_basis
                     e.g., [{"asset": "BTC", "quantity": 0.5, "cost_basis": 20000}, ...]
        """
        self._cached_holdings = []
        for h in holdings:
            asset = h['asset'].upper()
            quantity = float(h.get('quantity', 0))
            cost_basis = float(h.get('cost_basis', 0))
            current_price = float(h.get('current_price', 0))
            current_value = quantity * current_price
            pnl = current_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            self._cached_holdings.append(PortfolioHolding(
                asset=asset,
                quantity=quantity,
                current_price=current_price,
                current_value=current_value,
                cost_basis=cost_basis,
                pnl=pnl,
                pnl_percent=pnl_percent,
                color=get_asset_color(asset)
            ))

    def fetch_from_ticker_api(self) -> Optional[Dict]:
        """
        Fetch portfolio data from the dedicated ticker API endpoint.
        This endpoint uses API key authentication and returns all data in one call.
        The user is identified from the API key on the server side.
        """
        if not self.api_base_url or not self.api_key:
            logging.warning("API URL or API key not configured")
            return None

        try:
            url = f"{self.api_base_url}/api/ticker/portfolio"
            params = {
                'portfolioId': self.portfolio_id
            }
            headers = {
                'X-API-Key': self.api_key
            }
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logging.error("Ticker API authentication failed. Check your API key.")
            elif e.response.status_code == 404:
                logging.error("Portfolio not found. Check portfolioId.")
            else:
                logging.error(f"Ticker API error: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to fetch from ticker API: {e}")
            return None

    def fetch_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current prices from the portfolio-tracker API"""
        if not self.api_base_url:
            logging.warning("No API URL configured, using cached prices")
            return self._cached_prices

        try:
            url = f"{self.api_base_url}/api/prices/current"
            params = {'symbols': ','.join(symbols)}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self._cached_prices = data.get('prices', {})
            return self._cached_prices
        except Exception as e:
            logging.error(f"Failed to fetch prices: {e}")
            return self._cached_prices

    def fetch_transactions(self) -> List[Dict]:
        """Fetch transactions from the portfolio-tracker API"""
        if not self.api_base_url:
            logging.warning("No API URL configured")
            return []

        try:
            url = f"{self.api_base_url}/api/transactions"
            params = {'portfolioId': self.portfolio_id}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch transactions: {e}")
            return []

    def calculate_holdings_from_transactions(self, transactions: List[Dict], prices: Dict[str, float]) -> List[PortfolioHolding]:
        """Calculate current holdings from transaction history"""
        holdings_map: Dict[str, Dict] = {}

        for tx in transactions:
            asset = tx['asset'].upper()
            tx_type = tx.get('type', 'Buy')
            quantity = float(tx.get('quantity', 0))
            cost_usd = float(tx.get('costUsd', 0) or 0)
            proceeds_usd = float(tx.get('proceedsUsd', 0) or 0)

            if asset not in holdings_map:
                holdings_map[asset] = {'quantity': 0, 'cost_basis': 0}

            if tx_type in ('Buy', 'Deposit'):
                holdings_map[asset]['quantity'] += quantity
                holdings_map[asset]['cost_basis'] += cost_usd
            elif tx_type in ('Sell', 'Withdrawal'):
                # For sells, reduce quantity and proportionally reduce cost basis
                if holdings_map[asset]['quantity'] > 0:
                    ratio = quantity / holdings_map[asset]['quantity']
                    holdings_map[asset]['cost_basis'] -= holdings_map[asset]['cost_basis'] * ratio
                holdings_map[asset]['quantity'] -= quantity

        holdings = []
        for asset, data in holdings_map.items():
            if data['quantity'] <= 0:
                continue

            current_price = prices.get(asset, 0)
            current_value = data['quantity'] * current_price
            cost_basis = data['cost_basis']
            pnl = current_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            holdings.append(PortfolioHolding(
                asset=asset,
                quantity=data['quantity'],
                current_price=current_price,
                current_value=current_value,
                cost_basis=cost_basis,
                pnl=pnl,
                pnl_percent=pnl_percent,
                color=get_asset_color(asset)
            ))

        # Sort by value descending
        holdings.sort(key=lambda h: h.current_value, reverse=True)
        return holdings

    def get_holdings(self, refresh: bool = False) -> List[PortfolioHolding]:
        """
        Get current portfolio holdings.

        Args:
            refresh: If True, fetch fresh data from API. If False, use cached data.
        """
        if self._cached_holdings and not refresh:
            return self._cached_holdings

        if not self.api_base_url:
            return self._cached_holdings or []

        # Try the dedicated ticker API first (if API key is configured)
        if self.api_key:
            data = self.fetch_from_ticker_api()
            if data and 'holdings' in data:
                self._cached_holdings = [
                    PortfolioHolding(
                        asset=h['asset'],
                        quantity=h['quantity'],
                        current_price=h['currentPrice'],
                        current_value=h['currentValue'],
                        cost_basis=h['costBasis'],
                        pnl=h['pnl'],
                        pnl_percent=h['pnlPercent'],
                        color=h['color']
                    )
                    for h in data['holdings']
                ]
                self._cached_btc_price = data.get('summary', {}).get('btcPrice', 0)
                return self._cached_holdings

        # Fallback to transaction-based calculation (requires session auth - won't work externally)
        transactions = self.fetch_transactions()
        if not transactions:
            return self._cached_holdings or []

        # Get unique assets
        assets = list(set(tx['asset'].upper() for tx in transactions))

        # Fetch prices
        prices = self.fetch_current_prices(assets)

        # Calculate holdings
        self._cached_holdings = self.calculate_holdings_from_transactions(transactions, prices)
        return self._cached_holdings

    def get_portfolio_summary(self, refresh: bool = False) -> PortfolioSummary:
        """Get a summary of the portfolio"""
        holdings = self.get_holdings(refresh)

        total_value = sum(h.current_value for h in holdings)
        total_cost = sum(h.cost_basis for h in holdings)
        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        return PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            holdings=holdings
        )

    def get_btc_price(self) -> float:
        """Get the cached BTC price from the last API call"""
        return self._cached_btc_price

    def get_allocation_data(self, refresh: bool = False) -> List[Tuple[str, float, str]]:
        """
        Get allocation data for pie chart.

        Returns:
            List of tuples: (asset_name, value_usd, color)
        """
        # Try ticker API first for fresh data
        if refresh and self.api_key and self.api_base_url:
            data = self.fetch_from_ticker_api()
            if data and 'allocation' in data:
                self._cached_btc_price = data.get('summary', {}).get('btcPrice', 0)
                return [
                    (a['asset'], a['value'], a['color'])
                    for a in data['allocation']
                ]

        # Fallback to holdings-based calculation
        holdings = self.get_holdings(refresh)
        return [(h.asset, h.current_value, h.color) for h in holdings if h.current_value > 0]

    def get_pnl_data(self, refresh: bool = False) -> List[Tuple[str, float, str]]:
        """
        Get P&L data for treemap/heatmap.

        Returns:
            List of tuples: (asset_name, pnl_value, color)
            Color is green for profit, red for loss
        """
        # Try ticker API first for fresh data
        if refresh and self.api_key and self.api_base_url:
            data = self.fetch_from_ticker_api()
            if data and 'pnlData' in data:
                self._cached_btc_price = data.get('summary', {}).get('btcPrice', 0)
                return [
                    (p['asset'], p['pnl'], p['color'])
                    for p in data['pnlData']
                ]

        # Fallback to holdings-based calculation
        holdings = self.get_holdings(refresh)
        result = []
        for h in holdings:
            if h.current_value > 0:  # Only show assets with holdings
                color = EINK_GREEN if h.pnl >= 0 else EINK_RED  # E-ink green/red
                result.append((h.asset, h.pnl, color))

        # Sort by absolute P&L descending
        result.sort(key=lambda x: abs(x[1]), reverse=True)
        return result

    def get_performance_7d_data(self, refresh: bool = False) -> List[Tuple[str, float, float, str]]:
        """
        Get 7-day performance data for treemap/heatmap.

        Returns:
            List of tuples: (asset_name, value_change, percent_change, color)
            Color is green for gains, red for losses
        """
        # Try ticker API first for fresh data
        if refresh and self.api_key and self.api_base_url:
            data = self.fetch_from_ticker_api()
            if data and 'performance7d' in data:
                self._cached_btc_price = data.get('summary', {}).get('btcPrice', 0)
                return [
                    (p['asset'], p['change'], p['changePercent'], p['color'])
                    for p in data['performance7d']
                ]

        # Fallback: return empty list if no API data
        return []
