"""iris.iris_plugins_variable_ingestion.historical_ingestion_plugin
================================================================

Historical data ingestion plugin for Pulse IRIS.

Fetches real historical data for known variables (FRED, Yahoo Finance) and
generates synthetic historical data for others. Returns a time-ordered list
of signal lists, where each inner list contains signals for a specific date.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
from typing import List, Dict, Any, Optional, Callable
import time # Added for rate limiting

import requests
import yfinance as yf
from fredapi import Fred
import pandas as pd
import numpy as np # Added for synthetic data generation
from pandas import DatetimeIndex

from core.variable_registry import registry
# from simulation_engine.worldstate import WorldState # Not needed in plugin
# from core.variable_accessor import set_variable # Not needed in plugin
# from simulation_engine.utils.worldstate_io import save_worldstate_to_file # Not needed in plugin

logger = logging.getLogger(__name__)

# Configuration
RETRODICTION_TIMELINE_YEARS = 5
# SNAPSHOTS_DIR = "snapshots" # Not needed in plugin
HISTORY_SNAPSHOT_PREFIX = "turn_history_"

# Initialize FRED and Yahoo Finance clients
FRED_KEY = os.getenv("FRED_API_KEY", "")
_FRED = Fred(api_key=FRED_KEY) if FRED_KEY else None

# Mapping of Pulse variable names to external data identifiers and transformations
EXTERNAL_DATA_MAP: Dict[str, Dict[str, Any]] = {
    # FRED (Economic/Financial)
    "us_10y_yield": {"source": "FRED", "id": "DGS10", "transform": lambda x: x / 100}, # FRED returns percent
    "cpi_yoy": {"source": "FRED", "id": "CPIAUCSL", "transform": lambda x: x},
    "gdp_growth_annual": {"source": "FRED", "id": "A191RL1Q225SBEA", "transform": lambda x: x}, # Real Gross Domestic Product, Percent Change from Preceding Period, Annual
    "unemployment_rate_fred": {"source": "FRED", "id": "UNRATE", "transform": lambda x: x / 100}, # Unemployment Rate
    "ppi_final_demand": {"source": "FRED", "id": "PPIACO", "transform": lambda x: x}, # Producer Price Index: Final Demand
    "retail_sales_total": {"source": "FRED", "id": "RSXFS", "transform": lambda x: x}, # Retail Sales: Total
    "industrial_production_index": {"source": "FRED", "id": "INDPRO", "transform": lambda x: x}, # Industrial Production Index
    "housing_starts_total": {"source": "FRED", "id": "HOUST", "transform": lambda x: x}, # Housing Starts: Total
    "consumer_sentiment_umich": {"source": "FRED", "id": "UMCSENT", "transform": lambda x: x}, # Consumer Sentiment Index
    "trade_balance_goods_services": {"source": "FRED", "id": "BOPGSTB", "transform": lambda x: x}, # Balance on Goods and Services
    "federal_debt_total": {"source": "FRED", "id": "GFDEBTN", "transform": lambda x: x}, # Federal Debt: Total Public Debt
    "corporate_profits_after_tax": {"source": "FRED", "id": "CP", "transform": lambda x: x}, # Corporate Profits After Tax (without IVA and CCAdj)
    "us_eff_fed_funds_rate": {"source": "FRED", "id": "EFFR", "transform": lambda x: x / 100}, # Effective Federal Funds Rate
    "us_prime_loan_rate": {"source": "FRED", "id": "MPRIME", "transform": lambda x: x / 100}, # Bank Prime Loan Rate
    "us_treasury_yield_1y": {"source": "FRED", "id": "DGS1", "transform": lambda x: x / 100}, # Market Yield on U.S. Treasury Securities at 1-Year Constant Maturity
    "us_treasury_yield_5y": {"source": "FRED", "id": "DGS5", "transform": lambda x: x / 100}, # Market Yield on U.S. Treasury Securities at 5-Year Constant Maturity
    "us_treasury_yield_30y": {"source": "FRED", "id": "DGS30", "transform": lambda x: x / 100}, # Market Yield on U.S. Treasury Securities at 30-Year Constant Maturity
    "monetary_base_total": {"source": "FRED", "id": "BOGMBASE", "transform": lambda x: x}, # Monetary Base; Total
    "velocity_m2_money_stock": {"source": "FRED", "id": "M2V", "transform": lambda x: x}, # Velocity of M2 Money Stock
    "exchange_rate_usd_eur": {"source": "FRED", "id": "DEXUSEU", "transform": lambda x: x}, # U.S. Dollars to One Euro Spot Exchange Rate
    "wti_crude_oil_price": {"source": "FRED", "id": "WTISPLC", "transform": lambda x: x}, # West Texas Intermediate (WTI) Crude Oil Price
    "brent_crude_oil_price": {"source": "FRED", "id": "DCOILBRENTEU", "transform": lambda x: x}, # Brent Crude Oil Price
    
    
    "copper_price": {"source": "FRED", "id": "PCOPPUSDM", "transform": lambda x: x}, # Copper Prices
    
    "vix_close_fred": {"source": "FRED", "id": "VIXCLS", "transform": lambda x: x}, # VIX Close (redundant with YF, but good to have FRED option)
    "consumer_credit_outstanding": {"source": "FRED", "id": "TOTALSL", "transform": lambda x: x}, # Total Consumer Credit Outstanding
    "commercial_industrial_loans": {"source": "FRED", "id": "BUSLOANS", "transform": lambda x: x}, # Commercial and Industrial Loans, All Commercial Banks
    "housing_price_index_case_shiller": {"source": "FRED", "id": "CSUSHPINSA", "transform": lambda x: x}, # S&P/Case-Shiller U.S. National Home Price Index
    "new_single_family_houses_sold": {"source": "FRED", "id": "MSPNHSUS", "transform": lambda x: x}, # Median Sales Price of New Houses Sold in the U.S.
    "personal_consumption_expenditures": {"source": "FRED", "id": "PCE", "transform": lambda x: x}, # Personal Consumption Expenditures
    "durable_goods_orders": {"source": "FRED", "id": "DGORDER", "transform": lambda x: x}, # Manufacturers' New Orders: Durable Goods
    "nonfarm_business_labor_productivity": {"source": "FRED", "id": "PRS85006091", "transform": lambda x: x}, # Nonfarm Business Sector: Labor Productivity
    "average_hourly_earnings": {"source": "FRED", "id": "CES0500000003", "transform": lambda x: x}, # Average Hourly Earnings of All Employees, Total Private
    "employment_population_ratio": {"source": "FRED", "id": "EMRATIO", "transform": lambda x: x / 100}, # Employment-Population Ratio
    "participation_rate": {"source": "FRED", "id": "CIVPART", "transform": lambda x: x / 100}, # Labor Force Participation Rate
    "initial_unemployment_claims": {"source": "FRED", "id": "ICSA", "transform": lambda x: x}, # Initial Claims
    "continuing_unemployment_claims": {"source": "FRED", "id": "CCSA", "transform": lambda x: x}, # Continued Claims
    "industrial_capacity_utilization": {"source": "FRED", "id": "TCU", "transform": lambda x: x}, # Capacity Utilization: Total Industry
    "manufacturing_capacity_utilization": {"source": "FRED", "id": "CUMFNS", "transform": lambda x: x}, # Capacity Utilization: Manufacturing
    
    
    
    "leading_economic_index": {"source": "FRED", "id": "USSLIND", "transform": lambda x: x}, # Leading Index for the United States
    "consumer_price_index_urban": {"source": "FRED", "id": "CPIAUCNS", "transform": lambda x: x}, # Consumer Price Index for All Urban Consumers: All Items
    "personal_consumption_expenditures_price_index": {"source": "FRED", "id": "PCEPI", "transform": lambda x: x}, # Personal Consumption Expenditures Price Index
    "gross_private_domestic_investment": {"source": "FRED", "id": "GPDI", "transform": lambda x: x}, # Gross Private Domestic Investment
    "net_exports_goods_services": {"source": "FRED", "id": "NETEXP", "transform": lambda x: x}, # Net Exports of Goods and Services
    "government_consumption_investment": {"source": "FRED", "id": "GCE", "transform": lambda x: x}, # Government Consumption Expenditures and Gross Investment
    "corporate_bond_yield_baa": {"source": "FRED", "id": "BAMLC0A4CBBB", "transform": lambda x: x / 100}, # Moody's Seasoned Baa Corporate Bond Yield
    
    
    "treasury_bill_rate_3m": {"source": "FRED", "id": "DTB3", "transform": lambda x: x / 100}, # Market Yield on U.S. Treasury Securities at 3-Month Constant Maturity
    "effective_federal_funds_rate_upper_bound": {"source": "FRED", "id": "DFEDTARU", "transform": lambda x: x / 100}, # Federal Funds Effective Rate: Upper Bound
    "effective_federal_funds_rate_lower_bound": {"source": "FRED", "id": "DFEDTARL", "transform": lambda x: x / 100}, # Federal Funds Effective Rate: Lower Bound
    "reserve_balances_with_federal_reserve_banks": {"source": "FRED", "id": "RESBALNS", "transform": lambda x: x}, # Reserve Balances with Federal Reserve Banks
    "total_assets_of_federal_reserve": {"source": "FRED", "id": "WALCL", "transform": lambda x: x}, # Total Assets, All Federal Reserve Banks
    
    "consumer_price_index_energy": {"source": "FRED", "id": "CPIENGSL", "transform": lambda x: x}, # Consumer Price Index for All Urban Consumers: Energy
    "consumer_price_index_food": {"source": "FRED", "id": "CPIAPPSL", "transform": lambda x: x}, # Consumer Price Index for All Urban Consumers: Food
    "real_disposable_personal_income": {"source": "FRED", "id": "DSPIC96", "transform": lambda x: x}, # Real Disposable Personal Income
    "personal_saving_rate": {"source": "FRED", "id": "PSAVERT", "transform": lambda x: x / 100}, # Personal Saving Rate
    "net_worth_of_households": {"source": "FRED", "id": "TNWBSHNO", "transform": lambda x: x}, # Net Worth of Households and Non-Profit Organizations
    "total_nonfarm_payroll": {"source": "FRED", "id": "PAYEMS", "transform": lambda x: x}, # Total Nonfarm Payrolls
    
    "new_orders_nondefense_capital_goods": {"source": "FRED", "id": "NEWORDER", "transform": lambda x: x}, # Manufacturers' New Orders: Nondefense Capital Goods Excluding Aircraft
    
    
    
    "housing_permits_total": {"source": "FRED", "id": "PERMIT", "transform": lambda x: x}, # New Private Housing Units Authorized by Building Permits: Total
    # Yahoo Finance (Market/Sector/Assets)
    "spx_close": {"source": "YahooFinance", "id": "^GSPC", "transform": lambda x: x},
    "vix_close": {"source": "YahooFinance", "id": "^VIX", "transform": lambda x: x},
    "djia_close": {"source": "YahooFinance", "id": "^DJI", "transform": lambda x: x}, # Dow Jones Industrial Average
    "nasdaq_composite_close": {"source": "YahooFinance", "id": "^IXIC", "transform": lambda x: x}, # NASDAQ Composite
    "russell_2000_close": {"source": "YahooFinance", "id": "^RUT", "transform": lambda x: x}, # Russell 2000
    "ftse_100_close": {"source": "YahooFinance", "id": "^FTSE", "transform": lambda x: x}, # FTSE 100
    "dax_performance_close": {"source": "YahooFinance", "id": "^GDAXI", "transform": lambda x: x}, # DAX PERFORMANCE-INDEX
    "nikkei_225_close": {"source": "YahooFinance", "id": "^N225", "transform": lambda x: x}, # Nikkei 225
    "hang_seng_index_close": {"source": "YahooFinance", "id": "^HSI", "transform": lambda x: x}, # HANG SENG INDEX
    "shanghai_composite_close": {"source": "YahooFinance", "id": "000001.SS", "transform": lambda x: x}, # Shanghai Composite Index
    "sp_tsx_composite_close": {"source": "YahooFinance", "id": "^GSPTSE", "transform": lambda x: x}, # S&P/TSX Composite Index
    "all_ordinaries_close": {"source": "YahooFinance", "id": "^AORD", "transform": lambda x: x}, # ALL ORDINARIES
    "ipc_mexico_close": {"source": "YahooFinance", "id": "^MXX", "transform": lambda x: x}, # IPC MEXICO
    "ibovespa_brazil_close": {"source": "YahooFinance", "id": "^BVSP", "transform": lambda x: x}, # Bovespa Index
    "cac_40_close": {"source": "YahooFinance", "id": "^FCHI", "transform": lambda x: x}, # CAC 40
    "euro_stoxx_50_close": {"source": "YahooFinance", "id": "^STOXX50E", "transform": lambda x: x}, # ESTX 50 PR.SE.
    "swiss_market_index_close": {"source": "YahooFinance", "id": "^SSMI", "transform": lambda x: x}, # Swiss Market Index
    "s_p_asx_200_close": {"source": "YahooFinance", "id": "^AXJO", "transform": lambda x: x}, # S&P/ASX 200
    "korea_composite_stock_price_index_close": {"source": "YahooFinance", "id": "^KS11", "transform": lambda x: x}, # KOSPI Composite Index
    "nifty_50_close": {"source": "YahooFinance", "id": "^NSEI", "transform": lambda x: x}, # Nifty 50
    "sensex_india_close": {"source": "YahooFinance", "id": "^BSESN", "transform": lambda x: x}, # S&P BSE SENSEX
    "bse_100_india_close": {"source": "YahooFinance", "id": "^BSE100", "transform": lambda x: x}, # BSE 100
    "crypto_bitcoin_usd": {"source": "YahooFinance", "id": "BTC-USD", "transform": lambda x: x}, # Bitcoin USD
    "crypto_ethereum_usd": {"source": "YahooFinance", "id": "ETH-USD", "transform": lambda x: x}, # Ethereum USD
    "crypto_ripple_usd": {"source": "YahooFinance", "id": "XRP-USD", "transform": lambda x: x}, # Ripple USD
    "crypto_litecoin_usd": {"source": "YahooFinance", "id": "LTC-USD", "transform": lambda x: x}, # Litecoin USD
    "crypto_cardano_usd": {"source": "YahooFinance", "id": "ADA-USD", "transform": lambda x: x}, # Cardano USD
    "crypto_polkadot_usd": {"source": "YahooFinance", "id": "DOT-USD", "transform": lambda x: x}, # Polkadot USD
    "crypto_solana_usd": {"source": "YahooFinance", "id": "SOL-USD", "transform": lambda x: x}, # Solana USD
    "crypto_dogecoin_usd": {"source": "YahooFinance", "id": "DOGE-USD", "transform": lambda x: x}, # Dogecoin USD
    "crypto_shiba_inu_usd": {"source": "YahooFinance", "id": "SHIB-USD", "transform": lambda x: x}, # Shiba Inu USD
    "crypto_wrapped_bitcoin_usd": {"source": "YahooFinance", "id": "WBTC-USD", "transform": lambda x: x}, # Wrapped Bitcoin USD
    "gold_futures": {"source": "YahooFinance", "id": "GC=F", "transform": lambda x: x}, # Gold Futures
    "silver_futures": {"source": "YahooFinance", "id": "SI=F", "transform": lambda x: x}, # Silver Futures
    "copper_futures": {"source": "YahooFinance", "id": "HG=F", "transform": lambda x: x}, # Copper Futures
    "crude_oil_futures_wti": {"source": "YahooFinance", "id": "CL=F", "transform": lambda x: x}, # Crude Oil Futures (WTI)
    "brent_oil_futures": {"source": "YahooFinance", "id": "BZ=F", "transform": lambda x: x}, # Brent Oil Futures
    "natural_gas_futures": {"source": "YahooFinance", "id": "NG=F", "transform": lambda x: x}, # Natural Gas Futures
    "corn_futures": {"source": "YahooFinance", "id": "ZC=F", "transform": lambda x: x}, # Corn Futures
    "wheat_futures": {"source": "YahooFinance", "id": "ZW=F", "transform": lambda x: x}, # Wheat Futures
    "soybean_futures": {"source": "YahooFinance", "id": "ZS=F", "transform": lambda x: x}, # Soybean Futures
    "sugar_futures": {"source": "YahooFinance", "id": "SB=F", "transform": lambda x: x}, # Sugar Futures
    "coffee_futures": {"source": "YahooFinance", "id": "KC=F", "transform": lambda x: x}, # Coffee Futures
    "cocoa_futures": {"source": "YahooFinance", "id": "CC=F", "transform": lambda x: x}, # Cocoa Futures
    "cotton_futures": {"source": "YahooFinance", "id": "CT=F", "transform": lambda x: x}, # Cotton Futures
    "us_dollar_index_futures": {"source": "YahooFinance", "id": "DX=F", "transform": lambda x: x}, # U.S. Dollar Index Futures
    "euro_usd_futures": {"source": "YahooFinance", "id": "EURUSD=X", "transform": lambda x: x}, # EUR/USD Exchange Rate
    "usd_jpy_futures": {"source": "YahooFinance", "id": "JPY=X", "transform": lambda x: x}, # USD/JPY Exchange Rate
    "gbp_usd_futures": {"source": "YahooFinance", "id": "GBPUSD=X", "transform": lambda x: x}, # GBP/USD Exchange Rate
    "aud_usd_futures": {"source": "YahooFinance", "id": "AUDUSD=X", "transform": lambda x: x}, # AUD/USD Exchange Rate
    "usd_cad_futures": {"source": "YahooFinance", "id": "CAD=X", "transform": lambda x: x}, # USD/CAD Exchange Rate
    "usd_chf_futures": {"source": "YahooFinance", "id": "CHF=X", "transform": lambda x: x}, # USD/CHF Exchange Rate
    "nzd_usd_futures": {"source": "YahooFinance", "id": "NZDUSD=X", "transform": lambda x: x}, # NZD/USD Exchange Rate
    "usd_inr_futures": {"source": "YahooFinance", "id": "INR=X", "transform": lambda x: x}, # USD/INR Exchange Rate
    "cny_usd_futures": {"source": "YahooFinance", "id": "CNY=X", "transform": lambda x: x}, # CNY/USD Exchange Rate
    "us_10y_treasury_bond_futures": {"source": "YahooFinance", "id": "ZN=F", "transform": lambda x: x}, # US 10 Year T-Note Futures
    "us_30y_treasury_bond_futures": {"source": "YahooFinance", "id": "ZB=F", "transform": lambda x: x}, # US Long Bond Futures
    "vix_futures": {"source": "YahooFinance", "id": "VX=F", "transform": lambda x: x}, # VIX Futures (redundant with spot, good to have futures option)
    "sp_500_futures": {"source": "YahooFinance", "id": "ES=F", "transform": lambda x: x}, # S&P 500 Futures
    "nasdaq_100_futures": {"source": "YahooFinance", "id": "NQ=F", "transform": lambda x: x}, # NASDAQ 100 Futures
    "dow_jones_futures": {"source": "YahooFinance", "id": "YM=F", "transform": lambda x: x}, # Dow Jones Futures
    "russell_2000_futures": {"source": "YahooFinance", "id": "RTY=F", "transform": lambda x: x}, # Russell 2000 Futures
    "apple_stock": {"source": "YahooFinance", "id": "AAPL", "transform": lambda x: x}, # Apple Inc.
    "microsoft_stock": {"source": "YahooFinance", "id": "MSFT", "transform": lambda x: x}, # Microsoft Corporation
    "google_stock_a": {"source": "YahooFinance", "id": "GOOGL", "transform": lambda x: x}, # Alphabet Inc. (GOOGL)
    "amazon_stock": {"source": "YahooFinance", "id": "AMZN", "transform": lambda x: x}, # Amazon.com, Inc.
    "tesla_stock": {"source": "YahooFinance", "id": "TSLA", "transform": lambda x: x}, # Tesla, Inc.
    "facebook_stock": {"source": "YahooFinance", "id": "META", "transform": lambda x: x}, # Meta Platforms, Inc.
    "nvidia_stock": {"source": "YahooFinance", "id": "NVDA", "transform": lambda x: x}, # NVIDIA Corporation
    "berkshire_hathaway_b_stock": {"source": "YahooFinance", "id": "BRK-B", "transform": lambda x: x}, # Berkshire Hathaway Inc. (BRK-B)
    "jp_morgan_chase_stock": {"source": "YahooFinance", "id": "JPM", "transform": lambda x: x}, # JPMorgan Chase & Co.
    "johnson_johnson_stock": {"source": "YahooFinance", "id": "JNJ", "transform": lambda x: x}, # Johnson & Johnson
    "visa_stock": {"source": "YahooFinance", "id": "V", "transform": lambda x: x}, # Visa Inc.
    "mastercard_stock": {"source": "YahooFinance", "id": "MA", "transform": lambda x: x}, # Mastercard Incorporated
    "unitedhealth_group_stock": {"source": "YahooFinance", "id": "UNH", "transform": lambda x: x}, # UnitedHealth Group Incorporated
    "exxon_mobil_stock": {"source": "YahooFinance", "id": "XOM", "transform": lambda x: x}, # Exxon Mobil Corporation
    "chevron_stock": {"source": "YahooFinance", "id": "CVX", "transform": lambda x: x}, # Chevron Corporation
    "pfizer_stock": {"source": "YahooFinance", "id": "PFE", "transform": lambda x: x}, # Pfizer Inc.
    "merck_stock": {"source": "YahooFinance", "id": "MRK", "transform": lambda x: x}, # Merck & Co., Inc.
    "walmart_stock": {"source": "YahooFinance", "id": "WMT", "transform": lambda x: x}, # Walmart Inc.
    "home_depot_stock": {"source": "YahooFinance", "id": "HD", "transform": lambda x: x}, # The Home Depot, Inc.
    "mcdonalds_stock": {"source": "YahooFinance", "id": "MCD", "transform": lambda x: x}, # McDonald's Corporation
    "cocacola_stock": {"source": "YahooFinance", "id": "KO", "transform": lambda x: x}, # The Coca-Cola Company
    "pepsico_stock": {"source": "YahooFinance", "id": "PEP", "transform": lambda x: x}, # PepsiCo, Inc.
    "tech_sector_etf": {"source": "YahooFinance", "id": "XLK", "transform": lambda x: x}, # Technology Select Sector SPDR Fund
    "health_sector_etf": {"source": "YahooFinance", "id": "XLV", "transform": lambda x: x}, # Health Care Select Sector SPDR Fund
    "energy_sector_etf": {"source": "YahooFinance", "id": "XLE", "transform": lambda x: x}, # Energy Select Sector SPDR Fund
    "financial_sector_etf": {"source": "YahooFinance", "id": "XLF", "transform": lambda x: x}, # Financial Select Sector SPDR Fund
    "consumer_discretionary_sector_etf": {"source": "YahooFinance", "id": "XLY", "transform": lambda x: x}, # Consumer Discretionary Select Sector SPDR Fund
    "consumer_staples_sector_etf": {"source": "YahooFinance", "id": "XLP", "transform": lambda x: x}, # Consumer Staples Select Sector SPDR Fund
    "industrials_sector_etf": {"source": "YahooFinance", "id": "XLI", "transform": lambda x: x}, # Industrial Select Sector SPDR Fund
    "materials_sector_etf": {"source": "YahooFinance", "id": "XLB", "transform": lambda x: x}, # Materials Select Sector SPDR Fund
    "real_estate_sector_etf": {"source": "YahooFinance", "id": "XLRE", "transform": lambda x: x}, # Real Estate Select Sector SPDR Fund
    "utilities_sector_etf": {"source": "YahooFinance", "id": "XLU", "transform": lambda x: x}, # Utilities Select Sector SPDR Fund
    "communication_services_sector_etf": {"source": "YahooFinance", "id": "XLC", "transform": lambda x: x}, # Communication Services Select Sector SPDR Fund
    "vanguard_total_stock_market_etf": {"source": "YahooFinance", "id": "VTI", "transform": lambda x: x}, # Vanguard Total Stock Market ETF
    "vanguard_sp_500_etf": {"source": "YahooFinance", "id": "VOO", "transform": lambda x: x}, # Vanguard S&P 500 ETF
    "ishares_core_us_aggregate_bond_etf": {"source": "YahooFinance", "id": "AGG", "transform": lambda x: x}, # iShares Core U.S. Aggregate Bond ETF
    "vanguard_total_bond_market_etf": {"source": "YahooFinance", "id": "BND", "transform": lambda x: x}, # Vanguard Total Bond Market ETF
    "ishares_jpmorgan_usd_emerging_markets_bond_etf": {"source": "YahooFinance", "id": "EMB", "transform": lambda x: x}, # iShares J.P. Morgan USD Emerging Markets Bond ETF
    "ishares_iboxx_usd_investment_grade_corporate_bond_etf": {"source": "YahooFinance", "id": "LQD", "transform": lambda x: x}, # iShares iBoxx $ Investment Grade Corporate Bond ETF
    "ishares_iboxx_usd_high_yield_corporate_bond_etf": {"source": "YahooFinance", "id": "HYG", "transform": lambda x: x}, # iShares iBoxx $ High Yield Corporate Bond ETF
    "spdr_gold_shares": {"source": "YahooFinance", "id": "GLD", "transform": lambda x: x}, # SPDR Gold Shares
    "ishares_silver_trust": {"source": "YahooFinance", "id": "SLV", "transform": lambda x: x}, # iShares Silver Trust
    "united_states_oil_fund": {"source": "YahooFinance", "id": "USO", "transform": lambda x: x}, # United States Oil Fund
    "united_states_gasoline_fund": {"source": "YahooFinance", "id": "UGA", "transform": lambda x: x}, # United States Gasoline Fund
    "united_states_natural_gas_fund": {"source": "YahooFinance", "id": "UNG", "transform": lambda x: x}, # United States Natural Gas Fund
    "invesco_db_agriculture_fund": {"source": "YahooFinance", "id": "DBA", "transform": lambda x: x}, # Invesco DB Agriculture Fund
    "invesco_db_energy_fund": {"source": "YahooFinance", "id": "DBE", "transform": lambda x: x}, # Invesco DB Energy Fund
    "invesco_db_gold_fund": {"source": "YahooFinance", "id": "DGL", "transform": lambda x: x}, # Invesco DB Gold Fund
    "invesco_db_silver_fund": {"source": "YahooFinance", "id": "DBS", "transform": lambda x: x}, # Invesco DB Silver Fund
    "invesco_db_us_dollar_index_bullish": {"source": "YahooFinance", "id": "UUP", "transform": lambda x: x}, # Invesco DB US Dollar Index Bullish
    "invesco_db_us_dollar_index_bearish": {"source": "YahooFinance", "id": "UDN", "transform": lambda x: x}, # Invesco DB US Dollar Index Bearish
}

def fetch_historical_fred_series(series_id: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.Series | None:
    """Fetches historical data for a FRED series."""
    if _FRED is None:
        logger.warning("FRED_KEY not set. Cannot fetch FRED data.")
        return None
    try:
        # FRED get_series end date is inclusive
        data = _FRED.get_series(series_id, start_date, end_date)
        if data is not None:
            # Localize the index to UTC to match timeline_dates_index
            data.index = pd.to_datetime(data.index).tz_localize('UTC')
        return data.dropna() if data is not None else None
    except requests.exceptions.RequestException as e:
        # Catch specific request exceptions for better error handling
        error_message = f"Request error fetching FRED series {series_id}: {e}"
        if e.response is not None:
            error_message += f" Status Code: {e.response.status_code}, Response Body: {e.response.text}"
        logger.error(error_message)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching FRED series {series_id}: {e}")
        return None

def fetch_historical_yfinance_close(ticker: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.Series | None:
    """Fetches historical closing prices for a Yahoo Finance ticker."""
    try:
        # yfinance download end date is exclusive, so add a day
        data = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=(end_date + dt.timedelta(days=1)).strftime("%Y-%m-%d"), progress=False)
        if data is None or "Close" not in data:
            return None
        return data["Close"].dropna()
    except Exception as e:
        logger.error(f"Error fetching Yahoo Finance ticker {ticker}: {e}")
        return None

def generate_synthetic_historical_data(variable_name: str, timeline_dates: list[dt.datetime]) -> dict[dt.datetime, float]:
    """Generates synthetic historical data for a variable."""
    var_meta = registry.get(variable_name)
    # Handle case where var_meta is None
    default_value = var_meta.get("default", 0.5) if var_meta else 0.5
    # Generate synthetic data: start at default, add some random walk
    data = {}
    current_value = default_value
    for date in timeline_dates:
        # Simple random walk with a small step
        noise = np.random.normal(0, 0.01) # Mean 0, std dev 0.01
        current_value += noise
        # Optional: add some bounds based on variable registry range
        if var_meta and "range" in var_meta: # Check if var_meta is not None before accessing "range"
            min_val, max_val = var_meta["range"]
            current_value = max(min_val, min(max_val, current_value))
        data[date] = current_value
    return data


def historical_ingestion_plugin() -> List[List[Dict[str, Any]]]:
    """
    Iris plugin entry point for historical data ingestion.

    Returns a list of lists of signals, ordered by date.
    """
    logger.info("Running historical_ingestion_plugin...")

    end_date = dt.datetime.now(dt.timezone.utc)
    start_date = end_date - dt.timedelta(days=RETRODICTION_TIMELINE_YEARS * 365) # Approximate years

    # Generate a list of dates for the timeline (daily)
    # Generate a pandas DatetimeIndex for the timeline (daily) and make it timezone-aware (UTC)
    timeline_dates_index = pd.date_range(start=start_date, end=end_date, freq='D', tz=dt.timezone.utc)

    historical_data: dict[str, dict[dt.datetime, float]] = {}

    # Fetch real historical data
    for var_name, data_info in EXTERNAL_DATA_MAP.items():
        if data_info["source"] == "FRED":
            series_data = fetch_historical_fred_series(data_info["id"], start_date, end_date)
            if series_data is not None:
                # Align FRED data to our timeline dates (forward fill)
                aligned_data = series_data.reindex(timeline_dates_index, method='ffill')
                # Ensure keys are datetime objects
                # Iterate over the index of the aligned data to avoid KeyErrors
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and convert to dictionary, ensuring datetime keys
                # Apply transform during dictionary creation
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Iterate over the index of the filtered data and get values from the original aligned_data
                # Filter out NaN values
                filtered_aligned_data = aligned_data[pd.notna(aligned_data)]
                # Create the dictionary from filtered items, ensuring datetime keys and applying transform
                # Create the dictionary from filtered items, ensuring datetime keys and applying transform
                # Create the dictionary from filtered data, ensuring datetime keys and applying transform
                historical_data[var_name] = {date.to_pydatetime(): data_info["transform"](filtered_aligned_data.loc[date]) for date in filtered_aligned_data.index}
        # Add a small delay to avoid hitting FRED API rate limits
            time.sleep(0.5) # Increased delay to 500ms to avoid rate limits
        elif data_info["source"] == "YahooFinance":
            ticker_data = fetch_historical_yfinance_close(data_info["id"], start_date, end_date)
            if ticker_data is not None:
                 # Align Yahoo Finance data to our timeline dates (forward fill)
                # Align Yahoo Finance data to our timeline dates (forward fill)
                # Align Yahoo Finance data to our timeline dates (forward fill)
                # Get the index and ensure it's timezone-aware (UTC)
                # Ensure ticker_data index is a timezone-aware (UTC) DatetimeIndex
                ticker_data.index = pd.to_datetime(ticker_data.index, utc=True)

                # Reindex ticker_data using the timezone-aware timeline_dates_index
                aligned_data = ticker_data.reindex(timeline_dates_index, method='ffill')
                # Ensure keys are datetime objects
                # Iterate over the index of the aligned data to avoid KeyErrors
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Filter out NaN values and convert to dictionary, ensuring datetime keys
                # Apply transform during dictionary creation
                # Filter out NaN values and create the dictionary, ensuring datetime keys
                # Iterate over the index of the filtered data and get values from the original aligned_data
                # Filter out NaN values
                filtered_aligned_data = aligned_data[pd.notna(aligned_data)]
                # Create the dictionary from filtered items, ensuring datetime keys and applying transform
                # Create the dictionary from filtered items, ensuring datetime keys and applying transform
                # Create the dictionary from filtered data, ensuring datetime keys and applying transform
                historical_data[var_name] = {date.to_pydatetime(): data_info["transform"](filtered_aligned_data.loc[date]) for date in filtered_aligned_data.index}

    # Generate synthetic historical data for other variables
    all_variables = registry.all()
    variables_with_external_data = set(EXTERNAL_DATA_MAP.keys())
    variables_for_synthetic_data = [var for var in all_variables if var not in variables_with_external_data]

    for var_name in variables_for_synthetic_data:
         # Pass the original list of naive datetime objects to generate_synthetic_historical_data
         historical_data[var_name] = generate_synthetic_historical_data(var_name, [date.replace(tzinfo=None) for date in timeline_dates_index])

    # Structure the data as a list of lists of signals per date
    historical_signals_timeline: List[List[Dict[str, Any]]] = []
    for current_date in timeline_dates_index:
        signals_for_date: List[Dict[str, Any]] = []
        for var_name in all_variables:
            var_meta = registry.get(var_name) # Get var_meta here
            # Use the historical data for this date, fall back to default if data is missing
            # Use the historical data for this date. If data is missing, the value will be None.
            value = historical_data.get(var_name, {}).get(current_date)
            signal = {
                "name": var_name,
                "value": value,
                "source": "historical_ingestion_plugin", # Indicate source
                "timestamp": current_date.isoformat(),
                "meta": {"description": f"Historical data for {var_name} on {current_date.date()}"}
            }
            signals_for_date.append(signal)
        historical_signals_timeline.append(signals_for_date)

    logger.info(f"Generated historical signals for {len(historical_signals_timeline)} dates.")
    return historical_signals_timeline

if __name__ == "__main__":
    # Example of how to run the plugin and process the output
    historical_data_by_date = historical_ingestion_plugin()
    print(f"Plugin returned data for {len(historical_data_by_date)} dates.")
    # Example: print signals for the first date
    if historical_data_by_date:
        print("Signals for the first date:")
        # Convert timestamp back to timezone-naive for printing if needed, or handle timezone in display
        for signal in historical_data_by_date[0]:
            print(f"  {signal['name']}: {signal['value']} ({signal['timestamp']})")

    # To create snapshots, you would iterate through historical_data_by_date,
    # create a WorldState for each date, and save it. This part will be
    # handled by adapting ingest_to_snapshots.py or a new script.