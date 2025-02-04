with import (fetchTarball https://github.com/NixOS/nixpkgs/archive/5ad6a14c6bf098e98800b091668718c336effc95.tar.gz) { };
let
  sillyORMPackage = pkgs.python312Packages.buildPythonPackage rec {
    pname = "sillyorm";
    version = "0.9.0";
    pyproject = true;

    build-system = [
      python312Packages.setuptools
    ];

    src = fetchPypi {
      inherit pname version;
      hash = "sha256-NRX+4IT+Wif3X5qlnShN+FT/kN4+gq7earT44mgxCVI=";
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
      rev = "050482f272af4fab564c15238bd7b17ecf22197d";
      hash = "sha256-If8H++PzRlrb/uV3fRanVWBGaJsMi2sgYnSBTZ4sF9U=";
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
