"""
variable_registry.py

Unified Variable Intelligence Layer
Combines static definition registry with dynamic runtime wrapper for search, ranking, tagging,
and trust/fragility performance tracking.

Pulse Version: v0.28
"""

from __future__ import annotations


import json
import os
from typing import Dict, Any, Tuple, Set, List, Optional, Callable
from core.path_registry import PATHS
from contextlib import suppress

# === Canonical Static Variable Dictionary ===
VARIABLE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Economic variables (backed by FRED)
    "us_10y_yield": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.10],
        "description": "US 10-Year Treasury Yield (FRED: DGS10)",
    },
    "cpi_yoy": {
        "type": "economic",
        "default": 0.03,
        "range": [0.00, 0.15],
        "description": "Consumer Price Index, Year-over-Year (FRED: CPIAUCSL)",
    },
    "gdp_growth_annual": {
        "type": "economic",
        "default": 0.02,
        "range": [-0.10, 0.10],
        "description": "Real Gross Domestic Product, Percent Change from Preceding Period, Annual (FRED: A191RL1Q225SBEA)",
    },
    "unemployment_rate_fred": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.25],
        "description": "Unemployment Rate (FRED: UNRATE)",
    },
    "ppi_final_demand": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 200.0],
        "description": "Producer Price Index: Final Demand (FRED: PPIACO)",
    },
    "retail_sales_total": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 200.0],
        "description": "Retail Sales: Total (FRED: RSXFS)",
    },
    "industrial_production_index": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Industrial Production Index (FRED: INDPRO)",
    },
    "housing_starts_total": {
        "type": "economic",
        "default": 1500.0,
        "range": [500.0, 3000.0],
        "description": "Housing Starts: Total (FRED: HOUST)",
    },
    "consumer_sentiment_umich": {
        "type": "economic",
        "default": 80.0,
        "range": [40.0, 120.0],
        "description": "Consumer Sentiment Index (FRED: UMCSENT)",
    },
    "trade_balance_goods_services": {
        "type": "economic",
        "default": -50.0,
        "range": [-100.0, 50.0],
        "description": "Balance on Goods and Services (FRED: BOPGSTB)",
    },
    "federal_debt_total": {
        "type": "economic",
        "default": 30000.0,
        "range": [10000.0, 50000.0],
        "description": "Federal Debt: Total Public Debt (FRED: GFDEBTN)",
    },
    "corporate_profits_after_tax": {
        "type": "economic",
        "default": 2000.0,
        "range": [1000.0, 4000.0],
        "description": "Corporate Profits After Tax (without IVA and CCAdj) (FRED: CP)",
    },
    "us_eff_fed_funds_rate": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.10],
        "description": "Effective Federal Funds Rate (FRED: EFFR)",
    },
    "us_prime_loan_rate": {
        "type": "economic",
        "default": 0.08,
        "range": [0.03, 0.15],
        "description": "Bank Prime Loan Rate (FRED: MPRIME)",
    },
    "us_treasury_yield_1y": {
        "type": "economic",
        "default": 0.04,
        "range": [0.00, 0.08],
        "description": "Market Yield on U.S. Treasury Securities at 1-Year Constant Maturity (FRED: DGS1)",
    },
    "us_treasury_yield_5y": {
        "type": "economic",
        "default": 0.045,
        "range": [0.00, 0.09],
        "description": "Market Yield on U.S. Treasury Securities at 5-Year Constant Maturity (FRED: DGS5)",
    },
    "us_treasury_yield_30y": {
        "type": "economic",
        "default": 0.048,
        "range": [0.01, 0.10],
        "description": "Market Yield on U.S. Treasury Securities at 30-Year Constant Maturity (FRED: DGS30)",
    },
    "monetary_base_total": {
        "type": "economic",
        "default": 5000.0,
        "range": [1000.0, 10000.0],
        "description": "Monetary Base; Total (FRED: BOGMBASE)",
    },
    "velocity_m2_money_stock": {
        "type": "economic",
        "default": 1.2,
        "range": [0.8, 2.0],
        "description": "Velocity of M2 Money Stock (FRED: M2V)",
    },
    "exchange_rate_usd_eur": {
        "type": "economic",
        "default": 1.1,
        "range": [0.8, 1.5],
        "description": "U.S. Dollars to One Euro Spot Exchange Rate (FRED: DEXUSEU)",
    },
    "wti_crude_oil_price": {
        "type": "economic",
        "default": 80.0,
        "range": [20.0, 150.0],
        "description": "West Texas Intermediate (WTI) Crude Oil Price (FRED: WTISPLC)",
    },
    "brent_crude_oil_price": {
        "type": "economic",
        "default": 85.0,
        "range": [25.0, 160.0],
        "description": "Brent Crude Oil Price (FRED: DCOILBRENTECM)",
    },
    "gold_price_london_fix": {
        "type": "market",
        "default": 1800.0,
        "range": [1000.0, 3000.0],
        "description": "Gold Price LBM (FRED: GOLDAMGBD228NLBM)",
    },
    "silver_price_london_fix": {
        "type": "market",
        "default": 25.0,
        "range": [10.0, 50.0],
        "description": "Silver Price (FRED: SLVRUSD)",
    },
    "copper_price": {
        "type": "market",
        "default": 4.0,
        "range": [2.0, 6.0],
        "description": "Copper Prices (FRED: PCOPPUSDM)",
    },
    "baltic_dry_index": {
        "type": "market",
        "default": 1500.0,
        "range": [500.0, 5000.0],
        "description": "Baltic Dry Index (FRED: BDIY)",
    },
    "vix_close_fred": {
        "type": "market",
        "default": 20.0,
        "range": [10.0, 80.0],
        "description": "VIX Close (FRED: VIXCLS)",
    },
    "consumer_credit_outstanding": {
        "type": "economic",
        "default": 4000.0,
        "range": [2000.0, 6000.0],
        "description": "Total Consumer Credit Outstanding (FRED: TOTALSL)",
    },
    "commercial_industrial_loans": {
        "type": "economic",
        "default": 3000.0,
        "range": [1000.0, 5000.0],
        "description": "Commercial and Industrial Loans, All Commercial Banks (FRED: BUSLOANS)",
    },
    "housing_price_index_case_shiller": {
        "type": "economic",
        "default": 300.0,
        "range": [150.0, 500.0],
        "description": "S&P/Case-Shiller U.S. National Home Price Index (FRED: CSUSHPINSA)",
    },
    "new_single_family_houses_sold": {
        "type": "economic",
        "default": 400.0,
        "range": [200.0, 800.0],
        "description": "Median Sales Price of New Houses Sold in the U.S. (FRED: MSPNHSUS)",
    },
    "personal_consumption_expenditures": {
        "type": "economic",
        "default": 15000.0,
        "range": [10000.0, 20000.0],
        "description": "Personal Consumption Expenditures (FRED: PCE)",
    },
    "durable_goods_orders": {
        "type": "economic",
        "default": 250.0,
        "range": [150.0, 400.0],
        "description": "Manufacturers' New Orders: Durable Goods (FRED: DGORDER)",
    },
    "nonfarm_business_labor_productivity": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Nonfarm Business Sector: Labor Productivity (FRED: PRS85006091)",
    },
    "average_hourly_earnings": {
        "type": "economic",
        "default": 30.0,
        "range": [20.0, 40.0],
        "description": "Average Hourly Earnings of All Employees, Total Private (FRED: CES0500000003)",
    },
    "employment_population_ratio": {
        "type": "economic",
        "default": 0.60,
        "range": [0.50, 0.70],
        "description": "Employment-Population Ratio (FRED: EMRATIO)",
    },
    "participation_rate": {
        "type": "economic",
        "default": 0.62,
        "range": [0.55, 0.68],
        "description": "Labor Force Participation Rate (FRED: CIVPART)",
    },
    "initial_unemployment_claims": {
        "type": "economic",
        "default": 250.0,
        "range": [150.0, 500.0],
        "description": "Initial Claims (FRED: ICSA)",
    },
    "continuing_unemployment_claims": {
        "type": "economic",
        "default": 1800.0,
        "range": [1000.0, 3000.0],
        "description": "Continued Claims (FRED: CCSA)",
    },
    "industrial_capacity_utilization": {
        "type": "economic",
        "default": 78.0,
        "range": [70.0, 85.0],
        "description": "Capacity Utilization: Total Industry (FRED: TCU)",
    },
    "manufacturing_capacity_utilization": {
        "type": "economic",
        "default": 76.0,
        "range": [68.0, 83.0],
        "description": "Capacity Utilization: Manufacturing (FRED: CUMFNS)",
    },
    "new_orders_manufacturing": {
        "type": "economic",
        "default": 240.0,
        "range": [140.0, 380.0],
        "description": "Manufacturers' New Orders: Durable Goods, Excluding Transportation (FRED: AMDMROPD)",
    },
    "ism_manufacturing_pmi": {
        "type": "economic",
        "default": 50.0,
        "range": [40.0, 60.0],
        "description": "ISM Manufacturing PMI (FRED: NAPM)",
    },
    "ism_services_pmi": {
        "type": "economic",
        "default": 55.0,
        "range": [45.0, 65.0],
        "description": "ISM Services PMI (FRED: NMFCI)",
    },
    "leading_economic_index": {
        "type": "economic",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "Leading Index for the United States (FRED: USSLIND)",
    },
    "consumer_price_index_urban": {
        "type": "economic",
        "default": 300.0,
        "range": [200.0, 400.0],
        "description": "Consumer Price Index for All Urban Consumers: All Items (FRED: CPIAUCNS)",
    },
    "personal_consumption_expenditures_price_index": {
        "type": "economic",
        "default": 120.0,
        "range": [100.0, 150.0],
        "description": "Personal Consumption Expenditures Price Index (FRED: PCEPI)",
    },
    "gross_private_domestic_investment": {
        "type": "economic",
        "default": 4000.0,
        "range": [2000.0, 6000.0],
        "description": "Gross Private Domestic Investment (FRED: GPDI)",
    },
    "net_exports_goods_services": {
        "type": "economic",
        "default": -60.0,
        "range": [-150.0, 0.0],
        "description": "Net Exports of Goods and Services (FRED: NETEXP)",
    },
    "government_consumption_investment": {
        "type": "economic",
        "default": 3500.0,
        "range": [2500.0, 4500.0],
        "description": "Government Consumption Expenditures and Gross Investment (FRED: GCE)",
    },
    "corporate_bond_yield_baa": {
        "type": "market",
        "default": 0.05,
        "range": [0.02, 0.10],
        "description": "Moody's Seasoned Baa Corporate Bond Yield (FRED: BAMLC0A4CBBB)",
    },
    "municipal_bond_yield_aaby": {
        "type": "market",
        "default": 0.03,
        "range": [0.01, 0.06],
        "description": "S&P Municipal Bond Index Yield (FRED: MUNICBD)",
    },
    "commercial_paper_rate_3m": {
        "type": "economic",
        "default": 0.04,
        "range": [0.00, 0.08],
        "description": "Commercial Paper: Tier 1, 3-Month (FRED: CPAL3M)",
    },
    "treasury_bill_rate_3m": {
        "type": "economic",
        "default": 0.045,
        "range": [0.00, 0.07],
        "description": "Market Yield on U.S. Treasury Securities at 3-Month Constant Maturity (FRED: DTB3)",
    },
    "effective_federal_funds_rate_upper_bound": {
        "type": "economic",
        "default": 0.0525,
        "range": [0.00, 0.06],
        "description": "Federal Funds Effective Rate: Upper Bound (FRED: DFEDTARU)",
    },
    "effective_federal_funds_rate_lower_bound": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.0575],
        "description": "Federal Funds Effective Rate: Lower Bound (FRED: DFEDTARL)",
    },
    "reserve_balances_with_federal_reserve_banks": {
        "type": "economic",
        "default": 3000.0,
        "range": [1000.0, 5000.0],
        "description": "Reserve Balances with Federal Reserve Banks (FRED: RESBALNS)",
    },
    "total_assets_of_federal_reserve": {
        "type": "economic",
        "default": 8000.0,
        "range": [4000.0, 10000.0],
        "description": "Total Assets, All Federal Reserve Banks (FRED: WALCL)",
    },
    "consumer_price_index_medical_care": {
        "type": "economic",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Consumer Price Index for All Urban Consumers: Medical Care (FRED: CPIAUCSLMED)",
    },
    "consumer_price_index_energy": {
        "type": "economic",
        "default": 300.0,
        "range": [100.0, 500.0],
        "description": "Consumer Price Index for All Urban Consumers: Energy (FRED: CPIENGSL)",
    },
    "consumer_price_index_food": {
        "type": "economic",
        "default": 300.0,
        "range": [200.0, 400.0],
        "description": "Consumer Price Index for All Urban Consumers: Food (FRED: CPIAPPSL)",
    },
    "real_disposable_personal_income": {
        "type": "economic",
        "default": 15000.0,
        "range": [10000.0, 20000.0],
        "description": "Real Disposable Personal Income (FRED: DSPIC96)",
    },
    "personal_saving_rate": {
        "type": "economic",
        "default": 0.05,
        "range": [0.00, 0.15],
        "description": "Personal Saving Rate (FRED: PSAVERT)",
    },
    "net_worth_of_households": {
        "type": "economic",
        "default": 150000.0,
        "range": [100000.0, 200000.0],
        "description": "Net Worth of Households and Non-Profit Organizations (FRED: TNWBSHNO)",
    },
    "total_nonfarm_payroll": {
        "type": "economic",
        "default": 150000.0,
        "range": [130000.0, 170000.0],
        "description": "Total Nonfarm Payrolls (FRED: PAYEMS)",
    },
    "average_weekly_hours_manufacturing": {
        "type": "economic",
        "default": 40.0,
        "range": [35.0, 45.0],
        "description": "Average Weekly Hours of Production and Nonsupervisory Employees: Manufacturing (FRED: CES3000000007)",
    },
    "new_orders_nondefense_capital_goods": {
        "type": "economic",
        "default": 80.0,
        "range": [50.0, 120.0],
        "description": "Manufacturers' New Orders: Nondefense Capital Goods Excluding Aircraft (FRED: NEWORDER)",
    },
    "shipments_manufacturing": {
        "type": "economic",
        "default": 250.0,
        "range": [150.0, 400.0],
        "description": "Manufacturers' Shipments: Durable Goods, Excluding Transportation (FRED: AMDMUORS)",
    },
    "inventories_manufacturing": {
        "type": "economic",
        "default": 400.0,
        "range": [200.0, 600.0],
        "description": "Manufacturers' Inventories: Durable Goods, Excluding Transportation (FRED: AMDMUIR)",
    },
    "housing_completions_total": {
        "type": "economic",
        "default": 1400.0,
        "range": [400.0, 2800.0],
        "description": "Housing Completions: Total (FRED: COMPUT)",
    },
    "housing_permits_total": {
        "type": "economic",
        "default": 1500.0,
        "range": [500.0, 3000.0],
        "description": "New Private Housing Units Authorized by Building Permits: Total (FRED: PERMIT)",
    },
    "existing_home_sales": {
        "type": "economic",
        "default": 5.0,
        "range": [3.0, 7.0],
        "description": "Existing Home Sales (FRED: EXHOSLUSW)",
    },
    "new_single_family_house_price_index": {
        "type": "economic",
        "default": 400.0,
        "range": [200.0, 600.0],
        "description": "All-Transactions House Price Index for the United States (FRED: ATNHPIUS)",
    },
    "case_shiller_20_city_hpi": {
        "type": "economic",
        "default": 300.0,
        "range": [150.0, 500.0],
        "description": "S&P/Case-Shiller 20-City Composite Home Price Index (FRED: SPCS20RSA)",
    },
    "consumer_confidence_board": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Consumer Confidence Index (FRED: CONCC)",
    },
    "business_confidence_index": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Business Confidence Index (FRED: BCI)",
    },
    "industrial_production_manufacturing": {
        "type": "economic",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "Industrial Production: Manufacturing (FRED: IPMAN)",
    },
    "new_orders_consumer_goods": {
        "type": "economic",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Manufacturers' New Orders: Consumer Goods (FRED: ACOGNO)",
    },
    "shipments_consumer_goods": {
        "type": "economic",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Manufacturers' Shipments: Consumer Goods (FRED: ACOGNS)",
    },
    "inventories_consumer_goods": {
        "type": "economic",
        "default": 800.0,
        "range": [600.0, 1000.0],
        "description": "Manufacturers' Inventories: Consumer Goods (FRED: ACOGNI)",
    },
    "retail_sales_ex_auto": {
        "type": "economic",
        "default": 4000.0,
        "range": [2000.0, 6000.0],
        "description": "Retail Sales: Total Less Motor Vehicle and Parts Dealers (FRED: RSXFSN)",
    },
    "retail_sales_building_material": {
        "type": "economic",
        "default": 400.0,
        "range": [200.0, 600.0],
        "description": "Retail Sales: Building Material and Garden Equipment and Supplies Dealers (FRED: RSFSDBS)",
    },
    "retail_sales_clothing": {
        "type": "economic",
        "default": 200.0,
        "range": [100.0, 300.0],
        "description": "Retail Sales: Clothing and Clothing Accessories Stores (FRED: RSFSDC)",
    },
    "retail_sales_electronics": {
        "type": "economic",
        "default": 150.0,
        "range": [50.0, 250.0],
        "description": "Retail Sales: Electronics and Appliance Stores (FRED: RSFSDE)",
    },
    "retail_sales_food_beverage": {
        "type": "economic",
        "default": 800.0,
        "range": [600.0, 1000.0],
        "description": "Retail Sales: Food and Beverage Stores (FRED: RSFSDFFB)",
    },
    "retail_sales_health_personal_care": {
        "type": "economic",
        "default": 300.0,
        "range": [200.0, 400.0],
        "description": "Retail Sales: Health and Personal Care Stores (FRED: RSFSDHC)",
    },
    "retail_sales_sporting_hobby_book": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Retail Sales: Sporting Goods, Hobby, Book, and Music Stores (FRED: RSFSDSA)",
    },
    "retail_sales_general_merchandise": {
        "type": "economic",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Retail Sales: General Merchandise Stores (FRED: RSFSDGM)",
    },
    "retail_sales_motor_vehicle_parts": {
        "type": "economic",
        "default": 1000.0,
        "range": [600.0, 1400.0],
        "description": "Retail Sales: Motor Vehicle and Parts Dealers (FRED: MRTSSM441)",
    },
    "retail_sales_nonstore": {
        "type": "economic",
        "default": 1000.0,
        "range": [600.0, 1400.0],
        "description": "Retail Sales: Nonstore Retailers (FRED: MRTSSM454)",
    },
    "retail_sales_food_services_drinking": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Food Services and Drinking Places Sales (FRED: MRTSSM722)",
    },
    "housing_inventory_for_sale": {
        "type": "economic",
        "default": 1000.0,
        "range": [500.0, 1500.0],
        "description": "Housing Inventory: For Sale (FRED: MSACSR)",
    },
    "housing_vacancy_rate_rental": {
        "type": "economic",
        "default": 0.07,
        "range": [0.04, 0.10],
        "description": "Rental Vacancy Rate for the United States (FRED: RRVRUSQ156N)",
    },
    "housing_vacancy_rate_homeowner": {
        "type": "economic",
        "default": 0.01,
        "range": [0.005, 0.02],
        "description": "Homeowner Vacancy Rate for the United States (FRED: HOVSVAC)",
    },
    "median_asking_rent_us": {
        "type": "economic",
        "default": 1500.0,
        "range": [1000.0, 2000.0],
        "description": "Median Asking Rent for the United States (FRED: MEDRIPA)",
    },
    "median_asking_sales_price_us": {
        "type": "economic",
        "default": 400000.0,
        "range": [200000.0, 600000.0],
        "description": "Median Asking Sales Price for the United States (FRED: MEDSALESPRICE)",
    },
    "personal_consumption_expenditures_chain_price_index": {
        "type": "economic",
        "default": 120.0,
        "range": [100.0, 150.0],
        "description": "Personal Consumption Expenditures Chain-Type Price Index (FRED: PCECTP)",
    },
    "personal_consumption_expenditures_ex_food_energy_chain_price_index": {
        "type": "economic",
        "default": 120.0,
        "range": [100.0, 150.0],
        "description": "Personal Consumption Expenditures Excluding Food and Energy Chain-Type Price Index (FRED: PCEPILFE)",
    },
    "gross_domestic_product_chain_price_index": {
        "type": "economic",
        "default": 120.0,
        "range": [100.0, 150.0],
        "description": "Gross Domestic Product: Chain-Type Price Index (FRED: GDPCTPI)",
    },
    "producer_price_index_finished_goods": {
        "type": "economic",
        "default": 130.0,
        "range": [80.0, 180.0],
        "description": "Producer Price Index by Commodity: Finished Goods (FRED: WPUSOP3000)",
    },
    "producer_price_index_intermediate_goods": {
        "type": "economic",
        "default": 130.0,
        "range": [80.0, 180.0],
        "description": "Producer Price Index by Commodity: Intermediate Goods (FRED: WPUSOP2000)",
    },
    "producer_price_index_crude_goods": {
        "type": "economic",
        "default": 130.0,
        "range": [80.0, 180.0],
        "description": "Producer Price Index by Commodity: Crude Materials (FRED: WPUSOP1000)",
    },
    "employment_cost_index_total_compensation": {
        "type": "economic",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Employment Cost Index: Total Compensation for All Civilian Workers (FRED: ECIALLCIV)",
    },
    "employment_cost_index_wages_salaries": {
        "type": "economic",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Employment Cost Index: Wages and Salaries for All Civilian Workers (FRED: ECIWAG)",
    },
    "employment_cost_index_benefits": {
        "type": "economic",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Employment Cost Index: Benefits for All Civilian Workers (FRED: ECISTB)",
    },
    "unit_labor_costs_nonfarm_business": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Unit Labor Costs for the Nonfarm Business Sector (FRED: ULCNFB)",
    },
    "nonfarm_business_sector_output_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Output Per Hour of All Persons in the Nonfarm Business Sector (FRED: OPHNFB)",
    },
    "nonfarm_business_sector_compensation_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Compensation Per Hour for the Nonfarm Business Sector (FRED: COMPNFB)",
    },
    "manufacturing_sector_output_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Output Per Hour of All Persons in the Manufacturing Sector (FRED: OPHMFG)",
    },
    "manufacturing_sector_compensation_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Compensation Per Hour for the Manufacturing Sector (FRED: COMPMFG)",
    },
    "manufacturing_sector_unit_labor_costs": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Unit Labor Costs for the Manufacturing Sector (FRED: ULCMFG)",
    },
    "business_sector_output_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Output Per Hour of All Persons in the Business Sector (FRED: OPHBUS)",
    },
    "business_sector_compensation_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Compensation Per Hour for the Business Sector (FRED: COMPBUS)",
    },
    "business_sector_unit_labor_costs": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Unit Labor Costs for the Business Sector (FRED: ULCBUS)",
    },
    "nonfinancial_corporate_business_sector_output_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Output Per Hour of All Persons in the Nonfinancial Corporate Business Sector (FRED: OPHNFCB)",
    },
    "nonfinancial_corporate_business_sector_compensation_per_hour": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Compensation Per Hour for the Nonfinancial Corporate Business Sector (FRED: COMPNFCB)",
    },
    "nonfinancial_corporate_business_sector_unit_labor_costs": {
        "type": "economic",
        "default": 110.0,
        "range": [90.0, 130.0],
        "description": "Unit Labor Costs for the Nonfinancial Corporate Business Sector (FRED: ULCNFCB)",
    },
    "real_gdp_per_capita": {
        "type": "economic",
        "default": 60000.0,
        "range": [40000.0, 80000.0],
        "description": "Real Gross Domestic Product per Capita (FRED: A939RX0Q048SBEA)",
    },
    "gross_national_income": {
        "type": "economic",
        "default": 25000.0,
        "range": [15000.0, 35000.0],
        "description": "Gross National Income (FRED: GNI)",
    },
    "net_national_product": {
        "type": "economic",
        "default": 20000.0,
        "range": [10000.0, 30000.0],
        "description": "Net National Product (FRED: NDP)",
    },
    "national_income_private_industries": {
        "type": "economic",
        "default": 18000.0,
        "range": [10000.0, 26000.0],
        "description": "National Income: Private Industries (FRED: NIPI)",
    },
    "national_income_government": {
        "type": "economic",
        "default": 2000.0,
        "range": [1000.0, 3000.0],
        "description": "National Income: Government (FRED: NIGOV)",
    },
    "personal_income_ex_transfer_payments": {
        "type": "economic",
        "default": 18000.0,
        "range": [10000.0, 26000.0],
        "description": "Personal Income Excluding Transfer Payments (FRED: PIEPT)",
    },
    "disposable_personal_income_per_capita": {
        "type": "economic",
        "default": 50000.0,
        "range": [30000.0, 70000.0],
        "description": "Real Disposable Personal Income per Capita (FRED: A229RX0)",
    },
    "personal_consumption_expenditures_per_capita": {
        "type": "economic",
        "default": 40000.0,
        "range": [20000.0, 60000.0],
        "description": "Real Personal Consumption Expenditures per Capita (FRED: A794RX0Q048SBEA)",
    },
    "gross_private_domestic_investment_residential_structures": {
        "type": "economic",
        "default": 500.0,
        "range": [200.0, 800.0],
        "description": "Private Residential Fixed Investment: Structures (FRED: PRFIS)",
    },
    "gross_private_domestic_investment_residential_equipment": {
        "type": "economic",
        "default": 500.0,
        "range": [200.0, 800.0],
        "description": "Private Residential Fixed Investment: Equipment (FRED: PRFIE)",
    },
    "gross_private_domestic_investment_nonresidential_structures": {
        "type": "economic",
        "default": 1000.0,
        "range": [500.0, 1500.0],
        "description": "Private Nonresidential Fixed Investment: Structures (FRED: PNFIS)",
    },
    "gross_private_domestic_investment_nonresidential_equipment": {
        "type": "economic",
        "default": 1000.0,
        "range": [500.0, 1500.0],
        "description": "Private Nonresidential Fixed Investment: Equipment (FRED: PNFIE)",
    },
    "change_in_private_inventories_farm": {
        "type": "economic",
        "default": 10.0,
        "range": [-20.0, 40.0],
        "description": "Change in Private Inventories: Farm (FRED: VPCCFI)",
    },
    "change_in_private_inventories_nonfarm": {
        "type": "economic",
        "default": 40.0,
        "range": [-80.0, 160.0],
        "description": "Change in Private Inventories: Nonfarm (FRED: VPCCNFI)",
    },
    "exports_goods_industrial_supplies": {
        "type": "economic",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Exports of Goods: Industrial Supplies and Materials (FRED: EXPIN)",
    },
    "exports_goods_capital_goods": {
        "type": "economic",
        "default": 700.0,
        "range": [400.0, 1000.0],
        "description": "Exports of Goods: Capital Goods (FRED: EXPCAP)",
    },
    "exports_goods_automotive": {
        "type": "economic",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Exports of Goods: Automotive Vehicles, Parts, and Engines (FRED: EXPTO)",
    },
    "exports_goods_consumer_goods": {
        "type": "economic",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Exports of Goods: Consumer Goods (FRED: EXPCONS)",
    },
    "exports_goods_foods_feeds_beverages": {
        "type": "economic",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Exports of Goods: Foods, Feeds, and Beverages (FRED: EXPFFB)",
    },
    "imports_goods_industrial_supplies": {
        "type": "economic",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Imports of Goods: Industrial Supplies and Materials (FRED: IMPIN)",
    },
    "imports_goods_capital_goods": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Imports of Goods: Capital Goods (FRED: IMPCAP)",
    },
    "imports_goods_automotive": {
        "type": "economic",
        "default": 200.0,
        "range": [150.0, 250.0],
        "description": "Imports of Goods: Automotive Vehicles, Parts, and Engines (FRED: IMPTO)",
    },
    "imports_goods_consumer_goods": {
        "type": "economic",
        "default": 700.0,
        "range": [500.0, 900.0],
        "description": "Imports of Goods: Consumer Goods (FRED: IMPCONS)",
    },
    "imports_goods_foods_feeds_beverages": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Imports of Goods: Foods, Feeds, and Beverages (FRED: IMPFFB)",
    },
    "balance_of_payments_goods": {
        "type": "economic",
        "default": -50.0,
        "range": [-100.0, 0.0],
        "description": "Balance on Goods (FRED: BOPG)",
    },
    "balance_of_payments_services": {
        "type": "economic",
        "default": 50.0,
        "range": [0.0, 100.0],
        "description": "Balance on Services (FRED: BOPS)",
    },
    "balance_of_payments_primary_income": {
        "type": "economic",
        "default": 30.0,
        "range": [0.0, 60.0],
        "description": "Balance on Primary Income (FRED: BOPPI)",
    },
    "balance_of_payments_secondary_income": {
        "type": "economic",
        "default": -10.0,
        "range": [-30.0, 0.0],
        "description": "Balance on Secondary Income (FRED: BOPSI)",
    },
    "federal_government_current_receipts": {
        "type": "economic",
        "default": 4000.0,
        "range": [3000.0, 5000.0],
        "description": "Federal Government: Current Receipts (FRED: FGRECPTC)",
    },
    "federal_government_current_expenditures": {
        "type": "economic",
        "default": 5000.0,
        "range": [4000.0, 6000.0],
        "description": "Federal Government: Current Expenditures (FRED: FGEXPUTC)",
    },
    "state_local_government_current_receipts": {
        "type": "economic",
        "default": 3000.0,
        "range": [2000.0, 4000.0],
        "description": "State and Local Government: Current Receipts (FRED: SLGRECPTC)",
    },
    "state_local_government_current_expenditures": {
        "type": "economic",
        "default": 3000.0,
        "range": [2000.0, 4000.0],
        "description": "State and Local Government: Current Expenditures (FRED: SLGEXPUTC)",
    },
    "total_government_current_receipts": {
        "type": "economic",
        "default": 7000.0,
        "range": [5000.0, 9000.0],
        "description": "Government: Current Receipts (FRED: GGRECPTC)",
    },
    "total_government_current_expenditures": {
        "type": "economic",
        "default": 8000.0,
        "range": [6000.0, 10000.0],
        "description": "Government: Current Expenditures (FRED: GGEXPUTC)",
    },
    "total_government_net_saving": {
        "type": "economic",
        "default": -1000.0,
        "range": [-2000.0, 0.0],
        "description": "Government Net Saving (FRED: GGNS)",
    },
    "net_operating_surplus_government": {
        "type": "economic",
        "default": 0.0,
        "range": [-100.0, 100.0],
        "description": "Net Operating Surplus: Government (FRED: NOSGOV)",
    },
    "consumption_of_fixed_capital_government": {
        "type": "economic",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Consumption of Fixed Capital: Government (FRED: KCNGOV)",
    },
    "net_domestic_product_government": {
        "type": "economic",
        "default": 2500.0,
        "range": [1500.0, 3500.0],
        "description": "Net Domestic Product: Government (FRED: NDPGOV)",
    },
    "national_income_government_enterprises": {
        "type": "economic",
        "default": 50.0,
        "range": [0.0, 100.0],
        "description": "National Income: Government Enterprises (FRED: NIGOVE)",
    },
    "national_income_general_government": {
        "type": "economic",
        "default": 2000.0,
        "range": [1000.0, 3000.0],
        "description": "National Income: General Government (FRED: NIGOVG)",
    },
    "personal_income_wages_salaries": {
        "type": "economic",
        "default": 10000.0,
        "range": [7000.0, 13000.0],
        "description": "Personal Income: Wages and Salaries (FRED: WASCOR)",
    },
    "personal_income_supplements_to_wages": {
        "type": "economic",
        "default": 2000.0,
        "range": [1000.0, 3000.0],
        "description": "Personal Income: Supplements to Wages and Salaries (FRED: SOWS)",
    },
    "personal_income_proprietors_income": {
        "type": "economic",
        "default": 1500.0,
        "range": [1000.0, 2000.0],
        "description": "Personal Income: Proprietors' Income with Inventory Valuation Adjustment and Capital Consumption Adjustment (FRED: POPTI)",
    },
    "personal_income_rental_income": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Personal Income: Rental Income of Persons with Capital Consumption Adjustment (FRED: RPI)",
    },
    "personal_income_personal_dividend_income": {
        "type": "economic",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Personal Income: Personal Dividend Income (FRED: DVDIV)",
    },
    "personal_income_personal_interest_income": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Personal Income: Personal Interest Income (FRED: INTAD)",
    },
    "personal_income_personal_current_transfer_receipts": {
        "type": "economic",
        "default": 3000.0,
        "range": [2000.0, 4000.0],
        "description": "Personal Income: Personal Current Transfer Receipts (FRED: PCTR)",
    },
    "personal_income_less_contributions_social_insurance": {
        "type": "economic",
        "default": 1000.0,
        "range": [700.0, 1300.0],
        "description": "Personal Income: Less: Contributions for Government Social Insurance, Fifth Decile (FRED: LSI)",
    },
    "disposable_personal_income_personal_current_taxes": {
        "type": "economic",
        "default": 2000.0,
        "range": [1500.0, 2500.0],
        "description": "Disposable Personal Income: Personal Current Taxes (FRED: PCTAX)",
    },
    "personal_outlays": {
        "type": "economic",
        "default": 18000.0,
        "range": [10000.0, 25000.0],
        "description": "Personal Outlays (FRED: POUT)",
    },
    "personal_consumption_expenditures_durable_goods_motor_vehicles_parts": {
        "type": "economic",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Personal Consumption Expenditures: Durable Goods: Motor Vehicles and Parts (FRED: PCEDGMV)",
    },
    "personal_consumption_expenditures_durable_goods_furnishings_durable_household_equipment": {
        "type": "economic",
        "default": 300.0,
        "range": [200.0, 400.0],
        "description": "Personal Consumption Expenditures: Durable Goods: Furnishings and Durable Household Equipment (FRED: PCEDGFH)",
    },
    "personal_consumption_expenditures_durable_goods_recreational_goods_vehicles": {
        "type": "economic",
        "default": 400.0,
        "range": [200.0, 600.0],
        "description": "Personal Consumption Expenditures: Durable Goods: Recreational Goods and Vehicles (FRED: PCEDGRV)",
    },
    "personal_consumption_expenditures_durable_goods_other": {
        "type": "economic",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Personal Consumption Expenditures: Durable Goods: Other Durable Goods (FRED: PCEDGO)",
    },
    "personal_consumption_expenditures_nondurable_goods_food_beverages": {
        "type": "economic",
        "default": 800.0,
        "range": [600.0, 1000.0],
        "description": "Personal Consumption Expenditures: Nondurable Goods: Food and Beverages (FRED: PCENDGFB)",
    },
    "personal_consumption_expenditures_nondurable_goods_clothing_footwear": {
        "type": "economic",
        "default": 200.0,
        "range": [100.0, 300.0],
        "description": "Personal Consumption Expenditures: Nondurable Goods: Clothing and Footwear (FRED: PCENDGCF)",
    },
    "personal_consumption_expenditures_nondurable_goods_gasoline_other_energy_goods": {
        "type": "economic",
        "default": 300.0,
        "range": [100.0, 500.0],
        "description": "Personal Consumption Expenditures: Nondurable Goods: Gasoline and Other Energy Goods (FRED: PCENDGGE)",
    },
    "personal_consumption_expenditures_nondurable_goods_other": {
        "type": "economic",
        "default": 1500.0,
        "range": [1000.0, 2000.0],
        "description": "Personal Consumption Expenditures: Nondurable Goods: Other Nondurable Goods (FRED: PCENDGO)",
    },
    "personal_consumption_expenditures_services_housing_utilities": {
        "type": "economic",
        "default": 3000.0,
        "range": [2000.0, 4000.0],
        "description": "Personal Consumption Expenditures: Services: Housing and Utilities (FRED: PCESSHU)",
    },
    "personal_consumption_expenditures_services_health_care": {
        "type": "economic",
        "default": 2500.0,
        "range": [1500.0, 3500.0],
        "description": "Personal Consumption Expenditures: Services: Health Care (FRED: PCESHC)",
    },
    "personal_consumption_expenditures_services_transportation": {
        "type": "economic",
        "default": 1000.0,
        "range": [700.0, 1300.0],
        "description": "Personal Consumption Expenditures: Services: Transportation Services (FRED: PCESST)",
    },
    "personal_consumption_expenditures_services_recreation": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Personal Consumption Expenditures: Services: Recreation Services (FRED: PCESSR)",
    },
    "personal_consumption_expenditures_services_food_services_accommodations": {
        "type": "economic",
        "default": 800.0,
        "range": [500.0, 1100.0],
        "description": "Personal Consumption Expenditures: Services: Food Services and Accommodations (FRED: PCESSFA)",
    },
    "personal_consumption_expenditures_services_financial_insurance": {
        "type": "economic",
        "default": 1000.0,
        "range": [700.0, 1300.0],
        "description": "Personal Consumption Expenditures: Services: Financial Services and Insurance (FRED: PCESSFI)",
    },
    "personal_consumption_expenditures_services_other": {
        "type": "economic",
        "default": 2000.0,
        "range": [1500.0, 2500.0],
        "description": "Personal Consumption Expenditures: Services: Other Services (FRED: PCESSO)",
    },
    # Market/Asset Classes (backed by Yahoo Finance)
    "spx_close": {
        "type": "market",
        "default": 4000.0,
        "range": [2000.0, 6000.0],
        "description": "S&P 500 Close (Yahoo Finance: ^GSPC)",
    },
    "vix_close": {
        "type": "market",
        "default": 20.0,
        "range": [10.0, 80.0],
        "description": "VIX Close (Yahoo Finance: ^VIX)",
    },
    "djia_close": {
        "type": "market",
        "default": 35000.0,
        "range": [20000.0, 50000.0],
        "description": "Dow Jones Industrial Average Close (Yahoo Finance: ^DJI)",
    },
    "nasdaq_composite_close": {
        "type": "market",
        "default": 14000.0,
        "range": [8000.0, 20000.0],
        "description": "NASDAQ Composite Close (Yahoo Finance: ^IXIC)",
    },
    "russell_2000_close": {
        "type": "market",
        "default": 2000.0,
        "range": [1000.0, 3000.0],
        "description": "Russell 2000 Close (Yahoo Finance: ^RUT)",
    },
    "ftse_100_close": {
        "type": "market",
        "default": 7500.0,
        "range": [5000.0, 10000.0],
        "description": "FTSE 100 Close (Yahoo Finance: ^FTSE)",
    },
    "dax_performance_close": {
        "type": "market",
        "default": 16000.0,
        "range": [10000.0, 20000.0],
        "description": "DAX PERFORMANCE-INDEX Close (Yahoo Finance: ^GDAXI)",
    },
    "nikkei_225_close": {
        "type": "market",
        "default": 30000.0,
        "range": [20000.0, 40000.0],
        "description": "Nikkei 225 Close (Yahoo Finance: ^N225)",
    },
    "hang_seng_index_close": {
        "type": "market",
        "default": 20000.0,
        "range": [15000.0, 25000.0],
        "description": "HANG SENG INDEX Close (Yahoo Finance: ^HSI)",
    },
    "shanghai_composite_close": {
        "type": "market",
        "default": 3000.0,
        "range": [2000.0, 4000.0],
        "description": "Shanghai Composite Index Close (Yahoo Finance: 000001.SS)",
    },
    "sp_tsx_composite_close": {
        "type": "market",
        "default": 20000.0,
        "range": [15000.0, 25000.0],
        "description": "S&P/TSX Composite Index Close (Yahoo Finance: ^GSPTSE)",
    },
    "all_ordinaries_close": {
        "type": "market",
        "default": 7500.0,
        "range": [5000.0, 10000.0],
        "description": "ALL ORDINARIES Close (Yahoo Finance: ^AORD)",
    },
    "ipc_mexico_close": {
        "type": "market",
        "default": 50000.0,
        "range": [30000.0, 70000.0],
        "description": "IPC MEXICO Close (Yahoo Finance: ^MXX)",
    },
    "ibovespa_brazil_close": {
        "type": "market",
        "default": 120000.0,
        "range": [80000.0, 160000.0],
        "description": "Bovespa Index Close (Yahoo Finance: ^BVSP)",
    },
    "cac_40_close": {
        "type": "market",
        "default": 7000.0,
        "range": [5000.0, 9000.0],
        "description": "CAC 40 Close (Yahoo Finance: ^FCHI)",
    },
    "euro_stoxx_50_close": {
        "type": "market",
        "default": 4000.0,
        "range": [3000.0, 5000.0],
        "description": "ESTX 50 PR.SE. Close (Yahoo Finance: ^STOXX50E)",
    },
    "swiss_market_index_close": {
        "type": "market",
        "default": 11000.0,
        "range": [9000.0, 13000.0],
        "description": "Swiss Market Index Close (Yahoo Finance: ^SSMI)",
    },
    "s_p_asx_200_close": {
        "type": "market",
        "default": 7000.0,
        "range": [5000.0, 9000.0],
        "description": "S&P/ASX 200 Close (Yahoo Finance: ^AXJO)",
    },
    "korea_composite_stock_price_index_close": {
        "type": "market",
        "default": 2500.0,
        "range": [2000.0, 3000.0],
        "description": "KOSPI Composite Index Close (Yahoo Finance: ^KS11)",
    },
    "nifty_50_close": {
        "type": "market",
        "default": 18000.0,
        "range": [15000.0, 21000.0],
        "description": "Nifty 50 Close (Yahoo Finance: ^NSEI)",
    },
    "sensex_india_close": {
        "type": "market",
        "default": 60000.0,
        "range": [50000.0, 70000.0],
        "description": "S&P BSE SENSEX Close (Yahoo Finance: ^BSESN)",
    },
    "bse_100_india_close": {
        "type": "market",
        "default": 60000.0,
        "range": [50000.0, 70000.0],
        "description": "BSE 100 Close (Yahoo Finance: ^BSE100)",
    },
    "crypto_bitcoin_usd": {
        "type": "market",
        "default": 40000.0,
        "range": [10000.0, 100000.0],
        "description": "Bitcoin USD Price (Yahoo Finance: BTC-USD)",
    },
    "crypto_ethereum_usd": {
        "type": "market",
        "default": 2500.0,
        "range": [500.0, 5000.0],
        "description": "Ethereum USD Price (Yahoo Finance: ETH-USD)",
    },
    "crypto_ripple_usd": {
        "type": "market",
        "default": 0.5,
        "range": [0.1, 2.0],
        "description": "Ripple USD Price (Yahoo Finance: XRP-USD)",
    },
    "crypto_litecoin_usd": {
        "type": "market",
        "default": 100.0,
        "range": [50.0, 200.0],
        "description": "Litecoin USD Price (Yahoo Finance: LTC-USD)",
    },
    "crypto_cardano_usd": {
        "type": "market",
        "default": 0.5,
        "range": [0.1, 2.0],
        "description": "Cardano USD Price (Yahoo Finance: ADA-USD)",
    },
    "crypto_polkadot_usd": {
        "type": "market",
        "default": 10.0,
        "range": [5.0, 20.0],
        "description": "Polkadot USD Price (Yahoo Finance: DOT-USD)",
    },
    "crypto_solana_usd": {
        "type": "market",
        "default": 50.0,
        "range": [10.0, 100.0],
        "description": "Solana USD Price (Yahoo Finance: SOL-USD)",
    },
    "crypto_dogecoin_usd": {
        "type": "market",
        "default": 0.1,
        "range": [0.05, 0.5],
        "description": "Dogecoin USD Price (Yahoo Finance: DOGE-USD)",
    },
    "crypto_shiba_inu_usd": {
        "type": "market",
        "default": 0.00001,
        "range": [0.000005, 0.00005],
        "description": "Shiba Inu USD Price (Yahoo Finance: SHIB-USD)",
    },
    "crypto_wrapped_bitcoin_usd": {
        "type": "market",
        "default": 40000.0,
        "range": [10000.0, 100000.0],
        "description": "Wrapped Bitcoin USD Price (Yahoo Finance: WBTC-USD)",
    },
    "gold_futures": {
        "type": "market",
        "default": 1800.0,
        "range": [1000.0, 3000.0],
        "description": "Gold Futures Price (Yahoo Finance: GC=F)",
    },
    "silver_futures": {
        "type": "market",
        "default": 25.0,
        "range": [10.0, 50.0],
        "description": "Silver Futures Price (Yahoo Finance: SI=F)",
    },
    "copper_futures": {
        "type": "market",
        "default": 4.0,
        "range": [2.0, 6.0],
        "description": "Copper Futures Price (Yahoo Finance: HG=F)",
    },
    "crude_oil_futures_wti": {
        "type": "market",
        "default": 80.0,
        "range": [20.0, 150.0],
        "description": "Crude Oil Futures (WTI) Price (Yahoo Finance: CL=F)",
    },
    "brent_oil_futures": {
        "type": "market",
        "default": 85.0,
        "range": [25.0, 160.0],
        "description": "Brent Oil Futures Price (Yahoo Finance: BZ=F)",
    },
    "natural_gas_futures": {
        "type": "market",
        "default": 3.0,
        "range": [1.0, 6.0],
        "description": "Natural Gas Futures Price (Yahoo Finance: NG=F)",
    },
    "corn_futures": {
        "type": "market",
        "default": 500.0,
        "range": [300.0, 700.0],
        "description": "Corn Futures Price (Yahoo Finance: ZC=F)",
    },
    "wheat_futures": {
        "type": "market",
        "default": 600.0,
        "range": [400.0, 800.0],
        "description": "Wheat Futures Price (Yahoo Finance: ZW=F)",
    },
    "soybean_futures": {
        "type": "market",
        "default": 1200.0,
        "range": [800.0, 1600.0],
        "description": "Soybean Futures Price (Yahoo Finance: ZS=F)",
    },
    "sugar_futures": {
        "type": "market",
        "default": 0.2,
        "range": [0.1, 0.3],
        "description": "Sugar Futures Price (Yahoo Finance: SB=F)",
    },
    "coffee_futures": {
        "type": "market",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Coffee Futures Price (Yahoo Finance: KC=F)",
    },
    "cocoa_futures": {
        "type": "market",
        "default": 2500.0,
        "range": [1500.0, 3500.0],
        "description": "Cocoa Futures Price (Yahoo Finance: CC=F)",
    },
    "cotton_futures": {
        "type": "market",
        "default": 80.0,
        "range": [60.0, 100.0],
        "description": "Cotton Futures Price (Yahoo Finance: CT=F)",
    },
    "us_dollar_index_futures": {
        "type": "market",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "U.S. Dollar Index Futures Price (Yahoo Finance: DX=F)",
    },
    "euro_usd_futures": {
        "type": "market",
        "default": 1.1,
        "range": [0.8, 1.5],
        "description": "EUR/USD Exchange Rate (Yahoo Finance: EURUSD=X)",
    },
    "usd_jpy_futures": {
        "type": "market",
        "default": 140.0,
        "range": [100.0, 180.0],
        "description": "USD/JPY Exchange Rate (Yahoo Finance: JPY=X)",
    },
    "gbp_usd_futures": {
        "type": "market",
        "default": 1.25,
        "range": [1.0, 1.5],
        "description": "GBP/USD Exchange Rate (Yahoo Finance: GBPUSD=X)",
    },
    "aud_usd_futures": {
        "type": "market",
        "default": 0.65,
        "range": [0.5, 0.8],
        "description": "AUD/USD Exchange Rate (Yahoo Finance: AUDUSD=X)",
    },
    "usd_cad_futures": {
        "type": "market",
        "default": 1.35,
        "range": [1.1, 1.6],
        "description": "USD/CAD Exchange Rate (Yahoo Finance: CAD=X)",
    },
    "usd_chf_futures": {
        "type": "market",
        "default": 0.9,
        "range": [0.7, 1.1],
        "description": "USD/CHF Exchange Rate (Yahoo Finance: CHF=X)",
    },
    "nzd_usd_futures": {
        "type": "market",
        "default": 0.6,
        "range": [0.4, 0.75],
        "description": "NZD/USD Exchange Rate (Yahoo Finance: NZDUSD=X)",
    },
    "usd_inr_futures": {
        "type": "market",
        "default": 83.0,
        "range": [70.0, 90.0],
        "description": "USD/INR Exchange Rate (Yahoo Finance: INR=X)",
    },
    "cny_usd_futures": {
        "type": "market",
        "default": 7.2,
        "range": [6.5, 8.0],
        "description": "CNY/USD Exchange Rate (Yahoo Finance: CNY=X)",
    },
    "us_10y_treasury_bond_futures": {
        "type": "market",
        "default": 115.0,
        "range": [100.0, 130.0],
        "description": "US 10 Year T-Note Futures Price (Yahoo Finance: ZN=F)",
    },
    "us_30y_treasury_bond_futures": {
        "type": "market",
        "default": 135.0,
        "range": [110.0, 160.0],
        "description": "US Long Bond Futures Price (Yahoo Finance: ZB=F)",
    },
    "vix_futures": {
        "type": "market",
        "default": 20.0,
        "range": [10.0, 80.0],
        "description": "VIX Futures Price (Yahoo Finance: VX=F)",
    },
    "sp_500_futures": {
        "type": "market",
        "default": 4000.0,
        "range": [2000.0, 6000.0],
        "description": "S&P 500 Futures Price (Yahoo Finance: ES=F)",
    },
    "nasdaq_100_futures": {
        "type": "market",
        "default": 14000.0,
        "range": [8000.0, 20000.0],
        "description": "NASDAQ 100 Futures Price (Yahoo Finance: NQ=F)",
    },
    "dow_jones_futures": {
        "type": "market",
        "default": 35000.0,
        "range": [20000.0, 50000.0],
        "description": "Dow Jones Futures Price (Yahoo Finance: YM=F)",
    },
    "russell_2000_futures": {
        "type": "market",
        "default": 2000.0,
        "range": [1000.0, 3000.0],
        "description": "Russell 2000 Futures Price (Yahoo Finance: RTY=F)",
    },
    "apple_stock": {
        "type": "market",
        "default": 150.0,
        "range": [50.0, 300.0],
        "description": "Apple Inc. Stock Price (Yahoo Finance: AAPL)",
    },
    "microsoft_stock": {
        "type": "market",
        "default": 250.0,
        "range": [100.0, 500.0],
        "description": "Microsoft Corporation Stock Price (Yahoo Finance: MSFT)",
    },
    "google_stock_a": {
        "type": "market",
        "default": 100.0,
        "range": [50.0, 200.0],
        "description": "Alphabet Inc. (GOOGL) Stock Price (Yahoo Finance: GOOGL)",
    },
    "amazon_stock": {
        "type": "market",
        "default": 100.0,
        "range": [50.0, 200.0],
        "description": "Amazon.com, Inc. Stock Price (Yahoo Finance: AMZN)",
    },
    "tesla_stock": {
        "type": "market",
        "default": 200.0,
        "range": [50.0, 500.0],
        "description": "Tesla, Inc. Stock Price (Yahoo Finance: TSLA)",
    },
    "facebook_stock": {
        "type": "market",
        "default": 200.0,
        "range": [100.0, 400.0],
        "description": "Meta Platforms, Inc. Stock Price (Yahoo Finance: META)",
    },
    "nvidia_stock": {
        "type": "market",
        "default": 500.0,
        "range": [100.0, 1000.0],
        "description": "NVIDIA Corporation Stock Price (Yahoo Finance: NVDA)",
    },
    "berkshire_hathaway_b_stock": {
        "type": "market",
        "default": 300.0,
        "range": [200.0, 400.0],
        "description": "Berkshire Hathaway Inc. (BRK-B) Stock Price (Yahoo Finance: BRK-B)",
    },
    "jp_morgan_chase_stock": {
        "type": "market",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "JPMorgan Chase & Co. Stock Price (Yahoo Finance: JPM)",
    },
    "johnson_johnson_stock": {
        "type": "market",
        "default": 170.0,
        "range": [150.0, 200.0],
        "description": "Johnson & Johnson Stock Price (Yahoo Finance: JNJ)",
    },
    "visa_stock": {
        "type": "market",
        "default": 200.0,
        "range": [150.0, 250.0],
        "description": "Visa Inc. Stock Price (Yahoo Finance: V)",
    },
    "mastercard_stock": {
        "type": "market",
        "default": 350.0,
        "range": [250.0, 450.0],
        "description": "Mastercard Incorporated Stock Price (Yahoo Finance: MA)",
    },
    "unitedhealth_group_stock": {
        "type": "market",
        "default": 500.0,
        "range": [400.0, 600.0],
        "description": "UnitedHealth Group Incorporated Stock Price (Yahoo Finance: UNH)",
    },
    "exxon_mobil_stock": {
        "type": "market",
        "default": 100.0,
        "range": [50.0, 150.0],
        "description": "Exxon Mobil Corporation Stock Price (Yahoo Finance: XOM)",
    },
    "chevron_stock": {
        "type": "market",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Chevron Corporation Stock Price (Yahoo Finance: CVX)",
    },
    "pfizer_stock": {
        "type": "market",
        "default": 30.0,
        "range": [20.0, 40.0],
        "description": "Pfizer Inc. Stock Price (Yahoo Finance: PFE)",
    },
    "merck_stock": {
        "type": "market",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "Merck & Co., Inc. Stock Price (Yahoo Finance: MRK)",
    },
    "walmart_stock": {
        "type": "market",
        "default": 150.0,
        "range": [120.0, 180.0],
        "description": "Walmart Inc. Stock Price (Yahoo Finance: WMT)",
    },
    "home_depot_stock": {
        "type": "market",
        "default": 300.0,
        "range": [250.0, 350.0],
        "description": "The Home Depot, Inc. Stock Price (Yahoo Finance: HD)",
    },
    "mcdonalds_stock": {
        "type": "market",
        "default": 250.0,
        "range": [200.0, 300.0],
        "description": "McDonald's Corporation Stock Price (Yahoo Finance: MCD)",
    },
    "cocacola_stock": {
        "type": "market",
        "default": 60.0,
        "range": [50.0, 70.0],
        "description": "The Coca-Cola Company Stock Price (Yahoo Finance: KO)",
    },
    "pepsico_stock": {
        "type": "market",
        "default": 170.0,
        "range": [150.0, 200.0],
        "description": "PepsiCo, Inc. Stock Price (Yahoo Finance: PEP)",
    },
    "tech_sector_etf": {
        "type": "market",
        "default": 180.0,
        "range": [100.0, 300.0],
        "description": "Technology Select Sector SPDR Fund Price (Yahoo Finance: XLK)",
    },
    "health_sector_etf": {
        "type": "market",
        "default": 130.0,
        "range": [100.0, 160.0],
        "description": "Health Care Select Sector SPDR Fund Price (Yahoo Finance: XLV)",
    },
    "energy_sector_etf": {
        "type": "market",
        "default": 80.0,
        "range": [50.0, 110.0],
        "description": "Energy Select Sector SPDR Fund Price (Yahoo Finance: XLE)",
    },
    "financial_sector_etf": {
        "type": "market",
        "default": 40.0,
        "range": [30.0, 50.0],
        "description": "Financial Select Sector SPDR Fund Price (Yahoo Finance: XLF)",
    },
    "consumer_discretionary_sector_etf": {
        "type": "market",
        "default": 150.0,
        "range": [100.0, 200.0],
        "description": "Consumer Discretionary Select Sector SPDR Fund Price (Yahoo Finance: XLY)",
    },
    "consumer_staples_sector_etf": {
        "type": "market",
        "default": 70.0,
        "range": [50.0, 90.0],
        "description": "Consumer Staples Select Sector SPDR Fund Price (Yahoo Finance: XLP)",
    },
    "industrials_sector_etf": {
        "type": "market",
        "default": 100.0,
        "range": [70.0, 130.0],
        "description": "Industrial Select Sector SPDR Fund Price (Yahoo Finance: XLI)",
    },
    "materials_sector_etf": {
        "type": "market",
        "default": 50.0,
        "range": [30.0, 70.0],
        "description": "Materials Select Sector SPDR Fund Price (Yahoo Finance: XLB)",
    },
    "real_estate_sector_etf": {
        "type": "market",
        "default": 40.0,
        "range": [30.0, 50.0],
        "description": "Real Estate Select Sector SPDR Fund Price (Yahoo Finance: XLRE)",
    },
    "utilities_sector_etf": {
        "type": "market",
        "default": 70.0,
        "range": [50.0, 90.0],
        "description": "Utilities Select Sector SPDR Fund Price (Yahoo Finance: XLU)",
    },
    "communication_services_sector_etf": {
        "type": "market",
        "default": 50.0,
        "range": [30.0, 70.0],
        "description": "Communication Services Select Sector SPDR Fund Price (Yahoo Finance: XLC)",
    },
    "vanguard_total_stock_market_etf": {
        "type": "market",
        "default": 200.0,
        "range": [100.0, 300.0],
        "description": "Vanguard Total Stock Market ETF Price (Yahoo Finance: VTI)",
    },
    "vanguard_sp_500_etf": {
        "type": "market",
        "default": 400.0,
        "range": [200.0, 600.0],
        "description": "Vanguard S&P 500 ETF Price (Yahoo Finance: VOO)",
    },
    "ishares_core_us_aggregate_bond_etf": {
        "type": "market",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "iShares Core U.S. Aggregate Bond ETF Price (Yahoo Finance: AGG)",
    },
    "vanguard_total_bond_market_etf": {
        "type": "market",
        "default": 80.0,
        "range": [60.0, 100.0],
        "description": "Vanguard Total Bond Market ETF Price (Yahoo Finance: BND)",
    },
    "ishares_jpmorgan_usd_emerging_markets_bond_etf": {
        "type": "market",
        "default": 100.0,
        "range": [80.0, 120.0],
        "description": "iShares J.P. Morgan USD Emerging Markets Bond ETF Price (Yahoo Finance: EMB)",
    },
    "ishares_iboxx_usd_investment_grade_corporate_bond_etf": {
        "type": "market",
        "default": 120.0,
        "range": [100.0, 140.0],
        "description": "iShares iBoxx $ Investment Grade Corporate Bond ETF Price (Yahoo Finance: LQD)",
    },
    "ishares_iboxx_usd_high_yield_corporate_bond_etf": {
        "type": "market",
        "default": 80.0,
        "range": [60.0, 100.0],
        "description": "iShares iBoxx $ High Yield Corporate Bond ETF Price (Yahoo Finance: HYG)",
    },
    "spdr_gold_shares": {
        "type": "market",
        "default": 180.0,
        "range": [100.0, 300.0],
        "description": "SPDR Gold Shares Price (Yahoo Finance: GLD)",
    },
    "ishares_silver_trust": {
        "type": "market",
        "default": 25.0,
        "range": [10.0, 50.0],
        "description": "iShares Silver Trust Price (Yahoo Finance: SLV)",
    },
    "united_states_oil_fund": {
        "type": "market",
        "default": 60.0,
        "range": [20.0, 100.0],
        "description": "United States Oil Fund Price (Yahoo Finance: USO)",
    },
    "united_states_gasoline_fund": {
        "type": "market",
        "default": 2.0,
        "range": [1.0, 3.0],
        "description": "United States Gasoline Fund Price (Yahoo Finance: UGA)",
    },
    "united_states_natural_gas_fund": {
        "type": "market",
        "default": 10.0,
        "range": [5.0, 20.0],
        "description": "United States Natural Gas Fund Price (Yahoo Finance: UNG)",
    },
    "invesco_db_agriculture_fund": {
        "type": "market",
        "default": 20.0,
        "range": [15.0, 25.0],
        "description": "Invesco DB Agriculture Fund Price (Yahoo Finance: DBA)",
    },
    "invesco_db_energy_fund": {
        "type": "market",
        "default": 20.0,
        "range": [15.0, 25.0],
        "description": "Invesco DB Energy Fund Price (Yahoo Finance: DBE)",
    },
    "invesco_db_gold_fund": {
        "type": "market",
        "default": 18.0,
        "range": [10.0, 25.0],
        "description": "Invesco DB Gold Fund Price (Yahoo Finance: DGL)",
    },
    "invesco_db_silver_fund": {
        "type": "market",
        "default": 20.0,
        "range": [10.0, 30.0],
        "description": "Invesco DB Silver Fund Price (Yahoo Finance: DBS)",
    },
    "invesco_db_us_dollar_index_bullish": {
        "type": "market",
        "default": 25.0,
        "range": [20.0, 30.0],
        "description": "Invesco DB US Dollar Index Bullish Price (Yahoo Finance: UUP)",
    },
    "invesco_db_us_dollar_index_bearish": {
        "type": "market",
        "default": 20.0,
        "range": [15.0, 25.0],
        "description": "Invesco DB US Dollar Index Bearish Price (Yahoo Finance: UDN)",
    },
    # New Alpha Vantage Stock Symbols
    "jpm_stock": {
        "type": "market",
        "default": 180.0,
        "range": [120.0, 250.0],
        "description": "JPMorgan Chase & Co. Stock Price (Alpha Vantage: JPM)",
    },
    "v_stock": {
        "type": "market",
        "default": 270.0,
        "range": [200.0, 350.0],
        "description": "Visa Inc. Stock Price (Alpha Vantage: V)",
    },
    "pg_stock": {
        "type": "market",
        "default": 160.0,
        "range": [130.0, 200.0],
        "description": "Procter & Gamble Co. Stock Price (Alpha Vantage: PG)",
    },
    "dis_stock": {
        "type": "market",
        "default": 110.0,
        "range": [80.0, 150.0],
        "description": "The Walt Disney Company Stock Price (Alpha Vantage: DIS)",
    },
    "nflx_stock": {
        "type": "market",
        "default": 550.0,
        "range": [400.0, 700.0],
        "description": "Netflix, Inc. Stock Price (Alpha Vantage: NFLX)",
    },
    # High-Frequency Technical Indicators
    "hf_ma_10": {
        "type": "market",
        "default": 0.0,
        "range": [-1000.0, 10000.0],
        "description": "10-period Moving Average of high-frequency data",
    },
    "hf_intraday_volume": {
        "type": "market",
        "default": 0.0,
        "range": [0.0, 1000000000.0],
        "description": "Intraday Volume from high-frequency data",
    },
    "hf_intraday_volatility": {
        "type": "market",
        "default": 0.0,
        "range": [0.0, 1000.0],
        "description": "Intraday Volatility from high-frequency data",
    },
    "orb_price": {
        "type": "market",
        "default": 80.0,
        "range": [20.0, 150.0],
        "description": "OPEC Reference Basket Price (Manual Data)",
    },
}


