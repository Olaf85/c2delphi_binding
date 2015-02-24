import argparse
import os
import shutil
import subprocess
from os.path import *

_curdir = abspath(os.curdir)
BIN_PATH = normpath(_curdir + "/../gcc/bin")
INCLUDE_PATH = normpath(_curdir + "/../gcc/include")
PLATFORMS = ["arm", "arm64", "x86", "x64"]

def compile_file(args, dirname, fname, platform):
    print "compile " + join(dirname, fname) + " for %s" %platform
    name = fname[:fname.rfind(".")]
    cmd = normpath(BIN_PATH + "/" + platform + "/gcc.exe ")
    cmd += "-I%s -c -nostdinc -o%s.obj " %(INCLUDE_PATH, name)
    for i in args.I:
        cmd += "-I%s " %i
    if platform in ("x86", "x64"):
        cmd += "-msse " # SSE2?
    elif platform in ("arm"):
        cmd += "-mthumb-interwork "
    cmd += join(dirname, fname)

    PIPE = subprocess.PIPE
    p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,
        stderr=subprocess.STDOUT, env={"PATH": normpath(BIN_PATH + "/" + platform)})
    while True:
        s = p.stdout.readline()
        if not s: break
        print s,

    obj = join(_curdir, "%s.obj" %name)
    if platform == "x86":
        p = subprocess.Popen(normpath(_curdir + "/../coff2omf.exe ") + obj, shell=True,
            stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
        while True:
            s = p.stdout.readline()
            if not s: break
            print s,
        p = subprocess.Popen(normpath(_curdir + "/../omf2d.exe ") + obj, shell=True,
            stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)
        while True:
            s = p.stdout.readline()
            if not s: break
            print s,

    dir = normpath(args.t %platform)
    if not isdir(dir):
        os.makedirs(dir)
    if isfile(join(dir, "%s.obj" %name)):
        os.remove(join(dir, "%s.obj" %name))
    shutil.move(obj, dir)

def compile_dir(args, dirname, names):
    for name in names:
        if isfile(join(dirname, name)):
            if name.lower().endswith(".c") or name.lower().endswith(".cpp"):
                for platform in PLATFORMS:
                    compile_file(args, dirname, name, platform)
        

parser = argparse.ArgumentParser()
parser.add_argument("-s", required=True)
parser.add_argument("-p", required=True)
parser.add_argument("-t", required=True)
parser.add_argument("-I", action="append")
args = parser.parse_args()

fname = ""
if not isabs(args.s):
    args.s = normpath(_curdir + "/" + args.s)
if isfile(args.s):
    args.s, fname = split(args.s)
if not isabs(args.t):
    args.t = _curdir + "/" + args.t + "/%s/" + args.p
else:
    args.t += ("/%s/" + args.p)
I = []
if args.I:
    for i in args.I:
        if not isabs(i):
            i = normpath(_curdir + "/" + i)
        I.append(i)
args.I = I

if fname:
    if isfile(join(args.s, fname)):
        if name.lower().endswith(".c") or name.lower().endswith(".cpp"):
            for platform in PLATFORMS:
                compile_file(args, args.s, fname, platform)
else:
    walk(args.s, compile_dir, args)


