"""Run lockin_tran_ng.cir (Microchip MCP6021 model) for a list of cases and print the results.

Usage (KiCad's Python):
  python.exe ngrun_lockin.py                 the three signal levels
  python.exe ngrun_lockin.py name "Ipk=10n Vos3=0.5m" [tstop [tmax]]     one named case
tmax is the largest time step (default 20u). If a run stops with "timestep too small", a slightly
different tmax (for example 15u) usually gets it through.
Each case is run in a fresh ngspice process, and the results are appended to lockin_tran_ng.log.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = [("0 nA", "Ipk=0"), ("10 nA", "Ipk=10n"), ("100 nA", "Ipk=100n")]


def run_case(name, params, tstop=3.0, tmax="20u"):
    text = open(os.path.join(HERE, "lockin_tran_ng.cir")).read()
    for key, val in (p.split("=") for p in params.split()):
        text, n = re.subn(r"(?<![\w])%s=[^\s]+" % key, "%s=%s" % (key, val), text, count=1)
        if not n:
            raise SystemExit("no parameter " + key)
    text = text.replace(".tran 20u 3 0 20u", ".tran 20u %g 0 %s" % (tstop, tmax))
    tmp = os.path.join(HERE, "_ng_case_%d.cir" % os.getpid())
    open(tmp, "w").write(text)
    a, b = tstop - 0.5, tstop
    cmds = ["let d = v(out)-v(vref)",
            "meas tran vout_dc avg d from=%g to=%g" % (a, b),
            "meas tran vout_rip pp d from=%g to=%g" % (a, b),
            "meas tran tia_max max v(tia) from=%g to=%g" % (a, b),
            "meas tran ac_max max v(ac) from=%g to=%g" % (a, b),
            "meas tran ac_min min v(ac) from=%g to=%g" % (a, b)]
    res = subprocess.run([sys.executable, os.path.join(HERE, "ngrun.py"), tmp] + cmds,
                         capture_output=True, text=True, cwd=HERE)
    os.remove(tmp)
    got = dict(re.findall(r"(vout_dc|vout_rip|tia_max|ac_max|ac_min)\s*=\s*([-+.\deE]+)", res.stdout))
    errors = [l for l in (res.stdout + res.stderr).splitlines() if any(k in l for k in ("rror", "too small", "aborted"))]
    line = "%-28s %-28s " % (name, params) + "  ".join("%s=%s" % kv for kv in got.items())
    if errors or not got:
        line += "  FAILED: " + " | ".join(errors[:3])
    print(line, flush=True)
    with open(os.path.join(HERE, "lockin_tran_ng.log"), "a") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        run_case(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 3.0,
                 sys.argv[4] if len(sys.argv) > 4 else "20u")
    else:
        for name, params in CASES:
            run_case(name, params)
