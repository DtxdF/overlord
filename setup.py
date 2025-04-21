from setuptools import setup, find_packages

VERSION = "0.4.0"

def get_description():
    return "\
Overlord is a fast, distributed orchestrator for FreeBSD jails oriented to GitOps. \
You define a file with the service intended to run on your cluster and deployment \
takes seconds to minutes."

setup(
    name="overlord",
    version=VERSION,
    description="Deploy FreeBSD jails as fast as you code",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    author="Jesús Daniel Colmenares Oviedo",
    author_email="DtxdF@disroot.org",
    url="https://github.com/DtxdF/overlord",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: BSD",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities"
    ],
    package_dir={"" : "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    license="BSD 3-Clause",
    license_files="LICENSE",
    install_requires=[
        "click",
        "pyaml-env",
        "python-dotenv",
        "tornado",
        "httpx[h2,brotli,zstd]",
        "aiostalk@git+https://github.com/DtxdF/aiostalk.git",
        "psutil",
        "pymemcache",
        "pyjwt",
        "aiofiles",
        "humanfriendly",
        "ifaddr",
        "asciitree",
        "etcd3gw",
        "dnspython",
        "pyyaml"
    ],
    entry_points={
        "console_scripts" : [
            "overlord = overlord.__init__:cli"
        ]
    }
)
