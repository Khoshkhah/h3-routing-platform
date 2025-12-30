# Contributing to H3-Toolkit

Thank you for your interest in contributing to H3-Toolkit! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/h3-toolkit.git
   cd h3-toolkit
   ```

2. **Create a development environment**
   ```bash
   conda create -n h3-toolkit-dev python=3.11
   conda activate h3-toolkit-dev
   conda install -c conda-forge boost-cpp cmake
   pip install -e ".[dev]"
   ```

3. **Build the C++ extensions**
   ```bash
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug ..
   make -j4
   cp _h3_toolkit_cpp*.so ../src/python/h3_toolkit/
   ```

4. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## Code Structure

```
h3-toolkit/
├── src/
│   ├── cpp/                    # C++ implementation
│   │   ├── include/h3_toolkit.hpp
│   │   └── src/h3_toolkit.cpp
│   ├── bindings/               # pybind11 bindings
│   │   └── python_bindings.cpp
│   └── python/                 # Python package
│       └── h3_toolkit/
│           ├── __init__.py     # Package exports + C++ wrappers
│           ├── geom.py         # Pure Python geometry
│           └── utils.py        # Pure Python utilities
├── tests/                      # Test suite
└── docs/                       # Documentation
```

## Development Guidelines

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Document all public functions with docstrings

**C++:**
- Use C++17 features
- Follow Google C++ Style Guide
- Add Doxygen comments for public functions

### Adding a New Function

1. **Implement in C++** (`src/cpp/src/h3_toolkit.cpp`)
2. **Add declaration** (`src/cpp/include/h3_toolkit.hpp`)
3. **Add pybind11 binding** (`src/bindings/python_bindings.cpp`)
4. **Add Python wrapper** (`src/python/h3_toolkit/__init__.py`)
5. **Add pure Python fallback** (`src/python/h3_toolkit/geom.py` or `utils.py`)
6. **Write tests** (`tests/test_h3_toolkit.py`)
7. **Update documentation** (`docs/api_reference.md`)

### Testing

- All new functions must have tests
- Test both Python and C++ implementations
- Test edge cases (pentagons, high resolutions, etc.)

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_h3_toolkit.py::test_children_on_boundary_faces -v

# Run with coverage
pytest tests/ --cov=h3_toolkit --cov-report=html
```

### Benchmarking

When adding performance-critical code, include benchmarks:

```python
import time
from h3_toolkit import function_python, function_cpp

cell = '86283082fffffff'

# Benchmark
for name, func in [('Python', function_python), ('C++', function_cpp)]:
    start = time.time()
    for _ in range(100):
        func(cell)
    elapsed = (time.time() - start) * 10  # ms per call
    print(f"{name}: {elapsed:.2f} ms")
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the guidelines above
3. **Write tests** for any new functionality
4. **Update documentation** if needed
5. **Run the test suite** to ensure everything passes
6. **Submit a pull request** with a clear description

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] C++ code compiles without warnings
- [ ] Python type hints added

## Reporting Issues

When reporting issues, please include:

1. **H3-Toolkit version** (`h3_toolkit.__version__`)
2. **Python version** (`python --version`)
3. **Operating system**
4. **Minimal reproducible example**
5. **Full error traceback**

## Questions?

Feel free to open an issue for any questions about contributing!