# === Helpers for defaults / quick validation (unchanged) ===============
def get_default_variable_state() -> Dict[str, float]:
    return {k: v["default"] for k, v in VARIABLE_REGISTRY.items()}


def validate_variables(
    variable_dict: Dict[str, Any],
) -> Tuple[bool, Set[str], Set[str]]:
    known_keys = set(VARIABLE_REGISTRY.keys())
    input_keys = set(variable_dict.keys())
    missing = known_keys - input_keys
    unexpected = input_keys - known_keys
    return (len(missing) == 0 and len(unexpected) == 0, missing, unexpected)


def get_variables_by_type(var_type: str) -> List[str]:
    return [k for k, v in VARIABLE_REGISTRY.items() if v.get("type") == var_type]


# === Extended Runtime Accessor =========================================
REGISTRY_PATH = PATHS.get("VARIABLE_REGISTRY", "configs/variable_registry.json")


class VariableRegistry:
    """
    Registry for all variables in the Pulse system.

    This class manages the:
    - Static variable definitions
    - Runtime tracking of values
    - Variable search and metadata
    - Forecasting capability
    """

    # Shared containers (class-level → every instance sees same data)
    _external_ingesters: List[Callable[[], Dict[str, float]]] = []

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or REGISTRY_PATH
        self.variables: Dict[str, Dict[str, Any]] = VARIABLE_REGISTRY.copy()
        self._forecast_values = {}  # Store forecasts by variable name
        self._runtime_values = {}  # Store runtime values by variable name
        self._variable_tags = {}  # Store tags for variables
        self._initialized = False

        self._load()
        self._load_persisted_values()
        self._generate_example_forecasts()
        self._initialized = True

    # ── persistence ----------------------------------------------------
    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                with suppress(Exception):
                    updated = json.load(f)
                    self.variables.update(updated)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.variables, f, indent=2)

    def _load_persisted_values(self):
        """Load persisted values from disk if available."""
        with suppress(Exception):
            if os.path.exists(
                PATHS.get("variable_values_path", "./data/variable_values.json")
            ):
                with open(
                    PATHS.get("variable_values_path", "./data/variable_values.json"),
                    "r",
                ) as f:
                    self._runtime_values = json.load(f)

    def _generate_example_forecasts(self):
        """Generate example forecast values for demo purposes."""
        import random

        for var_name, var_def in self.variables.items():
            # Generate a random forecast within the defined range
            if "range" in var_def:
                low, high = var_def["range"]
                forecast_val = random.uniform(low, high)

                # Format the value to 4 decimal places for readability
                self._forecast_values[var_name] = round(forecast_val, 4)
            else:
                # If no range is defined, use the default value
                self._forecast_values[var_name] = var_def.get("default", 0)

    # ── registration & lookup -----------------------------------------
    def register_variable(
        self,
        name: str,
        meta: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register or update a variable entry (back-compat: meta|metadata)."""
        meta = meta or metadata or {}
        self.variables[name] = meta
        self._save()

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        return self.variables.get(name)

    # Convenience listings
    def all(self) -> List[str]:
        return list(self.variables.keys())

    def filter_by_tag(self, tag: str) -> List[str]:
        return [k for k, v in self.variables.items() if tag in v.get("tags", [])]

    def filter_by_type(self, var_type: str) -> List[str]:
        return [k for k, v in self.variables.items() if v.get("type") == var_type]

    def list_trust_ranked(self) -> List[str]:
        return sorted(
            self.variables.keys(),
            key=lambda k: self.variables[k].get("trust_weight", 1.0),
            reverse=True,
        )

    # ── NEW Phase-1 hooks ———————————————————————————————
    def bind_external_ingestion(self, loader: Callable[[], Dict[str, float]]) -> None:
        """Attach a callable that returns a **flat** {var: value} mapping."""
        if loader not in self._external_ingesters:
            self._external_ingesters.append(loader)

    def flag_missing_variables(self, snapshot: Dict[str, float]) -> List[str]:
        """Return registry variables absent from `snapshot`."""
        return [name for name in self.variables if name not in snapshot]

    def score_variable_activity(self, snapshot: Dict[str, float]) -> Dict[str, float]:
        """Naive |value| scoring for quick 'most active' ranking."""
        return {k: abs(v) for k, v in snapshot.items()}

    # ── live-data convenience (optional) ------------------------------
    def bind_data_source(
        self, signal_provider_fn: Callable[[], Dict[str, Any]]
    ) -> None:
        self._signal_provider = signal_provider_fn

    def get_live_value(self, var_name: str) -> Optional[float]:
        if hasattr(self, "_signal_provider") and var_name in self.variables:
            try:
                signals = self._signal_provider()
                return signals.get(var_name)
            except Exception as exc:  # noqa: BLE001
                print(f"[VariableRegistry] Error fetching {var_name}: {exc}")
        return None

    # ── Forecasting methods -------------------------------------------
    def is_initialized(self):
        """Returns whether the registry has been initialized."""
        return self._initialized

    def get_forecast_variables(self):
        """Returns a list of all variables that have forecasts."""
        return list(self._forecast_values.keys())

    def get_forecast_value(self, variable_name):
        """Get the latest forecast value for a variable."""
        return self._forecast_values.get(variable_name)

    def set_forecast_value(self, variable_name, value):
        """Set a forecast value for a variable."""
        self._forecast_values[variable_name] = value

    def set_live_value(self, variable_name, value):
        """Set the current runtime value for a variable."""
        self._runtime_values[variable_name] = value

    def get_variable_definition(self, variable_name):
        """Get the definition of a variable."""
        return self.variables.get(variable_name)

    def get_variable_names(self, variable_type=None):
        """Get all variable names, optionally filtered by type."""
        if variable_type:
            return [
                name
                for name, def_dict in self.variables.items()
                if def_dict.get("type") == variable_type
            ]
        return list(self.variables.keys())

    def add_variable_tag(self, variable_name, tag):
        """Add a tag to a variable."""
        if variable_name not in self._variable_tags:
            self._variable_tags[variable_name] = set()
        self._variable_tags[variable_name].add(tag)

    def get_variable_tags(self, variable_name):
        """Get all tags for a variable."""
        return list(self._variable_tags.get(variable_name, set()))


# === Project-wide singleton ============================================
registry = VariableRegistry()  # import this wherever you need the shared instance

if __name__ == "__main__":
    vr = VariableRegistry()
    print("Variables loaded:", len(vr.all()))
