# Source from bash or zsh: source scripts/activate.sh
if [ -n "${ZSH_VERSION:-}" ]; then
    _emit_activation_file="${(%):-%N}"
else
    _emit_activation_file="${BASH_SOURCE[0]}"
fi
_emit_root="$(cd "$(dirname "$_emit_activation_file")/.." && pwd)"
source "$_emit_root/.venv/bin/activate"
export MPLCONFIGDIR="$_emit_root/.cache/matplotlib"
export JUPYTER_CONFIG_DIR="$_emit_root/.cache/jupyter"
export JUPYTER_DATA_DIR="$_emit_root/.cache/jupyter/data"
export JUPYTER_RUNTIME_DIR="$_emit_root/.cache/jupyter/runtime"
mkdir -p "$MPLCONFIGDIR" "$JUPYTER_CONFIG_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_RUNTIME_DIR"
unset _emit_root _emit_activation_file
