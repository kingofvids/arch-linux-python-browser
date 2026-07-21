from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime
import subprocess
import hashlib
import random

app = Flask(__name__)
CORS(app)

# Simulated package database
PACKAGE_DB = {
    'base': {
        'linux': {'version': '6.0.12-arch1-1', 'size': '15.2 MB', 'deps': []},
        'linux-firmware': {'version': '20230117.3e5e8bb-1', 'size': '289.7 MB', 'deps': []},
        'base': {'version': '2-2', 'size': '1.2 KB', 'deps': ['linux', 'linux-firmware']},
    },
    'core': {
        'bash': {'version': '5.1.016-2', 'size': '1.5 MB', 'deps': []},
        'glibc': {'version': '2.36-11', 'size': '4.1 MB', 'deps': []},
        'gcc': {'version': '12.2.1-2', 'size': '85.3 MB', 'deps': ['glibc']},
        'make': {'version': '4.3-4', 'size': '546 KB', 'deps': []},
        'binutils': {'version': '2.39.0-2', 'size': '11.2 MB', 'deps': []},
        'coreutils': {'version': '9.1-1', 'size': '3.4 MB', 'deps': []},
        'curl': {'version': '7.87.0-2', 'size': '1.8 MB', 'deps': []},
        'git': {'version': '2.39.0-1', 'size': '16.5 MB', 'deps': ['curl']},
        'vim': {'version': '9.0.870-1', 'size': '12.3 MB', 'deps': []},
        'nano': {'version': '7.2-1', 'size': '436 KB', 'deps': []},
        'openssh': {'version': '9.1p1-1', 'size': '984 KB', 'deps': []},
        'python': {'version': '3.11.1-1', 'size': '58.4 MB', 'deps': []},
        'python-pip': {'version': '22.3.1-1', 'size': '2.1 MB', 'deps': ['python']},
        'gnome': {'version': '43.0-1', 'size': '1.2 GB', 'deps': []},
        'gnome-shell': {'version': '43.3-1', 'size': '8.5 MB', 'deps': ['gnome']},
        'flatpak': {'version': '1.14.1-1', 'size': '8.2 MB', 'deps': []},
    },
    'extra': {
        'nodejs': {'version': '19.4.0-1', 'size': '42.1 MB', 'deps': []},
        'docker': {'version': '20.10.21-1', 'size': '85.6 MB', 'deps': []},
        'postgresql': {'version': '15.1-1', 'size': '24.5 MB', 'deps': []},
        'mysql': {'version': '8.0.32-1', 'size': '425.3 MB', 'deps': []},
        'mongodb': {'version': '5.0.14-1', 'size': '312.7 MB', 'deps': []},
        'nginx': {'version': '1.23.3-1', 'size': '1.8 MB', 'deps': []},
        'apache': {'version': '2.4.54-1', 'size': '5.7 MB', 'deps': []},
    },
    'flathub': {
        'org.gnome.Nautilus': {'version': '43.1', 'size': '8.3 MB', 'deps': []},
        'org.gnome.TextEditor': {'version': '43.0', 'size': '2.1 MB', 'deps': []},
        'org.firefox.firefox': {'version': '109.0', 'size': '157.8 MB', 'deps': []},
        'org.telegram.desktop': {'version': '4.5.3', 'size': '98.2 MB', 'deps': []},
        'com.spotify.Client': {'version': '1.1.97', 'size': '312.5 MB', 'deps': []},
        'org.blender.Blender': {'version': '3.4.1', 'size': '256.3 MB', 'deps': []},
        'com.github.tchx84.Flatseal': {'version': '2.0.4', 'size': '1.2 MB', 'deps': []},
        'org.videolan.VLC': {'version': '3.0.18', 'size': '78.5 MB', 'deps': []},
    }
}

# Desktop Environment Data
DESKTOP_APPS = {
    'nautilus': {'name': 'Files', 'icon': '📁', 'cmd': 'nautilus'},
    'gnome-terminal': {'name': 'Terminal', 'icon': '⌨️', 'cmd': 'gnome-terminal'},
    'gedit': {'name': 'Text Editor', 'icon': '📝', 'cmd': 'gedit'},
    'firefox': {'name': 'Firefox', 'icon': '🌐', 'cmd': 'firefox'},
    'settings': {'name': 'Settings', 'icon': '⚙️', 'cmd': 'gnome-control-center'},
    'calculator': {'name': 'Calculator', 'icon': '🧮', 'cmd': 'gnome-calculator'},
    'music': {'name': 'Music Player', 'icon': '🎵', 'cmd': 'rhythmbox'},
}

