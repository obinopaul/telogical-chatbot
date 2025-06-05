"""This module provides example tools for for the LangChain platform.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional, cast, Dict, Literal, Union
from typing_extensions import Annotated
import json
from enum import Enum
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator
from typing import List, Optional, Dict, Any
import traceback
from langchain.tools.base import StructuredTool
from langchain_core.runnables import Runnable
from langchain.prompts import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import AzureChatOpenAI
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timedelta
import asyncio
import aiohttp
import random 
import re
import pandas as pd 
from langchain.schema import HumanMessage, AIMessage
from langchain_core.messages import AnyMessage, HumanMessage
from langchain.chains import create_retrieval_chain
from langchain.tools import BaseTool, Tool
from langgraph_swarm import create_handoff_tool, create_swarm, add_active_agent_router
import requests
import logging
from dotenv import load_dotenv
load_dotenv()

# ------------------------------------------------------------------------------------------------------------------------------

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Get absolute path to the data directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
data_dir = os.path.join(project_root, "data")

# Use absolute paths for the CSV files
ZIP_CODE_CSV_PATH = os.path.join(data_dir, os.getenv("ZIP_CODE_CSV_PATH", "geo-data.csv"))
DMA_CSV_PATH = os.path.join(data_dir, os.getenv("DMA_CSV_PATH", "DMAs.csv"))

# Debug message to verify path
# print(f"Looking for ZIP code file at: {ZIP_CODE_CSV_PATH}")
# print(f"Looking for DMA file at: {DMA_CSV_PATH}")
# --- Constants (Replace with your actual values or load from environment) ---
DEFAULT_GRAPHQL_ENDPOINT = os.getenv("TELOGICAL_GRAPHQL_ENDPOINT_2", "YOUR_GRAPHQL_ENNDPOINT_HERE")
DEFAULT_AUTH_TOKEN = os.getenv("TELOGICAL_AUTH_TOKEN_2", "YOUR_AUTH_TOKEN_HERE")
DEFAULT_LOCALE = os.getenv("TELOGICAL_LOCALE", "YOUR_LOCALE_HERE")
# Path to CSV files in the data folder
DEFAULT_TIMEOUT = 30  # seconds for each GraphQL request


# --- Telogical LLM ---
TELOGICAL_MODEL_ENDPOINT_GPT = os.getenv("TELOGICAL_MODEL_ENDPOINT_GPT")
TELOGICAL_API_KEY_GPT = os.getenv("TELOGICAL_API_KEY_GPT")
TELOGICAL_MODEL_DEPLOYMENT_GPT = os.getenv("TELOGICAL_MODEL_DEPLOYMENT_GPT")
TELOGICAL_MODEL_API_VERSION_GPT = os.getenv("TELOGICAL_MODEL_API_VERSION_GPT")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

llm_telogical = AzureChatOpenAI(
    azure_deployment=TELOGICAL_MODEL_DEPLOYMENT_GPT,  # Your deployment name in Azure
    api_version=TELOGICAL_MODEL_API_VERSION_GPT,  # Or the version you're using
    azure_endpoint=TELOGICAL_MODEL_ENDPOINT_GPT,
    api_key=TELOGICAL_API_KEY_GPT,
)

# llm_telogical = ChatNVIDIA(
#                 model='meta/llama-4-scout-17b-16e-instruct',
#                 api_key = NVIDIA_API_KEY
#         )


# llm_telogical = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-preview-05-20",
#     api_key=GEMINI_API_KEY,
# )

# ------------------------------------------------------------------------------
# --- Tool 2: zipcode_finder_tool (Find Zip Codes) ---
# -------------------------------------------------------------------------------

"""
This module provides a flexible ZipCode Finder tool for LangChain that's more robust
to different input formats from LLMs.
"""




class LocationType(str, Enum):
    """Valid location types for ZIP code searches."""
    CITY = 'city'
    COUNTY = 'county'
    STATE = 'state'

class ZipCodeFinder:
    """
    Utility class to find ZIP codes based on location information from a local CSV,
    with optional state filtering for disambiguation.
    """
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        # Standardize column names expected in the CSV
        self.COLUMNS = {
            'zip': 'zipcode',
            'city': 'city',
            'county': 'county',
            'state_full': 'state',
            'state_abbr': 'state_abbr'
        }
        self.df = self._load_data()
        if self.df is None:
            raise RuntimeError(f"Failed to load or prepare data from {csv_path}")
        log.info(f"ZipCodeFinder initialized with data from {csv_path}")

    def _load_data(self) -> Optional[pd.DataFrame]:
        """Load and prepare the ZIP code data."""
        if not os.path.exists(self.csv_path):
            log.error(f"ZIP code CSV file not found: {self.csv_path}")
            return None

        try:
            df = pd.read_csv(self.csv_path, low_memory=False)
            df.columns = [str(col).strip().lower() for col in df.columns]

            # Check if essential columns exist
            missing_cols = [col for col in self.COLUMNS.values() if col not in df.columns]
            if missing_cols:
                log.error(f"CSV file {self.csv_path} is missing required columns: {missing_cols}")
                return None

            # Ensure zipcode is string type with leading zeros
            df[self.COLUMNS['zip']] = df[self.COLUMNS['zip']].astype(str).str.zfill(5)

            # Convert relevant text columns to lowercase for matching
            for key in ['city', 'county', 'state_full', 'state_abbr']:
                col_name = self.COLUMNS[key]
                if col_name in df.columns and df[col_name].dtype == 'object':
                    # Handle potential NaN/None values before lowercasing
                    df[col_name] = df[col_name].fillna('').astype(str).str.lower().str.strip()

            log.info(f"Successfully loaded and processed {len(df)} rows from {self.csv_path}")
            return df

        except Exception as e:
            log.error(f"Error loading or processing CSV file {self.csv_path}: {e}")
            return None

    def get_zipcode(self,
                   location: str,
                   location_type: LocationType,
                   state_qualifier: Optional[str] = None) -> Optional[str]:
        """
        Get a single random ZIP code for a location, optionally filtered by state.

        Args:
            location: Location name (e.g., 'Norman', 'Cleveland', 'Illinois', 'OK').
                      Search is case-insensitive.
            location_type: Type of the location (CITY, COUNTY, STATE).
            state_qualifier: Optional state name or abbreviation to filter results.

        Returns:
            A single ZIP code (as string) or None if no match found.
        """
        if self.df is None:
            log.warning("ZipCodeFinder DataFrame not loaded. Cannot search.")
            return None
        if not location or not location.strip():
            log.warning("Location cannot be empty.")
            return None

        primary_search_val = location.lower().strip()
        primary_search_col = ''

        # Determine primary search column and handle state searches directly
        if location_type == LocationType.CITY:
            primary_search_col = self.COLUMNS['city']
        elif location_type == LocationType.COUNTY:
            primary_search_col = self.COLUMNS['county']
        elif location_type == LocationType.STATE:
            # If primary type is STATE, check if input looks like abbr or full name
            if len(primary_search_val) == 2:
                primary_search_col = self.COLUMNS['state_abbr']
            else:
                primary_search_col = self.COLUMNS['state_full']
            state_qualifier = None  # State qualifier is redundant for state searches
        else:
            log.error(f"Invalid location_type provided: {location_type}")
            return None

        if primary_search_col not in self.df.columns:
            log.error(f"Primary search column '{primary_search_col}' not found in DataFrame.")
            return None

        # Initial filter based on primary location
        try:
            filtered_df = self.df[self.df[primary_search_col] == primary_search_val].copy()
        except Exception as e:
            log.error(f"Error during filtering for '{primary_search_val}' in '{primary_search_col}': {e}")
            return None

        if filtered_df.empty:
            log.info(f"No match found for {location_type.value} '{location}'.")
            return None

        # Apply secondary state filter if provided and needed
        if state_qualifier and state_qualifier.strip() and location_type != LocationType.STATE:
            state_qualifier_val = state_qualifier.lower().strip()
            # Determine if qualifier is abbr or full name
            is_abbr = len(state_qualifier_val) == 2
            state_col = self.COLUMNS['state_abbr'] if is_abbr else self.COLUMNS['state_full']

            if state_col not in filtered_df.columns:
                log.warning(f"State column '{state_col}' not found for filtering by '{state_qualifier}'. Using primary results only.")
            else:
                # Apply the secondary filter
                try:
                    filtered_df = filtered_df[filtered_df[state_col] == state_qualifier_val]
                except Exception as e:
                    log.error(f"Error filtering by state '{state_qualifier_val}': {e}")
                    return None

        # Final check if df is empty after state filter
        if filtered_df.empty:
            log.info(f"No match found for {location_type.value} '{location}' in state '{state_qualifier}'.")
            return None

        # Get all matching zip codes
        zip_codes = filtered_df[self.COLUMNS['zip']].unique().tolist()
        
        if not zip_codes:
            return None
            
        # Select one random zip code
        selected_zip = random.choice(zip_codes)
        
        log.info(f"Selected random zip code '{selected_zip}' for {location_type.value} '{location}'"
                f"{f' in state {state_qualifier}' if state_qualifier else ''} from {len(zip_codes)} options.")
        return selected_zip

    def parse_location_string(self, location_string: str) -> Dict[str, Any]:
        """
        Parse a location string like "Norman, OK" into its components.
        
        Args:
            location_string: A string representing a location, potentially with state
            
        Returns:
            Dictionary with location, location_type, and state if present
        """
        parts = [part.strip() for part in location_string.split(',')]
        
        if len(parts) == 1:
            # No comma, just a location name
            location = parts[0]
            # If it's 2 letters, assume it's a state abbreviation
            if len(location) == 2 and location.isalpha():
                return {"location": location, "location_type": "state"}
            else:
                return {"location": location, "location_type": "city"}
        elif len(parts) == 2:
            # Location, State format
            location, state = parts
            # If state is 2 letters, it's likely an abbreviation
            if len(state) == 2 and state.isalpha():
                return {"location": location, "location_type": "city", "state": state}
            else:
                # Could be "County, State"
                if "county" in location.lower():
                    location = location.lower().replace("county", "").strip()
                    return {"location": location, "location_type": "county", "state": state}
                else:
                    return {"location": location, "location_type": "city", "state": state}
        
        # Default fallback
        return {"location": location_string, "location_type": "city"}


# Initialize the shared instance
try:
    shared_zip_finder = ZipCodeFinder(ZIP_CODE_CSV_PATH)
except Exception as e:
    log.error(f"Failed to initialize ZipCodeFinder: {e}")
    shared_zip_finder = None


# Simple input schema for the tool - accepts different formats
class SimpleZipCodeInput(BaseModel):
    """Simplified input schema for the ZIP code finder tool."""
    location: str = Field(
        ..., 
        description="Location to find zip code for (e.g., 'Norman, OK' or 'Chicago, Illinois')"
    )


# Multi-location input schema for the tool
class MultiLocationZipCodeInput(BaseModel):
    """Input schema for finding ZIP codes for multiple locations."""
    location_names: List[str] = Field(
        ...,
        description="List of location names (e.g., ['Norman', 'Chicago', 'Miami'])"
    )
    location_types: Optional[List[str]] = Field(
        None,
        description="Optional list of location types ('city', 'county', 'state') corresponding to each location name. "
                   "If not provided, will default to 'city' for each location."
    )
    states: Optional[List[Optional[str]]] = Field(
        None,
        description="Optional list of states (name or abbreviation) to disambiguate locations. "
                   "Use empty string or null for locations that don't need state qualification."
    )
    
    @model_validator(mode='before')
    @classmethod
    def validate_and_normalize_inputs(cls, data):
        """Ensure all lists are the same length and have proper defaults."""
        if not isinstance(data, dict):
            return data
            
        if "location_names" not in data or not data["location_names"]:
            raise ValueError("location_names must be provided and cannot be empty")
            
        # Ensure location_names is a list
        if isinstance(data["location_names"], str):
            data["location_names"] = [data["location_names"]]
            
        num_locations = len(data["location_names"])
        
        # Set default location types if not provided
        if "location_types" not in data or not data["location_types"]:
            data["location_types"] = ["city"] * num_locations
        elif len(data["location_types"]) < num_locations:
            # Extend with defaults if too short
            data["location_types"].extend(["city"] * (num_locations - len(data["location_types"])))
            
        # Set default states if not provided
        if "states" not in data or not data["states"]:
            data["states"] = [""] * num_locations  # Use empty strings instead of None
        elif len(data["states"]) < num_locations:
            # Extend with empty strings if too short
            data["states"].extend([""] * (num_locations - len(data["states"])))
            
        # Convert None values to empty strings in states
        if "states" in data and data["states"]:
            data["states"] = ["" if s is None or s == "null" or s == "none" or s == "" else s 
                             for s in data["states"]]
            
        return data


class ZipCodeFinderTool:
    """Tool to find ZIP codes for locations with flexible input handling."""
    
    def __init__(self):
        self.finder = shared_zip_finder
        
    def find_single_zipcode(self, location: str) -> Dict[str, Any]:
        """
        Find a ZIP code for a single location string like "Norman, OK".
        
        Args:
            location: Location string
            
        Returns:
            Dictionary with the result
        """
        if not self.finder:
            return {"error": "ZipCodeFinder is not initialized. Check CSV path and format."}
            
        try:
            # Parse the location string
            location_info = self.finder.parse_location_string(location)
            
            # Get the zipcode
            zipcode = self.finder.get_zipcode(
                location=location_info["location"],
                location_type=location_info["location_type"],
                state_qualifier=location_info.get("state")
            )
            
            if zipcode:
                return {
                    "location": location,
                    "zipcode": zipcode,
                    "status": "success",
                    "parsed_as": location_info
                }
            else:
                return {
                    "location": location,
                    "zipcode": None,
                    "status": "no_results_found",
                    "parsed_as": location_info
                }
                
        except Exception as e:
            log.error(f"Error finding zipcode for '{location}': {e}")
            return {
                "location": location,
                "error": str(e),
                "status": "error"
            }
    
    def find_multiple_zipcodes(self, structured_locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find ZIP codes for multiple locations.
        
        Args:
            structured_locations: List of structured location dictionaries
            
        Returns:
            Dictionary with results for each location
        """
        if not self.finder:
            return {"error": "ZipCodeFinder is not initialized. Check CSV path and format."}
            
        results = {}
        
        for loc in structured_locations:
            # Handle structured location
            location = loc.get("location", "")
            if not location:
                continue
                
            location_type_str = loc.get("location_type", "city")
            try:
                location_type = LocationType(location_type_str.lower())
            except ValueError:
                location_type = LocationType.CITY
                
            state = loc.get("state")
            if state == "":
                state = None
            
            # Create a display name that includes state if available
            display_name = location
            if state:
                display_name = f"{location}, {state}"
            
            zipcode = self.finder.get_zipcode(
                location=location,
                location_type=location_type,
                state_qualifier=state
            )
            
            if zipcode:
                results[display_name] = {
                    "zipcode": zipcode,
                    "status": "success",
                    "location_type": location_type.value,
                    "state": state
                }
            else:
                results[display_name] = {
                    "zipcode": None,
                    "status": "no_results_found",
                    "location_type": location_type.value,
                    "state": state
                }
            
        return {
            "results": results,
            "total_locations_processed": len(structured_locations),
            "locations_with_results": sum(1 for loc, data in results.items() 
                                         if data.get("status") == "success")
        }


