# Amazing Marvin Model Context Provider

This is a Model Context Provider for [Amazing Marvin](https://amazingmarvin.com/) that provides your tasks, projects, categories, and other data from your Marvin account to AI models.

## Features

- Connects to Amazing Marvin API to fetch your productivity data
- Uses Server-Sent Events (SSE) transport for efficient data streaming
- Easy to install and configure
- Compatible with AI assistants that support context providers

## Installation

### Requirements
- Python >= 3.8
- Cursor, Windsurf, Claude Desktop or another MCP Client
- Amazing Marvin account with API access

### Using Smithery (Recommended)

You can easily install this MCP with [Smithery](https://github.com/ai-smith/smithery):

```bash
smithery install amazing-marvin-mcp
```

### Manual Installation

#### Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
 "mcpServers": {
   "amazing-marvin": {
     "command": "python",
     "args": ["-m", "amazing_marvin_mcp"],
     "env": {
       "AMAZING_MARVIN_API_KEY": "your-api-key-here"
     }
   }
 }
}
```

#### Cursor

Add this to your MCP settings:

```json
{
 "mcpServers": {
   "amazing-marvin": {
     "command": "python",
     "args": ["-m", "amazing_marvin_mcp"],
     "env": {
       "AMAZING_MARVIN_API_KEY": "your-api-key-here"
     }
   }
 }
}
```

#### VS Code

Add this to your VS Code MCP settings:

```json
{
 "mcpServers": {
   "amazing-marvin": {
     "command": "python",
     "args": ["-m", "amazing_marvin_mcp"],
     "env": {
       "AMAZING_MARVIN_API_KEY": "your-api-key-here"
     }
   }
 }
}
```

#### Using pip

```bash
pip install amazing-marvin-mcp
```

#### From Source

```bash
git clone https://github.com/bgheneti/Amazing-Marvin-MCP.git
cd Amazing-Marvin-MCP
pip install -e .
```

## Configuration

You'll need an API key from Amazing Marvin to use this MCP. You can get your API key by:

1. Going to Settings in Amazing Marvin
2. Navigating to the API section
3. Enabling the API and copying your API token

Then set the API key as an environment variable:

```bash
export AMAZING_MARVIN_API_KEY="your-api-key"
```

Alternatively, create a `.env` file in the root directory with:

```
AMAZING_MARVIN_API_KEY=your-api-key
```

## Usage

### Starting the server

```bash
amazing-marvin-mcp
```

This will start the server on port 3000 by default. You can customize the port by setting the `PORT` environment variable.

### Querying for context

The MCP will respond to different query types:
- Tasks/todos: Any query containing "task" or "todo"  
- Projects: Any query containing "project"
- Categories: Any query containing "category" or "categor"
- Specific dates: Any query containing a date in YYYY-MM-DD format
- All data: Any query containing "all"

If no specific context is requested, it will default to returning your tasks.

## Default Projects and Inbox

When you connect your Amazing Marvin account, the MCP will recognize **Work** and **Personal** as default projects that are automatically created for most users. These help you organize your tasks into common categories right from the start.  
Additionally, the **Inbox** serves as a special area for capturing uncategorized tasks before you sort them into projects.

- **Work**: Default project for professional or job-related tasks.
- **Personal**: Default project for personal or non-work tasks.
- **Inbox**: Special holding area for new or uncategorized tasks.

You can rename, remove, or add more projects as needed.

## Development

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/Amazing-Marvin-MCP.git
cd Amazing-Marvin-MCP
pip install -e ".[dev]"
```

### Testing

To test your API connection and fetch your projects:

```bash
python api_test.py --api-key "your-api-key" --test-projects
```

This will verify that your projects (including default ones) are accessible via the MCP.

## License

MIT