# Linux Kernel sample files structure (kept for brevity)
KERNEL_FILES = {
    'linux': {
        'README': 'Linux Kernel 6.0.12 - See /src/linux for kernel source'
    }
}

# Virtual file system
VIRTUAL_FS = {
    '/': {
        'type': 'directory',
        'contents': {
            'home': {'type': 'directory', 'contents': {
                'user': {'type': 'directory', 'contents': {
                    'Desktop': {'type': 'directory', 'contents': {}},
                    'Documents': {'type': 'directory', 'contents': {}},
                    'README.txt': {'type': 'file', 'content': 'Welcome to Arch Linux Terminal!\\nRun "startde" to launch the desktop environment.'},
                }}\
            }},
            'etc': {'type': 'directory', 'contents': {
                'os-release': {'type': 'file', 'content': 'NAME="Arch Linux"\\nID=arch\\nID_LIKE=archlinux\\nPRETTY_NAME="Arch Linux"\\nVERSION="rolling"'},
            }},
            'usr': {'type': 'directory', 'contents': {'bin': {'type': 'directory', 'contents': {}}}},
            'var': {'type': 'directory', 'contents': {
                'cache': {'type': 'directory', 'contents': {
                    'pacman': {'type': 'directory', 'contents': {
                        'pkg': {'type': 'directory', 'contents': {}}\
                    }}\
                }},
            }},
            'src': {'type': 'directory', 'contents': KERNEL_FILES},
            'bin': {'type': 'directory', 'contents': {}},
        }
    }
}

# Session state for each user
sessions = {}

class FileSystem:
    def __init__(self):
        self.fs = VIRTUAL_FS
        self.current_dir = '/home/user'
        self.installed_packages = {'base', 'bash', 'glibc', 'coreutils', 'gnome', 'gnome-shell'}
        self.installed_flatpaks = set()
        self.in_desktop = False
        self.desktop_windows = {}
        self.active_window = None
    
    def get_path_parts(self, path):
        if path.startswith('/'):
            path = path[1:]
        return [p for p in path.split('/') if p]
    
    def navigate_to_path(self, path):
        if path == '/':
            return self.fs['/']
        
        parts = self.get_path_parts(path)
        current = self.fs['/']
        
        for part in parts:
            if part in current.get('contents', {}):
                current = current['contents'][part]
            else:
                return None
        
        return current
    
    def resolve_path(self, path):
        if path.startswith('/'):
            return path
        
        if path == '.':
            return self.current_dir
        
        if path == '..':
            parts = self.get_path_parts(self.current_dir)
            if parts:
                return '/' + '/'.join(parts[:-1])
            return '/'
        
        if self.current_dir == '/':
            return '/' + path
        else:
            return self.current_dir + '/' + path
    
    def list_directory(self, path):
        node = self.navigate_to_path(path)
        if node is None:
            return None
        if node.get('type') != 'directory':
            return None
        return node.get('contents', {})
    
    def read_file(self, path):
        node = self.navigate_to_path(path)
        if node is None:
            return None
        if node.get('type') != 'file':
            return None
        return node.get('content', '')
    
    def create_directory(self, path, name):
        parent = self.navigate_to_path(path)
        if parent and parent.get('type') == 'directory':
            if name not in parent.get('contents', {}):
                parent['contents'][name] = {'type': 'directory', 'contents': {}}
                return True
        return False
    
    def create_file(self, path, name):
        parent = self.navigate_to_path(path)
        if parent and parent.get('type') == 'directory':
            if name not in parent.get('contents', {}):
                parent['contents'][name] = {'type': 'file', 'content': ''}
                return True
        return False
    
    def delete_item(self, path, name):
        parent = self.navigate_to_path(path)
        if parent and parent.get('type') == 'directory':
            if name in parent.get('contents', {}):
                del parent['contents'][name]
                return True
        return False

def get_all_packages():
    """Get all available packages from database"""
    all_pkgs = {}
    for repo, packages in PACKAGE_DB.items():
        all_pkgs.update(packages)
    return all_pkgs

