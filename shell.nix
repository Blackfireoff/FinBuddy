{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  name = "finbuddy-dev-env";

  packages = with pkgs; [
    nodejs_24

    python313
    python313Packages.pip
  ];
}