# Function wrapper for multi-location tool
def find_multiple_zipcodes(
    location_names: List[str],
    location_types: Optional[List[str]] = None,
    states: Optional[List[Optional[str]]] = None
) -> Dict[str, Any]:
    """
    Find ZIP codes for multiple locations.
    
    Args:
        location_names: List of location names (e.g., ['Norman', 'Chicago', 'Miami-Dade'])
        location_types: Optional list of location types ('city', 'county', 'state')
                       corresponding to each location name
        states: Optional list of states to disambiguate locations
                 
    Returns:
        Dictionary with results for each location
    """
    tool = ZipCodeFinderTool()
    
    # Handle defaults
    num_locations = len(location_names)
    if not location_types:
        location_types = ["city"] * num_locations
    if not states:
        states = [""] * num_locations  # Empty strings instead of None
        
    # Create structured location list
    structured_locations = []
    for i in range(num_locations):
        loc_type = location_types[i] if i < len(location_types) else "city"
        state = states[i] if i < len(states) else ""
        
        # Convert None or special values to empty string
        if state is None or state == "null" or state == "none":
            state = ""
            
        loc = {
            "location": location_names[i],
            "location_type": loc_type
        }
        if state:  # Only add state if it's not empty
            loc["state"] = state
            
        structured_locations.append(loc)
        
    return tool.find_multiple_zipcodes(structured_locations)


# Create simple tool for single location lookups
def find_zipcode_simple(location: str) -> str:
    """
    Find a ZIP code for a location.
    
    Args:
        location: Location string (e.g., 'Norman, OK' or 'Chicago, Illinois')
        
    Returns:
        Result string with the ZIP code or error message
    """
    tool = ZipCodeFinderTool()
    result = tool.find_single_zipcode(location)
    
    if result.get("status") == "success":
        return f"The ZIP code for {result['location']} is {result['zipcode']}."
    elif result.get("status") == "no_results_found":
        return f"No ZIP code found for {result['location']}."
    else:
        return f"Error finding ZIP code for {result['location']}: {result.get('error', 'Unknown error')}"


# Create the LangChain Tool for simple queries
zipcode_finder_simple = Tool(
    name="zipcode_finder_simple",
    description=(
        "Find a ZIP code for a location. Input should be a location string like 'City, State' "
        "or just 'City' or 'State'. Examples: 'Norman, OK', 'Chicago, Illinois', 'New York'"
    ),
    func=find_zipcode_simple
)


# Create the LangChain StructuredTool for multiple locations
zipcode_finder_tool = StructuredTool(
    name="zipcode_finder_tool",
    description=(
        "Find ZIP codes for one or more locations. Provide these parameters: "
        "'location_names' (required): list of location names (e.g., ['Norman', 'Chicago', 'Miami']), "
        "'location_types' (optional): list of location types ('city', 'county', 'state') corresponding to each location, "
        "'states' (optional): list of states to disambiguate locations (e.g., ['OK', 'IL', 'FL']). "
        "Use empty strings for locations that don't need state qualification. "
        "The tool returns exactly one ZIP code for each location. "
        "Example input: {'location_names': ['Norman', 'Chicago'], 'location_types': ['city', 'city'], 'states': ['OK', 'IL']}"
    ),
    func=find_multiple_zipcodes,
    args_schema=MultiLocationZipCodeInput
)


# ---------------------------------------------------------------------------
# Tool 2: GraphQL Query Tool (Parallel Execution)
# ---------------------------------------------------------------------------


class GraphQLQuery(BaseModel):
    """Schema for a single GraphQL query execution."""
    query: str = Field(
        ...,
        description="The GraphQL query string to execute."
    )
    query_id: Optional[str] = Field(
        None,
        description="Identifier for this query to help track results."
    )

class ParallelGraphQLExecutorInput(BaseModel):
    """Input schema for the Parallel GraphQL Executor tool."""
    queries: List[Union[GraphQLQuery, str, Dict[str, Any]]] = Field(
        ...,
        description="List of GraphQL queries to execute in parallel. Each item can be a GraphQLQuery object, a string (the query itself), or a dictionary containing 'query' and optional 'query_id'."
    )

    @field_validator('queries')
    def validate_queries(cls, queries):
        """Validate and normalize the list of queries."""
        if not queries:
            raise ValueError("The queries list cannot be empty.")

        normalized_queries = []
        for i, query in enumerate(queries):
            if isinstance(query, str):
                normalized_queries.append(GraphQLQuery(query=query, query_id=f"query_{i+1}"))
            elif isinstance(query, dict):
                try:
                    # Extract only the supported fields
                    query_data = {
                        "query": query.get("query"),
                        "query_id": query.get("query_id")
                    }
                    normalized_queries.append(GraphQLQuery(**query_data))
                except ValidationError as e:
                    raise ValueError(f"Invalid query format at index {i}: {e}")
            elif isinstance(query, GraphQLQuery):
                normalized_queries.append(query)
            else:
                raise ValueError(f"Invalid query format at index {i}. Expected a string, dict, or GraphQLQuery object.")
        return normalized_queries