def render_desktop(fs):
    """Render ASCII desktop environment"""
    width, height = 80, 24
    desktop = []
    
    # Top panel
    desktop.append('┌' + '─' * 78 + '┐')
    panel = '│ \x1b[44m\x1b[37m GNOME Desktop Environment \x1b[0m' + ' ' * 48 + '🔋 100%  🕐 ' + datetime.now().strftime('%H:%M') + ' │'
    desktop.append(panel)
    desktop.append('├' + '─' * 78 + '┤')
    
    # Desktop area with taskbar
    for i in range(height - 6):
        desktop.append('│' + ' ' * 78 + '│')
    
    # Bottom taskbar
    desktop.append('├' + '─' * 78 + '┤')
    taskbar = '│\x1b[44m\x1b[37m 🏠 Activities'
    for app in list(DESKTOP_APPS.values())[:5]:
        taskbar += f"  {app['icon']} {app['name'][:6]}"
    taskbar += ' ' * (79 - len(taskbar) + 8) + '│'
    desktop.append(taskbar)
    desktop.append('└' + '─' * 78 + '┘')
    
    return '\n'.join(desktop)

def render_window(title, content):
    """Render a desktop window"""
    width = 60
    window = []
    window.append('╔' + '═' * (width - 2) + '╗')
    window.append(f'║ \x1b[44m\x1b[37m{title:<{width-4}}\x1b[0m │')
    window.append('╠' + '═' * (width - 2) + '╣')
    
    lines = content.split('\n')
    for line in lines[:10]:
        truncated = line[:width-4] if len(line) > width-4 else line
        window.append(f'║ {truncated:<{width-4}} │')
    
    window.append('╠' + '═' * (width - 2) + '╣')
    window.append('║ [Close] [Min] [Max]' + ' ' * (width - 24) + '║')
    window.append('╚' + '═' * (width - 2) + '╝')
    
    return '\n'.join(window)

