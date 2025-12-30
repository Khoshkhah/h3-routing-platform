"""
H3-Toolkit setup with optional C++ extension building.
"""
import os
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.build_ext import build_ext


class CMakeBuild(build_ext):
    """Custom build command that builds C++ extension via CMake."""
    
    def run(self):
        # Check if cmake is available
        try:
            subprocess.check_output(['cmake', '--version'])
        except OSError:
            print("CMake not found. Installing without C++ bindings.")
            print("For C++ bindings, install cmake and rebuild.")
            return
        
        # Build directory
        build_dir = os.path.join(os.path.dirname(__file__), 'build')
        os.makedirs(build_dir, exist_ok=True)
        
        # Configure
        cmake_args = [
            'cmake',
            '-DCMAKE_BUILD_TYPE=Release',
            '..'
        ]
        
        # Build
        build_args = [
            'cmake',
            '--build', '.',
            '--target', '_h3_toolkit_cpp',
            '--config', 'Release',
            '-j'
        ]
        
        try:
            print("Building C++ extension...")
            subprocess.check_call(cmake_args, cwd=build_dir)
            subprocess.check_call(build_args, cwd=build_dir)
            
            # Copy the built module to the package
            import glob
            so_files = glob.glob(os.path.join(build_dir, '_h3_toolkit_cpp*.so'))
            if so_files:
                import shutil
                dest = os.path.join(os.path.dirname(__file__), 'src', 'python', 'h3_toolkit')
                for so_file in so_files:
                    shutil.copy(so_file, dest)
                    print(f"Installed: {os.path.basename(so_file)}")
            else:
                print("Warning: C++ module not found after build.")
                
        except subprocess.CalledProcessError as e:
            print(f"C++ build failed: {e}")
            print("Installing without C++ bindings.")


setup(
    name="h3-toolkit",
    version="0.1.0",
    description="Advanced H3 boundary tracing and geometry utilities",
    author="H3-Toolkit Contributors",
    package_dir={"": "src/python"},
    packages=find_packages(where="src/python"),
    python_requires=">=3.8",
    install_requires=[
        "h3>=4.0.0",
        "shapely>=2.0.0",
        "geojson>=3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "folium",
            "jupyter",
        ],
    },
    cmdclass={
        'build_ext': CMakeBuild,
    },
    # Include compiled extensions if they exist
    package_data={
        'h3_toolkit': ['*.so', '*.pyd', '*.dylib'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: C++",
    ],
)
