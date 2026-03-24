# sam-mcp

An MCP server for accessing [SAM.gov](https://sam.gov) APIs, built with [FastMCP](https://github.com/jlowin/fastmcp) and Python.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A SAM.gov API key — get one at [sam.gov/workspace/profile/account-details](https://sam.gov/workspace/profile/account-details)

## Setup

```bash
git clone https://github.com/rsivilli/sam-mcp
cd sam-mcp
cp .env.example .env
```

Edit `.env` and set your API key:

```env
SAM_API_KEY=your_api_key_here
```

## Running the server

**stdio** (for MCP clients that spawn the process, e.g. Claude Desktop):

```bash
uv run sam-mcp
```

**HTTP** (for connecting remotely):

```bash
uv run sam-mcp-http
```

## Claude Desktop configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/sam-mcp", "sam-mcp"],
      "env": {
        "SAM_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available tools

### Entity & registration

| Tool | Description |
|---|---|
| `search_entities` | Search registered entities (vendors/organizations) by name, UEI, CAGE code, state, country, or registration status |
| `get_entity` | Get full details for a specific entity by UEI |
| `resolve_company` | Resolve a company name to its SAM.gov entity record and UEI — returns the single best match |

### Opportunities & exclusions

| Tool | Description |
|---|---|
| `search_opportunities` | Search contract opportunities/solicitations by keyword, NAICS code, set-aside type, date range, and more. `postedFrom` and `postedTo` are required. |
| `search_exclusions` | Search for debarred or suspended parties by name, UEI, or CAGE code |

### Contract awards

| Tool | Description |
|---|---|
| `search_contract_awards` | Search FPDS contract award records by recipient UEI, agency, NAICS code, date range, or dollar amount |
| `get_similar_awards` | Given a contract PIID, find other awarded contracts with the same NAICS code, awarding agency, and set-aside type |

### Company intelligence

| Tool | Description |
|---|---|
| `get_company_profile` | Full profile of a company: entity registration and contract awards in a single call |
| `find_competitors` | Find companies registered under the same NAICS codes as a given entity |
| `search_subawards` | Search FSRS subcontract reports by PIID, agency, award type, or date range |
| `get_subawards_by_prime` | *(disabled — subaward PIID filter unverified against live API; re-enable once confirmed with a system account key)* |

## API rate limits

Rate limits are per API key per day and reset at midnight UTC.

| User type | Daily limit |
|---|---|
| Non-federal (no SAM.gov role) | 10 requests/day |
| Non-federal (with SAM.gov role) | 1,000 requests/day |
| Federal personal key | 1,000 requests/day |
| Federal system account | 10,000 requests/day |

For production use, a **system account** key is recommended. Apply through your SAM.gov account settings.

## Development

Install dev dependencies and set up pre-commit hooks:

```bash
uv sync
uv run pre-commit install
```

Run linting and formatting checks:

```bash
uv run pre-commit run --all-files
```
