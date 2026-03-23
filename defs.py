import os
import time, sys, platform, threading, bcrypt, getpass, subprocess
import subprocess as sub
from playsound3 import playsound # (not implemented yet)
from colorama import init, Fore
from random import randint as rand
init()




defaltcfgfl = "chk.cfg"
enabled_apps = set()

def is_first_run():
    if not os.path.exists(defaltcfgfl):
        # This is the first run
        with open(defaltcfgfl, "w") as f:
            f.write(
                "If you are reading this, you should listen to my music. https://cemj.shop."
            )
        return True
    else:
        # Not the first run
        return False


def run_subprocess(shell_cmd):
    try:
        # prefer shell=False style when possible; allow shell-like string for convenience
        if platform.system() == "Windows":
            completed = sub.run(
                ["powershell", "-Command", shell_cmd], capture_output=True, text=True
            )
        else:
            completed = sub.run(shell_cmd, shell=True, capture_output=True, text=True)
        if completed.returncode == 0:
            print(completed.stdout.strip())
        else:
            print("Command returned nonzero status.")
            print(completed.stderr.strip())
        return completed.returncode
    except Exception as e:
        print("Error running command:", e)
        return -1


def execute_command(command):
    command = command.strip()
    if not command:
        return
    elif command.lower() == "exit":
        sys.exit()
    elif command == "cp":
        f1l = input("who to copy?\n> ")
        f2l = input("where to copy?\n> ")
        run_subprocess(f"cp {f1l} {f2l}")
    elif command == "rm":
        f1l = input("who to remove?\n> ")
        run_subprocess(f"rm {f1l}")
    elif command == "ls":
        run_subprocess("ls")
    elif command == "cat":
        f1l = input("who to cat?\n> ")
        run_subprocess(f"cat {f1l}")
    elif command == "pwd":
        run_subprocess("pwd")
    elif command == "clear":
        os.system("clear")
    elif command == "help":
        print(
            """
Available commands:
- cp: Copy a file
- rm: Remove a file
- ls: List files
- cat: Display file content
- pwd: Print working directory
- clear: Clear the screen
- exit: Exit the shell
- help: Show this help message(additional help with --os, --security and --code
- whoami: who am i?
- lsblk: List block devices (doesn't run on windows)
- mkdir: Create a directory
- touch: Create a file
- mv: Move/Rename a file
- echo: Print text
- appstore: Browse and install apps
- randomgame: Guessing game
            """
        )
    elif command == "lsblk":
        run_subprocess("lsblk")
    elif command == "whoami":
        print(getpass.getuser())
    elif command == "mkdir":
        d1r = input("directory name?\n> ")
        run_subprocess(f"mkdir {d1r}")
    elif command == "touch":
        f1l = input("file name?\n> ")
        try:
            with open(f1l, "a"):
                os.utime(f1l, None)
        except Exception as e:
            print(f"Error touching file: {e}")
    elif command == "mv":
        f1l = input("source?\n> ")
        f2l = input("destination?\n> ")
        run_subprocess(f"mv {f1l} {f2l}")
    elif command == "echo":
        txt = input("text to echo?\n> ")
        print(txt)
    elif command == "appstore":
        print("--- SwagOs App Store ---")
        print(f"1. neofetch ({'enabled' if 'neofetch' in enabled_apps else 'disabled'})")
        print(f"2. vim ({'enabled' if 'vim' in enabled_apps else 'disabled'})")
        choice = input("Enter app name to enable/install: ")
        if choice in ["neofetch", "vim"]:
            if choice in enabled_apps:
                print(f"{choice} is already enabled.")
            else:
                print(f"Installing {choice}...")
                time.sleep(1)
                enabled_apps.add(choice)
                print(f"{choice} is now enabled.")
        else:
            print("App not found.")
    elif command == "vim":
        if "vim" in enabled_apps:
            fn = input("File to edit?\n> ").strip()
            print(f"Editing {fn}. Type ':wq' on a new line to save and exit.")
            lines = []
            while True:
                line = input().rstrip('\r')
                if line.strip() == ":wq":
                    break
                lines.append(line)
            with open(fn, "w") as f:
                f.write("\n".join(lines))
            print(f"Saved {fn}")
        else:
            print("vim isnt enabled, please install it on appstore.")
    elif command == "help --os":
        print(Fore.GREEN + "In the SwagOS TUI, You can use commands from your own host OS!\nEx: ls = runs on your own os\nvim: runs the vim from SwagOS.")
    elif command == "help --security":
        print(Fore.BLUE + "In SwagOS, we take your password very seriously. The password is encrypted with bcrypt and only decrypted with the original password + the hash.")
        #idfk what to write, what a dumb idea of mine
    elif command == ":)":
        print(":D")
    elif command == "randomgame":
        return
        #finish tmrrw
    else:
        run_subprocess(command)
