with import (fetchTarball https://github.com/NixOS/nixpkgs/archive/5ad6a14c6bf098e98800b091668718c336effc95.tar.gz) { };
let
  sillyORMPackage = pkgs.python312Packages.buildPythonPackage rec {
    pname = "sillyorm";
    version = "0.6.0";
    pyproject = true;

    build-system = [
      python312Packages.setuptools
    ];

    src = fetchPypi {
      inherit pname version;
      hash = "sha256-0rfS5sQQLa6L71r89cBkI5Q7qC6ySQOJhH+jvfQKwt0=";
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
      rev = "a3dadd0ec7c37ebb8915cfe86fdc12b499add2f2";
      hash = "sha256-7aD9bAtOCbp4mwP3POASz/2dEheyMyrI3O9LjEB1i/s=";
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