class ParallelGraphQLExecutor:
    """
    A robust tool that executes multiple GraphQL queries in parallel.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        auth_token: Optional[str] = None,
        locale: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the GraphQL executor with configuration options.

        Args:
            endpoint: GraphQL API endpoint URL. Defaults to environment variable.
            auth_token: Authorization token for the GraphQL API. Defaults to environment variable.
            locale: Locale setting for the API. Defaults to environment variable.
            timeout: Timeout in seconds for each GraphQL request. Defaults to 30 seconds.
        """
        self.endpoint = endpoint or DEFAULT_GRAPHQL_ENDPOINT
        self.auth_token = auth_token or DEFAULT_AUTH_TOKEN
        self.locale = locale or DEFAULT_LOCALE
        self.timeout = timeout

        # Basic configuration validation
        if self.endpoint == "YOUR_GRAPHQL_ENDPOINT_HERE":
            log.warning("Using placeholder GraphQL endpoint. Please configure the actual endpoint.")
        if self.auth_token == "YOUR_AUTH_TOKEN_HERE":
            log.warning("Using placeholder auth token. Authentication may fail.")

    async def _execute_single_query(self, session: aiohttp.ClientSession, query_item: GraphQLQuery) -> Dict[str, Any]:
        """
        Asynchronously execute a single GraphQL query using the provided session.

        Args:
            session: aiohttp ClientSession for making the request.
            query_item: GraphQLQuery object with the query and associated data.

        Returns:
            Dictionary with the query results, status, and any error information.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Locale": self.locale
        }
        payload = {
            "query": query_item.query
        }

        query_id = query_item.query_id or "unnamed_query"

        try:
            async with session.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "query_id": query_id,
                        "status": "success",
                        "result": result.get("data"),  # Return only the 'data' part of the response
                        "errors": result.get("errors")  # Include any GraphQL errors
                    }
                else:
                    error_text = await response.text()
                    log.error(f"Query {query_id} failed with status {response.status}: {error_text}")
                    return {
                        "query_id": query_id,
                        "status": "error",
                        "error": f"HTTP Error: {response.status}",
                        "details": error_text
                    }
        except asyncio.TimeoutError:
            log.error(f"Query {query_id} timed out")
            return {
                "query_id": query_id,
                "status": "error",
                "error": "Timeout",
                "details": f"The query execution timed out after {self.timeout} seconds."
            }
        except aiohttp.ClientError as e:
            log.error(f"Query {query_id} failed due to a client error: {str(e)}")
            return {
                "query_id": query_id,
                "status": "error",
                "error": f"Client Error: {type(e).__name__}",
                "details": str(e)
            }
        except Exception as e:
            log.error(f"Query {query_id} failed with an unexpected exception: {str(e)}")
            return {
                "query_id": query_id,
                "status": "error",
                "error": f"Exception: {type(e).__name__}",
                "details": str(e)
            }

    async def execute_queries_async(self, queries: List[GraphQLQuery]) -> Dict[str, Any]:
        """
        Asynchronously execute multiple GraphQL queries in parallel.

        Args:
            queries: List of GraphQLQuery objects to execute.

        Returns:
            Dictionary where keys are the query_ids and values are the results of each query.
        """
        if not queries:
            return {"error": "No queries provided"}
        if self.endpoint == "YOUR_GRAPHQL_ENDPOINT_HERE":
            return {"error": "GraphQL endpoint not configured. Please set the TELOGICAL_GRAPHQL_ENDPOINT environment variable or pass it during tool initialization."}

        async with aiohttp.ClientSession() as session:
            tasks = [self._execute_single_query(session, query) for query in queries]
            results = await asyncio.gather(*tasks)

        # Structure the output by query_id
        structured_results = {result.get("query_id"): result for result in results}
        return structured_results

    def execute_queries(self, queries: List[Union[GraphQLQuery, str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Synchronous wrapper for the asynchronous execution function.

        Args:
            queries: List of GraphQL queries to execute (can be strings, dicts, or GraphQLQuery objects).

        Returns:
            Dictionary where keys are the query_ids and values are the results of each query.
        """
        try:
            normalized_queries = ParallelGraphQLExecutorInput(queries=queries).queries
        except ValidationError as e:
            return {"error": "Invalid input format for queries", "details": str(e)}

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.execute_queries_async(normalized_queries))

# Create the LangChain StructuredTool instance
parallel_graphql_executor = StructuredTool(
    name="parallel_graphql_executor",
    description=(
        "Executes multiple GraphQL queries in parallel against a specified endpoint. "
        "This tool is highly efficient for fetching data requiring multiple GraphQL calls. "
        "Input is a list of GraphQL queries, which can be provided as strings or objects "
        "with 'query' and 'query_id' fields. The output is a dictionary keyed by the query "
        "identifiers, containing the execution status and results. Variables should be "
        "hardcoded directly in your query strings."
    ),
    func=ParallelGraphQLExecutor().execute_queries,
    args_schema=ParallelGraphQLExecutorInput
)


# ---------------------------------------------------------------------------
# Tool 3: Introspection Tool
# ---------------------------------------------------------------------------

# GraphQL introspection query templates
INTROSPECTION_QUERIES = {
    "full_schema": """
    query IntrospectionQuery {
      __schema {
        queryType {
          name
        }
        mutationType {
          name
        }
        subscriptionType {
          name
        }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }

    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        ...InputValue
      }
      interfaces {
        ...TypeRef
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }

    fragment InputValue on __InputValue {
      name
      description
      type {
        ...TypeRef
      }
      defaultValue
    }

    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """,
    
    "types_only": """
    query TypesQuery {
      __schema {
        types {
          name
          kind
          description
        }
      }
    }
    """,
    
    "queries_only": """
    query QueryFields {
    __schema {
        queryType {
        name
        fields {
            name
            description
            type {
            kind
            name
            ofType {
                kind
                name
            }
            }
            args {
            name
            description
            type {
                kind
                name
                ofType {
                kind
                name
                }
            }
            defaultValue
            }
        }
        }
        types {
        name
        kind
        description
        inputFields {
            name
            description
            type {
            kind
            name
            ofType {
                kind
                name
            }
            }
            defaultValue
        }
        }
    }
    }
    """,
    
    "mutations_only": """
    query MutationFields {
      __schema {
        mutationType {
          name
          fields {
            name
            description
            args {
              name
              description
              type {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
              defaultValue
            }
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
        }
      }
    }
    """,
    
    "type_details": """
    query TypeDetails($typeName: String!) {
      __type(name: $typeName) {
        name
        kind
        description
        fields(includeDeprecated: true) {
          name
          description
          args {
            name
            description
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
            defaultValue
          }
          type {
            name
            kind
            ofType {
              name
              kind
              ofType {
                name
                kind
              }
            }
          }
          isDeprecated
          deprecationReason
        }
        inputFields {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
          defaultValue
        }
        interfaces {
          name
        }
        enumValues(includeDeprecated: true) {
          name
          description
          isDeprecated
          deprecationReason
        }
        possibleTypes {
          name
        }
      }
    }
    """
}

