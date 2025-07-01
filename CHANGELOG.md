# Changelog

All notable changes to `openghg_calscales` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased](https://github.com/openghg/openghg/compare/0.1.1...HEAD)

### Added
- Added dependencies in pyproject.toml. [#PR 14](https://github.com/openghg/openghg_calscales/pull/14)
- Species synonyms for HFCs, HCFCs, PFCs
- NIES/SIO conversion factors for HFC-23 and HFC-125

## [0.1.1] - 2024-05-13

### Added

- Added co2 to synonyms - [Commit](https://github.com/openghg/openghg_calscales/commit/a0b6f82901c26a610949f91be1aef2d4e3290fc2)

### Fixed

- Added fix for extracting index from `DataArray`` - [Commit](https://github.com/openghg/openghg_calscales/commit/29688ba65df06ef88defaad6ea0227ca64d49d2b)

### Changed

-  Changed behaviour so that Series/DataArray that is all NaN is returned, instead of raising an error - [Commit](https://github.com/openghg/openghg_calscales/commit/166d5113ee1914c8dd9293a3829148cf1dfe85e6)


## [0.1.0] - 2023-11-23

The first release of `openghg_calscales`
