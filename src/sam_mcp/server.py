import asyncio
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


@mcp.tool()
async def resolve_company(
    name: Annotated[
        str, Field(description="Company name to look up (supports wildcards with *)")
    ],
    state: Annotated[
        Optional[str], Field(description="Narrow by two-letter state code, e.g. CO")
    ] = None,
) -> dict:
    """Resolve a company name to its SAM.gov entity record and UEI.
    Returns the single best match, or an error if none found."""
    params = _params(
        legalBusinessName=name,
        physicalAddressStateOrProvinceCode=state,
        samRegistered="Yes",
        pageSize=5,
    )
    response = await _get_client().get("/entity-information/v3/entities", params=params)
    response.raise_for_status()
    data = response.json()
    entities = data.get("entityData", [])
    if not entities:
        return {"error": f"No entity found matching '{name}'"}
    best = entities[0]
    core = best.get("entityRegistration", {})
    return {
        "uei": core.get("ueiSAM"),
        "legal_business_name": core.get("legalBusinessName"),
        "cage_code": core.get("cageCode"),
        "registration_status": core.get("registrationStatus"),
        "other_matches": len(entities) - 1,
    }


@mcp.tool()
async def search_contract_awards(
    recipient_uei: Annotated[
        Optional[str], Field(description="UEI of the award recipient")
    ] = None,
    agency_id: Annotated[Optional[str], Field(description="Awarding agency ID")] = None,
    naics_code: Annotated[Optional[str], Field(description="NAICS code")] = None,
    award_date_from: Annotated[
        Optional[str], Field(description="Award date from (MM/DD/YYYY)")
    ] = None,
    award_date_to: Annotated[
        Optional[str], Field(description="Award date to (MM/DD/YYYY)")
    ] = None,
    amount_from: Annotated[
        Optional[float], Field(description="Minimum obligated amount in dollars")
    ] = None,
    amount_to: Annotated[
        Optional[float], Field(description="Maximum obligated amount in dollars")
    ] = None,
    contract_type: Annotated[
        Optional[str],
        Field(
            description="Contract type, e.g. DEFINITIVE CONTRACT, INDEFINITE DELIVERY CONTRACT"
        ),
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 100)", ge=1, le=100)
    ] = 10,
) -> dict:
    """Search FPDS contract award records — actual awarded contracts, not open solicitations.
    Use recipient_uei to find all contracts awarded to a specific company."""
    params = _params(
        recipientUEI=recipient_uei,
        awardingAgencyId=agency_id,
        naicsCode=naics_code,
        awardDateFrom=award_date_from,
        awardDateTo=award_date_to,
        obligatedAmountFrom=amount_from,
        obligatedAmountTo=amount_to,
        contractType=contract_type,
        page=page,
        pageSize=page_size,
    )
    response = await _get_client().get(
        "/contract-data/v2/contractAwards", params=params
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def find_competitors(
    uei: Annotated[
        str, Field(description="UEI of the company to find competitors for")
    ],
    state: Annotated[
        Optional[str], Field(description="Narrow to a specific state, e.g. CO")
    ] = None,
    page_size: Annotated[
        int,
        Field(description="Number of competitors to return (max 100)", ge=1, le=100),
    ] = 25,
) -> dict:
    """Find companies registered under the same NAICS codes as the given entity.
    Useful for mapping the competitive landscape around a specific contractor."""
    entity_resp = await _get_client().get(
        "/entity-information/v3/entities",
        params=_params(ueiSAM=uei),
    )
    entity_resp.raise_for_status()
    entities = entity_resp.json().get("entityData", [])
    if not entities:
        return {"error": f"No entity found for UEI {uei}"}

    entity = entities[0]
    naics_list: list[str] = [
        n.get("naicsCode")
        for n in entity.get("assertions", {})
        .get("goodsAndServices", {})
        .get("naicsList", [])
        if n.get("naicsCode")
    ]
    if not naics_list:
        return {"error": "No NAICS codes found for this entity", "uei": uei}

    # Query each NAICS code in parallel, take up to 3 to avoid flooding
    async def _search_naics(code: str) -> list:
        r = await _get_client().get(
            "/entity-information/v3/entities",
            params=_params(
                naicsCode=code,
                physicalAddressStateOrProvinceCode=state,
                samRegistered="Yes",
                pageSize=page_size,
            ),
        )
        r.raise_for_status()
        return r.json().get("entityData", [])

    results = await asyncio.gather(*[_search_naics(c) for c in naics_list[:3]])

    # Deduplicate by UEI, exclude the original company
    seen: set[str] = {uei}
    competitors: list[dict] = []
    for batch in results:
        for e in batch:
            e_uei = e.get("entityRegistration", {}).get("ueiSAM")
            if e_uei and e_uei not in seen:
                seen.add(e_uei)
                competitors.append(e)

    return {
        "uei": uei,
        "naics_codes_used": naics_list[:3],
        "competitors": competitors,
    }


@mcp.tool()
async def get_similar_awards(
    contract_id: Annotated[
        str, Field(description="Prime contract or award ID to base the search on")
    ],
    page_size: Annotated[
        int,
        Field(description="Number of similar awards to return (max 100)", ge=1, le=100),
    ] = 10,
) -> dict:
    """Given a contract ID, find other awarded contracts with the same NAICS code,
    awarding agency, and set-aside type."""
    award_resp = await _get_client().get(
        "/contract-data/v2/contractAwards",
        params=_params(awardId=contract_id, pageSize=1),
    )
    award_resp.raise_for_status()
    awards = award_resp.json().get("contractAwardsData", [])
    if not awards:
        return {"error": f"No award found for contract ID '{contract_id}'"}

    ref = awards[0]
    naics_code = ref.get("naicsCode")
    agency_id = ref.get("awardingAgencyId")
    set_aside = ref.get("typeOfSetAside")

    similar_resp = await _get_client().get(
        "/contract-data/v2/contractAwards",
        params=_params(
            naicsCode=naics_code,
            awardingAgencyId=agency_id,
            typeOfSetAside=set_aside,
            pageSize=page_size,
        ),
    )
    similar_resp.raise_for_status()

    return {
        "reference_contract": contract_id,
        "matched_on": {
            "naics_code": naics_code,
            "agency_id": agency_id,
            "set_aside": set_aside,
        },
        "similar_awards": similar_resp.json(),
    }


@mcp.tool()
async def get_company_profile(
    uei: Annotated[str, Field(description="UEI of the company")],
    awards_page_size: Annotated[
        int, Field(description="Number of contract awards to include", ge=1, le=100)
    ] = 10,
    partners_page_size: Annotated[
        int, Field(description="Number of subaward records per direction", ge=1, le=100)
    ] = 10,
) -> dict:
    """Full profile of a company: entity registration details, contract awards,
    and subcontract partnerships — all in a single call."""
    entity_resp, awards_resp, sub_as_prime_resp, sub_as_sub_resp = await asyncio.gather(
        _get_client().get(
            "/entity-information/v3/entities",
            params=_params(ueiSAM=uei),
        ),
        _get_client().get(
            "/contract-data/v2/contractAwards",
            params=_params(recipientUEI=uei, pageSize=awards_page_size),
        ),
        _get_client().get(
            "/contract-data/v2/subAwards",
            params=_params(primeEntityUEI=uei, pageSize=partners_page_size),
        ),
        _get_client().get(
            "/contract-data/v2/subAwards",
            params=_params(subEntityUEI=uei, pageSize=partners_page_size),
        ),
    )

    for r in (entity_resp, awards_resp, sub_as_prime_resp, sub_as_sub_resp):
        r.raise_for_status()

    entities = entity_resp.json().get("entityData", [])
    return {
        "entity": entities[0] if entities else None,
        "contract_awards": awards_resp.json(),
        "partners": {
            "as_prime": sub_as_prime_resp.json(),
            "as_sub": sub_as_sub_resp.json(),
        },
    }


def main_stdio():
    mcp.run(transport="stdio")


def main_http():
    mcp.run(transport="http")


if __name__ == "__main__":
    main_stdio()
