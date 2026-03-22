import os
import sys
import getpass
import bcrypt
import defs
from colorama import Fore, init
import argparse
parser = argparse.ArgumentParser(
    description="Only option is to factory reset."
)
parser.add_argument("--factoryreset", "-f", action="store_true", help="Delets the passwords,names and hostnames.")
args = parser.parse_args()
if args.factoryreset:
    os.remove("p.cfg")
    os.remove("h.cfg")
    os.remove("chk.cfg")
    os.remove("u.cfg")
    print("Restarting the app.")
    sys.exit(0)



init()


# Welcome To SwagOs
# 1. if you are running on windows, dont use cmd. some commands arent compatible,like rm and ls.
try:
    from playsound3 import playsound
except ImportError:
    print("Warning: playsound not installed. Audio will be disabled.")
    playsound = None

if defs.is_first_run():
    # Clear/Create files
    open("u.cfg", "w").close()
    open("h.cfg", "w").close()
    open("p.cfg", "w").close()

    input(Fore.BLUE + "Welcome to SwagOs! Learn about it:\n- Its an Complete TUI tool, with commands.\n- Its an multiplataform app, so you can use on linux, windows and even android!\n- Great for Windows users learn linux commands,without leaving the OS.\n(press any key to continue)")
    nm = input(Fore.LIGHTBLACK_EX + "Whats your name?\n> ")
    with open("u.cfg", "w") as f:
        f.write(nm)
    print(f"Welcome, {nm}!")

    while True:
        pswd = getpass.getpass(Fore.RED + "Insert Your Password! (Needs to be 8+ characters.)\n> ")
        if len(pswd) >= 8:
            break
        print(Fore.YELLOW + "Password must be at least 8 characters long.")

    bytz = pswd.encode("utf-8")
    hashed = bcrypt.hashpw(bytz, bcrypt.gensalt())
    with open("p.cfg", "wb") as f:
        f.write(hashed)
    hn = input("Whats is this computer called?\n(Tip: If you want,you can use names like 'LinuxWannabe', or even 'uwu'.)\n> ")
    with open("h.cfg", "w") as f:
        f.write(hn)
    print(Fore.GREEN + "Welcome to SwagOS!")

else:
    if not all(os.path.exists(f) for f in ["h.cfg", "u.cfg", "p.cfg"]):
        print(Fore.RED + "Error: Configuration files are missing. Please delete chk.cfg and restart.")
        sys.exit(1)

    with open("h.cfg", "r") as h_file:
        hn = h_file.read().strip()

    with open("u.cfg", "r") as u_file:
        nm = u_file.read().strip()

    with open("p.cfg", "rb") as p_file:
        pss = p_file.read().strip()

    while True:
        passwdtst = getpass.getpass("Whats your password?\n> ")
        if bcrypt.checkpw(passwdtst.encode("utf-8"), pss):
            print(Fore.GREEN + "Welcome to SwagOS.")
            break
        else:
            print(Fore.RED + "Incorrect password.")

while True:
    try:
        prompt = f"{nm}@{hn}> "
        terminal = input(Fore.YELLOW + prompt)
        defs.execute_command(terminal)
    except KeyboardInterrupt:
        print("\nUse 'exit' to quit.")
    except EOFError:
        sys.exit(0)
