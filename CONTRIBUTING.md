# Conventional Commits Guidelines

We have adopted Conventional Commits for our project. For detailed information, please refer to the [official specification](https://www.conventionalcommits.org/).

## Overview

Conventional Commits is a lightweight convention for creating an explicit commit history. It provides an easy set of rules for creating commit messages that are both human and machine-readable.

## Basic Structure

A commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Types

Common types include:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

## Minimal Examples

- `feat: add user authentication feature`
- `fix: resolve issue with data persistence`
- `docs: update README with new API endpoints`
- `style: fix lint errors`
- `test: add missing tests`
- `chore: update dependencies`

## Best Practices

1. **Keep commits small**: Each commit should be focused and easy to understand. This makes review and potential rollbacks simpler.

2. **Open Pull Requests for major changes**: If you're making numerous commits or doing significant refactoring, open a pull request for review.

3. **Be descriptive**: While keeping the subject line concise, use the body to explain the what and why of the commit, not the how.

4. **Reference issues**: If your commit addresses an issue, reference it in the footer (e.g., `Closes #123`).

By following these guidelines, we can maintain a clean, readable, and useful commit history that enhances our development process.