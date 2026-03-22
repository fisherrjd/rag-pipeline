{ pkgs ? import
    (fetchTarball {
      name = "jpetrucciani-2026-03-21";
      url = "https://github.com/jpetrucciani/nix/archive/11743603c508c846237c4db4c2f750b3f3900ab5.tar.gz";
      sha256 = "0k9w04mhwncqafaiaas7hz4ygc1z9xk0nnqax3qn3nlgfzcpwz58";
    })
    { }
}:
let
  name = "rag-pipeline";
  uvEnv = pkgs.uv-nix.mkEnv {
    inherit name; python = pkgs.python314;
    workspaceRoot = pkgs.hax.filterSrc { path = ./.; };
    pyprojectOverrides = final: prev: { };
  };

  tools = with pkgs; {
    cli = [
      jfmt
      nixup
    ];
    uv = [ uv uvEnv ];
    scripts = pkgs.lib.attrsets.attrValues scripts;
  };

  scripts = with pkgs; { };
  paths = pkgs.lib.flatten [ (builtins.attrValues tools) ];
  env = pkgs.buildEnv {
    inherit name paths; buildInputs = paths;
  };
in
(env.overrideAttrs (_: {
  inherit name;
  NIXUP = "0.0.10";
} // uvEnv.uvEnvVars)) // { inherit scripts; }
