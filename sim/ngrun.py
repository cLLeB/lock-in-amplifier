"""Run a SPICE file with the ngspice engine that ships inside KiCad (no separate install).

ngspice is started in PSpice-compatibility mode so that Microchip's MCP6021 model, which is
written for PSpice, loads without edits.

Usage (KiCad's Python):  python.exe ngrun.py file.cir "command" ["command" ...]
Each command is an ngspice command run after the simulation, e.g. "print v(out)".
"""
import ctypes
import os
import sys

BIN = os.path.dirname(sys.executable)
os.add_dll_directory(BIN)
ng = ctypes.CDLL(os.path.join(BIN, "ngspice.dll"))

SendChar = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
SendStat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
Exit = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
quiet = [False]


@SendChar
def on_char(msg, _id, _user):
    text = msg.decode("latin-1")
    if not quiet[0] or any(k in text for k in ("rror", "arning", "too small", "aborted")):
        print(text)
    return 0


@SendStat
def on_stat(_msg, _id, _user):
    return 0


@Exit
def on_exit(status, _unload, _quit, _id, _user):
    print("ngspice exit", status)
    return 0


def cmd(text):
    return ng.ngSpice_Command(text.encode())


if __name__ == "__main__":
    ng.ngSpice_Init(on_char, on_stat, on_exit, None, None, None, None)
    cmd("set ngbehavior=ps")
    cm = os.path.join(os.path.dirname(BIN), "lib", "ngspice")
    for name in ("spice2poly", "analog", "table", "xtradev"):
        cmd("codemodel " + os.path.join(cm, name + ".cm").replace("\\", "/"))
    quiet[0] = not os.environ.get("NGVERBOSE")
    cmd("source " + sys.argv[1].replace("\\", "/"))
    cmd("run")
    quiet[0] = False
    for c in sys.argv[2:]:
        cmd(c)
