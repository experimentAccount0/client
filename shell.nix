{ pkgs ? import ./nixpkgs.nix
}:

with pkgs;

let
  pyEnv = python27Full.withPackages (self: with self; [
    pip
    virtualenv
    pillow
  ]);

  systemDeps = [
    cacert
    libffi
    openssl
    pkgconfig
    sqlite
    zlib
  ];

  devDeps = [ file which ];

  allDeps = [pyEnv] ++ systemDeps ++ devDeps;

in

stdenv.mkDerivation {
  name = "cloudmesh_client_env";
  buildInputs = allDeps;
  shellHook = ''
    # https://github.com/pikajude/darwinixpkgs/blob/master/doc/languages-frameworks/python.md
    # fixes: ZIP does not support timestamps before 1980
    export SOURCE_DATE_EPOCH=$(date +%s)

    export SSL_CERT_FILE=${cacert}/etc/ssl/certs/ca-bundle.crt
    test -d venv || virtualenv venv
    source venv/bin/activate

    pip install -r requirements.txt
  '';
}
