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
      rev = "32a5b121ea1e072b871e0f333a92309f7a3e9ec4";
      hash = "sha256-awCMipb7hxodO+GAO6/jzl63UyM+fvU1BK+c7OtHQiw=";
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
      rev = "40d314b35209fb12c6dec6bbb35cefcfcdae966e";
      hash = "sha256-InHDP0RVWNR4dB00ucOWpHMJJ4hvDMa7q88ExB9obSM=";
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