class IntrospectionTool:
    """
    Tool for executing GraphQL introspection queries to explore API schemas.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        auth_token: Optional[str] = None,
        locale: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the GraphQL introspection tool with configuration options.
        
        Args:
            endpoint: GraphQL API endpoint URL. Defaults to environment variable.
            auth_token: Authorization token for the GraphQL API. Defaults to environment variable.
            locale: Locale setting for the API. Defaults to environment variable.
            timeout: Timeout in seconds for each GraphQL request. Defaults to 30 seconds.
        """
        self.endpoint = endpoint or DEFAULT_GRAPHQL_ENDPOINT
        self.auth_token = auth_token or DEFAULT_AUTH_TOKEN
        self.locale = locale or DEFAULT_LOCALE
        self.timeout = timeout
        
        # Basic configuration validation
        if self.endpoint == "YOUR_GRAPHQL_ENDPOINT_HERE":
            log.warning("Using placeholder GraphQL endpoint. Please configure the actual endpoint.")
        if self.auth_token == "YOUR_AUTH_TOKEN_HERE":
            log.warning("Using placeholder auth token. Authentication may fail.")
            
    async def execute_introspection_query(self, query_type: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL introspection query against the endpoint.
        
        Args:
            query_type: Type of introspection query to run (full_schema, types_only, etc.)
            variables: Optional variables to pass with the introspection query
            
        Returns:
            Dictionary with the introspection results
        """
        if query_type not in INTROSPECTION_QUERIES:
            return {
                "error": f"Unknown query type: {query_type}",
                "available_query_types": list(INTROSPECTION_QUERIES.keys())
            }
            
        query = INTROSPECTION_QUERIES[query_type]
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Locale": self.locale
        }
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "errors" in result:
                            return {
                                "status": "error",
                                "errors": result["errors"],
                                "message": "The introspection query returned errors"
                            }
                        
                        if "data" in result:
                            # Success case
                            return {
                                "status": "success",
                                "data": result["data"],
                                "query_type": query_type
                            }
                        
                        return {
                            "status": "error",
                            "message": "The response did not contain a data field",
                            "raw_response": result
                        }
                    else:
                        error_text = await response.text()
                        log.error(f"Introspection query failed with status {response.status}: {error_text}")
                        return {
                            "status": "error",
                            "error": f"HTTP Error: {response.status}",
                            "details": error_text
                        }
        except asyncio.TimeoutError:
            log.error(f"Introspection query timed out")
            return {
                "status": "error",
                "error": "Timeout",
                "details": f"The introspection query timed out after {self.timeout} seconds"
            }
        except aiohttp.ClientError as e:
            log.error(f"Introspection query failed due to a client error: {str(e)}")
            return {
                "status": "error",
                "error": f"Client Error: {type(e).__name__}",
                "details": str(e)
            }
        except Exception as e:
            log.error(f"Introspection query failed with an unexpected exception: {str(e)}")
            return {
                "status": "error",
                "error": f"Exception: {type(e).__name__}",
                "details": str(e)
            }
            
    def run_introspection(
        self, 
        query_type: Literal["full_schema", "types_only", "queries_only", "mutations_only", "type_details"],
        type_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a GraphQL introspection query synchronously.
        
        Args:
            query_type: Type of introspection query to run
            type_name: When query_type is 'type_details', this specifies which type to get details for
            
        Returns:
            Dictionary with the introspection results
        """
        variables = None
        if query_type == "type_details":
            if not type_name:
                return {
                    "status": "error",
                    "error": "Missing type_name",
                    "details": "The 'type_details' query requires a type_name parameter"
                }
            variables = {"typeName": type_name}
            
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(self.execute_introspection_query(query_type, variables))
        
        # For type_details query, add the requested type name to the result
        if query_type == "type_details" and result.get("status") == "success":
            result["type_name"] = type_name
            
        return result
        
    def analyze_schema(self, introspection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the schema to extract useful insights and summaries.
        
        Args:
            introspection_result: Result of an introspection query
            
        Returns:
            Dictionary with schema analysis results
        """
        if introspection_result.get("status") != "success":
            return {
                "status": "error",
                "error": "Cannot analyze failed introspection result",
                "details": introspection_result
            }
            
        data = introspection_result.get("data", {})
        schema = data.get("__schema")
        
        if not schema:
            return {
                "status": "error",
                "error": "No schema data found in introspection result"
            }
            
        analysis = {
            "status": "success",
            "summary": {}
        }
        
        # Get all types
        types = schema.get("types", [])
        if types:
            # Count types by kind
            type_counts = {}
            object_types = []
            input_types = []
            enum_types = []
            scalar_types = []
            interface_types = []
            union_types = []
            
            for t in types:
                kind = t.get("kind")
                if kind not in type_counts:
                    type_counts[kind] = 0
                type_counts[kind] += 1
                
                # Collect type names by category
                if kind == "OBJECT" and not t.get("name", "").startswith("__"):
                    object_types.append(t.get("name"))
                elif kind == "INPUT_OBJECT":
                    input_types.append(t.get("name"))
                elif kind == "ENUM":
                    enum_types.append(t.get("name"))
                elif kind == "SCALAR":
                    scalar_types.append(t.get("name"))
                elif kind == "INTERFACE":
                    interface_types.append(t.get("name"))
                elif kind == "UNION":
                    union_types.append(t.get("name"))
            
            analysis["summary"]["type_counts"] = type_counts
            analysis["summary"]["object_types"] = object_types
            analysis["summary"]["input_types"] = input_types
            analysis["summary"]["enum_types"] = enum_types
            analysis["summary"]["scalar_types"] = scalar_types
            analysis["summary"]["interface_types"] = interface_types
            analysis["summary"]["union_types"] = union_types
            
        # Get query and mutation operations
        query_type = schema.get("queryType", {})
        if query_type:
            query_name = query_type.get("name")
            analysis["summary"]["query_root_type"] = query_name
            
        mutation_type = schema.get("mutationType", {})
        if mutation_type:
            mutation_name = mutation_type.get("name")
            analysis["summary"]["mutation_root_type"] = mutation_name
            
        subscription_type = schema.get("subscriptionType", {})
        if subscription_type:
            subscription_name = subscription_type.get("name")
            analysis["summary"]["subscription_root_type"] = subscription_name
            
        # Get directives
        directives = schema.get("directives", [])
        if directives:
            directive_names = [d.get("name") for d in directives]
            analysis["summary"]["directives"] = directive_names
            
        return analysis
    
    def find_related_types(self, type_name: str, introspection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find types that are related to the specified type.
        
        Args:
            type_name: Name of the type to find relationships for
            introspection_result: Result of a full schema introspection query
            
        Returns:
            Dictionary with related types information
        """
        if introspection_result.get("status") != "success":
            return {
                "status": "error",
                "error": "Cannot analyze failed introspection result",
                "details": introspection_result
            }
            
        data = introspection_result.get("data", {})
        schema = data.get("__schema")
        
        if not schema:
            return {
                "status": "error",
                "error": "No schema data found in introspection result"
            }
            
        types = schema.get("types", [])
        
        # Find the target type
        target_type = None
        for t in types:
            if t.get("name") == type_name:
                target_type = t
                break
                
        if not target_type:
            return {
                "status": "error",
                "error": f"Type '{type_name}' not found in schema"
            }
            
        # Find relationships
        related_types = {
            "status": "success",
            "type_name": type_name,
            "fields_using_type": [],         # Fields in other types that return this type
            "input_fields_using_type": [],   # Input fields that use this type
            "implementing_types": [],        # Types that implement this interface (if it's an interface)
            "implemented_interfaces": [],    # Interfaces implemented by this type (if it's an object)
            "union_members": [],             # Union types that include this type
            "member_of_unions": []           # Union types that this type is a member of
        }
        
        # Find fields in other types that return this type
        for t in types:
            t_name = t.get("name")
            if t_name == type_name or t_name.startswith("__"):
                continue
                
            # Check fields
            fields = t.get("fields", [])
            for field in fields:
                field_type = field.get("type", {})
                
                # Unwrap non-null and list types to get to the named type
                while field_type.get("kind") in ["NON_NULL", "LIST"]:
                    field_type = field_type.get("ofType", {})
                    
                if field_type.get("name") == type_name:
                    related_types["fields_using_type"].append({
                        "type_name": t_name,
                        "field_name": field.get("name")
                    })
                    
            # Check input fields
            input_fields = t.get("inputFields", [])
            for field in input_fields:
                field_type = field.get("type", {})
                
                # Unwrap non-null and list types
                while field_type.get("kind") in ["NON_NULL", "LIST"]:
                    field_type = field_type.get("ofType", {})
                    
                if field_type.get("name") == type_name:
                    related_types["input_fields_using_type"].append({
                        "type_name": t_name,
                        "field_name": field.get("name")
                    })
                    
            # If this is an interface, find implementing types
            if target_type.get("kind") == "INTERFACE":
                possible_types = target_type.get("possibleTypes", [])
                for pt in possible_types:
                    related_types["implementing_types"].append(pt.get("name"))
                    
            # If this is an object, find implemented interfaces
            if target_type.get("kind") == "OBJECT":
                interfaces = target_type.get("interfaces", [])
                for iface in interfaces:
                    related_types["implemented_interfaces"].append(iface.get("name"))
                    
            # If this is a union, find member types
            if target_type.get("kind") == "UNION":
                possible_types = target_type.get("possibleTypes", [])
                for pt in possible_types:
                    related_types["union_members"].append(pt.get("name"))
                    
            # Find unions that include this type
            if t.get("kind") == "UNION":
                possible_types = t.get("possibleTypes", [])
                for pt in possible_types:
                    if pt.get("name") == type_name:
                        related_types["member_of_unions"].append(t_name)
                        
        return related_types

# Input schema for the introspection tool
class GraphQLIntrospectionInput(BaseModel):
    """Input schema for the GraphQL Introspection Tool."""
    query_type: Literal["full_schema", "types_only", "queries_only", "mutations_only", "type_details"] = Field(
        ...,
        description="Type of introspection query to run"
    )
    type_name: Optional[str] = Field(
        None,
        description="When query_type is 'type_details', this specifies which type to get details for"
    )
    
    @model_validator(mode='before')
    @classmethod
    def validate_input(cls, data):
        """Validate that type_name is provided when necessary."""
        if isinstance(data, dict):
            query_type = data.get("query_type")
            type_name = data.get("type_name")
            
            if query_type == "type_details" and not type_name:
                raise ValueError("type_name is required when query_type is 'type_details'")
                
        return data

# Create the introspection tool object
introspection_tool = IntrospectionTool()

# Create the LangChain StructuredTool
graphql_introspection_tool = StructuredTool(
    name="graphql_introspection",
    description=(
        "Performs GraphQL introspection queries to explore API schemas. "
        "This tool can analyze schema structure, discover types, examine relationships between types, "
        "and provide detailed information about fields, arguments, and more. "
        "Available query types: full_schema, types_only, queries_only, mutations_only, type_details. "
        "When using 'type_details', you must also provide a 'type_name' parameter."
    ),
    func=introspection_tool.run_introspection,
    args_schema=GraphQLIntrospectionInput
)

# ---------------------------------------------------------------------------
# Tool 3b: GraphQL Introspection (schema_analyzer_tool)
# ---------------------------------------------------------------------------

# Create a schema analyzer tool for post-processing introspection results
class SchemaAnalysisInput(BaseModel):
    """Input schema for the Schema Analysis Tool."""
    introspection_result: Dict[str, Any] = Field(
        ...,
        description="The result of a graphql_introspection query to analyze"
    )

schema_analyzer_tool = StructuredTool(
    name="analyze_graphql_schema",
    description=(
        "Analyzes GraphQL introspection results to extract useful insights. "
        "This tool summarizes the schema structure, counts types by category, "
        "identifies key entry points, and provides other useful metadata about the schema. "
        "Input should be the result object from a previous graphql_introspection query."
    ),
    func=introspection_tool.analyze_schema,
    args_schema=SchemaAnalysisInput
)

# ---------------------------------------------------------------------------
# Tool 3c: GraphQL Introspection (type_relationships_tool)
# ---------------------------------------------------------------------------

# Create a type relationships tool
class TypeRelationshipsInput(BaseModel):
    """Input schema for the Type Relationships Tool."""
    type_name: str = Field(
        ...,
        description="Name of the type to find relationships for"
    )
    introspection_result: Dict[str, Any] = Field(
        ...,
        description="The result of a full_schema graphql_introspection query"
    )

type_relationships_tool = StructuredTool(
    name="find_graphql_type_relationships",
    description=(
        "Finds relationships between GraphQL types in a schema. "
        "This tool discovers which types reference the specified type, which fields use it, "
        "what interfaces it implements or are implemented by it, and its union type memberships. "
        "Requires a type_name and the result of a 'full_schema' introspection query."
    ),
    func=introspection_tool.find_related_types,
    args_schema=TypeRelationshipsInput
)


# ---------------------------------------------------------------------------
# Tool 4: Transfer tools
# ---------------------------------------------------------------------------


transfer_to_reflection_agent = create_handoff_tool(
    agent_name="ReflectionAgent",
    description=(
        "Use this tool to transfer the conversation to the 'ReflectionAgent' when experiencing persistent errors "
        "from database queries or tool calls. The ReflectionAgent specializes in analyzing errors in detail, "
        "diagnosing root causes from database schemas or tool execution, and can call specialized sub-tools "
        "to implement fixes. Transfer to this agent when standard error resolution approaches have failed multiple times."
    )
)

transfer_to_main_agent = create_handoff_tool(
    agent_name="MainAgent",
    description=(
        "Use this tool to transfer the conversation to the 'MainAgent' which handles primary conversation "
        "management, parallel query execution, and delivering final results to users. This agent has tools "
        "for location-based searches, finding zip codes for cities, retrieving database schemas, and executing "
        "primary queries. The MainAgent attempts to resolve errors independently but will transfer to the "
        "ReflectionAgent for persistent issues requiring specialized analysis."
    )
)


# ---------------------------------------------------------------------------
# Tool 5: Unified Introspection Tool (graphql_unified_introspection_tool)
# ---------------------------------------------------------------------------

# Combined GraphQL introspection query template
UNIFIED_INTROSPECTION_QUERY = """
query UnifiedIntrospectionQuery {
    __schema {
        queryType {
        name
        fields {
            name
            description
            type {
            kind
            name
            ofType {
                kind
                name
            }
            }
            args {
            name
            description
            type {
                kind
                name
                ofType {
                kind
                name
                }
            }
            defaultValue
            }
        }
        }
        types {
        name
        kind
        description
        inputFields {
            name
            description
            type {
            kind
            name
            ofType {
                kind
                name
            }
            }
            defaultValue
        }
        }

    mutationType {
      name
      fields {
        name
        description
        args {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
          defaultValue
        }
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
      }
    }
    types {
      name
      kind
      description
      fields {
        name
        description
        args {
          name
          description
          type {
            name
            kind
            ofType {
              name
              kind
            }
          }
          defaultValue
        }
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        name
        description
        type {
          name
          kind
          ofType {
            name
            kind
          }
        }
        defaultValue
      }
      interfaces {
        name
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        name
      }
    }
  }
}
"""

class UnifiedIntrospectionTool:
    """
    Tool for executing a unified GraphQL introspection query to explore the API schema.
    This query fetches the schema structure, available queries, mutations, types, fields, and their relationships in one go.
    """
    
    def __init__(self, endpoint: Optional[str] = None, auth_token: Optional[str] = None, locale: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self.endpoint = endpoint or DEFAULT_GRAPHQL_ENDPOINT
        self.auth_token = auth_token or DEFAULT_AUTH_TOKEN
        self.locale = locale or DEFAULT_LOCALE
        self.timeout = timeout
        
    async def execute_unified_introspection_query(self) -> Dict[str, Any]:
        """
        Execute the unified GraphQL introspection query to get both queries and full schema details.
        
        Returns:
            Dictionary with the introspection results
        """
        query = UNIFIED_INTROSPECTION_QUERY
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.auth_token,
            "Locale": self.locale
        }
        
        payload = {
            "query": query
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if "errors" in result:
                            return {
                                "status": "error",
                                "errors": result["errors"],
                                "message": "The introspection query returned errors"
                            }
                        
                        if "data" in result:
                            # Success case
                            return {
                                "status": "success",
                                "data": result["data"]
                            }
                        
                        return {
                            "status": "error",
                            "message": "The response did not contain a data field",
                            "raw_response": result
                        }
                    else:
                        error_text = await response.text()
                        log.error(f"Unified introspection query failed with status {response.status}: {error_text}")
                        return {
                            "status": "error",
                            "error": f"HTTP Error: {response.status}",
                            "details": error_text
                        }
        except asyncio.TimeoutError:
            log.error(f"Introspection query timed out")
            return {
                "status": "error",
                "error": "Timeout",
                "details": f"The introspection query timed out after {self.timeout} seconds"
            }
        except aiohttp.ClientError as e:
            log.error(f"Introspection query failed due to a client error: {str(e)}")
            return {
                "status": "error",
                "error": f"Client Error: {type(e).__name__}",
                "details": str(e)
            }
        except Exception as e:
            log.error(f"Introspection query failed with an unexpected exception: {str(e)}")
            return {
                "status": "error",
                "error": f"Exception: {type(e).__name__}",
                "details": str(e)
            }

# Input schema for the unified introspection tool
class GraphQLUnifiedIntrospectionInput(BaseModel):
    """Input schema for the Unified Introspection Tool."""
    type_name: Optional[str] = Field(None, description="When querying specific type details, provide the type name.")

# Create the LangChain StructuredTool for Unified Introspection
graphql_unified_introspection_tool = StructuredTool(
    name="graphql_unified_introspection",
    description=(
        "Performs a unified GraphQL introspection query that retrieves schema structure, "
        "available queries, mutations, types, fields, and their relationships in a single response."
    ),
    func=UnifiedIntrospectionTool().execute_unified_introspection_query,
    args_schema=GraphQLUnifiedIntrospectionInput
)



# ---------------------------------------------------------------------------
# Tool 4: GraphQL Query Tool (Parallel Execution)
# ---------------------------------------------------------------------------

class GraphQLSchemaIntrospector:
    """
    A tool for introspecting GraphQL schemas and generating documentation.
    
    This class provides a flexible way to fetch and process GraphQL schema information
    without writing to a file, instead returning the documentation as a variable.
    """
    
    def __init__(
        self, 
        endpoint: str = DEFAULT_GRAPHQL_ENDPOINT, 
        auth_token: Optional[str] = DEFAULT_AUTH_TOKEN, 
        locale: str = DEFAULT_LOCALE
    ):
        """
        Initialize the GraphQL Schema Introspector.
        
        Args:
            endpoint (str): The GraphQL endpoint URL
            auth_token (str, optional): Authorization token for the GraphQL API
            locale (str, optional): Locale for the request
        """
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.locale = locale
        
        # Introspection query
        self.introspection_query = """
        {
          __schema {
            queryType {
              fields {
                name
                description
                type {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
                args {
                  name
                  description
                  type {
                    kind
                    name
                    ofType {
                      kind
                      name
                    }
                  }
                }
              }
            }
            types {
              name
              kind
              fields {
                name
                type {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
              inputFields {
                name
                description
                type {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
        """
    
    def fetch_schema(self) -> Dict[str, Any]:
        """
        Fetch the GraphQL schema using introspection query.
        
        Returns:
            Dict: Parsed JSON response containing schema data
        
        Raises:
            Exception: If there's an error fetching or processing the schema
        """
        try:
            # Prepare headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': self.auth_token,
                'Accept-Language': self.locale
            }
            
            # Prepare payload
            payload = {
                'query': self.introspection_query
            }
            
            # Make the request
            response = requests.post(
                self.endpoint, 
                headers=headers, 
                json=payload
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the JSON
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                raise Exception(f'GraphQL errors: {data["errors"]}')
            
            return data
        
        except Exception as e:
            raise Exception(f'Error fetching schema: {e}')
    
    def generate_documentation(self, introspection_data: Dict[str, Any]) -> str:
        """
        Generate markdown documentation from introspection data.
        
        Args:
            introspection_data (Dict): Schema data from introspection query
        
        Returns:
            str: Markdown-formatted documentation
        """
        documentation = ["# GraphQL Schema Reference\n"]
        
        # Get all the query fields
        queries = introspection_data["data"]["__schema"]["queryType"]["fields"]
        
        # Map of return type objects for easy lookup
        type_map = {}
        for type_obj in introspection_data["data"]["__schema"]["types"]:
            type_map[type_obj["name"]] = type_obj
        
        # Process each query
        for query in queries:
            # Start with query name
            section = [f"## Query: {query['name']}"]
            
            # Extract and clean description
            description = query.get("description", "")
            description = description.replace("description: ", "").split("\nArguments:")[0].strip()
            section.append(f"**Description:** {description}\n")
            
            # Process arguments
            if not query.get("args"):
                section.append("**Arguments:** None\n")
            else:
                section.append("**Arguments:**")
                
                # For each argument
                for arg in query["args"]:
                    # Get argument type
                    arg_type_name = ""
                    is_required = False
                    
                    if arg["type"]["kind"] == "NON_NULL":
                        is_required = True
                        arg_type_name = arg["type"]["ofType"]["name"]
                    else:
                        arg_type_name = arg["type"].get("name")
                    
                    section.append(f"- {arg['name']}: {arg_type_name}{'!' if is_required else ''} {'(required)' if is_required else ''}")
                    
                    # Find the corresponding input type
                    input_type = type_map.get(arg_type_name)
                    if input_type and input_type.get("inputFields"):
                        # For each field in the input type
                        for field in input_type["inputFields"]:
                            field_type = ""
                            field_required = False
                            
                            if field["type"]["kind"] == "NON_NULL":
                                field_required = True
                                field_type = field["type"]["ofType"]["name"]
                            else:
                                field_type = field["type"].get("name")
                            
                            # Extract description and example
                            field_desc = ""
                            example = ""
                            
                            if field.get("description"):
                                desc_lines = field["description"].split("\n")
                                
                                # Extract example
                                for line in desc_lines:
                                    if "example:" in line:
                                        example = line.split("example:")[1].strip()
                                        break
                                
                                # Extract description
                                for line in desc_lines:
                                    if "description:" in line:
                                        field_desc = line.split("description:")[1].strip()
                                        break
                            
                            # Add to documentation
                            requirement = "required" if field_required else "optional"
                            example_text = f". Example: {example}" if example else ""
                            section.append(f"  - {field['name']}: {field_type}{'!' if field_required else ''} ({requirement}) - {field_desc}{example_text}")
            
            # Process return type
            return_type_name = ""
            if query["type"]["kind"] == "LIST":
                return_type_name = f"[{query['type']['ofType']['name']}]"
            else:
                name = query["type"].get("name")
                ofType = query["type"].get("ofType", {})
                ofType_name = ofType.get("name") if ofType else None
                return_type_name = name if name else (ofType_name if ofType_name else "Unknown")
            
            section.append(f"\n**Return Type:** {return_type_name}\n")
            
            # Process return fields
            section.append("**Return Fields:**")
            
            # Get the base return type name (without the List wrapper)
            if query["type"]["kind"] == "LIST":
                base_type_name = query["type"]["ofType"]["name"]
            else:
                name = query["type"].get("name")
                ofType = query["type"].get("ofType", {})
                ofType_name = ofType.get("name") if ofType else None
                base_type_name = name if name else (ofType_name if ofType_name else "Unknown")
            
            # Find the return type and its fields
            return_type = type_map.get(base_type_name)
            if return_type and return_type.get("fields"):
                for field in return_type["fields"]:
                    section.append(f"- {field['name']}")
            elif base_type_name == "package":
                section.append("*(Same as fetchPackageById)*")
            else:
                section.append("- (Fields not available in introspection)")
            
            # Add this query's documentation to the overall documentation
            documentation.append("\n".join(section))
        
        return "\n\n".join(documentation)
    
    def get_schema_documentation(self) -> str:
        """
        Fetch and generate schema documentation in one step.
        
        Returns:
            str: Markdown-formatted documentation of the GraphQL schema
        """
        schema_data = self.fetch_schema()
        return self.generate_documentation(schema_data)
    
    def get_schema_dict(self) -> Dict[str, Any]:
        """
        Fetch the raw schema data as a dictionary.
        
        Returns:
            Dict: Raw schema data from the introspection query
        """
        return self.fetch_schema()


# # result = await graphql_unified_introspection_tool.func()
# introspector = GraphQLSchemaIntrospector()
# # Get documentation as a markdown string
# docs = introspector.get_schema_documentation()
# # Alternatively, get the raw schema dictionary
# schema_dict = introspector.get_schema_dict()

# ---------------------------------------------------------------------------
# Tool 7: Same GraphQL Queries Introspection tool
# ---------------------------------------------------------------------------

INTROSPECTION_QUERY = """
{
  __schema {
    queryType {
      fields {
        name
        description
        type {
          kind
          name
          ofType { kind name }
        }
        args {
          name
          description
          type {
            kind
            name
            ofType { kind name }
          }
        }
      }
    }
    types {
      name
      kind
      fields {
        name
        type { kind name ofType { kind name } }
      }
      inputFields {
        name
        description
        type { kind name ofType { kind name } }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------
# HELPERS – *identical* to your original logic, minus file-writes
# ---------------------------------------------------------------------

# GraphQL introspection query
INTROSPECTION_QUERY = """
{
  __schema {
    queryType {
      fields {
        name
        description
        type {
          kind
          name
          ofType { kind name }
        }
        args {
          name
          description
          type {
            kind
            name
            ofType { kind name }
          }
        }
      }
    }
    types {
      name
      kind
      fields {
        name
        type { kind name ofType { kind name } }
      }
      inputFields {
        name
        description
        type { kind name ofType { kind name } }
      }
    }
  }
}
"""

# Helper function to generate markdown from introspection data
def _generate_schema_markdown(introspection: Dict[str, Any]) -> str:
    """Generates markdown documentation from GraphQL introspection data."""
    doc_lines = ["# GraphQL Schema Reference\n"]
    schema = introspection["data"]["__schema"]
    type_map = {t["name"]: t for t in schema["types"]}

    for q in schema["queryType"]["fields"]:
        section = [f"## Query: {q['name']}"]
        desc = (q.get("description") or "").replace("description:", "").split("\nArguments:")[0].strip()
        section.append(f"**Description:** {desc or 'N/A'}\n")

        if not q.get("args"):
            section.append("**Arguments:** None\n")
        else:
            section.append("**Arguments:**")
            for a in q["args"]:
                is_required = a["type"]["kind"] == "NON_NULL"
                arg_type = (
                    a["type"]["ofType"]["name"] if is_required
                    else a["type"].get("name")
                )
                section.append(f"- {a['name']}: {arg_type}{'!' if is_required else ''}"
                               f" {'(required)' if is_required else ''}")

                arg_input = type_map.get(arg_type)
                if arg_input and arg_input.get("inputFields"):
                    for f in arg_input["inputFields"]:
                        f_req = f["type"]["kind"] == "NON_NULL"
                        f_type = (
                            f["type"]["ofType"]["name"] if f_req
                            else f["type"].get("name")
                        )
                        f_desc = ""
                        example = ""
                        if f.get("description"):
                            for line in f["description"].splitlines():
                                if line.startswith("example:"):
                                    example = line.split("example:")[1].strip()
                                if line.startswith("description:"):
                                    f_desc = line.split("description:")[1].strip()
                        ex = f". Example: {example}" if example else ""
                        section.append(
                            f"  - {f['name']}: {f_type}{'!' if f_req else ''}"
                            f" ({'required' if f_req else 'optional'}) - {f_desc}{ex}"
                        )

        # Return-type lines
        rt_kind = q["type"]["kind"]
        if rt_kind == "LIST":
            rt_name = f"[{q['type']['ofType']['name']}]"
            base_rt = q["type"]["ofType"]["name"]
        else:
            rt_name = q["type"].get("name") or q["type"]["ofType"]["name"]
            base_rt = rt_name

        section.append(f"\n**Return Type:** {rt_name}\n")
        section.append("**Return Fields:**")
        return_type = type_map.get(base_rt)
        if return_type and return_type.get("fields"):
            section += [f"- {f['name']}" for f in return_type["fields"]]
        elif base_rt == "package":
            section.append("*(Same as fetchPackageById)*")
        else:
            section.append("- (Fields not available in introspection)")

        doc_lines.append("\n".join(section))

    return "\n\n".join(doc_lines)

# Define a no-arguments input schema
class GraphQLSchemaInput(BaseModel):
    """
    Input schema for GraphQL Schema tool - no parameters needed.
    The tool uses preconfigured connection settings.
    """
    pass

# Simple synchronous implementation
def fetch_graphql_schema() -> Dict[str, Any]:
    """
    Fetches and formats the GraphQL schema documentation from the configured endpoint.
    
    Returns:
        Dictionary with schema documentation in markdown format or error details
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": DEFAULT_AUTH_TOKEN,
        "Accept-Language": DEFAULT_LOCALE,
    }
    payload = {"query": INTROSPECTION_QUERY}
    
    try:
        response = requests.post(
            DEFAULT_GRAPHQL_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=DEFAULT_TIMEOUT
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "http_status": response.status_code,
                "details": response.text,
            }
            
        data = response.json()
        
        if "errors" in data:
            return {"status": "error", "errors": data["errors"]}
        
        markdown = _generate_schema_markdown(data)
        return {"status": "success", "documentation": markdown}
        
    except requests.Timeout:
        return {"status": "error", "message": "Request timed out"}
    except requests.RequestException as e:
        return {"status": "error", "message": f"Request error: {e}"}

# Create the final tool
graphql_schema_tool = StructuredTool.from_function(
    func=fetch_graphql_schema,
    name="graphql_schema_markdown",
    description="Fetches the GraphQL schema from the configured endpoint and returns a complete markdown reference of all available queries, arguments, and return types.",
    args_schema=GraphQLSchemaInput
)



# ---------------------------------------------------------------------
# graphql_schema_tool_2: GraphQL Schema Introspection Tool (Main)
# ---------------------------------------------------------------------

# Main introspection query to fetch the entire schema
full_introspection_query_2 = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      ...FullType
    }
    directives {
      name
      description
      locations
      args {
        ...InputValue
      }
    }
  }
}

