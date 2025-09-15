from setuptools import setup, find_packages

setup(
    name="sriaas_booking",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],  # Frappe is already in the bench env
)
