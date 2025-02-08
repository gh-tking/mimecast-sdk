from setuptools import setup, find_packages

setup(
    name="mimecast-sdk",
    version="0.1.0",
    description="Python SDK for Mimecast API 2.0",
    author="OpenHands",
    author_email="openhands@all-hands.dev",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=['requests>=2.25.0'],
    extras_require={},
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

)