def execute_command(session_id, command):
    """Execute a command and return output"""
    if session_id not in sessions:
        sessions[session_id] = {
            'fs': FileSystem(),
            'history': []
        }
    
    session = sessions[session_id]
    fs = session['fs']
    
    session['history'].append(command)
    
    parts = command.strip().split()
    if not parts:
        return ''
    
    cmd = parts[0]
    args = parts[1:]
    
    # Desktop Environment Commands
    if cmd == 'startde':
        if fs.in_desktop:
            return 'Desktop environment already running'
        fs.in_desktop = True
        return '__STARTDE__'
    
    elif cmd == 'flatpak':
        if not args:
            return 'flatpak: missing arguments'
        
        flag = args[0]
        
        if flag == 'install':
            if len(args) < 2:
                return 'flatpak install: missing package name'
            pkg = args[1]
            
            if pkg not in PACKAGE_DB.get('flathub', {}):
                return f"error: flatpak '{pkg}' not found in flathub"
            
            if pkg in fs.installed_flatpaks:
                return f"flatpak: {pkg} is already installed"
            
            pkg_info = PACKAGE_DB['flathub'][pkg]
            fs.installed_flatpaks.add(pkg)
            return f"Downloading {pkg}...\\nInstalling {pkg} {pkg_info['version']}...\\n{pkg}: installed ({pkg_info['size']})"
        
        elif flag == 'remove':
            if len(args) < 2:
                return 'flatpak remove: missing package name'
            pkg = args[1]
            
            if pkg not in fs.installed_flatpaks:
                return f"error: flatpak '{pkg}' not installed"
            
            fs.installed_flatpaks.discard(pkg)
            return f"Removing {pkg}...\\n{pkg}: removed"
        
        elif flag == 'list' or flag == '--app':
            if not fs.installed_flatpaks:
                return 'No flatpak applications installed'
            return '\\n'.join([f"{app} {PACKAGE_DB['flathub'][app]['version']}" 
                             for app in sorted(fs.installed_flatpaks) if app in PACKAGE_DB['flathub']])
        
        elif flag == 'search':
            if len(args) < 2:
                return 'flatpak search: missing search term'
            search = args[1].lower()
            results = []
            for app, info in PACKAGE_DB['flathub'].items():
                if search in app.lower() or search in info['name'].lower():
                    results.append(f"{app:30} {info['version']:15} {info['size']}")
            return '\\n'.join(results) if results else f"No flatpaks found matching '{search}'"
        
        elif flag == 'run':
            if len(args) < 2:
                return 'flatpak run: missing application id'
            app = args[1]
            if app not in fs.installed_flatpaks:
                return f"error: flatpak '{app}' not installed. Install with: flatpak install {app}"
            return f"Running {app}...\\nApplication launched in sandbox"
        
        elif flag == '-h' or flag == '--help':
            return '''flatpak 1.14.1 - Application deployment framework

Usage: flatpak [options] command [arguments]

Commands:
  install <app>      Install application from flathub
  remove <app>       Remove application
  run <app>          Run application
  list               List installed applications
  search <term>      Search flathub
  -h, --help         Show this help

Examples:
  flatpak install org.firefox.firefox
  flatpak list
  flatpak run org.firefox.firefox'''
        
        else:
            return f"flatpak: unknown command '{flag}'"
    
    # Pacman commands
    elif cmd == 'pacman':
        if not args:
            return 'pacman: missing arguments\\nTry: pacman -h for help'
        
        flag = args[0] if args else ''
        
        if flag == '-S' or flag == '--sync':
            if len(args) < 2:
                return 'pacman -S: missing package name'
            pkg_name = args[1].lower()
            all_pkgs = get_all_packages()
            
            if pkg_name not in all_pkgs:
                return f"error: package '{pkg_name}' not found"
            
            if pkg_name in fs.installed_packages:
                return f"warning: {pkg_name} is already installed"
            
            pkg_info = all_pkgs[pkg_name]
            fs.installed_packages.add(pkg_name)
            return f"resolving dependencies...\\ninstalling {pkg_name} {pkg_info['version']}...\\n{pkg_name}: installed ({pkg_info['size']})"
        
        elif flag == '-R' or flag == '--remove':
            if len(args) < 2:
                return 'pacman -R: missing package name'
            pkg_name = args[1].lower()
            
            if pkg_name == 'base' or pkg_name == 'bash':
                return f"error: failed to remove '{pkg_name}' (required base package)"
            
            if pkg_name not in fs.installed_packages:
                return f"error: package '{pkg_name}' not found"
            
            fs.installed_packages.discard(pkg_name)
            return f"removing {pkg_name}...\\n{pkg_name}: removed"
        
        elif flag == '-Q' or flag == '--query':
            if len(args) > 1 and args[1].lower() == 'all':
                sorted_pkgs = sorted(fs.installed_packages)
                return '\\n'.join([f"{pkg} {get_all_packages()[pkg]['version']}" for pkg in sorted_pkgs if pkg in get_all_packages()])
            elif len(args) > 1:
                pkg_name = args[1].lower()
                if pkg_name in fs.installed_packages and pkg_name in get_all_packages():
                    pkg_info = get_all_packages()[pkg_name]
                    return f"{pkg_name} {pkg_info['version']}"
                return f"error: package '{pkg_name}' not found"
            else:
                sorted_pkgs = sorted(fs.installed_packages)
                return '\\n'.join([f"{pkg} {get_all_packages()[pkg]['version']}" for pkg in sorted_pkgs if pkg in get_all_packages()])
        
        elif flag == '-Ss':
            if len(args) < 2:
                return 'pacman -Ss: missing search term'
            search_term = args[1].lower()
            all_pkgs = get_all_packages()
            results = []
            
            for repo, packages in PACKAGE_DB.items():
                for pkg_name, pkg_info in packages.items():
                    if search_term in pkg_name.lower():
                        results.append(f"{repo}/{pkg_name} {pkg_info['version']}\\n    {pkg_name} package")
            
            return '\\n'.join(results) if results else f"No packages found matching '{search_term}'"
        
        elif flag == '-Syu':
            return ":: Synchronizing package databases...\\n:: Starting full system upgrade...\\nthere is nothing to do\\n(already up to date)"
        
        elif flag == '-h' or flag == '--help':
            return '''pacman 6.0.2 - package manager for Arch Linux

Usage: pacman [options] [targets]

Options:
  -S, --sync            Install or upgrade packages
  -R, --remove          Remove packages
  -Q, --query           Query the package database
  -Ss                   Search package database
  -Syu                  Update all packages
  -h, --help            Show this help

Examples:
  pacman -S vim         Install vim
  pacman -R vim         Remove vim
  pacman -Q             List installed packages
  pacman -Ss python     Search for python packages
  pacman -Syu           Update system'''
        else:
            return f"pacman: unknown option '{flag}'"
    
    # Help command
    elif cmd == 'help':
        return """Available commands:
  ls              - List directory contents
  cd <dir>        - Change directory
  pwd             - Print working directory
  cat <file>      - Display file contents
  echo <text>     - Print text
  mkdir <dir>     - Create directory
  touch <file>    - Create file
  rm <name>       - Remove file/directory
  find <pattern>  - Find files matching pattern
  grep <text>     - Search in files
  tree            - Show directory tree
  pacman          - Arch package manager
  flatpak         - Sandboxed application manager
  startde         - Start desktop environment (GNOME)
  neofetch        - System info
  screenfetch     - System info with ASCII art
  lsb_release     - Distribution info
  archey          - Arch Linux info display
  uname           - System information
  whoami          - Current user
  date            - Current date and time
  clear           - Clear screen
  help            - Show this help message
  exit            - Exit terminal"""
    
    # System information commands
    elif cmd == 'neofetch':
        return f'''  /\\\\
 /  \\ 
/    \\
\\    /
 \\  / 
  \\/

Arch Linux
Kernel: 6.0.12-arch1-1
Uptime: 2 days, 5 hours
Packages: {len(fs.installed_packages)}  
Flatpak Apps: {len(fs.installed_flatpaks)}
Shell: bash
CPU: Intel(R) Core(TM) i7-9700K
Memory: 12.5 GB / 16 GB
Disk: 256 GB / 512 GB'''
    
    elif cmd == 'screenfetch':
        return f'''         _,met=$$$$$gg.
      ,g$$$$$$$$$$$$$$$P.
    ,g$$P"     ""\"\"Y$$.".
   ,$$P\\'              `$$.
  \'d$\'     -=_       \\$$.
  $$P      d$$$       $$$.
  $$      d$$$P      $$$$.
  $$dg_ ,$$$$\'     .$$$$$.
  `Y$P\'  $$$$P      $$$$$.
   `$"   "$$P\"       Y$$$.
    g dg  "$$P"       Y$$.
   $P    "$$P\'        $$$. 

Arch Linux
Hostname: arch-linux
Kernel: 6.0.12-arch1-1 x86_64
Uptime: 2 days, 5 hours
Packages: {len(fs.installed_packages)}  
Flatpak: {len(fs.installed_flatpaks)}
Shell: bash 5.1.016
CPU: Intel i7-9700K
RAM: 12.5 GB / 16 GB
Disk: 256 GB / 512 GB'''
    
    elif cmd == 'lsb_release':
        return '''LSB Version: 1.4
Distributor ID: Arch
Description: Arch Linux
Release: rolling
Codename: rolling'''
    
    elif cmd == 'archey':
        return f'''               +                
               #                 
              ###                
             #####               
            #######              
           #########             
          ###########            
         #############           
        ###############          
       #################         
      ###################        
 n  ######Arch Linux######        
    ########kernel#########      
   ##########six-point######     
  ############zero##############

Arch Linux | Kernel: 6.0.12-arch1-1
Packages: {len(fs.installed_packages)} | Flatpak: {len(fs.installed_flatpaks)}
Shell: bash | RAM: 12.5 GB / 16 GB'''
    
    elif cmd == 'ls':
        path = args[0] if args else fs.current_dir
        path = fs.resolve_path(path)
        contents = fs.list_directory(path)
        if contents is None:
            return f"ls: cannot access '{path}': No such file or directory"
        
        if '-la' in ' '.join(args):
            output = "total 24\\n"
            output += f"drwxr-xr-x 2 user user 4096 Jul 21 10:00 .\\n"
            output += f"drwxr-xr-x 3 user user 4096 Jul 21 10:00 ..\\n"
            for name, item in contents.items():
                if item['type'] == 'directory':
                    output += f"drwxr-xr-x 2 user user 4096 Jul 21 10:00 {name}\\n"
                else:
                    content = item.get('content', '')
                    size = len(content.encode('utf-8'))
                    output += f"-rw-r--r-- 1 user user {size:>5} Jul 21 10:00 {name}\\n"
            return output.rstrip()
        else:
            return '  '.join(sorted(contents.keys())) if contents else ''
    
    elif cmd == 'cd':
        if not args:
            fs.current_dir = '/home/user'
            return ''
        new_dir = fs.resolve_path(args[0])
        node = fs.navigate_to_path(new_dir)
        if node is None:
            return f"cd: no such file or directory: {args[0]}"
        if node.get('type') != 'directory':
            return f"cd: not a directory: {args[0]}"
        fs.current_dir = new_dir
        return ''
    
    elif cmd == 'pwd':
        return fs.current_dir
    
    elif cmd == 'cat':
        if not args:
            return 'cat: missing operand'
        path = fs.resolve_path(args[0])
        content = fs.read_file(path)
        if content is None:
            return f"cat: {args[0]}: No such file or directory"
        return content
    
    elif cmd == 'echo':
        return ' '.join(args)
    
    elif cmd == 'mkdir':
        if not args:
            return 'mkdir: missing operand'
        if fs.create_directory(fs.current_dir, args[0]):
            return ''
        return f"mkdir: cannot create directory '{args[0]}'"
    
    elif cmd == 'touch':
        if not args:
            return 'touch: missing operand'
        if fs.create_file(fs.current_dir, args[0]):
            return ''
        return f"touch: cannot create file '{args[0]}'"
    
    elif cmd == 'rm':
        if not args:
            return 'rm: missing operand'
        if fs.delete_item(fs.current_dir, args[0]):
            return ''
        return f"rm: cannot remove '{args[0]}': No such file or directory"
    
    elif cmd == 'find':
        if not args:
            return 'find: missing pattern'
        pattern = args[0].lower()
        results = []
        
        def search_dir(path, node):
            if node.get('type') == 'directory':
                for name, item in node.get('contents', {}).items():
                    full_path = path + '/' + name if path else '/' + name
                    if pattern in name.lower():
                        results.append(full_path)
                    search_dir(full_path, item)
        
        search_dir('', fs.navigate_to_path(fs.current_dir))
        return '\\n'.join(results) if results else f'find: no matches for {pattern}'
    
    elif cmd == 'grep':
        if len(args) < 2:
            return 'grep: missing arguments'
        pattern = args[0]
        filepath = fs.resolve_path(args[1])
        content = fs.read_file(filepath)
        if content is None:
            return f"grep: {args[1]}: No such file or directory"
        
        matches = []
        for i, line in enumerate(content.split('\\n'), 1):
            if pattern in line:
                matches.append(f"{i}: {line}")
        return '\\n'.join(matches) if matches else ''
    
    elif cmd == 'head':
        if not args:
            return 'head: missing operand'
        path = fs.resolve_path(args[0])
        content = fs.read_file(path)
        if content is None:
            return f"head: {args[0]}: No such file or directory"
        lines = content.split('\\n')[:10]
        return '\\n'.join(lines)
    
    elif cmd == 'tail':
        if not args:
            return 'tail: missing operand'
        path = fs.resolve_path(args[0])
        content = fs.read_file(path)
        if content is None:
            return f"tail: {args[0]}: No such file or directory"
        lines = content.split('\\n')[-10:]
        return '\\n'.join(lines)
    
    elif cmd == 'tree':
        def build_tree(node, prefix='', is_last=True, depth=0, max_depth=3):
            if depth > max_depth:
                return ''
            
            output = ''
            if depth == 0:
                output = fs.current_dir + '\\n'
            
            if node.get('type') == 'directory':
                items = sorted(node.get('contents', {}).items())
                for i, (name, item) in enumerate(items):
                    is_last_item = i == len(items) - 1
                    current_prefix = '└── ' if is_last_item else '├── '
                    output += prefix + current_prefix + name
                    
                    if item['type'] == 'directory':
                        output += '/'
                        next_prefix = prefix + ('    ' if is_last_item else '│   ')
                        output += '\\n' + build_tree(item, next_prefix, is_last_item, depth + 1, max_depth)
                    else:
                        output += '\\n'
            
            return output
        
        node = fs.navigate_to_path(fs.current_dir)
        return build_tree(node).rstrip()
    
    elif cmd == 'uname':
        if '-a' in args:
            return 'Linux arch-linux 6.0.12-arch1-1 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux'
        return 'Linux'
    
    elif cmd == 'whoami':
        return 'user'
    
    elif cmd == 'date':
        return datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')
    
    elif cmd == 'clear':
        return '__CLEAR__'
    
    elif cmd == 'exit':
        return '__EXIT__'
    
    else:
        return f"{cmd}: command not found"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/execute', methods=['POST'])
def api_execute():
    data = request.json
    session_id = data.get('session_id', 'default')
    command = data.get('command', '')
    
    output = execute_command(session_id, command)
    
    session = sessions.get(session_id, {})
    fs = session.get('fs', FileSystem())
    
    return jsonify({
        'output': output,
        'cwd': fs.current_dir,
        'in_desktop': fs.in_desktop
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
