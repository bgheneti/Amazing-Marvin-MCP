# 🚀 Amazing Marvin AI Assistant Integration

[![PyPI version](https://img.shields.io/pypi/v/amazing-marvin-mcp.svg)](https://pypi.org/project/amazing-marvin-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI downloads](https://img.shields.io/pypi/dm/amazing-marvin-mcp.svg)](https://pypi.org/project/amazing-marvin-mcp/)
[![Model Context Protocol](https://img.shields.io/badge/MCP-Compatible-brightgreen.svg)](https://modelcontextprotocol.io/)
[![smithery badge](https://smithery.ai/badge/@bgheneti/amazing-marvin-mcp)](https://smithery.ai/server/@bgheneti/amazing-marvin-mcp)

> Connect your Amazing Marvin productivity system with AI assistants for smarter task management

## 📋 Table of Contents

- [What is this?](#-what-is-this)
- [Quick Start (2 minutes)](#-quick-start-2-minutes)
- [What can you do with this?](#-what-can-you-do-with-this)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Development](#-development)
- [Privacy & Security](#-privacy--security)

## 🎯 What is this?

This connects your [Amazing Marvin](https://amazingmarvin.com/) productivity system with AI assistants like Claude, Cursor, and others. Instead of manually copying your tasks and projects into chat, your AI assistant can see and help with your actual Amazing Marvin data.

### ✨ Key Benefits

- 🔄 **Stay in sync** - Your AI assistant always sees your current tasks, projects, and goals
- 📋 **Smart help** - Get personalized advice based on your actual workload and priorities
- ⚡ **Save time** - No more copy-pasting task lists or explaining your projects
- 🎯 **Better focus** - AI helps you identify what's most important right now
- 🔒 **Private** - Your data stays between Amazing Marvin and your AI assistant

## ⚡ Quick Start (2 minutes)

### Step 1: Get your Amazing Marvin API key
1. Open Amazing Marvin → Settings → API
2. Enable the API and copy your token
3. Keep this handy! 🔑

### Step 2: Install
**Easy way (Smithery):**
```bash
npx -y @smithery/cli install @bgheneti/amazing-marvin-mcp --client claude
```
Paste the API key when prompted

**Alternative (pip):**
```bash
pip install amazing-marvin-mcp
```
Then add to your AI client config (see [installation guide](#-installation))

### Step 3: Verify it's working
Ask your AI: *"What tasks do I have today?"*

🎉 **That's it!** Your AI can now see your Amazing Marvin data.

---

## 💡 What can you do with this?

Once connected, your AI assistant becomes your personal productivity coach with access to your real Amazing Marvin data:

### 📅 Daily Planning Help
*"What should I focus on today?"* - Get personalized recommendations based on your actual deadlines and priorities

*"I'm feeling overwhelmed - what's most important?"* - AI helps you cut through the noise and identify what really matters

### 🎯 Project Insights
*"How is my website redesign project going?"* - See progress, completed tasks, and what's left to do

*"Show me everything related to client work this week"* - Get organized views of your tasks by project or category

### 📊 Progress Tracking
*"What did I accomplish this week?"* - Review your productivity patterns and celebrate wins

*"Which days am I most productive?"* - Understand your patterns to plan better

### ⏰ Smart Scheduling
*"What's overdue and needs attention?"* - Never lose track of important deadlines

*"Help me plan tomorrow based on what I have scheduled"* - Get realistic daily plans that work

### ⏱️ Time Tracking
*"Start tracking time on this task"* - Seamlessly manage time tracking from your AI chat

*"What have I been working on today?"* - Review your time allocation and focus

**Why this is better than generic productivity advice:** Your AI sees your actual tasks, deadlines, and progress - so the help you get is personalized to your real situation, not generic tips.

**Note:** This covers most Amazing Marvin features, though some advanced customizations and strategies have limited API access.

## 📦 Installation

### Option 1: Smithery (Easiest)
```bash
npx -y @smithery/cli install @bgheneti/amazing-marvin-mcp --client claude
```
[Visit Smithery Registry](https://smithery.ai/server/@bgheneti/amazing-marvin-mcp) for other clients.

### Option 2: Pip + Manual Config

**Why choose this option:**
- ✅ Works with any MCP-compatible AI client
- ✅ Easy to update: just `pip install --upgrade amazing-marvin-mcp`

#### Prerequisites
- ✅ Python 3.10+
- ✅ Claude Desktop, Cursor, Windsurf, VS Code, or another MCP client
- ✅ Amazing Marvin account with API access

#### Installation
```bash
# Install from PyPI (recommended)
pip install amazing-marvin-mcp
```

#### 📱 Client Configuration

<details>
<summary>🖥️ Claude Desktop</summary>

Add to your `claude_desktop_config.json`:

**📍 Config file locations:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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
</details>

<details>
<summary>🎯 Cursor</summary>

Add to your MCP settings:

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
</details>

<details>
<summary>💨 Windsurf</summary>

Add to your Windsurf MCP configuration:

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
</details>

<details>
<summary>🆚 VS Code</summary>

Add to your VS Code MCP configuration:

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
</details>

## 💡 Usage Examples

The MCP provides specific tools that your AI can use. Simply ask your AI to help with productivity tasks and it will use the appropriate tools:

| What you might ask | Tools the AI will use |
|-------------------|----------------------|
| *"What tasks do I have today?"* | `get_tasks()` |
| *"Show me my projects"* | `get_projects()` |
| *"What's overdue?"* | `get_due_items()` |
| *"Create a new task for X"* | `create_task()` |
| *"Mark task Y as done"* | `mark_task_done()` |
| *"Start tracking time on this"* | `start_time_tracking()` |

### 📁 How it understands your setup

Your AI assistant automatically understands your Amazing Marvin structure:

- **Work & Personal projects** - Keeps your professional and personal tasks organized
- **Categories and labels** - Knows how you've organized your productivity system
- **Due dates and priorities** - Understands what's urgent vs. important
- **Completed vs. pending** - Tracks your progress and momentum

No need to explain your system - your AI just gets it!

## 🔧 Troubleshooting

### ❌ Common Issues

<details>
<summary><strong>"API key not found" error</strong></summary>

**Problem**: The MCP can't find your API key.

**Solutions**:
1. Verify your API key is correct in Amazing Marvin Settings → API
2. Check the environment variable: `echo $AMAZING_MARVIN_API_KEY`
3. Restart your AI client after setting the key
4. Ensure no extra spaces in your API key
</details>

<details>
<summary><strong>"Connection refused" or timeout errors</strong></summary>

**Problem**: Can't connect to Amazing Marvin API.

**Solutions**:
1. Check your internet connection
2. Verify Amazing Marvin service status
3. Try the connection test: `python -c "import requests; print(requests.get('https://serv.amazingmarvin.com/api').status_code)"`
4. Check if you're behind a corporate firewall
</details>

<details>
<summary><strong>AI says "I don't see any Amazing Marvin data"</strong></summary>

**Problem**: MCP is running but not returning data.

**Solutions**:
1. Ask explicitly: *"Use the Amazing Marvin tool to get my tasks"*
2. Check if you have any tasks in Amazing Marvin
3. Verify API permissions in Amazing Marvin settings
4. Restart your AI client
</details>

<details>
<summary><strong>Python module not found</strong></summary>

**Problem**: `ModuleNotFoundError: No module named 'amazing_marvin_mcp'`

**Solutions**:
1. Reinstall: `pip install --force-reinstall amazing-marvin-mcp`
2. Check Python path: `python -c "import sys; print(sys.path)"`
3. Use full path: `which python` and use that in your config
</details>

## ❓ Common Questions

<details>
<summary><strong>Is my data safe?</strong></summary>

Absolutely! Your Amazing Marvin data stays between you, Amazing Marvin, and your AI assistant. The connection runs on your computer - nothing is stored on external servers or shared with anyone else.
</details>

<details>
<summary><strong>Which AI assistants work with this?</strong></summary>

Any AI assistant that supports the Model Context Protocol, including Claude Desktop, Cursor, VS Code, and Windsurf. More are being added regularly.
</details>

<details>
<summary><strong>What can my AI assistant see?</strong></summary>

Your AI can see:
- ✅ Your tasks, projects, and categories
- ✅ Due dates, priorities, and completion status
- ✅ Time tracking and goals
- ✅ Labels and organizational structure
- ✅ Productivity history and patterns

Basically everything you see in Amazing Marvin, your AI can see too.
</details>

<details>
<summary><strong>Will this make my AI assistant slower?</strong></summary>

Not noticeably. The system fetches your data from Amazing Marvin when you ask productivity questions. Response time depends on your internet connection, but it's usually very quick.
</details>

<details>
<summary><strong>Can my AI assistant change my tasks?</strong></summary>

Yes, if you ask it to! Your AI can:
- ✅ Create new tasks and projects
- ✅ Mark tasks as done
- ✅ Start and stop time tracking
- ✅ Organize tasks in batches

Don't worry - it only makes changes when you specifically ask it to.
</details>

<details>
<summary><strong>Can I see completed tasks?</strong></summary>

Yes! The MCP can find and display completed tasks in several ways:

**📊 In Daily Focus View:**
- ✅ Shows today's completed tasks alongside pending ones
- ✅ Includes completion count and productivity notes
- ✅ Separates completed from pending for clear progress tracking

**📁 In Project Overviews:**
- ✅ Lists completed vs pending tasks separately
- ✅ Shows completion rate and progress summary
- ✅ Provides detailed task breakdowns

**🔍 Efficient Historical Access:**
- ✅ Get completed tasks for any specific date (e.g., "June 10th")
- ✅ Flexible time range summaries (1 day, 7 days, 30 days, or custom date ranges)
- ✅ **Complete task data included** - no additional API calls needed for task details
- ✅ **Smart caching** - historical data cached for 10 minutes to avoid redundant calls
- ✅ Project-wise completion analytics with resolved project names
- ✅ Efficient API filtering with cache hit rate tracking
- ✅ Real-time access to completion timestamps and project correlations
</details>

<details>
<summary><strong>What can't the MCP do?</strong></summary>

**🚫 Cannot Delete or Remove:**
- ❌ Delete tasks (requires special API permissions)
- ❌ Delete projects or categories
- ❌ Remove labels or goals
- ❌ Clear time tracking history

**📝 Cannot Edit:**
- ❌ Modify existing task content (title, notes, due dates)
- ❌ Move tasks between projects
- ❌ Change task priorities or labels
- ❌ Update project settings

**📚 Limited Access:**
- ❌ Full historical completed task archive
- ❌ Detailed time tracking reports (only basic tracking)
- ❌ Private notes or sensitive data
- ❌ Advanced Amazing Marvin features (strategies, rewards setup)

For these operations, use the Amazing Marvin app directly.
</details>

<details>
<summary><strong>How often is the data updated?</strong></summary>

Data is fetched in real-time with each request to Amazing Marvin's API. There's no background syncing or caching - you always get the most current data from your Amazing Marvin account.
</details>

## 👨‍💻 Development

### 🛠️ Setup
```bash
git clone https://github.com/bgheneti/Amazing-Marvin-MCP.git
cd Amazing-Marvin-MCP
pip install -e ".[dev]"
pre-commit install
```

### 🔑 Set your API key

**Option A: Environment variable**
```bash
export AMAZING_MARVIN_API_KEY="your-api-key-here"
```

**Option B: Create a `.env` file**
```env
AMAZING_MARVIN_API_KEY=your-api-key-here
```

### 🧪 Testing
```bash
pytest tests/ -v
```

**⚠️ Note**: Tests create temporary items in your Amazing Marvin account with `[TEST]` prefixes. These may need manual cleanup due to API limitations.

### 📋 Code Quality
```bash
# Run all checks
pre-commit run --all-files

# Individual tools
ruff check .          # Linting
ruff format .         # Formatting
mypy .               # Type checking
pytest tests/        # Tests
```

### 🔄 Available Tools
The MCP provides 27 comprehensive tools to AI assistants:

**📖 Read Operations:**
- `get_tasks()` - Today's scheduled items
- `get_projects()` - All projects
- `get_categories()` - All categories
- `get_due_items()` - Overdue/due items
- `get_child_tasks()` - Subtasks
- `get_labels()` - Task labels
- `get_goals()` - Goals and objectives
- `get_account_info()` - Account details
- `get_completed_tasks()` - Completed items with date categorization
- `get_completed_tasks_for_date()` - Completed items for specific date
- `get_productivity_summary_for_time_range()` - Flexible productivity analytics (by days, or start/end dates)
- `get_currently_tracked_item()` - Active time tracking

**✏️ Write Operations:**
- `create_task()` - Create new tasks
- `mark_task_done()` - Complete tasks
- `create_project()` - Create new projects
- `start_time_tracking()` - Begin time tracking
- `stop_time_tracking()` - End time tracking
- `batch_mark_done()` - Complete multiple tasks
- `batch_create_tasks()` - Create multiple tasks
- `claim_reward_points()` - Claim kudos points

**🔧 Utility Operations:**
- `test_api_connection()` - Verify API connectivity
- `get_project_overview()` - Project analytics
- `get_daily_focus()` - Daily priorities
- `get_productivity_summary()` - Performance metrics
- `time_tracking_summary()` - Time analytics
- `quick_daily_planning()` - Planning assistance
- `create_project_with_tasks()` - Project setup
- `get_time_tracks()` - Time tracking history

## 🤝 Contributing

### 🚀 Publishing New Versions

This project uses automated publishing to PyPI via GitHub Actions.

**For maintainers:**
```bash
# Make your changes and test them
pytest tests/ -v
ruff check src/
mypy src/amazing_marvin_mcp/

# Use the release script to bump version and create tag
python scripts/release.py patch   # for bug fixes
python scripts/release.py minor   # for new features
python scripts/release.py major   # for breaking changes

# Push to trigger CI and PyPI publish
git push origin main
git push origin v1.x.x
```

**The workflow:**
1. ✅ Tests run on Python 3.8-3.12
2. ✅ Linting and type checking pass
3. 📦 Package is built and checked
4. 🚀 Published to PyPI automatically on version tags

### 🔧 Local Development Setup
```bash
git clone https://github.com/bgheneti/Amazing-Marvin-MCP.git
cd Amazing-Marvin-MCP
pip install -e ".[dev]"
pre-commit install
```

### 🧪 Testing
You can also manually publish to Test PyPI by running the workflow manually on GitHub.

## 🔒 Privacy & Security

### 🛡️ Your Data Protection
- **Local Processing**: MCP runs entirely on your machine
- **Direct Connection**: Data goes directly from Amazing Marvin to your AI
- **No Cloud Storage**: Nothing is stored on external servers
- **API Key Security**: Store your key securely using environment variables

### 🔐 Best Practices
- ✅ Use environment variables for API keys (not config files)
- ✅ Don't share your API key in screenshots or logs
- ✅ Keep your API key secure and treat it like a password

### ⚖️ Performance & Limitations

**What to expect:**
- Your AI assistant fetches fresh data from Amazing Marvin when you ask questions
- Historical data is cached briefly to avoid repeated requests
- Response time depends on your internet connection to Amazing Marvin
- Very frequent requests might occasionally hit rate limits (just wait a moment)

**Technical details:**
- Data is fetched in real-time for accuracy
- Some data is cached for 10 minutes to improve speed
- Batch operations work efficiently for multiple tasks
- All the core Amazing Marvin features are supported

## 📄 License

MIT License - see [LICENSE](https://opensource.org/licenses/MIT) for details.

---

<div align="center">

**Made with ❤️ for Amazing Marvin users**

[Report Issues](https://github.com/bgheneti/Amazing-Marvin-MCP/issues) • [Suggest Improvements](https://github.com/bgheneti/Amazing-Marvin-MCP/issues/new) • [Star on GitHub](https://github.com/bgheneti/Amazing-Marvin-MCP)

</div>