fragment FullType on __Type {
  kind
  name
  description
  fields(includeDeprecated: true) {
    name
    description
    args {
      ...InputValue
    }
    type {
      ...TypeRef
    }
    isDeprecated
    deprecationReason
  }
  inputFields {
    ...InputValue
  }
  interfaces {
    ...TypeRef
  }
  enumValues(includeDeprecated: true) {
    name
    description
    isDeprecated
    deprecationReason
  }
  possibleTypes {
    ...TypeRef
  }
}

fragment InputValue on __InputValue {
  name
  description
  type { ...TypeRef }
  defaultValue
}

fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

# Define a no-arguments input schema, similar to the sample
class GraphQLSchemaInput_2(BaseModel):
    """
    Input schema for GraphQL Schema tool - no parameters needed.
    The tool uses preconfigured connection settings.
    """
    pass

def execute_graphql_query(query, variables={}):
    """
    Executes a GraphQL query against the configured endpoint
    
    Args:
        query (str): The GraphQL query to execute
        variables (dict): Variables for the query (optional)
        
    Returns:
        dict: The query result
    """
    try:
        response = requests.post(
            DEFAULT_GRAPHQL_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": DEFAULT_AUTH_TOKEN,
                "locale": DEFAULT_LOCALE
            },
            json={
                "query": query,
                "variables": variables
            },
            timeout=DEFAULT_TIMEOUT
        )
        
        if not response.ok:
            return {"error": f"GraphQL request failed: {response.status_code} {response.reason}"}
        
        return response.json()
    except Exception as error:
        return {"error": f"Error executing GraphQL query: {str(error)}"}

