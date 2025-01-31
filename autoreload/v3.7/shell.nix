with import (fetchTarball https://github.com/NixOS/nixpkgs/archive/5ad6a14c6bf098e98800b091668718c336effc95.tar.gz) { };
let
  sillyORMPackage = pkgs.python312Packages.buildPythonPackage rec {
    pname = "sillyorm";
    version = "0.8.1";
    pyproject = true;

    build-system = [
      python312Packages.setuptools
    ];

    /*
    src = fetchPypi {
      inherit pname version;
      hash = "sha256-J/k/P178iNjoGApD0kj08uymqlftFXsqGfUoUIHhcIc=";
    };
    */
    src = fetchgit {
      url = "https://github.com/theverygaming/sillyORM.git";
      rev = "cfddd5c848f287faee8f0c9d7971034202588d25";
      hash = "sha256-o9mNc7RQtUkMyCM6HmdnmtXhzV+T7MhCMmGEOODcqiE=";
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
      rev = "8fb07dee5afe563817d263d40fdc0b1058635c94";
      hash = "sha256-oh2wDka06JvzCITC7j+xDcJncOOvysI71daHQGN5uIU=";
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
