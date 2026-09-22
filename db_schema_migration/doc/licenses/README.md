# Directory of fallback license files

When the SBOM build script is unable to locate the license file for an
installed package, it will look into this directory for a fallback
license file.

## Naming the files

Each file should be named `{package-name}-{package-version}.md`, for example
`beautifulsoup4-4.12.3.md` (for package called _beautifulsoup4_ version 4.12.3).
Extension is optional, but must match the contents of the file.

If the version of the fallback license does not match with the version of the
package installed, it still gets included in the SBOM,
but a warning will get raised.

(It's also possible to name a license file without a version,
it will still get used, but it's not recommended.)

## Testing the SBOM build

```shell
pipenv run build-sbom
```

The sbom-build script lives in the `build-tools` repository,
and can be copied from there, (but do not commit the copy into this repository.)
Also, it can be symlinked if this repository is checked out as a submodule of
`build-tools`.

```shell
ln -s ../scripts/assbom.py ./
```
