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

| Tool | Description |
|---|---|
| `search_entities` | Search registered entities (vendors/organizations) by name, UEI, CAGE code, state, country, or registration status |
| `get_entity` | Get full details for a specific entity by UEI |
| `search_opportunities` | Search contract opportunities/solicitations by keyword, NAICS code, set-aside type, date range, and more |
| `search_exclusions` | Search for debarred or suspended parties by name, UEI, or CAGE code |

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