def resolve_type_reference(type_ref):
    """
    Resolves a type reference to a string representation
    
    Args:
        type_ref (dict): The type reference object from introspection
        
    Returns:
        str: String representation of the type
    """
    if not type_ref:
        return 'null'
    
    if type_ref.get('kind') == 'NON_NULL':
        return f"{resolve_type_reference(type_ref.get('ofType'))}!"
    
    if type_ref.get('kind') == 'LIST':
        return f"[{resolve_type_reference(type_ref.get('ofType'))}]"
    
    return type_ref.get('name')

def get_referenced_types(field, schema):
    """
    Recursively finds all types referenced by a field
    
    Args:
        field (dict): The field to analyze
        schema (dict): The full schema
        
    Returns:
        dict: Dictionary of types grouped by kind
    """
    all_types = schema.get('types', [])
    referenced_types = {
        'inputs': [],     # Inputs first, as requested
        'objects': [],
        'interfaces': [],
        'enums': [],
        'unions': []
    }
    
    # Start with the return type
    process_type_reference(field.get('type'), all_types, referenced_types)
    
    # Process argument types
    for arg in field.get('args', []):
        process_type_reference(arg.get('type'), all_types, referenced_types)
    
    return referenced_types

def process_type_reference(type_ref, all_types, referenced_types, processed_types=None):
    """
    Recursively processes a type reference to find all related types
    
    Args:
        type_ref (dict): Type reference to process
        all_types (list): All types in the schema
        referenced_types (dict): Dictionary to store found types by kind
        processed_types (set): Set of already processed type names to avoid cycles
    """
    if processed_types is None:
        processed_types = set()
    
    if not type_ref:
        return
    
    # Handle non-null and list wrappers
    if type_ref.get('kind') in ['NON_NULL', 'LIST']:
        process_type_reference(type_ref.get('ofType'), all_types, referenced_types, processed_types)
        return
    
    type_name = type_ref.get('name')
    if not type_name or type_name in processed_types:
        return
    
    # Mark as processed to avoid infinite recursion
    processed_types.add(type_name)
    
    # Find the full type definition
    type_obj = next((t for t in all_types if t.get('name') == type_name), None)
    if not type_obj:
        return
    
    # Add to appropriate category
    kind = type_obj.get('kind')
    if kind == 'OBJECT':
        if type_name not in [t.get('name') for t in referenced_types['objects']]:
            referenced_types['objects'].append(type_obj)
    elif kind == 'INPUT_OBJECT':
        if type_name not in [t.get('name') for t in referenced_types['inputs']]:
            referenced_types['inputs'].append(type_obj)
    elif kind == 'INTERFACE':
        if type_name not in [t.get('name') for t in referenced_types['interfaces']]:
            referenced_types['interfaces'].append(type_obj)
    elif kind == 'ENUM':
        if type_name not in [t.get('name') for t in referenced_types['enums']]:
            referenced_types['enums'].append(type_obj)
    elif kind == 'UNION':
        if type_name not in [t.get('name') for t in referenced_types['unions']]:
            referenced_types['unions'].append(type_obj)
    
    # If it's an object type, process its fields
    if kind == 'OBJECT':
        for field in type_obj.get('fields', []):
            process_type_reference(field.get('type'), all_types, referenced_types, processed_types)
    
    # If it's an input type, process its input fields
    if kind == 'INPUT_OBJECT':
        for field in type_obj.get('inputFields', []):
            process_type_reference(field.get('type'), all_types, referenced_types, processed_types)
    
    # If it's an interface, process its fields
    if kind == 'INTERFACE':
        for field in type_obj.get('fields', []):
            process_type_reference(field.get('type'), all_types, referenced_types, processed_types)
    
    # If it's a union, process its possible types
    if kind == 'UNION':
        for possible_type in type_obj.get('possibleTypes', []):
            process_type_reference(possible_type, all_types, referenced_types, processed_types)

