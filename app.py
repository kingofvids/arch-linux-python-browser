from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Virtual file system
VIRTUAL_FS = {
    '/': {
        'type': 'directory',
        'contents': {
            'home': {'type': 'directory', 'contents': {
                'user': {'type': 'directory', 'contents': {
                    'Desktop': {'type': 'directory', 'contents': {}},
                    'Documents': {'type': 'directory', 'contents': {}},
                    'README.txt': {'type': 'file', 'content': 'Welcome to Arch Linux Terminal!\nThis is a browser-based terminal emulator.'},
                    'archlinux.txt': {'type': 'file', 'content': 'Arch Linux is a lightweight and flexible Linux distribution.\nIt follows the KISS principle - Keep It Simple, Stupid.'}
                }}
            }},
            'etc': {'type': 'directory', 'contents': {
                'os-release': {'type': 'file', 'content': 'NAME="Arch Linux"\nID=arch\nID_LIKE=archlinux\nPRETTY_NAME="Arch Linux"\nVERSION="rolling"'}
            }},
            'bin': {'type': 'directory', 'contents': {}},
            'usr': {'type': 'directory', 'contents': {'bin': {'type': 'directory', 'contents': {}}}},
        }
    }
}

# Session state for each user
sessions = {}

class FileSystem:
    def __init__(self):
        self.fs = VIRTUAL_FS
        self.current_dir = '/'
    
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
    
    # Commands
    if cmd == 'help':
        return """Available commands:
  ls              - List directory contents
  cd <dir>        - Change directory
  pwd             - Print working directory
  cat <file>      - Display file contents
  echo <text>     - Print text
  mkdir <dir>     - Create directory
  touch <file>    - Create file
  rm <name>       - Remove file/directory
  uname           - System information
  whoami          - Current user
  date            - Current date and time
  clear           - Clear screen
  help            - Show this help message
  exit            - Exit terminal"""
    
    elif cmd == 'ls':
        path = args[0] if args else fs.current_dir
        path = fs.resolve_path(path)
        contents = fs.list_directory(path)
        if contents is None:
            return f"ls: cannot access '{path}': No such file or directory"
        
        if '-la' in ' '.join(args):
            output = "total 24\n"
            output += f"drwxr-xr-x 2 user user 4096 Jul 21 10:00 .\n"
            output += f"drwxr-xr-x 3 user user 4096 Jul 21 10:00 ..\n"
            for name, item in contents.items():
                if item['type'] == 'directory':
                    output += f"drwxr-xr-x 2 user user 4096 Jul 21 10:00 {name}\n"
                else:
                    output += f"-rw-r--r-- 1 user user  128 Jul 21 10:00 {name}\n"
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
    
    elif cmd == 'uname':
        if '-a' in args:
            return 'Linux arch-linux 5.18.0-arch1-1 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux'
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
        'cwd': fs.current_dir
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
