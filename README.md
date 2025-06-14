Cronjob , Data Wrapper for crypto research

## C++ Utilities

The `WorkbenchCpp` directory contains a collection of C++ translation
stubs generated from the Python modules under `Workbench/`.  Dataclasses
are converted into simple C++ structs while keeping a directory layout
that mirrors the original project.  The directory also contains the
previous C++ utilities and `SwapArbStrategyBot` skeleton.

To regenerate the header files you can run

```bash
python tools/generate_cpp_skeletons.py
```

An example program is provided and can be built by running `make` inside
`WorkbenchCpp`.
