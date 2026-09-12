import os, subprocess, sys

MSVC = r"D:\Microsoft Visual Studio\2022\Enterprise\VC\Tools\MSVC\14.44.35207"
SDK = r"D:\Windows Kits\10"
CL = os.path.join(MSVC, "bin", "Hostx64", "x64", "cl.exe")
LIBE = os.path.join(MSVC, "bin", "Hostx64", "x64", "lib.exe")
PROJ = r"E:\code\TrafficMonitorPlugins_TMP-WeatherPro"

inc = [
    os.path.join(MSVC, "include"),
    os.path.join(SDK, "Include", "10.0.26100.0", "ucrt"),
    os.path.join(SDK, "Include", "10.0.26100.0", "shared"),
    os.path.join(SDK, "Include", "10.0.26100.0", "um"),
    os.path.join(PROJ, "dependencies", "yyjson", "src"),
    os.path.join(PROJ, "dependencies", "jwt", "include"),
    os.path.join(PROJ, "dependencies", "httplib"),
    os.path.join(PROJ, "third_party", "zlib", "include"),
    os.path.join(PROJ, "third_party", "openssl", "include"),
]
libdirs = [
    os.path.join(MSVC, "lib", "x64"),
    os.path.join(SDK, "Lib", "10.0.26100.0", "ucrt", "x64"),
    os.path.join(SDK, "Lib", "10.0.26100.0", "um", "x64"),
]

env = os.environ.copy()
env["INCLUDE"] = ";".join(inc)
env["LIB"] = ";".join(libdirs)
env["PATH"] = os.path.join(MSVC, "bin", "Hostx64", "x64") + ";" + env.get("PATH", "")

sources = [
    os.path.join(PROJ, "dependencies", "yyjson", "src", "yyjson.c"),
    "DataDef.cpp",
    "DataProviderOpenWeather.cpp",
    "DataProviderQWeather.cpp",
    "DataProviderSpiderWeatherComCn.cpp",
    "AppLocale.cpp",
    "Logger.cpp",
    "utils.cpp",
]

config = sys.argv[1] if len(sys.argv) > 1 else "Debug"
if config == "Debug":
    cflags = ["/nologo", "/c", "/MDd", "/Zi", "/EHsc", "/std:c++20", "/utf-8",
              "/permissive-", "/D_DEBUG", "/D_LIB", "/DWIN32_LEAN_AND_MEAN",
              "/DNOMINMAX", "/DCPPHTTPLIB_OPENSSL_SUPPORT", "/DCPPHTTPLIB_ZLIB_SUPPORT"]
    outdir = os.path.join(PROJ, "lib", "x64", "Debug")
    outname = "WPCore.lib"
else:
    cflags = ["/nologo", "/c", "/MD", "/O2", "/EHsc", "/std:c++20", "/utf-8",
              "/permissive-", "/DNDEBUG", "/D_LIB", "/DWIN32_LEAN_AND_MEAN",
              "/DNOMINMAX", "/DCPPHTTPLIB_OPENSSL_SUPPORT", "/DCPPHTTPLIB_ZLIB_SUPPORT"]
    outdir = os.path.join(PROJ, "lib", "x64", "Release")
    outname = "WPCore.lib"

os.makedirs(outdir, exist_ok=True)
objdir = os.path.join(PROJ, "WPCore", "obj", "x64", config)
os.makedirs(objdir, exist_ok=True)

objs = []
for s in sources:
    base = os.path.basename(s)
    obj = os.path.join(objdir, os.path.splitext(base)[0] + ".obj")
    objs.append(obj)
    cmd = [CL] + cflags + [f"/Fo{obj}", s]
    print(">> compiling", base)
    r = subprocess.run(cmd, env=env, cwd=os.path.join(PROJ, "WPCore"))
    if r.returncode != 0:
        print("FAILED:", base)
        sys.exit(1)

out = os.path.join(outdir, outname)
# 模拟 MSBuild 静态库工程行为：把 zlib/OpenSSL 静态库合并进 WPCore.lib，
# 使 WeatherPro 链接时只需 WPCore.lib（与原工程 vcxproj 语义一致）
dep_libs = [
    os.path.join(PROJ, "third_party", "zlib", "lib",
                 "zlibd.lib" if config == "Debug" else "zlib.lib"),
    os.path.join(PROJ, "third_party", "openssl", "lib", "libssl_static.lib"),
    os.path.join(PROJ, "third_party", "openssl", "lib", "libcrypto_static.lib"),
]
missing = [p for p in dep_libs if not os.path.exists(p)]
if missing:
    print("MISSING DEP LIBS:", missing)
    sys.exit(1)
cmd = [LIBE, "/nologo", f"/out:{out}"] + objs + dep_libs
print(">> archiving", out)
r = subprocess.run(cmd, env=env)
if r.returncode != 0:
    sys.exit(1)
print("OK ->", out, os.path.getsize(out), "bytes")
