{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  name = "finbuddy-dev-env";

  packages = with pkgs; [
    nodejs_24
  ];
}
