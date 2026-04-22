{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    parts.url = "github:hercules-ci/flake-parts";
  };

  outputs =
    inputs:
    inputs.parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      perSystem =
        {
          system,
          pkgs,
          ...
        }:
        {
          _module.args.pkgs = import inputs.nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };

          devShells.default =
            let
              pythonDeps = ps: [
                ps.fastapi
                ps.uvicorn
                ps.httpx
                ps.langchain-core
                ps.langchain-openai
                ps.langgraph
                ps.openai
                ps.pydantic
                ps.pymongo
                ps.python-multipart
              ];
              pythonEnv = pkgs.python3.withPackages pythonDeps;
            in
            pkgs.mkShell {
              packages = [
                pythonEnv
                pkgs.podman-compose
                pkgs.nodejs
              ];
              shellHook = ''
                export PYTHONPATH="$PYTHONPATH:$PWD/src"
              '';
            };

          packages = rec {
            frontend = pkgs.buildNpmPackage {
              pname = "hiring-agent-frontend";
              version = "0.1.0";
              src = ./frontend;
              npmDepsHash = "sha256-uOQOt5jDJ35QolyuwUAKJ8F8Fe7OD/6wcekK8GqDfjg=";
              installPhase = ''
                cp -r dist $out
              '';
            };

            hiring-agent =
              let
                pythonDeps = ps: [
                  ps.fastapi
                  ps.uvicorn
                  ps.httpx
                  ps.langchain-core
                  ps.langchain-openai
                  ps.langgraph
                  ps.openai
                  ps.pydantic
                  ps.pymongo
                  ps.python-multipart
                ];
                pythonEnv = pkgs.python3.withPackages pythonDeps;
              in
              pkgs.stdenv.mkDerivation {
                pname = "hiring-agent";
                version = "0.1.0";
                src = ./.;
                buildInputs = [ pythonEnv ];
                installPhase = ''
                  mkdir -p $out/share/hiring-agent
                  cp -r src AGENTS.md $out/share/hiring-agent/

                  # Copy pre-compiled frontend to share
                  mkdir -p $out/share/hiring-agent/frontend/dist
                  cp -r ${frontend}/* $out/share/hiring-agent/frontend/dist/

                  mkdir -p $out/bin
                  cat > $out/bin/hiring-agent <<EOF
                  #!/bin/sh
                  export PYTHONPATH="\$PYTHONPATH:$out/share/hiring-agent/src"
                  exec ${pythonEnv}/bin/uvicorn api.main:app --app-dir $out/share/hiring-agent/src "\$@"
                  EOF
                  chmod +x $out/bin/hiring-agent
                '';
              };

            default = hiring-agent;

            docker = pkgs.dockerTools.buildImage {
              name = "hiring-agent";
              tag = "latest";
              config = {
                Cmd = [ "${pkgs.lib.getExe default}" ];
                Env = [ "PYTHONUNBUFFERED=1" ];
              };
            };
          };
        };
    };
}
