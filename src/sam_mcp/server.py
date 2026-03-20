from typing import Annotated, Optional
import httpx
from fastmcp import FastMCP
from pydantic import Field

from sam_mcp.config import settings

mcp = FastMCP("SAM.gov")

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(base_url=settings.sam_base_url, timeout=30)
    return _client


def _params(**kwargs) -> dict:
    """Build query params with API key, dropping None values."""
    return {
        "api_key": settings.sam_api_key,
        **{k: v for k, v in kwargs.items() if v is not None},
    }


@mcp.tool()
async def search_entities(
    uei: Annotated[
        Optional[str], Field(description="Unique Entity Identifier (UEI)")
    ] = None,
    legal_business_name: Annotated[
        Optional[str],
        Field(description="Legal business name (supports wildcards with *)"),
    ] = None,
    cage_code: Annotated[Optional[str], Field(description="CAGE code")] = None,
    state: Annotated[
        Optional[str], Field(description="Two-letter state code, e.g. VA")
    ] = None,
    country: Annotated[
        Optional[str], Field(description="Country code, e.g. USA")
    ] = None,
    registration_status: Annotated[
        Optional[str], Field(description="Active, Inactive, or All (default Active)")
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 100)", ge=1, le=100)
    ] = 10,
) -> dict:
    """Search for registered entities (vendors/organizations) in SAM.gov."""
    params = _params(
        ueiSAM=uei,
        legalBusinessName=legal_business_name,
        cageCode=cage_code,
        physicalAddressStateOrProvinceCode=state,
        physicalAddressCountryCode=country,
        samRegistered="Yes",
        registrationStatus=registration_status,
        page=page,
        pageSize=page_size,
    )
    response = await _get_client().get("/entity-information/v3/entities", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def get_entity(
    uei: Annotated[
        str, Field(description="Unique Entity Identifier (UEI) of the entity")
    ],
) -> dict:
    """Get detailed information for a specific entity by UEI."""
    params = _params(ueiSAM=uei)
    response = await _get_client().get("/entity-information/v3/entities", params=params)
    response.raise_for_status()
    data = response.json()
    entities = data.get("entityData", [])
    if not entities:
        return {"error": f"No entity found for UEI {uei}"}
    return entities[0]


@mcp.tool()
async def search_opportunities(
    keyword: Annotated[Optional[str], Field(description="Keyword search term")] = None,
    opportunity_type: Annotated[
        Optional[str],
        Field(
            description="Type codes: p=presolicitation, o=solicitation, k=combined synopsis, etc."
        ),
    ] = None,
    posted_from: Annotated[
        Optional[str], Field(description="Posted from date (MM/DD/YYYY)")
    ] = None,
    posted_to: Annotated[
        Optional[str], Field(description="Posted to date (MM/DD/YYYY)")
    ] = None,
    naics_code: Annotated[Optional[str], Field(description="NAICS code")] = None,
    set_aside_code: Annotated[
        Optional[str], Field(description="Set-aside type, e.g. SBA, 8A, HZC, etc.")
    ] = None,
    state: Annotated[
        Optional[str],
        Field(description="Two-letter state code for place of performance"),
    ] = None,
    limit: Annotated[
        int, Field(description="Number of results to return (max 1000)", ge=1, le=1000)
    ] = 10,
    offset: Annotated[int, Field(description="Offset for pagination", ge=0)] = 0,
) -> dict:
    """Search for contract opportunities (solicitations) on SAM.gov."""
    params = _params(
        q=keyword,
        optype=opportunity_type,
        postedFrom=posted_from,
        postedTo=posted_to,
        ncode=naics_code,
        setAside=set_aside_code,
        state=state,
        limit=limit,
        offset=offset,
    )
    response = await _get_client().get("/opportunities/v2/search", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def search_exclusions(
    name: Annotated[
        Optional[str],
        Field(description="Individual or firm name (supports wildcards with *)"),
    ] = None,
    cage_code: Annotated[Optional[str], Field(description="CAGE code")] = None,
    uei: Annotated[
        Optional[str], Field(description="Unique Entity Identifier (UEI)")
    ] = None,
    exclusion_type: Annotated[
        Optional[str],
        Field(description="Ineligible Firm, Prohibition/Restriction, or Reciprocal"),
    ] = None,
    exclusion_program: Annotated[
        Optional[str], Field(description="Non-Procurement or Procurement")
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 100)", ge=1, le=100)
    ] = 10,
) -> dict:
    """Search for excluded parties (debarred/suspended entities) on SAM.gov."""
    params = _params(
        exclusionName=name,
        cageCode=cage_code,
        ueiSAM=uei,
        exclusionType=exclusion_type,
        exclusionProgram=exclusion_program,
        page=page,
        pageSize=page_size,
    )
    response = await _get_client().get("/exclusions/v1/", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def search_subawards(
    prime_uei: Annotated[
        Optional[str],
        Field(description="UEI of the prime contractor — returns their subcontractors"),
    ] = None,
    sub_uei: Annotated[
        Optional[str],
        Field(
            description="UEI of the subcontractor — returns primes they worked under"
        ),
    ] = None,
    prime_award_id: Annotated[
        Optional[str],
        Field(
            description="Prime contract/award ID to scope results to a specific contract"
        ),
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 100)", ge=1, le=100)
    ] = 10,
) -> dict:
    """Search FSRS subcontract reports. Use prime_uei to find a company's subcontractors,
    or sub_uei to find the prime contractors a company has worked under."""
    params = _params(
        primeEntityUEI=prime_uei,
        subEntityUEI=sub_uei,
        primeAwardKey=prime_award_id,
        page=page,
        pageSize=page_size,
    )
    response = await _get_client().get("/contract-data/v2/subAwards", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def get_company_partners(
    uei: Annotated[str, Field(description="UEI of the company to look up")],
    page_size: Annotated[
        int,
        Field(description="Results per page for each query (max 100)", ge=1, le=100),
    ] = 25,
) -> dict:
    """Return a unified view of a company's subcontract partnerships:
    - as_prime: companies they have brought on as subcontractors
    - as_sub: prime contractors they have worked under"""
    import asyncio

    prime_resp, sub_resp = await asyncio.gather(
        _get_client().get(
            "/contract-data/v2/subAwards",
            params=_params(primeEntityUEI=uei, pageSize=page_size),
        ),
        _get_client().get(
            "/contract-data/v2/subAwards",
            params=_params(subEntityUEI=uei, pageSize=page_size),
        ),
    )
    prime_resp.raise_for_status()
    sub_resp.raise_for_status()

    return {
        "uei": uei,
        "as_prime": prime_resp.json(),
        "as_sub": sub_resp.json(),
    }


def main_stdio():
    mcp.run(transport="stdio")


def main_http():
    mcp.run(transport="http")


if __name__ == "__main__":
    main_stdio()
