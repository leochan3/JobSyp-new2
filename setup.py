from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="jobspy-enhanced",
    version="1.0.0",
    author="LeoChan",
    author_email="leochan3@github.com",
    description="Enhanced JobSpy with company-specific Indeed scraping",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/leochan3/JobSyp-new2",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=1.3.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "regex>=2021.0.0",
        "pydantic>=1.8.0",
    ],
    keywords="job scraping indeed linkedin glassdoor google ziprecruiter company-specific",
    project_urls={
        "Bug Reports": "https://github.com/leochan3/JobSyp-new2/issues",
        "Source": "https://github.com/leochan3/JobSyp-new2",
        "Documentation": "https://github.com/leochan3/JobSyp-new2/blob/main/COMPANY_SCRAPING_GUIDE.md",
    },
) 