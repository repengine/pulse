"""Wikidata SPARQL - structured knowledge data ingestion plugin.

This plugin fetches data from Wikidata using SPARQL queries. Wikidata is a free
and collaborative knowledge base that contains structured data about a wide range
of topics including companies, countries, people, scientific concepts, and more.

The plugin uses the Wikidata Query Service (SPARQL endpoint) to retrieve data and
processes it into signals that can be used for providing contextual information
to forecasting models.

No API key is required for basic usage, but requests are rate-limited.

Example:
--------
```python
from iris.iris_plugins import IrisPluginManager
from iris.iris_plugins_variable_ingestion.wikidata_plugin import WikidataPlugin

mgr = IrisPluginManager()
mgr.register_plugin(WikidataPlugin())
print(mgr.run_plugins())
```
"""
import datetime as dt
import logging
import os
import time
import random
from typing import List, Dict, Any, Optional, Set, Tuple, Union
import json
import re
from urllib.parse import quote

import requests
from iris.iris_plugins import IrisPluginManager
from iris.iris_utils.ingestion_persistence import (
    ensure_data_directory,
    save_request_metadata,
    save_api_response,
    save_processed_data
)

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "wikidata"

# Base URL for the Wikidata SPARQL endpoint
_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# User agent for Wikidata API requests (they require a descriptive user agent)
_USER_AGENT = "PulseEconomicForecastTool/1.0 (https://github.com/pulse-economic-forecasting)"

# Domain topics to query
_DOMAINS = {
    "companies": [
        # Top tech companies
        {"id": "Q380", "name": "Apple Inc."},
        {"id": "Q380", "name": "Apple"},
        {"id": "Q380", "name": "Apple Inc"},
        {"id": "Q219541", "name": "Microsoft"},
        {"id": "Q219541", "name": "Microsoft Corporation"},
        {"id": "Q95", "name": "Google"},
        {"id": "Q95", "name": "Google LLC"},
        {"id": "Q20800404", "name": "Alphabet Inc."},
        {"id": "Q9366", "name": "Amazon"},
        {"id": "Q9366", "name": "Amazon.com"},
        # Financial institutions
        {"id": "Q922059", "name": "JPMorgan Chase"},
        {"id": "Q487907", "name": "Goldman Sachs"},
        {"id": "Q664334", "name": "Bank of America"},
        {"id": "Q192815", "name": "Citigroup"},
        {"id": "Q811794", "name": "Morgan Stanley"},
    ],
    "central_banks": [
        {"id": "Q308209", "name": "Federal Reserve System"},
        {"id": "Q308209", "name": "Federal Reserve"},
        {"id": "Q8660", "name": "European Central Bank"},
        {"id": "Q8660", "name": "ECB"},
        {"id": "Q9061", "name": "Bank of Japan"},
        {"id": "Q180811", "name": "Bank of England"},
        {"id": "Q157258", "name": "People's Bank of China"},
    ],
    "countries": [
        {"id": "Q30", "name": "United States"},
        {"id": "Q30", "name": "USA"},
        {"id": "Q148", "name": "China"},
        {"id": "Q145", "name": "United Kingdom"},
        {"id": "Q145", "name": "UK"},
        {"id": "Q183", "name": "Germany"},
        {"id": "Q17", "name": "Japan"},
        {"id": "Q142", "name": "France"},
        {"id": "Q668", "name": "India"},
        {"id": "Q20", "name": "Norway"},
        {"id": "Q34", "name": "Sweden"},
    ],
    "commodities": [
        {"id": "Q11343", "name": "gold"},
        {"id": "Q850", "name": "copper"},
        {"id": "Q677", "name": "iron"},
        {"id": "Q641", "name": "silver"},
        {"id": "Q897", "name": "platinum"},
        {"id": "Q192843", "name": "crude oil"},
        {"id": "Q2119", "name": "natural gas"},
        {"id": "Q38361", "name": "wheat"},
        {"id": "Q11005", "name": "corn"},
        {"id": "Q83426", "name": "soybean"},
    ],
    "economic_indicators": [
        {"id": "Q47160", "name": "GDP"},
        {"id": "Q47160", "name": "gross domestic product"},
        {"id": "Q179851", "name": "CPI"},
        {"id": "Q179851", "name": "consumer price index"},
        {"id": "Q28143799", "name": "PPI"},
        {"id": "Q28143799", "name": "producer price index"},
        {"id": "Q181076", "name": "unemployment"},
        {"id": "Q190813", "name": "interest rate"},
        {"id": "Q846750", "name": "foreign exchange reserves"},
    ]
}