def generate_type_section(type_obj, schema):
    """
    Generates markdown for a type
    
    Args:
        type_obj (dict): The type object
        schema (dict): The full schema
        
    Returns:
        str: Markdown for the type section
    """
    markdown = f"##### {type_obj.get('name')}\n\n"
    
    if type_obj.get('description'):
        markdown += f"{type_obj.get('description')}\n\n"
    
    kind = type_obj.get('kind')
    
    # Generate fields for objects and interfaces
    if kind in ['OBJECT', 'INTERFACE'] and type_obj.get('fields'):
        markdown += "Fields:\n\n"
        markdown += "| Name | Type | Description |\n"
        markdown += "| ---- | ---- | ----------- |\n"
        
        for field in type_obj.get('fields', []):
            type_str = resolve_type_reference(field.get('type'))
            desc = field.get('description', '').replace('\n', ' ') if field.get('description') else ''
            markdown += f"| `{field.get('name')}` | `{type_str}` | {desc} |\n"
        
        markdown += "\n"
    
    # Generate input fields for input objects
    if kind == 'INPUT_OBJECT' and type_obj.get('inputFields'):
        markdown += "Input Fields:\n\n"
        markdown += "| Name | Type | Description |\n"
        markdown += "| ---- | ---- | ----------- |\n"
        
        for field in type_obj.get('inputFields', []):
            type_str = resolve_type_reference(field.get('type'))
            desc = field.get('description', '').replace('\n', ' ') if field.get('description') else ''
            markdown += f"| `{field.get('name')}` | `{type_str}` | {desc} |\n"
        
        markdown += "\n"
    
    # Generate enum values for enums
    if kind == 'ENUM' and type_obj.get('enumValues'):
        markdown += "Enum Values:\n\n"
        markdown += "| Name | Description |\n"
        markdown += "| ---- | ----------- |\n"
        
        for value in type_obj.get('enumValues', []):
            desc = value.get('description', '').replace('\n', ' ') if value.get('description') else ''
            markdown += f"| `{value.get('name')}` | {desc} |\n"
        
        markdown += "\n"
    
    # Generate possible types for unions
    if kind == 'UNION' and type_obj.get('possibleTypes'):
        markdown += "Possible Types:\n\n"
        markdown += "\n".join([f"- `{pt.get('name')}`" for pt in type_obj.get('possibleTypes', [])])
        markdown += "\n\n"
    
    return markdown

def generate_query_section(field, schema):
    """
    Generates markdown for a single query with all its details and related types
    
    Args:
        field (dict): The query field object
        schema (dict): The full schema object to reference related types
        
    Returns:
        str: Markdown representation of the query with all its related types
    """
    return_type = resolve_type_reference(field.get('type'))
    markdown = f"## Query: {field.get('name')}\n\n"
    
    if field.get('description'):
        markdown += f"{field.get('description')}\n\n"
    
    markdown += f"**Return Type:** `{return_type}`\n\n"
    
    args = field.get('args', [])
    if args and len(args) > 0:
        markdown += "### Arguments\n\n"
        markdown += "| Name | Type | Description |\n"
        markdown += "| ---- | ---- | ----------- |\n"
        
        for arg in args:
            arg_type_str = resolve_type_reference(arg.get('type'))
            arg_desc = arg.get('description', '').replace('\n', ' ') if arg.get('description') else ''
            markdown += f"| `{arg.get('name')}` | `{arg_type_str}` | {arg_desc} |\n"
    
    markdown += "\n"
    
    # Add related types section
    markdown += "### Related Types\n\n"
    
    # Get all types referenced by this query
    referenced_types = get_referenced_types(field, schema)
    
    # Group types by kind
    for kind, types in referenced_types.items():
        if types:
            markdown += f"#### {kind.title()}\n\n"
            for type_obj in types:
                markdown += generate_type_section(type_obj, schema)
    
    markdown += "\n---\n\n"  # Separator between queries
    
    return markdown

def generate_queries_section(schema):
    """
    Generates markdown for the queries section, with each query and all its related types
    
    Args:
        schema (dict): The schema object from introspection
        
    Returns:
        str: Query section markdown
    """
    query_type_name = schema.get('queryType', {}).get('name')
    query_type = next((t for t in schema.get('types', []) if t.get('name') == query_type_name), None)
    
    if not query_type:
        return '# Queries\n\nNo queries found.\n\n'
    
    markdown = "# Queries\n\n"
    fields = query_type.get('fields', [])
    
    if fields and len(fields) > 0:
        for field in fields:
            markdown += generate_query_section(field, schema)
    
    return markdown

def generate_mutations_section(schema):
    """
    Generates markdown for all mutations with their related types
    
    Args:
        schema (dict): The schema object from introspection
        
    Returns:
        str: Markdown for mutations
    """
    if not schema.get('mutationType'):
        return '# Mutations\n\nNo mutations available.\n\n'
    
    mutation_type_name = schema.get('mutationType', {}).get('name')
    mutation_type = next((t for t in schema.get('types', []) if t.get('name') == mutation_type_name), None)
    
    if not mutation_type:
        return '# Mutations\n\nNo mutations found.\n\n'
    
    markdown = "# Mutations\n\n"
    fields = mutation_type.get('fields', [])
    
    if fields and len(fields) > 0:
        for field in fields:
            markdown += generate_query_section(field, schema)  # Reusing the same function for mutations
    
    return markdown

def generate_schema_markdown_2(schema):
    """
    Generates markdown for the entire schema
    
    Args:
        schema (dict): The schema object from introspection
        
    Returns:
        str: Full markdown documentation
    """
    markdown = "# GraphQL Schema Documentation\n\n"
    
    # Add a table of contents
    markdown += "## Table of Contents\n\n"
    markdown += "- [Queries](#queries)\n"
    markdown += "- [Mutations](#mutations)\n\n"
    
    # Add queries section with each query and its related types
    markdown += generate_queries_section(schema)
    
    # Add mutations section with each mutation and its related types
    markdown += generate_mutations_section(schema)
    
    return markdown

# The main function for the LangChain tool
def fetch_graphql_schema_2():
    """
    Fetches and formats the GraphQL schema documentation from the configured endpoint.
    
    Returns:
        Dictionary with schema documentation in markdown format or error details
    """
    try:
        # Execute the introspection query
        result = execute_graphql_query(full_introspection_query_2)
        
        if result.get('errors') or "error" in result:
            error_msg = result.get('errors') or result.get("error")
            return {
                "status": "error",
                "message": "GraphQL introspection errors",
                "details": error_msg
            }
        
        # Generate the markdown documentation with all queries
        markdown = generate_schema_markdown_2(result.get('data', {}).get('__schema', {}))
        
        return {
            "status": "success",
            "documentation": markdown
        }
    
    except Exception as error:
        return {
            "status": "error",
            "message": f"Failed to generate documentation: {str(error)}"
        }

# Create the LangChain tool with no required input parameters
graphql_schema_tool_2 = StructuredTool.from_function(
    func=fetch_graphql_schema_2,
    name="graphql_schema_markdown",
    description="Fetches the GraphQL schema from the configured endpoint and returns a complete markdown reference of all available queries, arguments, and return types.",
    args_schema=GraphQLSchemaInput_2
)


# ---------------------------------------------------------------------------
# Tool 4: GraphQL Introspection Agent Tool (graphql_introspection_agent_tool)
# ---------------------------------------------------------------------------
# Define the introspection tools
graphql_introspection_tools_all = [
    graphql_introspection_tool,  # Introspection tool for GraphQL schema
    graphql_schema_tool_2
]

introspection_system_message_content = """You are a helpful assistant specializing in GraphQL schema introspection and analysis. Your primary goal is to effectively use the available tools (GraphQL Introspection, Schema Analyzer, Type Relationships) to understand and explain the complete GraphQL schema of the API.

When a user asks questions about the database schema or API structure, carefully consider which tool is best suited to answer it:
- Use GraphQL Schema Tool 2 as the default introspection tool for general queries
- Use GraphQL Introspection as a secondary tool to retrieve the raw schema information

Your capabilities include:
1. Examining the database schema in detail - showing object types, fields, relationships, and query endpoints
2. Explaining the purpose and structure of specific types and fields
3. Breaking down the relationships between different database entities
4. Showing available queries and how to structure them properly
5. Providing examples of how to access specific data through the API

When responding:
- Break down complex queries into clear steps
- Clearly state your plan before making tool calls
- Present schema information in an organized, easy-to-understand format
- If a tool call fails, adapt your approach or explain the issue
- Present clear, comprehensive answers that accurately reflect the database structure

Remember that your goal is to help users fully understand the database schema, including all object types, queries, fields, and their relationships, enabling them to effectively use the GraphQL API.
"""

