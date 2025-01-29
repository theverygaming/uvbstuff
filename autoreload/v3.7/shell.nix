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
      rev = "06b63004479fc6411db2a9c7002cc2ba0293968e";
      hash = "sha256-T40FncjSgEt6d8252zZVrGWW7BG4LNefUy1ZA1ZIokc=";
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
      rev = "5d852ced63775656afb4ba878d04021c42149d06";
      hash = "sha256-t0yZrqDJANsEC7q4if3doQfH8Z1NHFqWin521lsnu68=";
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