# SPARQL query templates
_QUERY_TEMPLATES = {
    "company_info": """
        SELECT ?companyLabel ?foundingDate ?employeeCount ?revenueUSD ?netIncomeUSD ?country ?industryLabel ?ceoLabel ?websiteLabel WHERE {
          BIND(wd:%s AS ?company)
          OPTIONAL { ?company wdt:P571 ?foundingDate. }
          OPTIONAL { ?company wdt:P1128 ?employeeCount. }
          OPTIONAL { ?company wdt:P2139 ?revenueUSD. }
          OPTIONAL { ?company wdt:P2295 ?netIncomeUSD. }
          OPTIONAL { ?company wdt:P17 ?countryEntity. 
                    ?countryEntity rdfs:label ?country.
                    FILTER(LANG(?country) = "en") }
          OPTIONAL { ?company wdt:P452 ?industry.
                    ?industry rdfs:label ?industryLabel.
                    FILTER(LANG(?industryLabel) = "en") }
          OPTIONAL { ?company wdt:P169 ?ceo.
                    ?ceo rdfs:label ?ceoLabel.
                    FILTER(LANG(?ceoLabel) = "en") }
          OPTIONAL { ?company wdt:P856 ?website.
                    ?website rdfs:label ?websiteLabel.
                    FILTER(LANG(?websiteLabel) = "en") }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """,
    
    "country_economic_data": """
        SELECT ?countryLabel ?population ?gdpUSD ?gdpPerCapitaUSD ?currencyLabel ?inflationRate ?unemploymentRate ?centralBankLabel WHERE {
          BIND(wd:%s AS ?country)
          OPTIONAL { ?country wdt:P1082 ?population. }
          OPTIONAL { ?country wdt:P2131 ?gdpUSD. }
          OPTIONAL { ?country wdt:P2132 ?gdpPerCapitaUSD. }
          OPTIONAL { ?country wdt:P38 ?currency.
                    ?currency rdfs:label ?currencyLabel.
                    FILTER(LANG(?currencyLabel) = "en") }
          OPTIONAL { ?country wdt:P1279 ?inflationRate. }
          OPTIONAL { ?country wdt:P1198 ?unemploymentRate. }
          OPTIONAL { ?country wdt:P2070 ?centralBank.
                    ?centralBank rdfs:label ?centralBankLabel.
                    FILTER(LANG(?centralBankLabel) = "en") }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """,
    
    "central_bank_info": """
        SELECT ?centralBankLabel ?foundingDate ?countryLabel ?currencyLabel ?bankRatePercent ?reservesUSD ?governorLabel WHERE {
          BIND(wd:%s AS ?centralBank)
          OPTIONAL { ?centralBank wdt:P571 ?foundingDate. }
          OPTIONAL { ?centralBank wdt:P17 ?country.
                    ?country rdfs:label ?countryLabel.
                    FILTER(LANG(?countryLabel) = "en") }
          OPTIONAL { ?centralBank wdt:P38 ?currency.
                    ?currency rdfs:label ?currencyLabel.
                    FILTER(LANG(?currencyLabel) = "en") }
          OPTIONAL { ?centralBank wdt:P1179 ?bankRatePercent. }
          OPTIONAL { ?centralBank wdt:P2134 ?reservesUSD. }
          OPTIONAL { ?centralBank wdt:P169 ?governor.
                    ?governor rdfs:label ?governorLabel.
                    FILTER(LANG(?governorLabel) = "en") }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """,
    
    "commodity_info": """
        SELECT ?commodityLabel ?commodityClassLabel ?unitLabel ?priceUSD ?abundanceEarth WHERE {
          BIND(wd:%s AS ?commodity)
          OPTIONAL { ?commodity wdt:P31 ?commodityClass.
                    ?commodityClass rdfs:label ?commodityClassLabel.
                    FILTER(LANG(?commodityClassLabel) = "en") }
          OPTIONAL { ?commodity wdt:P2442 ?unitOfMeasurement.
                    ?unitOfMeasurement rdfs:label ?unitLabel.
                    FILTER(LANG(?unitLabel) = "en") }
          OPTIONAL { ?commodity wdt:P2284 ?priceUSD. }
          OPTIONAL { ?commodity wdt:P2241 ?abundanceEarth. }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """,
    
    "economic_indicator_info": """
        SELECT ?indicatorLabel ?definitionLabel ?publicationFrequency ?publisherLabel ?relatedIndicatorsLabel WHERE {
          BIND(wd:%s AS ?indicator)
          OPTIONAL { ?indicator schema:description ?definitionLabel.
                    FILTER(LANG(?definitionLabel) = "en") }
          OPTIONAL { ?indicator wdt:P2781 ?publicationFrequency. }
          OPTIONAL { ?indicator wdt:P123 ?publisher.
                    ?publisher rdfs:label ?publisherLabel.
                    FILTER(LANG(?publisherLabel) = "en") }
          OPTIONAL { ?indicator wdt:P1659 ?relatedIndicators.
                    ?relatedIndicators rdfs:label ?relatedIndicatorsLabel.
                    FILTER(LANG(?relatedIndicatorsLabel) = "en") }
          SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """,
}

