with import (fetchTarball https://github.com/NixOS/nixpkgs/archive/5ad6a14c6bf098e98800b091668718c336effc95.tar.gz) { };
let
  sillyORMPackage = pkgs.python312Packages.buildPythonPackage rec {
    pname = "sillyorm";
    version = "0.5.0";
    pyproject = true;

    build-system = [
      python312Packages.setuptools
    ];

    src = fetchPypi {
      inherit pname version;
      hash = "sha256-2UYka4ddE43LBQi0gdqLYKaEIWwYBPWYNkudsc3+O8A=";
    };
  };
  sillyPackage = pkgs.python312Packages.buildPythonPackage rec {
    pname = "silly";
    version = "0.0.1";
    pyproject = true;

    build-system = [
      python312Packages.setuptools
    ];

    dependencies = [
      sillyORMPackage
      python312Packages.flask
      python312Packages.lxml
    ];

    src = fetchgit {
      url = "https://github.com/theverygaming/silly.git";
      rev = "e92cf6dd99a2480b77a33f272cfb2912b07e7cc6";
      hash = "sha256-fHTG1OMwLZ0i7LQFSeYNfS54gHgvK7wbmBG4LKU2uto=";
    };
  };
in
stdenv.mkDerivation {
  name = "silly";
  buildInputs = [
    python312

    # dependencies
    sillyPackage
    python312Packages.requests

    # lint, fmt, type
    python312Packages.pylint
    python312Packages.mypy
    python312Packages.black

    # for convenience
    sqlitebrowser
  ];
}
