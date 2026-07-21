# Arch Linux Browser Terminal

A fully functional Arch Linux terminal emulator that runs in your browser. Built with Python (Flask) backend and modern web technologies.

## Features

- 🖥️ Full terminal emulation in the browser
- 🐧 Arch Linux command simulation
- 📝 Command history and autocomplete
- 🎨 Realistic terminal styling
- ⚡ Fast and responsive

## Installation

### Requirements
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kingofvids/arch-linux-python-browser.git
cd arch-linux-python-browser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

Type commands in the terminal just like a real Linux shell:

```bash
ls                    # List files and directories
cd <directory>        # Change directory
cat <file>           # Display file contents
uname -a             # System information
help                 # Show available commands
```

## Supported Commands

- `ls` / `ls -la` - List directory contents
- `cd` - Change directory
- `pwd` - Print working directory
- `cat` - Display file contents
- `echo` - Print text
- `mkdir` - Create directory
- `touch` - Create file
- `rm` - Remove file/directory
- `uname` - System information
- `whoami` - Current user
- `date` - Current date and time
- `clear` - Clear screen
- `help` - Show available commands

## Architecture

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Terminal Emulation**: xterm.js

## License

MIT License