class WikidataPlugin(IrisPluginManager):
    plugin_name = "wikidata_plugin"
    enabled = True     # No API key required for basic usage
    concurrency = 1    # Lower concurrency due to Wikidata rate limits
    
    # Request configuration
    REQUEST_TIMEOUT = 20.0  # SPARQL queries can take time
    RETRY_WAIT = 5.0        # Longer wait for rate limiting
    MAX_RETRIES = 2
    
    def __init__(self):
        """Initialize the Wikidata plugin."""
        # Ensure data directory exists for this source
        ensure_data_directory(_SOURCE_NAME)

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch structured knowledge data from Wikidata SPARQL endpoint."""
        signals = []
        
        # Choose a domain to query based on day of month to distribute API calls
        day_of_month = dt.datetime.now().day
        domains = list(_DOMAINS.keys())
        domain_idx = day_of_month % len(domains)
        domain = domains[domain_idx]
        
        logger.info(f"[wikidata_plugin] Fetching data for domain: {domain}")
        
        # Choose a random entity from the selected domain
        entities = _DOMAINS[domain]
        entity = random.choice(entities)
        entity_id = entity["id"]
        entity_name = entity["name"]
        
        logger.info(f"[wikidata_plugin] Selected entity: {entity_name} (Q{entity_id})")
        
        # Select the appropriate query template for the domain
        query_type = self._get_query_type_for_domain(domain)
        
        # Execute the query for the selected entity
        query_results = self._execute_sparql_query(entity_id, query_type)
        
        # Process the results into signals
        if query_results:
            entity_signals = self._process_query_results(domain, entity_id, entity_name, query_type, query_results)
            signals.extend(entity_signals)
        
        return signals
    
    def _get_query_type_for_domain(self, domain: str) -> str:
        """Get the appropriate query template for the domain.
        
        Args:
            domain: Domain name (e.g., 'companies', 'countries')
            
        Returns:
            Query type key for _QUERY_TEMPLATES
        """
        domain_query_map = {
            "companies": "company_info",
            "central_banks": "central_bank_info",
            "countries": "country_economic_data",
            "commodities": "commodity_info",
            "economic_indicators": "economic_indicator_info"
        }
        
        return domain_query_map.get(domain, "company_info")  # Default to company_info
    
    def _execute_sparql_query(self, entity_id: str, query_type: str) -> Optional[List[Dict[str, Any]]]:
        """Execute a SPARQL query for the given entity.
        
        Args:
            entity_id: Wikidata entity ID
            query_type: Type of query to execute
            
        Returns:
            Query results as processed JSON, or None if query failed
        """
        # Get the query template
        query_template = _QUERY_TEMPLATES.get(query_type)
        if not query_template:
            logger.error(f"[wikidata_plugin] Unknown query type: {query_type}")
            return None
        
        # Format the query with the entity ID
        query = query_template % entity_id
        
        # Set up request parameters
        params = {
            "query": query,
            "format": "json"
        }
        
        # Set up headers
        headers = {
            "Accept": "application/json",
            "User-Agent": _USER_AGENT
        }
        
        dataset_id = f"wikidata_{query_type}_{entity_id}"
        
        # Save request metadata before making the request
        save_request_metadata(
            dataset_id,
            params,
            source_name=_SOURCE_NAME,
            url=_SPARQL_ENDPOINT
        )
        
        # Make the API request with retries
        query_results = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.get(
                    _SPARQL_ENDPOINT,
                    params=params,
                    headers=headers,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                query_results = response.json()
                
                # Save API response
                save_api_response(
                    dataset_id,
                    query_results,
                    source_name=_SOURCE_NAME,
                    timestamp=dt.datetime.now().isoformat(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
                break
            except Exception as e:
                logger.warning(f"[wikidata_plugin] Request attempt {attempt+1} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_WAIT)
        
        # If all attempts failed, return None
        if not query_results:
            logger.error(f"[wikidata_plugin] Failed to fetch data for entity {entity_id} after {self.MAX_RETRIES + 1} attempts")
            return None
        
        # Process the results
        try:
            # Extract the bindings from the results
            bindings = query_results.get("results", {}).get("bindings", [])
            if not bindings:
                logger.warning(f"[wikidata_plugin] No results found for entity {entity_id}")
                return None
            
            # Process the bindings into a more usable format
            processed_results = []
            for binding in bindings:
                processed_result = {}
                for key, value in binding.items():
                    # Extract the actual value based on type
                    if value["type"] == "uri":
                        processed_result[key] = value["value"]
                    elif value["type"] == "literal":
                        if "datatype" in value and "date" in value["datatype"]:
                            # Parse dates
                            processed_result[key] = value["value"]
                        elif "datatype" in value and any(num_type in value["datatype"] for num_type in ["decimal", "integer", "float"]):
                            # Parse numbers
                            try:
                                processed_result[key] = float(value["value"])
                            except ValueError:
                                processed_result[key] = value["value"]
                        else:
                            # Keep as string
                            processed_result[key] = value["value"]
                
                processed_results.append(processed_result)
            
            return processed_results
        except Exception as e:
            logger.error(f"[wikidata_plugin] Error processing query results for entity {entity_id}: {e}")
            return None
    
    def _process_query_results(self, domain: str, entity_id: str, entity_name: str, query_type: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process SPARQL query results into signals.
        
        Args:
            domain: Domain of the entity
            entity_id: Wikidata entity ID
            entity_name: Human-readable name of the entity
            query_type: Type of query that was executed
            results: Results from the SPARQL query
            
        Returns:
            List of signal dictionaries
        """
        signals = []
        
        # Process the first result (SPARQL queries typically return just one row for our queries)
        if results:
            result = results[0]  # Take the first result
            safe_entity_name = re.sub(r'[^a-zA-Z0-9]', '_', entity_name.lower())
            
            # Process based on the query type
            if query_type == "company_info":
                # Extract company information
                if "employeeCount" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_employee_count",
                        "value": float(result["employeeCount"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "employee_count",
                            "unit": "employees"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_employee_count",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "revenueUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_revenue",
                        "value": float(result["revenueUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "revenue",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_revenue",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "netIncomeUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_net_income",
                        "value": float(result["netIncomeUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "net_income",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_net_income",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                # Create a company profile signal with all available data
                profile_data = {k: v for k, v in result.items()}
                profile_signal = {
                    "name": f"wikidata_{domain}_{safe_entity_name}_profile",
                    "value": 1.0,  # Presence indicator
                    "source": "wikidata",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "domain": domain,
                        "data_type": "company_profile",
                        "profile": profile_data
                    }
                }
                signals.append(profile_signal)
                save_processed_data(
                    f"{domain}_{safe_entity_name}_profile",
                    profile_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=profile_signal["timestamp"]
                )
                
            elif query_type == "country_economic_data":
                # Extract country economic data
                if "population" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_population",
                        "value": float(result["population"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "population",
                            "unit": "people"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_population",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "gdpUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_gdp",
                        "value": float(result["gdpUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "gdp",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_gdp",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "gdpPerCapitaUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_gdp_per_capita",
                        "value": float(result["gdpPerCapitaUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "gdp_per_capita",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_gdp_per_capita",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "inflationRate" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_inflation_rate",
                        "value": float(result["inflationRate"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "inflation_rate",
                            "unit": "%"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_inflation_rate",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "unemploymentRate" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_unemployment_rate",
                        "value": float(result["unemploymentRate"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "unemployment_rate",
                            "unit": "%"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_unemployment_rate",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                # Country profile with all data
                profile_data = {k: v for k, v in result.items()}
                profile_signal = {
                    "name": f"wikidata_{domain}_{safe_entity_name}_profile",
                    "value": 1.0,  # Presence indicator
                    "source": "wikidata",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "domain": domain,
                        "data_type": "country_profile",
                        "profile": profile_data
                    }
                }
                signals.append(profile_signal)
                save_processed_data(
                    f"{domain}_{safe_entity_name}_profile",
                    profile_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=profile_signal["timestamp"]
                )
                
            elif query_type == "central_bank_info":
                # Extract central bank information
                if "bankRatePercent" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_bank_rate",
                        "value": float(result["bankRatePercent"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "bank_rate",
                            "unit": "%"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_bank_rate",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "reservesUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_reserves",
                        "value": float(result["reservesUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "reserves",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_reserves",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                # Central bank profile
                profile_data = {k: v for k, v in result.items()}
                profile_signal = {
                    "name": f"wikidata_{domain}_{safe_entity_name}_profile",
                    "value": 1.0,  # Presence indicator
                    "source": "wikidata",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "domain": domain,
                        "data_type": "central_bank_profile",
                        "profile": profile_data
                    }
                }
                signals.append(profile_signal)
                save_processed_data(
                    f"{domain}_{safe_entity_name}_profile",
                    profile_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=profile_signal["timestamp"]
                )
                
            elif query_type == "commodity_info":
                # Extract commodity information
                if "priceUSD" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_price",
                        "value": float(result["priceUSD"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "price",
                            "unit": "USD"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_price",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                if "abundanceEarth" in result:
                    signal = {
                        "name": f"wikidata_{domain}_{safe_entity_name}_abundance",
                        "value": float(result["abundanceEarth"]),
                        "source": "wikidata",
                        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                        "metadata": {
                            "entity_id": entity_id,
                            "entity_name": entity_name,
                            "domain": domain,
                            "data_type": "abundance",
                            "unit": "ppm"
                        }
                    }
                    signals.append(signal)
                    save_processed_data(
                        f"{domain}_{safe_entity_name}_abundance",
                        signal,
                        source_name=_SOURCE_NAME,
                        timestamp=signal["timestamp"]
                    )
                
                # Commodity profile
                profile_data = {k: v for k, v in result.items()}
                profile_signal = {
                    "name": f"wikidata_{domain}_{safe_entity_name}_profile",
                    "value": 1.0,  # Presence indicator
                    "source": "wikidata",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "domain": domain,
                        "data_type": "commodity_profile",
                        "profile": profile_data
                    }
                }
                signals.append(profile_signal)
                save_processed_data(
                    f"{domain}_{safe_entity_name}_profile",
                    profile_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=profile_signal["timestamp"]
                )
                
            elif query_type == "economic_indicator_info":
                # Economic indicator profile
                profile_data = {k: v for k, v in result.items()}
                profile_signal = {
                    "name": f"wikidata_{domain}_{safe_entity_name}_profile",
                    "value": 1.0,  # Presence indicator
                    "source": "wikidata",
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "metadata": {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "domain": domain,
                        "data_type": "economic_indicator_profile",
                        "profile": profile_data
                    }
                }
                signals.append(profile_signal)
                save_processed_data(
                    f"{domain}_{safe_entity_name}_profile",
                    profile_signal,
                    source_name=_SOURCE_NAME,
                    timestamp=profile_signal["timestamp"]
                )
        
        return signals
    
    def get_knowledge_domains(self) -> Dict[str, List[str]]:
        """Get available knowledge domains.
        
        Returns:
            Dictionary with domain names as keys and lists of entity names as values
        """
        domains = {}
        for domain, entities in _DOMAINS.items():
            domains[domain] = [entity["name"] for entity in entities]
        
        return domains
    
    def get_entity_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """Get entity details by name.
        
        Args:
            name: Name of the entity to find
            
        Returns:
            Dictionary with entity details, or None if not found
        """
        # Search in all domains
        for domain, entities in _DOMAINS.items():
            for entity in entities:
                if entity["name"].lower() == name.lower():
                    return {"id": entity["id"], "name": entity["name"], "domain": domain}
        
        return None
