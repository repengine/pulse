# Pulse Deprecation & Milestone Review Policy

## Milestone Reviews

- At every `v0.X00` version, conduct a codebase review.
- Refactor modules for clarity, performance, and maintainability.
- Update documentation and tests as needed.

## Deprecation Policy

- Deprecated modules/functions are marked with a `@deprecated` decorator and a warning in the docstring.
- Deprecated code is removed after two milestone releases unless critical for backward compatibility.
- All deprecations are documented in `docs/deprecations.md`.