# Define the system message template for React agent
introspection_system_message_prompt = ChatPromptTemplate.from_messages([
    ("system", introspection_system_message_content),
    ("human", "{messages}")
])

# Create the React agent
introspection_agent = create_react_agent(
    model=llm_telogical,
    tools=graphql_introspection_tools_all,
    prompt=introspection_system_message_prompt
)

# Define the LangChain Tool
class ReactAgentToolInput(BaseModel):
    """Input schema for the React Agent Tool."""
    query: str = Field(
        ..., description="The user's natural language query or request for the GraphQL agent."
    )


class GraphQLIntrospectionAgent:
    """
    A tool that executes a React agent to introspect GraphQL schemas and run queries
    related to telecommunications market presence.
    """
    
    def execute(self, query: str) -> str:
        """
        Execute the internal React agent to process the user's query.
        
        Args:
            query: The user's natural language query or request
            
        Returns:
            A string containing the final answer and any intermediate tool messages
        """
        try:
            # Prepare the message content for the internal agent
            messages = [HumanMessage(content=query)]

            # Invoke the React agent synchronously
            response = introspection_agent.invoke(
                {"messages": messages}
                # Optional: Add configuration like max_iterations or timeouts here if needed
                # , config={"configurable": {"max_iterations": 15}}
            )
            
            # Extract the final answer - focus on the agent's true final answer
            final_answer = ""
            tool_messages = []
            
            # Process messages to separate final answer from tool messages
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                
                # Find actual final answer (last AIMessage without tool calls)
                for msg in reversed(messages):
                    # Check if it's an AIMessage without tool calls
                    if (hasattr(msg, '__class__') and msg.__class__.__name__ == 'AIMessage' and 
                        (not hasattr(msg, 'tool_calls') or not msg.tool_calls) and
                        hasattr(msg, 'content') and msg.content):
                        final_answer = msg.content
                        break
                
                # Collect tool messages, but filter out any that contain the same text as final_answer
                for msg in messages:
                    # Skip messages that are or contain the final answer to avoid duplication
                    if hasattr(msg, 'content') and msg.content and final_answer in msg.content:
                        continue
                        
                    # Process actual tool messages
                    if ((hasattr(msg, 'name') or 
                        (isinstance(msg, dict) and 'name' in msg) or 
                        (hasattr(msg, '__class__') and msg.__class__.__name__ in ['ToolMessage', 'FunctionMessage']))):
                        
                        tool_name = getattr(msg, 'name', None)
                        if tool_name is None and isinstance(msg, dict):
                            tool_name = msg.get('name', 'None')
                        
                        tool_content = getattr(msg, 'content', None)
                        if tool_content is None and isinstance(msg, dict):
                            tool_content = msg.get('content', '')
                        
                        # Only add valid tool messages with content, excluding any that contain the final answer
                        if tool_content and final_answer not in tool_content:
                            tool_messages.append((tool_name, tool_content))
            
            # If no final answer was found, check additional places
            if not final_answer and isinstance(response, dict):
                if "output" in response and isinstance(response["output"], str):
                    final_answer = response["output"]
            
            # Build the final result string
            result = ""
            if final_answer:
                result += f"Final Answer:\n{final_answer}\n\n"
            else:
                result += "Final Answer: No final answer was provided by the agent.\n\n"
            
            # Add tool messages
            if tool_messages:
                result += "Tool Messages:\n"
                for name, content in tool_messages:
                    result += f"Tool: {name or 'None'}\nOutput: {content}\n\n"
            
            return result

        except Exception as e:
            # Return an informative error message to the caller of the tool
            error_details = traceback.format_exc()
            return f"Error processing request with agent: {type(e).__name__} - {e}\n\nError details:\n{error_details}"

# --- Create the LangChain StructuredTool instance ---
graphql_introspection_agent_tool = StructuredTool(
    name="graphql_introspection_agent",
    description=(
        "Executes a React agent to introspect GraphQL schemas or run GraphQL queries "
        "related to telecommunications market presence based on natural language queries. "
        "Use this tool when you need to extract information from a GraphQL API using "
        "natural language instructions instead of direct GraphQL syntax."
    ),
    func=GraphQLIntrospectionAgent().execute,
    args_schema=ReactAgentToolInput
)

# ---------------------------------------------------------------------
# dma_code_lookup_tool: Designated Market Area Tool
# ---------------------------------------------------------------------

# Define Input Schema
class DMACodeLookupInput(BaseModel):
    dma_codes: List[str] = Field(..., description="List of DMA codes to look up.")
    
# Define the Tool
class DMACodeLookupTool:
    def __init__(self, csv_path: str = DMA_CSV_PATH):
        """
        Initialize the DMA Code Lookup Tool.
        
        Args:
            csv_path: Path to the CSV file containing DMA codes and descriptions.
        """
        self.csv_path = csv_path
        # Load the CSV data
        try:
            self.df = pd.read_csv(csv_path)
            # Convert DMACode to string to ensure matching works properly
            self.df['DMACode'] = self.df['DMACode'].astype(str)
        except Exception as e:
            raise ValueError(f"Error loading DMA code CSV file: {e}")
    
    def lookup_dma_codes(self, dma_codes: List[str], return_all_columns: bool = False) -> Dict[str, Any]:
        """
        Look up DMA codes and return their corresponding descriptions.
        
        Args:
            dma_codes: List of DMA codes to look up.
            return_all_columns: Whether to return all columns from the CSV or just the DMA name.
            
        Returns:
            Dictionary mapping DMA codes to their descriptions.
        """
        try:
            # Convert all codes to strings to ensure matching works properly
            dma_codes = [str(code) for code in dma_codes]
            
            results = {}
            not_found = []
            
            for code in dma_codes:
                # Find the matching row for this code
                matched_rows = self.df[self.df['DMACode'] == code]
                
                if not matched_rows.empty:
                    row = matched_rows.iloc[0]
                    results[code] = row['DMA']

                else:
                    not_found.append(code)
                    results[code] = None
            
            response = {
                "results": results,
                "not_found": not_found
            }
            
            return response
        except Exception as e:
            return {"error": str(e)}

# Create the LangChain Tool
dma_code_lookup_tool = StructuredTool(
    name="DMA_Code_Lookup",
    func=DMACodeLookupTool().lookup_dma_codes,
    description="Converts DMA codes to their corresponding names and descriptions by looking them up in a CSV file.",
    args_schema=DMACodeLookupInput
)


# ---------------------------------------------------------------------
# math_counting_tool: Math Counting Tool
# ---------------------------------------------------------------------
# Simplified Input Schema
class ListCountingToolInput(BaseModel):
    items: List[Any] = Field(
        ..., 
        description="List of items to count or filter (any type)."
    )
    operation: str = Field(
        ..., 
        description="Operation to perform: 'count_all', 'count_unique', or 'count_matching'."
    )
    key: Optional[str] = Field(
        None, 
        description="For dictionary items, the key to check when filtering (for 'count_matching' operation)."
    )
    value: Optional[Any] = Field(
        None,
        description="Value to match when filtering (for 'count_matching' operation)."
    )

class ListCountingTool:
    def __init__(self):
        """Initialize the List Counting Tool."""
        pass
    
    def count_items(
        self, 
        items: List[Any], 
        operation: str, 
        key: Optional[str] = None,
        value: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Count items in a list, with optional filtering.
        
        Args:
            items: List of items to count.
            operation: Type of counting to perform ('count_all', 'count_unique', or 'count_matching').
            key: For dictionary items, the key to check when filtering.
            value: Value to match when filtering.
            
        Returns:
            Dictionary containing the count and a simple message.
        """
        try:
            # Count all items (the basic operation)
            if operation == "count_all":
                count = len(items)
                return {
                    "count": count,
                    "message": f"There are {count} total items in the list."
                }
            
            # Count unique items
            elif operation == "count_unique":
                try:
                    # Try to use set directly
                    unique_count = len(set(items))
                except TypeError:
                    # Fall back to string representation for non-hashable items
                    unique_count = len(set(str(item) for item in items))
                
                total_count = len(items)
                return {
                    "unique_count": unique_count,
                    "total_count": total_count,
                    "duplicate_count": total_count - unique_count,
                    "message": f"There are {unique_count} unique items out of {total_count} total items."
                }
            
            # Count items matching criteria (filtered counting)
            elif operation == "count_matching":
                if value is None:
                    return {"error": "For 'count_matching' operation, a value must be provided."}
                
                matching_count = 0
                
                # For dictionary items with a specific key
                if key is not None:
                    for item in items:
                        if isinstance(item, dict) and key in item:
                            # If the key contains a list
                            if isinstance(item[key], list) and value in item[key]:
                                matching_count += 1
                            # Direct value comparison
                            elif item[key] == value:
                                matching_count += 1
                # For direct comparison with the items themselves
                else:
                    for item in items:
                        if item == value:
                            matching_count += 1
                
                return {
                    "matching_count": matching_count,
                    "total_count": len(items),
                    "percentage": (matching_count / len(items) * 100) if items else 0,
                    "message": f"Found {matching_count} items matching the criteria out of {len(items)} total items."
                }
                
            else:
                return {"error": f"Unknown operation: '{operation}'. Available operations: 'count_all', 'count_unique', 'count_matching'"}
                
        except Exception as e:
            return {"error": str(e)}

# Create the tool instance
list_counting_tool = ListCountingTool()

# Create the LangChain Tool
math_counting_tool = StructuredTool(
    name="math_counting_tool",
    func=list_counting_tool.count_items,
    description=(
        "Use this tool for accurate counting of items in lists when LLMs might make mistakes. "
        
        "Supported operations: "
        "1. 'count_all': Counts total items in a list"
        "2. 'count_unique': Counts distinct items, removing duplicates"
        "3. 'count_matching': Counts items matching specific criteria - most powerful operation "
        "   - For simple lists: Provide 'value' to match exact items "
        "   - For dictionaries: Use 'key' and 'value' (e.g., key='data', value='unlimited') "
        "   - Works with list fields (e.g., finds plans where 'features' list contains 'international') "
    ),

    args_schema=ListCountingToolInput
)