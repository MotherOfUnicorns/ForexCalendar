import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="forex_calendar",
    description="unofficial API for forexfactory.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MotherOfUnicorns/ForexCalendar",
    # packages=setuptools.find_packages(),
    py_modules=["forex_calendar"],
    python_requires=">=3.6",
)
