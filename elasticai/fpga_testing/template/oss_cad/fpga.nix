{
  pkgs,
  lib,
  config,
  inputs,
  ...
}: let
  pkgs-unstable = import inputs.nixpkgs-unstable {system = pkgs.stdenv.system;};
  uv_run = "${pkgs-unstable.uv}/bin/uv run --active";
  system = pkgs.stdenv.hostPlatform.system;
  oxc = inputs.openxc7.packages.${system};
  oxpkgs = inputs.openxc7.inputs.nixpkgs.legacyPackages.${system};
  nextpnr = oxc.nextpnr.overrideAttrs (old: {
    buildInputs =
      (old.buildInputs or [])
      ++ oxpkgs.lib.optionals oxpkgs.stdenv.isDarwin [oxpkgs.llvmPackages.openmp];
  });
  chipdb = oxc.nextpnr-xilinx-chipdb.spartan7.override {inherit nextpnr;};
  pyEnv = oxpkgs.python312.withPackages (ps:
    with ps; [
      textx
      pyyaml
      simplejson
      intervaltree
      arpeggio
      setuptools
      future
      sortedcontainers
      cython
      packaging
      more-itertools
      jaraco-functools
    ]);
  fasm2frames = pkgs.writeShellScriptBin "openxc7-fasm2frames" ''
    export PYTHONPATH="${oxc.prjxray}/usr/share/python3:${oxc.fasm}/lib/python3.12/site-packages"
    exec ${pyEnv}/bin/python3 ${oxc.prjxray}/bin/fasm2frames "$@"
  '';
in {
  packages =
    [
      pkgs.zlib # needed as dependency cocotb/ghdl under circumstances
      pkgs.gnutar
      pkgs.picotool
      nextpnr
      oxc.prjxray
      fasm2frames
    ]
    ++ lib.optionals pkgs.stdenv.isLinux [oxc.fpga-assembler];

  env = {
    NEXTPNR_XILINX_DIR = "${nextpnr}";
    PRJXRAY_DB_DIR = "${nextpnr}/share/nextpnr/external/prjxray-db";
    CHIPDB_DIR = "${chipdb}";
  };

  scripts = {
    flash_dirty_jtag = {
      exec = ''
        if [[ -e $DEVENV_ROOT/external/dirtyJtag.uf2 ]]; then
          RELEASE=$(wget -qO- "https://api.github.com/repos/phdussud/pico-dirtyJtag/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
          URL="https://github.com/phdussud/pico-dirtyJtag/releases/download/$RELEASE/dirtyJtag.uf2"
          echo "Downloading DirtyJTAG ($URL) ... "
          cd $DEVENV_ROOT/external && wget -q "$URL"
          echo "Done"
        else
          echo "RP2040/2350 Executable found."
        fi

        picotool load --verify --force --execute dirtyJtag.uf2
      '';
      package = pkgs.bash;
    };
    get_latest_oss_cad_suite_release = {
      exec = ''
        echo $(wget -qO- "https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
      '';
      package = pkgs.bash;
    };
    check_oss_cad_available = {
      exec = ''
        if [[ -e $DEVENV_ROOT/oss-cad-suite/VERSION ]]; then
            LATEST=$(get_latest_oss_cad_suite_release | tr -d "-")
            CURRENT=$(cat $DEVENV_ROOT/oss-cad-suite/VERSION)
            if [[ "$LATEST" != "$CURRENT" ]]; then
                echo "You have currently Version $CURRENT of the oss-cad-suite installed. A newer version ($LATEST) is available. If you want to update, please enter 'download_build_tools' into terminal."
            fi
        elif [[ -e $HOME/oss-cad-suite/VERSION ]]; then
            LATEST=$(get_latest_oss_cad_suite_release | tr -d "-")
            CURRENT=$(cat $HOME/oss-cad-suite/VERSION)
            if [[ "$LATEST" != "$CURRENT" ]]; then
                echo "You have currently Version $CURRENT of the oss-cad-suite installed. A newer version ($LATEST) is available. If you want to update, please enter 'download_build_tools' into terminal."
            fi
        else
            echo "You don't have the oss-cad-suite installed. Please enter 'download_oss_cad' into terminal"
        fi
      '';
      package = pkgs.bash;
    };
    download_oss_cad = {
      exec = ''
        if [[ "$(uname -m)" == "arm64" ]]; then
          ARCH='arm64'
        elif [[ "$(uname -m)" == "x86_64" ]]; then
          ARCH="x64"
        else
          echo "Architecture not supported!"
          exit 1
        fi
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
           OS="linux"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
          OS="darwin"
        else
          echo "OS not supported!"
          exit 1
        fi

        echo "Where should OSS-CAD-Suite be installed?"
        echo "  [l] Local project directory ($DEVENV_ROOT)"
        echo "  [h] Home directory ($HOME)"
        read -p "Choice [l/h]: " INSTALL_CHOICE

        case "$INSTALL_CHOICE" in
          l|L)
            INSTALL_DIR="$DEVENV_ROOT"
            ;;
          h|H)
            INSTALL_DIR="$HOME"
            ;;
          *)
            echo "Invalid choice. Please enter 'l' or 'h'."
            exit 1
            ;;
        esac

        RELEASE=$(get_latest_oss_cad_suite_release)
        URL="https://github.com/YosysHQ/oss-cad-suite-build/releases/download/$RELEASE/oss-cad-suite-$OS-$ARCH-$(echo "$RELEASE" | tr -d "-").tgz"

        echo "Downloading OSS-CAD-Suite ($URL) ..."
        cd "$INSTALL_DIR" && wget -qO- "$URL" | gunzip | tar xf -
        echo "Done"

        if [[ "$OS" == "darwin" ]]; then
          "$INSTALL_DIR/oss-cad-suite/activate"
        fi
      '';
      package = pkgs.bash;
    };
  };

  enterShell = ''
    echo ""
    check_oss_cad_available
    if [[ -e $DEVENV_ROOT/oss-cad-suite/environment ]]; then
        source $DEVENV_ROOT/oss-cad-suite/environment
        echo "Source oss-cad-suite from local project"
    elif [[ -e $HOME/oss-cad-suite/environment ]]; then
        source $HOME/oss-cad-suite/environment
        echo "Source oss-cad-suite from home directory"
    else
        echo "oss-cad-suite not found"
    fi
    echo ""
    unset VIRTUAL_ENV
  '';
}
