import pygame
import os
import sys
import platform
from prompt import Prompt
from commands import run_command

if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

THEMES = {
    "default": {
        "bg": (10, 10, 10),
        "text": (192, 192, 192),
        "error": (255, 80, 80),
        "warning": (255, 165, 0),
        "dirlist": (120, 180, 255),
        "suggestion": (100, 100, 100),
    },
    "solarized": {
        "bg": (0, 43, 54),
        "text": (131, 148, 150),
        "error": (220, 50, 47),
        "warning": (181, 137, 0),
        "dirlist": (38, 139, 210),
        "suggestion": (147, 161, 161),
    },
    "dracula": {
        "bg": (40, 42, 54),
        "text": (248, 248, 242),
        "error": (255, 85, 85),
        "warning": (241, 250, 140),
        "dirlist": (139, 233, 253),
        "suggestion": (98, 114, 164),
    },
}

current_theme = THEMES["default"]


def get_completions(cwd, curr_input, commands_list):
    curr_input = curr_input.strip()
    completions = []
    for cmd in commands_list:
        if cmd.startswith(curr_input):
            completions.append(cmd)
    try:
        for f in os.listdir(cwd):
            if f.startswith(curr_input):
                if os.path.isdir(os.path.join(cwd, f)):
                    completions.append(f + "/")
                else:
                    completions.append(f)
    except Exception:
        pass
    return sorted(set(completions))


