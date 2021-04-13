# brindex - local pip-compatible index server as a bridge to custom sources

The initial motivation for this package came from the need to have a private Python
package index without needing to host a server, while being compatible with `pip` (via
`--index-url` and `--extra-index-url` options) and its ecosystem. In particular, the
main intent was to be able to use a S3 bucket as a Python package index.

Therefore, the package includes support for S3 buckets out of the box. It also supports
serving from the local filesystem, though this is much less useful and that use case may
be best covered by other means.

However, the implementation is general enough that it allows custom implementation of
sources, as long as they conform to the same interface as the included `*Repo` and
`*Package` classes.

The way it works is by launching a local
[PEP503](https://www.python.org/dev/peps/pep-0503/)-compliant server that acts as a
bridge, generating appropriate responses that map to the custom repository with the
actual packages. Note that even though the web server could be deployed anywhere in
theory, it's really only intended to be run locally as that's what the original use case
requires.

To launch the server, run `brindex` with the appropriate command line arguments (see
`brindex --help`). With the server running, it's possible to use `pip` and related tools
by including the local index's URL (`http://localhost:8000`). Typically, that would mean
adding `--extra-index-url http://localhost:8000` to the `pip` invocation or to a
`requirements.txt` file.

For S3, the credentials must have been configured beforehand, for example via `aws configure`.
