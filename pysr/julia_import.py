import os
import sys
import warnings
from types import ModuleType
from typing import cast
import json

from .julia_registry_helpers import try_with_registry_fallback

# Check if JuliaCall is already loaded, and if so, warn the user
# about the relevant environment variables. If not loaded,
# set up sensible defaults.
if "juliacall" in sys.modules:
    warnings.warn(
        "juliacall module already imported. "
        "Make sure that you have set the environment variable `PYTHON_JULIACALL_HANDLE_SIGNALS=yes` to avoid segfaults. "
        "Also note that PySR will not be able to configure `PYTHON_JULIACALL_THREADS` or `PYTHON_JULIACALL_OPTLEVEL` for you."
    )
else:
    # Required to avoid segfaults (https://juliapy.github.io/PythonCall.jl/dev/faq/)
    if os.environ.get("PYTHON_JULIACALL_HANDLE_SIGNALS", "yes") != "yes":
        warnings.warn(
            "PYTHON_JULIACALL_HANDLE_SIGNALS environment variable is set to something other than 'yes' or ''. "
            + "You will experience segfaults if running with multithreading."
        )

    if os.environ.get("PYTHON_JULIACALL_THREADS", "auto") != "auto":
        warnings.warn(
            "PYTHON_JULIACALL_THREADS environment variable is set to something other than 'auto', "
            "so PySR was not able to set it. You may wish to set it to `'auto'` for full use "
            "of your CPU."
        )

    # TODO: Remove these when juliapkg lets you specify this
    for k, default in (
        ("PYTHON_JULIACALL_HANDLE_SIGNALS", "yes"),
        ("PYTHON_JULIACALL_THREADS", "auto"),
        ("PYTHON_JULIACALL_OPTLEVEL", "3"),
    ):
        os.environ[k] = os.environ.get(k, default)


autoload_extensions = os.environ.get("PYSR_AUTOLOAD_EXTENSIONS")
if autoload_extensions is not None:
    # Deprecated; so just pass to juliacall
    os.environ["PYTHON_JULIACALL_AUTOLOAD_IPYTHON_EXTENSION"] = autoload_extensions


# TODO: Remove if I find way to directly specify this via juliapkg

# Read juliapkg.json file to get project path
juliapkg_path = os.path.join(os.path.dirname(__file__), "juliapkg.json")
try:
    with open(juliapkg_path, "r") as f:
        juliapkg_config = json.load(f)
    
    # Set environment variable if "project" key exists
    if "project" in juliapkg_config:
        print(f"Setting PYTHON_JULIAPKG_PROJECT to {juliapkg_config['project']}")
        os.environ["PYTHON_JULIAPKG_PROJECT"] = juliapkg_config["project"]
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    # If file doesn't exist, can't be parsed, or doesn't have project key,
    # don't set the environment variable
    pass


def _import_juliacall():
    import juliacall  # type: ignore


try_with_registry_fallback(_import_juliacall)


from juliacall import AnyValue  # type: ignore
from juliacall import VectorValue  # type: ignore
from juliacall import Main as jl  # type: ignore

jl = cast(ModuleType, jl)


jl_version = (jl.VERSION.major, jl.VERSION.minor, jl.VERSION.patch)

jl.seval("using SymbolicRegression")
SymbolicRegression = jl.SymbolicRegression

# Expose `D` operator:
jl.seval("using SymbolicRegression: D")

jl.seval("using Pkg: Pkg")
Pkg = jl.Pkg
