import os, subprocess, sys

MSVC = r"D:\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.44.35207"
ATLMFC = os.path.join(MSVC, "atlmfc")
SDK = r"D:\Windows Kits\10"
BIN = os.path.join(MSVC, "bin", "Hostx64", "x64")
CL = os.path.join(BIN, "cl.exe")
LINK = os.path.join(BIN, "link.exe")
RC = os.path.join(SDK, "bin", "10.0.26100.0", "x64", "rc.exe")
PROJ = r"E:\code\TrafficMonitorPlugins_TMP-WeatherPro"
WP = os.path.join(PROJ, "WeatherPro")

config = sys.argv[1] if len(sys.argv) > 1 else "Release"
debug = (config == "Debug")

inc = [
    os.path.join(ATLMFC, "include"),
    os.path.join(MSVC, "include"),
    os.path.join(SDK, "Include", "10.0.26100.0", "ucrt"),
    os.path.join(SDK, "Include", "10.0.26100.0", "shared"),
    os.path.join(SDK, "Include", "10.0.26100.0", "um"),
    os.path.join(SDK, "Include", "10.0.26100.0", "cppwinrt"),
    PROJ,
    os.path.join(PROJ, "dependencies"),
    WP,
]
libdirs = [
    os.path.join(ATLMFC, "lib", "x64"),
    os.path.join(MSVC, "lib", "x64"),
    os.path.join(SDK, "Lib", "10.0.26100.0", "ucrt", "x64"),
    os.path.join(SDK, "Lib", "10.0.26100.0", "um", "x64"),
    os.path.join(PROJ, "lib", "x64", config),
]

env = os.environ.copy()
env["INCLUDE"] = ";".join(inc)
env["LIB"] = ";".join(libdirs)
env["PATH"] = BIN + ";" + env.get("PATH", "")

sources = [
    "pch.cpp",  # 先编译以创建 PCH
    "ApiCollections.cpp",
    "AutoLocSettingsDlg.cpp",
    "Common.cpp",
    "DataManager.cpp",
    "EditCtrlFloatNumber.cpp",
    "IconResources.cpp",
    "MainItem.cpp",
    "MainSettingsDlg.cpp",
    "ModalProgressDlg.cpp",
    "OptionsOwDlg.cpp",
    "OptionsQwDlg.cpp",
    "OptionsWccDlg.cpp",
    "PinnedItem.cpp",
    "PinnedItemSettingsDlg.cpp",
    "SetLocationDlg.cpp",
    "TextViewerDlg.cpp",
    "WeatherApiOpenWeather.cpp",
    "WeatherApiQWeather.cpp",
    "WeatherApiWCCS.cpp",
    "WeatherPro.cpp",
]

outdir = os.path.join(PROJ, "x64", config)
objdir = os.path.join(WP, "obj", "x64", config)
os.makedirs(outdir, exist_ok=True)
os.makedirs(objdir, exist_ok=True)
pch = os.path.join(objdir, "WeatherPro.pch")

common_defines = ["_WINDOWS", "_USRDLL", "_WINDLL", "_AFXDLL",
                 "_UNICODE", "UNICODE", "NOMINMAX", "WIN32_LEAN_AND_MEAN"]

if debug:
    cflags = ["/nologo", "/c", "/MDd", "/Zi", "/Od", "/RTC1", "/EHsc",
              "/std:c++20", "/utf-8", "/permissive-", "/W3", "/Gm-"]
    defines = common_defines + ["_DEBUG", "_DEBUG"]
    ldflags = ["/nologo", "/DLL", "/MACHINE:X64", "/SUBSYSTEM:WINDOWS",
               "/DEBUG", f"/PDB:{os.path.join(outdir, 'WeatherPro.pdb')}"]
    rcdefs = ["_DEBUG", "_UNICODE", "UNICODE"]
else:
    cflags = ["/nologo", "/c", "/MD", "/O2", "/Oi", "/Gy", "/Gm-", "/EHsc",
              "/std:c++20", "/utf-8", "/permissive-", "/W3", "/sdl"]
    defines = common_defines + ["NDEBUG"]
    ldflags = ["/nologo", "/DLL", "/MACHINE:X64", "/SUBSYSTEM:WINDOWS",
               "/OPT:REF", "/OPT:ICF"]
    rcdefs = ["NDEBUG", "_UNICODE", "UNICODE"]

def build_defines(ds):
    return [f"/D{d}" for d in ds]

objs = []
for s in sources:
    obj = os.path.join(objdir, os.path.splitext(s)[0] + ".obj")
    objs.append(obj)
    if os.path.exists(obj):
        os.remove(obj)
    if s == "pch.cpp":
        ych = [f'/Ycpch.h', f"/Fp{pch}"]
    else:
        ych = [f'/Yupch.h', f"/Fp{pch}"]
    cmd = [CL] + cflags + ych + build_defines(defines) + [f"/Fo{obj}", s]
    print(">> compiling", s)
    r = subprocess.run(cmd, env=env, cwd=WP)
    if r.returncode != 0:
        print("FAILED:", s)
        sys.exit(1)

# 资源编译
res = os.path.join(objdir, "WeatherPro.res")
rc_inc = ["/i" + p for p in [WP, os.path.join(ATLMFC, "include"),
                             os.path.join(SDK, "Include", "10.0.26100.0", "shared"),
                             os.path.join(SDK, "Include", "10.0.26100.0", "um"),
                             os.path.join(SDK, "Include", "10.0.26100.0", "ucrt")]]
rc_cmd = [RC, "/nologo", "/l0x804"] + [f"/d{d}" for d in rcdefs] + rc_inc + \
         [f"/fo{res}", "WeatherPro.rc"]
print(">> compiling WeatherPro.rc")
r = subprocess.run(rc_cmd, env=env, cwd=WP)
if r.returncode != 0:
    print("FAILED: WeatherPro.rc")
    sys.exit(1)

# 链接
dll = os.path.join(outdir, "WeatherPro.dll")
libs = ["gdiplus.lib", "WPCore.lib", "windowsapp.lib", "Version.lib",
        "mfc140u.lib", "kernel32.lib", "user32.lib", "gdi32.lib",
        "comdlg32.lib", "ws2_32.lib", "advapi32.lib", "shell32.lib",
        "ole32.lib", "oleaut32.lib", "uuid.lib", "winmm.lib", "shlwapi.lib"]
link_cmd = [LINK] + ldflags + [
    f"/OUT:{dll}",
    f"/IMPLIB:{os.path.join(outdir, 'WeatherPro.lib')}",
    "/DEF:WeatherPro.def",
] + objs + [res] + libs
print(">> linking WeatherPro.dll")
r = subprocess.run(link_cmd, env=env, cwd=WP)
if r.returncode != 0:
    print("FAILED: link")
    sys.exit(1)
print("OK ->", dll, os.path.getsize(dll), "bytes")
