import os
import shutil
import platform
import fnmatch
import subprocess
import sys
import getpass
import datetime
import socket
import tarfile
import zipfile
import collections

try:
    import psutil
except ImportError:
    psutil = None

COMMAND_HISTORY = []


def run_command(cwd, cmd):
    """
    Handle Linux-style shell commands.
    Returns updated cwd and output tuple (type, text).
    """
    stripped_cmd = cmd.strip()

    if stripped_cmd and not stripped_cmd.startswith("history"):
        COMMAND_HISTORY.append(stripped_cmd)

    parts = stripped_cmd.split()

    if not parts:
        return cwd, ("normal", "")

    command = parts[0].lower()

    if command == "cd":
        if len(parts) == 1:
            target = os.path.expanduser("~")
        else:
            target = parts[1]

        if target.startswith("~"):
            target = os.path.expanduser(target)
        elif not os.path.isabs(target):
            target = os.path.join(cwd, target)

        if os.path.isdir(target):
            cwd = os.path.abspath(target)
            return cwd, ("normal", f"Changed directory to {cwd}")
        else:
            return cwd, ("error", f"No such directory: {target}")

    elif command == "ls":
        try:
            items = os.listdir(cwd)
            
            return cwd, ("dirlist", "\n".join(items))
        except Exception as e:
            return cwd, ("error", f"Error listing directory: {str(e)}")

    elif command == "mkdir":
        if len(parts) < 2:
            return cwd, ("error", "Usage: mkdir <foldername>")
        folder_name = parts[1]
        path = os.path.join(cwd, folder_name)
        try:
            os.mkdir(path)
            return cwd, ("normal", f"Folder '{folder_name}' created.")
        except Exception as e:
            return cwd, ("error", f"Error creating folder: {str(e)}")

    elif command == "pwd":
        return cwd, ("normal", cwd)

    elif command == "rm":
        if len(parts) < 2:
            return cwd, ("error", "Usage: rm <file_or_folder>")
        target = os.path.join(cwd, parts[1])
        if not os.path.exists(target):
            return cwd, ("error", f"No such file or directory: {target}")
        try:
            if os.path.isdir(target):
                shutil.rmtree(target)
                return cwd, ("normal", f"Directory '{parts[1]}' removed.")
            else:
                os.remove(target)
                return cwd, ("normal", f"File '{parts[1]}' removed.")
        except Exception as e:
            return cwd, ("error", f"Error removing target: {str(e)}")

    elif command == "cat":
        if len(parts) < 2:
            return cwd, ("error", "Usage: cat <filename>")
        target = os.path.join(cwd, parts[1])
        if not os.path.isfile(target):
            return cwd, ("error", f"No such file: {target}")
        try:
            with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            return cwd, ("normal", content)
        except Exception as e:
            return cwd, ("error", f"Error reading file: {str(e)}")

    elif command == "touch":
        if len(parts) < 2:
            return cwd, ("error", "Usage: touch <filename>")
        target = os.path.join(cwd, parts[1])
        try:
            with open(target, 'a'):
                os.utime(target, None)
            return cwd, ("normal", f"Touched file: {parts[1]}")
        except Exception as e:
            return cwd, ("error", f"Error touching file: {str(e)}")

    elif command == "echo":
        return cwd, ("normal", " ".join(parts[1:]))

    elif command == "clear":
        return cwd, ("__clear__", "")

    elif command == "help":
        help_text = (
            "Available commands:\n"
            "cd [dir] - change directory\n"
            "ls - list directory contents\n"
            "mkdir - create directory\n"
            "pwd - print working directory\n"
            "rm - remove file or directory\n"
            "cat - print file content\n"
            "touch - create empty file or update timestamp\n"
            "echo - print provided text\n"
            "clear - clear the screen\n"
            "help - this help message\n"
            "cp - copy files or folders\n"
            "mv - move/rename files or folders\n"
            "find - search files by name\n"
            "grep - search text in files\n"
            "head [lines] - show first lines\n"
            "tail [lines] - show last lines\n"
            "chmod - change permissions (simulated)\n"
            "chown - change owner (simulated)\n"
            "ln -s - create symbolic link\n"
            "ps - list running processes\n"
            "kill - terminate process by PID\n"
            "top - show simplified process list\n"
            "df - show disk usage summary\n"
            "du - disk usage of directory\n"
            "tar -cf - create tar archive\n"
            "tar -xf - extract tar archive\n"
            "zip - create zip archive\n"
            "unzip - extract zip archive\n"
            "ping - ping host\n"
            "wget - download file\n"
            "curl - download / transfer data\n"
            "hostname - show system hostname\n"
            "whoami - show current user\n"
            "date - show current date/time\n"
            "history - show command history\n"
            "exit - exit shell\n"
            "env - show environment variables\n"
            "set - set environment variable\n"
            "theme [default|solarized|dracula] - change color theme\n"
            "Running script files by name with extension supported if present in directory."
        )
        return cwd, ("normal", help_text)

    elif command == "theme":
        # Just validate and return the theme name; winux.py will apply it
        if len(parts) != 2:
            return cwd, ("normal", "Usage: theme [default|solarized|dracula]")
        name = parts[1].lower()
        if name not in ("default", "solarized", "dracula"):
            return cwd, ("error", f"Unknown theme '{name}'.")
        return cwd, ("theme", name)

    elif command == "cp":
        if len(parts) < 3:
            return cwd, ("error", "Usage: cp <source> <destination>")
        src = parts[1]
        dst = parts[2]
        src_abs = src if os.path.isabs(src) else os.path.join(cwd, src)
        dst_abs = dst if os.path.isabs(dst) else os.path.join(cwd, dst)
        if os.path.isdir(src_abs):
            try:
                shutil.copytree(src_abs, dst_abs)
                return cwd, ("normal", f"Directory copied from '{src}' to '{dst}'")
            except Exception as e:
                return cwd, ("error", f"Error copying directory: {str(e)}")
        elif os.path.isfile(src_abs):
            try:
                shutil.copy2(src_abs, dst_abs)
                return cwd, ("normal", f"File copied from '{src}' to '{dst}'")
            except Exception as e:
                return cwd, ("error", f"Error copying file: {str(e)}")
        else:
            return cwd, ("error", f"Source does not exist: {src}")

    elif command == "mv":
        if len(parts) < 3:
            return cwd, ("error", "Usage: mv <source> <destination>")
        src = parts[1]
        dst = parts[2]
        src_abs = src if os.path.isabs(src) else os.path.join(cwd, src)
        dst_abs = dst if os.path.isabs(dst) else os.path.join(cwd, dst)
        try:
            shutil.move(src_abs, dst_abs)
            return cwd, ("normal", f"Moved '{src}' to '{dst}'")
        except Exception as e:
            return cwd, ("error", f"Error moving file/folder: {str(e)}")

    elif command == "find":
        if len(parts) < 2:
            return cwd, ("error", "Usage: find <pattern>")
        pattern = parts[1]
        matches = []
        for root, dirs, files in os.walk(cwd):
            for name in files + dirs:
                if fnmatch.fnmatch(name, pattern):
                    full_path = os.path.relpath(os.path.join(root, name), cwd)
                    matches.append(full_path)
        if matches:
            return cwd, ("normal", "\n".join(matches))
        else:
            return cwd, ("normal", "No matches found.")

    elif command == "grep":
        if len(parts) < 3:
            return cwd, ("error", "Usage: grep <pattern> <files...>")
        pattern = parts[1]
        files = parts[2:]
        matches = []
        for filename in files:
            file_path = filename if os.path.isabs(filename) else os.path.join(cwd, filename)
            if not os.path.isfile(file_path):
                matches.append(f"File not found: {filename}")
                continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for lineno, line in enumerate(f, 1):
                        if pattern in line:
                            matches.append(f"{filename}:{lineno}:{line.rstrip()}")
            except Exception as e:
                matches.append(f"Error reading {filename}: {str(e)}")
        if matches:
            return cwd, ("normal", "\n".join(matches))
        else:
            return cwd, ("normal", "No matches found.")

    elif command == "head":
        if len(parts) < 2:
            return cwd, ("error", "Usage: head <filename> [lines]")
        filename = parts[1]
        lines_count = 10
        if len(parts) >= 3:
            try:
                lines_count = int(parts[2])
            except ValueError:
                return cwd, ("error", "Lines argument must be an integer.")
        file_path = filename if os.path.isabs(filename) else os.path.join(cwd, filename)
        if not os.path.isfile(file_path):
            return cwd, ("error", f"No such file: {filename}")
        try:
            output_lines = []
            with open(file_path, "r", encoding="utf-8") as f:
                for _ in range(lines_count):
                    line = f.readline()
                    if line == '':
                        break
                    output_lines.append(line.rstrip())
            return cwd, ("normal", "\n".join(output_lines))
        except Exception as e:
            return cwd, ("error", f"Error reading file: {str(e)}")

    elif command == "tail":
        if len(parts) < 2:
            return cwd, ("error", "Usage: tail <filename> [lines]")
        filename = parts[1]
        lines_count = 10
        if len(parts) >= 3:
            try:
                lines_count = int(parts[2])
            except ValueError:
                return cwd, ("error", "Lines argument must be an integer.")
        file_path = filename if os.path.isabs(filename) else os.path.join(cwd, filename)
        if not os.path.isfile(file_path):
            return cwd, ("error", f"No such file: {filename}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                deq = collections.deque(f, maxlen=lines_count)
            return cwd, ("normal", "".join(deq))
        except Exception as e:
            return cwd, ("error", f"Error reading file: {str(e)}")

    elif command == "chmod":
        if len(parts) < 3:
            return cwd, ("error", "Usage: chmod <mode> <file>")
        
        return cwd, ("warning", "chmod is not supported on Windows in this shell. No action taken.")

    elif command == "chown":
        if len(parts) < 3:
            return cwd, ("error", "Usage: chown <owner> <file>")
        
        return cwd, ("warning", "chown is not supported on Windows in this shell. No action taken.")

    elif command == "ln":
        
        if len(parts) < 4 or parts[1] != "-s":
            return cwd, ("error", "Usage: ln -s <target> <linkname>")
        target = parts[2]
        linkname = parts[3]
        target_path = target if os.path.isabs(target) else os.path.join(cwd, target)
        link_path = linkname if os.path.isabs(linkname) else os.path.join(cwd, linkname)
        try:
            os.symlink(target_path, link_path)
            return cwd, ("normal", f"Symbolic link created from '{linkname}' to '{target}'")
        except Exception as e:
            return cwd, ("error", f"Error creating symlink: {str(e)}")

    elif command == "ps":
        if psutil is None:
            try:
                proc = subprocess.run(["tasklist"], capture_output=True, text=True)
                return cwd, ("normal", proc.stdout)
            except Exception as e:
                return cwd, ("error", f"Error retrieving process list: {str(e)}")
        else:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'username']):
                procs.append(f"{p.info['pid']:>6} {p.info['name'][:25]:25} {p.info['username']}")
            return cwd, ("normal", "\n".join(procs))

    elif command == "kill":
        if len(parts) < 2:
            return cwd, ("error", "Usage: kill <pid>")
        try:
            pid = int(parts[1])
            if psutil:
                p = psutil.Process(pid)
                p.terminate()
                return cwd, ("normal", f"Process {pid} terminated.")
            else:
                os.kill(pid, 15)
                return cwd, ("normal", f"Kill signal sent to process {pid}.")
        except Exception as e:
            return cwd, ("error", f"Error killing process: {str(e)}")

    elif command == "top":
        if psutil is None:
            return cwd, ("error", "psutil module not installed; top command unavailable.")
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                procs.append((p.info['cpu_percent'], p.info['pid'], p.info['name']))
            except psutil.NoSuchProcess:
                continue
        procs.sort(reverse=True)
        output_lines = ["  CPU%   PID NAME"]
        for cpu, pid, name in procs[:10]:
            output_lines.append(f"{cpu:6.1f} {pid:6} {name}")
        return cwd, ("normal", "\n".join(output_lines))

    elif command == "df":
        try:
            if hasattr(os, "statvfs"):
                stat = os.statvfs(cwd)
                total = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
                free = (stat.f_bfree * stat.f_frsize) / (1024 * 1024)
                used = total - free
                return cwd, ("normal", f"Filesystem: {cwd}\nTotal: {total:.2f} MB\nUsed: {used:.2f} MB\nFree: {free:.2f} MB")
            else:
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)
                free_bytes_available = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(cwd),
                    ctypes.byref(free_bytes_available),
                    ctypes.byref(total_bytes),
                    ctypes.byref(free_bytes),
                )
                MB = 1024 * 1024
                return cwd, ("normal", f"Filesystem: {cwd}\nTotal: {total_bytes.value/MB:.2f} MB\nUsed: {(total_bytes.value - free_bytes.value)/MB:.2f} MB\nFree: {free_bytes.value/MB:.2f} MB")
        except Exception as e:
            return cwd, ("error", f"Error getting disk info: {str(e)}")

    elif command == "du":
        if len(parts) < 2:
            path_to_check = cwd
        else:
            path_to_check = parts[1]
        if not os.path.isabs(path_to_check):
            path_to_check = os.path.join(cwd, path_to_check)
        if not os.path.exists(path_to_check):
            return cwd, ("error", f"No such file or directory: {path_to_check}")
        total_size = 0
        try:
            if os.path.isfile(path_to_check):
                total_size = os.path.getsize(path_to_check)
            else:
                for dirpath, dirnames, filenames in os.walk(path_to_check):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total_size += os.path.getsize(fp)
            return cwd, ("normal", f"{total_size / 1024:.2f} KB")
        except Exception as e:
            return cwd, ("error", f"Error calculating disk usage: {str(e)}")

    elif command == "tar":
        if len(parts) < 3:
            return cwd, ("error", "Usage: tar -cf (create)\n"
                                   "or: tar -xf (extract)")
        option = parts[1]
        if option == "-cf":
            archive_name = parts[2]
            files = parts[3:]
            archive_path = archive_name if os.path.isabs(archive_name) else os.path.join(cwd, archive_name)
            try:
                with tarfile.open(archive_path, "w") as tarf:
                    for f in files:
                        f_path = f if os.path.isabs(f) else os.path.join(cwd, f)
                        tarf.add(f_path, arcname=os.path.basename(f_path))
                return cwd, ("normal", f"Created tar archive {archive_name}")
            except Exception as e:
                return cwd, ("error", f"Error creating tar archive: {str(e)}")
        elif option == "-xf":
            archive_name = parts[2]
            archive_path = archive_name if os.path.isabs(archive_name) else os.path.join(cwd, archive_name)
            try:
                with tarfile.open(archive_path, "r") as tarf:
                    tarf.extractall(cwd)
                return cwd, ("normal", f"Extracted tar archive {archive_name}")
            except Exception as e:
                return cwd, ("error", f"Error extracting tar archive: {str(e)}")
        else:
            return cwd, ("error", "Unsupported tar option, use -cf or -xf")

    elif command == "zip":
        if len(parts) < 3:
            return cwd, ("error", "Usage: zip <archive.zip> <files...>")
        archive_name = parts[1]
        files = parts[2:]
        archive_path = archive_name if os.path.isabs(archive_name) else os.path.join(cwd, archive_name)
        try:
            with zipfile.ZipFile(archive_path, 'w') as z:
                for f in files:
                    f_path = f if os.path.isabs(f) else os.path.join(cwd, f)
                    if os.path.exists(f_path):
                        z.write(f_path, arcname=os.path.basename(f_path))
            return cwd, ("normal", f"Created zip archive {archive_name}")
        except Exception as e:
            return cwd, ("error", f"Error creating zip archive: {str(e)}")

    elif command == "unzip":
        if len(parts) < 2:
            return cwd, ("error", "Usage: unzip <archive.zip>")
        archive_name = parts[1]
        archive_path = archive_name if os.path.isabs(archive_name) else os.path.join(cwd, archive_name)
        try:
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(cwd)
            return cwd, ("normal", f"Extracted zip archive {archive_name}")
        except Exception as e:
            return cwd, ("error", f"Error extracting zip archive: {str(e)}")

    elif command == "ping":
        if len(parts) < 2:
            return cwd, ("error", "Usage: ping <host>")
        host = parts[1]
        try:
            count_flag = "-n" if platform.system().lower() == "windows" else "-c"
            ping_proc = subprocess.run(["ping", count_flag, "4", host], capture_output=True, text=True)
            return cwd, ("normal", ping_proc.stdout)
        except Exception as e:
            return cwd, ("error", f"Error pinging host: {str(e)}")

    elif command == "wget":
        if len(parts) < 2:
            return cwd, ("error", "Usage: wget <url>")
        url = parts[1]
        try:
            import requests
        except ImportError:
            return cwd, ("error", "requests module not installed; wget unavailable")
        filename = url.split('/')[-1] or "downloaded_file"
        filepath = os.path.join(cwd, filename)
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return cwd, ("normal", f"Downloaded {filename}")
        except Exception as e:
            return cwd, ("error", f"Error downloading file: {str(e)}")

    elif command == "curl":
        if len(parts) < 2:
            return cwd, ("error", "Usage: curl <url>")
        url = parts[1]
        try:
            import requests
        except ImportError:
            return cwd, ("error", "requests module not installed; curl unavailable")
        try:
            r = requests.get(url)
            r.raise_for_status()
            return cwd, ("normal", r.text)
        except Exception as e:
            return cwd, ("error", f"Error fetching URL: {str(e)}")

    elif command == "hostname":
        return cwd, ("normal", platform.node())

    elif command == "whoami":
        try:
            return cwd, ("normal", getpass.getuser())
        except Exception:
            try:
                return cwd, ("normal", os.getlogin())
            except Exception:
                return cwd, ("error", "Unable to get current user")

    elif command == "date":
        now = datetime.datetime.now()
        return cwd, ("normal", now.strftime("%a %b %d %H:%M:%S %Y"))

    elif command == "history":
        if COMMAND_HISTORY:
            numbered = [f"{i+1} {c}" for i, c in enumerate(COMMAND_HISTORY)]
            return cwd, ("normal", "\n".join(numbered))
        else:
            return cwd, ("normal", "No commands in history.")

    elif command == "exit":
        return cwd, "__exit__"

    elif command == "env":
        env_vars = [f"{k}={v}" for k, v in os.environ.items()]
        return cwd, ("normal", "\n".join(env_vars))

    elif command == "set":
        if len(parts) < 2 or '=' not in parts[1]:
            return cwd, ("error", "Usage: set VAR=VALUE")
        key_value = parts[1].split('=', 1)
        if len(key_value) != 2:
            return cwd, ("error", "Usage: set VAR=VALUE")
        key, value = key_value
        os.environ[key] = value
        return cwd, ("normal", f"Set {key}={value}")

    # --- SCRIPT EXECUTION if no other command matched ---
    script_exts = ['.py', '.sh', '.wnx']
    script_path = os.path.join(cwd, stripped_cmd)
    if os.path.isfile(script_path) and any(stripped_cmd.endswith(ext) for ext in script_exts):
        output_lines = []
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    cwd, output = run_command(cwd, line)
                    if isinstance(output, tuple) and len(output) == 2:
                        out_type, out_text = output
                    else:
                        out_type, out_text = "normal", str(output)
                    if out_text:
                        output_lines.append(f"> {line}")
                        output_lines.append(out_text)
            final_output = "\n".join(output_lines)
            return cwd, ("normal", final_output)
        except Exception as e:
            return cwd, ("error", f"Error running script {stripped_cmd}: {str(e)}")

    return cwd, ("error", f"Command not found: {command}")

