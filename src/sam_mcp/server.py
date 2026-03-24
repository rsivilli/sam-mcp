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
        Optional[str], Field(description="A=Active or E=Expired")
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 10)", ge=1, le=10)
    ] = 10,
) -> dict:
    """Search for registered entities (vendors/organizations) in SAM.gov."""
    # Docs: https://open.gsa.gov/api/entity-api/
    params = _params(
        ueiSAM=uei,
        legalBusinessName=legal_business_name,
        cageCode=cage_code,
        physicalAddressProvinceOrStateCode=state,
        physicalAddressCountryCode=country,
        registrationStatus=registration_status,
        page=page,
        size=page_size,
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
    # Docs: https://open.gsa.gov/api/entity-api/
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
    posted_from: Annotated[
        str,
        Field(
            description="Posted from date (MM/DD/YYYY) — required by API, max 1-year range"
        ),
    ],
    posted_to: Annotated[
        str,
        Field(
            description="Posted to date (MM/DD/YYYY) — required by API, max 1-year range"
        ),
    ],
    title: Annotated[
        Optional[str], Field(description="Opportunity title search term")
    ] = None,
    opportunity_type: Annotated[
        Optional[str],
        Field(
            description="Type codes: p=presolicitation, o=solicitation, k=combined synopsis, etc."
        ),
    ] = None,
    naics_code: Annotated[
        Optional[str], Field(description="NAICS code (max 6 digits)")
    ] = None,
    set_aside_code: Annotated[
        Optional[str],
        Field(description="Set-aside type, e.g. SBA, 8A, HZC, SDVOSBC, WOSB, etc."),
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
    # Docs: https://open.gsa.gov/api/get-opportunities-public-api/
    # Note: postedFrom and postedTo are required by the API (MM/DD/YYYY, max 1-year range)
    params = _params(
        title=title,
        ptype=opportunity_type,
        postedFrom=posted_from,
        postedTo=posted_to,
        ncode=naics_code,
        typeOfSetAside=set_aside_code,
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
        Field(
            description="Ineligible (Proceedings Pending), Ineligible (Proceedings Completed), Prohibition/Restriction, or Voluntary Exclusion"
        ),
    ] = None,
    exclusion_program: Annotated[
        Optional[str], Field(description="Procurement, NonProcurement, or Reciprocal")
    ] = None,
    page: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 10)", ge=1, le=10)
    ] = 10,
) -> dict:
    """Search for excluded parties (debarred/suspended entities) on SAM.gov."""
    # Docs: https://open.gsa.gov/api/exclusions-api/
    # Note: v1/v2/v3 are retired; v4 is current as of September 2024
    params = _params(
        exclusionName=name,
        cageCode=cage_code,
        ueiSAM=uei,
        exclusionType=exclusion_type,
        exclusionProgram=exclusion_program,
        page=page,
        size=page_size,
    )
    response = await _get_client().get(
        "/entity-information/v4/exclusions", params=params
    )
    response.raise_for_status()
    return response.json()


@mcp.tool()
async def search_subawards(
    piid: Annotated[
        Optional[str],
        Field(
            description="Prime contract PIID — retrieves all subawards under that contract"
        ),
    ] = None,
    prime_contract_key: Annotated[
        Optional[str],
        Field(
            description="Business key identifying subawards under a specific prime contract"
        ),
    ] = None,
    agency_id: Annotated[
        Optional[str],
        Field(description="Numeric agency ID of the contracting agency"),
    ] = None,
    referenced_idv_piid: Annotated[
        Optional[str],
        Field(description="Referenced IDV PIID to filter by contract family"),
    ] = None,
    prime_award_type: Annotated[
        Optional[str],
        Field(description="Type of prime award"),
    ] = None,
    from_date: Annotated[
        Optional[str],
        Field(description="Start date filter (YYYY-MM-DD)"),
    ] = None,
    to_date: Annotated[
        Optional[str],
        Field(description="End date filter (YYYY-MM-DD)"),
    ] = None,
    page_number: Annotated[int, Field(description="Page number (0-based)", ge=0)] = 0,
    page_size: Annotated[
        int, Field(description="Results per page (max 1000)", ge=1, le=1000)
    ] = 100,
) -> dict:
    """Search FSRS subcontract reports by contract PIID, agency, award type, or date range.
    Note: filtering by prime or sub entity UEI is not supported by this API —
    use search_contract_awards to find contracts by recipient UEI instead."""
    # Docs: https://open.gsa.gov/api/acquisition-subaward-reporting-api/
    params = _params(
        PIID=piid,
        primeContractKey=prime_contract_key,
        agencyId=agency_id,
        referencedIdvPIID=referenced_idv_piid,
        primeAwardType=prime_award_type,
        fromDate=from_date,
        toDate=to_date,
        pageNumber=page_number,
        pageSize=page_size,
    )
    response = await _get_client().get(
        "/prod/contract/v1/subcontracts/search", params=params
    )
    response.raise_for_status()
    return response.json()