def main():
    global current_theme

    pygame.init()
    windowed_size = (800, 600)
    is_fullscreen = False
    win = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
    pygame.display.set_caption("Winux")

    try:
        icon = pygame.image.load("icon.png")
        pygame.display.set_icon(icon)
    except pygame.error:
        print("Warning: Could not load icon.png file. Make sure it exists in the script folder.")

    font = pygame.font.SysFont('Consolas', 16)

    commands_list = [
        "cd", "ls", "mkdir", "pwd", "rm", "cat", "touch", "echo", "clear",
        "help", "cp", "mv", "find", "grep", "head", "tail", "chmod", "chown",
        "ln", "ps", "kill", "top", "df", "du", "tar", "zip", "unzip",
        "ping", "wget", "curl", "hostname", "whoami", "date", "history",
        "exit", "env", "set", "theme"
    ]

    history = []

    release = platform.release()
    version = platform.version()
    windows_version_full = f"Windows {release} (Build {version})"

    intro_lines = [
        "",
        " ___       __   ___  ________   ___  ___     ___    ___ ",
        "|\\  \\     |\\  \\|\\  \\|\\   ___  \\|\\  \\|\\  \\   |\\  \\  /  /|",
        "\\ \\  \\    \\ \\  \\ \\  \\ \\  \\\\ \\  \\ \\  \\\\\\  \\  \\ \\  \\/  / /",
        " \\ \\  \\  __\\ \\  \\ \\  \\ \\  \\\\ \\  \\ \\  \\\\\\  \\  \\ \\    / / ",
        "  \\ \\  \\|\\__\\_\\  \\ \\  \\ \\  \\\\ \\  \\ \\  \\\\\\  \\  /     \\/  ",
        "   \\ \\____________\\ \\__\\ \\__\\\\ \\__\\ \\_______\\/  /\\   \\  ",
        "    \\|____________|\\|__|\\|__| \\|__|\\|_______/__/ /\\ __\\ ",
        "                                            |__|/ \\|__| ",
        "",                                               
        "",                                               
        "Welcome to Winux Terminal [v1.0.0]",
        f"Running on {windows_version_full}",
        "(c) 2025 Winux Team [DE0Dev, sheerbomb905]. Tux and Windows in harmony.",
        ""
    ]

    for line in intro_lines:
        history.append(("normal", line))

    curr_input = ""
    cwd = os.path.expanduser("~/Desktop")
    if not os.path.isdir(cwd):
        cwd = os.path.expanduser("~")

    prompt = Prompt(font, cwd)
    scroll_offset = 0
    command_history = []
    command_history_index = -1
    completions = []
    show_completions = False
    completion_index = 0
    running = True
    clock = pygame.time.Clock()

    while running:
        line_height = font.get_height() + 2
        win_size = win.get_size()
        max_visible_lines = win_size[1] // line_height - 3
        max_scroll = max(0, len(history) - max_visible_lines)
        scroll_offset = max(0, min(scroll_offset, max_scroll))
        start_line = max(0, len(history) - max_visible_lines - scroll_offset)
        visible_history = history[start_line:start_line + max_visible_lines]

        win.fill(current_theme["bg"])
        y = 0

        for typ, line in visible_history:
            if typ == "error":
                color = current_theme["error"]
            elif typ == "warning":
                color = current_theme["warning"]
            elif typ == "dirlist":
                color = current_theme["dirlist"]
            else:
                color = current_theme["text"]
            line_surf = font.render(line, True, color)
            win.blit(line_surf, (10, y))
            y += line_height

        prompt.set_path(cwd)
        prompt.update()
        prompt.render(win, 10, y, curr_input)
        y += line_height

        if show_completions and completions:
            max_suggestions = 5
            suggestion_color = current_theme["suggestion"]
            for i, sug in enumerate(completions[:max_suggestions]):
                prefix = ">> " if i == completion_index else "   "
                sug_text = prefix + sug
                sug_surf = font.render(sug_text, True, suggestion_color)
                win.blit(sug_surf, (10, y))
                y += line_height

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                flags = pygame.RESIZABLE
                if is_fullscreen:
                    flags |= pygame.FULLSCREEN
                win = pygame.display.set_mode((event.w, event.h), flags)

            elif event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * 3

            elif event.type == pygame.KEYDOWN:
                if show_completions:
                    if event.key == pygame.K_TAB:
                        if completions:
                            curr_input = completions[completion_index]
                            show_completions = False
                            completions = []
                            completion_index = 0
                    elif event.key == pygame.K_UP:
                        if completion_index > 0:
                            completion_index -= 1
                    elif event.key == pygame.K_DOWN:
                        if completion_index < len(completions) - 1:
                            completion_index += 1
                    elif event.key == pygame.K_ESCAPE:
                        show_completions = False
                    else:
                        show_completions = False
                else:
                    if event.key == pygame.K_RETURN:
                        if curr_input.strip():
                            command_history.append(curr_input)
                            command_history_index = -1
                            history.append(("normal", f"{cwd}> {curr_input}"))
                            cwd, output = run_command(cwd, curr_input)

                            if output == "__exit__":
                                running = False
                                break
                            elif isinstance(output, tuple) and len(output) == 2:
                                out_type, out_text = output
                                if out_type == "__clear__":
                                    history = []
                                elif out_type == "theme":
                                    current_theme = THEMES.get(out_text, THEMES["default"])
                                    history.append(("normal", f"Theme set to {out_text}"))
                                else:
                                    for line in out_text.split("\n"):
                                        history.append((out_type, line))
                            else:
                                for line in str(output).split("\n"):
                                    history.append(("normal", line))
                        curr_input = ""
                        scroll_offset = 0

                    elif event.key == pygame.K_BACKSPACE:
                        curr_input = curr_input[:-1]
                        command_history_index = -1

                    elif event.key == pygame.K_TAB:
                        completions = get_completions(cwd, curr_input, commands_list)
                        if completions:
                            show_completions = True
                            completion_index = 0
                        else:
                            show_completions = False

                    elif event.key == pygame.K_UP:
                        if command_history:
                            if command_history_index == -1:
                                command_history_index = len(command_history) - 1
                            else:
                                command_history_index = max(0, command_history_index - 1)
                            curr_input = command_history[command_history_index]

                    elif event.key == pygame.K_DOWN:
                        if command_history:
                            if command_history_index == -1:
                                pass
                            else:
                                command_history_index += 1
                                if command_history_index >= len(command_history):
                                    command_history_index = -1
                                    curr_input = ""
                                else:
                                    curr_input = command_history[command_history_index]

                    elif event.key == pygame.K_F11:
                        is_fullscreen = not is_fullscreen
                        if is_fullscreen:
                            win = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
                        else:
                            win = pygame.display.set_mode(windowed_size, pygame.RESIZABLE)
                        scroll_offset = 0

                    else:
                        if event.unicode and event.unicode.isprintable():
                            curr_input += event.unicode
                            command_history_index = -1

        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
