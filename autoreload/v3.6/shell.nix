with import <nixpkgs> { };
let
in stdenv.mkDerivation {
  name = "autoreload";
  buildInputs = [
    deno
  ];
}