# TODO: Re-enable once subaward PIID filter is verified against live API.
# Live testing with a public key confirmed that the PIID param does not filter
# results — all 2.6M subaward records are returned regardless of value.
# Needs retesting with a system account key to rule out rate-limit interference.
# @mcp.tool()
async def get_subawards_by_prime(
    uei: Annotated[str, Field(description="UEI of the prime contractor")],
    max_contracts: Annotated[
        int,
        Field(
            description="Number of recent prime contracts to check (max 5)", ge=1, le=5
        ),
    ] = 3,
    page_size: Annotated[
        int,
        Field(description="Subaward results per contract (max 1000)", ge=1, le=1000),
    ] = 100,
) -> dict:
    """Find subaward reports under contracts where this entity is the prime awardee.

    WARNING: Uses 1 + max_contracts API calls per invocation. Users with public
    API access (10 calls/day) should set max_contracts=1 or avoid this tool.
    System account keys (10,000 calls/day) are recommended for regular use.

    Note: finding subawards where this entity is the *subcontractor* is not
    supported by the public SAM.gov API — use the SAM.gov web UI for that."""
    # Docs: https://open.gsa.gov/api/contract-awards/ (prime awards)
    #       https://open.gsa.gov/api/acquisition-subaward-reporting-api/ (subawards)

    # Step 1: find recent prime contracts for this entity
    awards_resp = await _get_client().get(
        "/contract-awards/v1/search",
        params=_params(awardeeUniqueEntityId=uei, limit=max_contracts),
    )
    awards_resp.raise_for_status()
    award_summaries = awards_resp.json().get("awardSummary", [])
    if not award_summaries:
        return {"error": f"No prime contracts found for UEI {uei}"}

    piids = [
        a.get("contractId", {}).get("piid")
        for a in award_summaries
        if a.get("contractId", {}).get("piid")
    ]
    if not piids:
        return {"error": "Could not extract PIIDs from contract awards response"}

    # Step 2: look up subawards for each PIID in parallel
    # TODO: PIID filter param unconfirmed — live testing showed it may not filter correctly.
    #       Verify against API with a system account key before relying on these results.
    sub_resps = await asyncio.gather(
        *[
            _get_client().get(
                "/prod/contract/v1/subcontracts/search",
                params=_params(PIID=piid, pageSize=page_size),
            )
            for piid in piids
        ]
    )

    results = []
    for piid, resp in zip(piids, sub_resps):
        resp.raise_for_status()
        results.append({"piid": piid, "subawards": resp.json()})

    return {
        "uei": uei,
        "contracts_checked": len(piids),
        "results": results,
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
    # Docs: https://open.gsa.gov/api/entity-api/
    params = _params(
        legalBusinessName=name,
        physicalAddressProvinceOrStateCode=state,
        registrationStatus="A",
        size=5,
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
    agency_id: Annotated[
        Optional[str],
        Field(description="Contracting department code, e.g. 9700 for DoD"),
    ] = None,
    naics_code: Annotated[Optional[str], Field(description="NAICS code")] = None,
    award_date_from: Annotated[
        Optional[str], Field(description="Award approved date from (MM/DD/YYYY)")
    ] = None,
    award_date_to: Annotated[
        Optional[str], Field(description="Award approved date to (MM/DD/YYYY)")
    ] = None,
    amount_from: Annotated[
        Optional[float], Field(description="Minimum obligated amount in dollars")
    ] = None,
    amount_to: Annotated[
        Optional[float], Field(description="Maximum obligated amount in dollars")
    ] = None,
    contract_type: Annotated[
        Optional[str],
        Field(description="Contract type name, e.g. PURCHASE ORDER, DELIVERY ORDER"),
    ] = None,
    offset: Annotated[int, Field(description="Pagination offset (0-based)", ge=0)] = 0,
    limit: Annotated[
        int, Field(description="Results per page (max 100)", ge=1, le=100)
    ] = 10,
) -> dict:
    """Search FPDS contract award records — actual awarded contracts, not open solicitations.
    Use recipient_uei to find all contracts awarded to a specific company."""
    # Docs: https://open.gsa.gov/api/contract-awards/
    approved_date = None
    if award_date_from and award_date_to:
        approved_date = f"[{award_date_from},{award_date_to}]"
    elif award_date_from:
        approved_date = award_date_from
    elif award_date_to:
        approved_date = award_date_to

    dollars_obligated = None
    if amount_from is not None and amount_to is not None:
        dollars_obligated = f"[{amount_from},{amount_to}]"
    elif amount_from is not None:
        dollars_obligated = str(amount_from)
    elif amount_to is not None:
        dollars_obligated = str(amount_to)

    params = _params(
        awardeeUniqueEntityId=recipient_uei,
        contractingDepartmentCode=agency_id,
        naicsCode=naics_code,
        approvedDate=approved_date,
        dollarsObligated=dollars_obligated,
        awardOrIDVTypeName=contract_type,
        offset=offset,
        limit=limit,
    )
    response = await _get_client().get("/contract-awards/v1/search", params=params)
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
        Field(description="Number of competitors to return (max 10)", ge=1, le=10),
    ] = 10,
) -> dict:
    """Find companies registered under the same NAICS codes as the given entity.
    Useful for mapping the competitive landscape around a specific contractor."""
    # Docs: https://open.gsa.gov/api/entity-api/
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
                physicalAddressProvinceOrStateCode=state,
                registrationStatus="A",
                size=page_size,
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
    """Given a contract PIID, find other awarded contracts with the same NAICS code,
    awarding agency, and set-aside type."""
    # Docs: https://open.gsa.gov/api/contract-awards/
    award_resp = await _get_client().get(
        "/contract-awards/v1/search",
        params=_params(piid=contract_id, limit=1),
    )
    award_resp.raise_for_status()
    awards = award_resp.json().get("awardSummary", [])
    if not awards:
        return {"error": f"No award found for contract ID '{contract_id}'"}

    ref = awards[0]
    core = ref.get("coreData", {})
    principal_naics = core.get("productOrServiceInformation", {}).get(
        "principalNaics", []
    )
    naics_code = principal_naics[0].get("code") if principal_naics else None
    agency_code = (
        core.get("federalOrganization", {})
        .get("contractingInformation", {})
        .get("contractingDepartment", {})
        .get("code")
    )
    set_aside_code = (
        core.get("competitionInformation", {}).get("typeOfSetAside", {}).get("code")
    )

    similar_resp = await _get_client().get(
        "/contract-awards/v1/search",
        params=_params(
            naicsCode=naics_code,
            contractingDepartmentCode=agency_code,
            typeOfSetAsideCode=set_aside_code,
            limit=page_size,
        ),
    )
    similar_resp.raise_for_status()

    return {
        "reference_contract": contract_id,
        "matched_on": {
            "naics_code": naics_code,
            "agency_code": agency_code,
            "set_aside_code": set_aside_code,
        },
        "similar_awards": similar_resp.json(),
    }


@mcp.tool()
async def get_company_profile(
    uei: Annotated[str, Field(description="UEI of the company")],
    awards_page_size: Annotated[
        int, Field(description="Number of contract awards to include", ge=1, le=100)
    ] = 10,
) -> dict:
    """Full profile of a company: entity registration details and contract awards
    in a single call."""
    # Docs: https://open.gsa.gov/api/entity-api/ (entity)
    #       https://open.gsa.gov/api/contract-awards/ (awards)
    entity_resp, awards_resp = await asyncio.gather(
        _get_client().get(
            "/entity-information/v3/entities",
            params=_params(ueiSAM=uei),
        ),
        _get_client().get(
            "/contract-awards/v1/search",
            params=_params(awardeeUniqueEntityId=uei, limit=awards_page_size),
        ),
    )

    for r in (entity_resp, awards_resp):
        r.raise_for_status()

    entities = entity_resp.json().get("entityData", [])
    return {
        "entity": entities[0] if entities else None,
        "contract_awards": awards_resp.json(),
    }


def main_stdio():
    mcp.run(transport="stdio")


def main_http():
    mcp.run(transport="http")


if __name__ == "__main__":
    main_stdio()
