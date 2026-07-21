# Required Branch Protection

GitHub branch protection is repository configuration and cannot be enforced by workflow files alone. Apply the following rules to both `main` and `develop` after the workflows from `PROD-002` have completed at least once.

## Pull Request Rules

- Require a pull request before merging.
- Require at least one approving review.
- Dismiss stale approvals when new commits are pushed.
- Require approval of the most recent reviewable push.
- Require conversation resolution before merging.
- Require branches to be up to date before merging.
- Do not allow bypassing the rules.
- Block force pushes and branch deletion.

## Required Status Checks

Select these check-run names in the GitHub ruleset:

- `Backend quality and tests`
- `Admin test, lint, and build`
- `Mobile test and typecheck`
- `Dependency, secret, and configuration scan`
- `Pull request dependency review`
- `CodeQL (python)`
- `CodeQL (javascript-typescript)`
- `Backend container image scan`
- `Admin container image scan`

The GitHub user interface may prefix a check with its workflow name, such as `Backend CI / Backend quality and tests`. Select the check whose job name exactly matches the list above.

## Configuration Procedure

1. Push the `PROD-002` workflow changes and let all four workflows run once.
2. Open the repository on GitHub.
3. Open **Settings → Rules → Rulesets**.
4. Create a branch ruleset targeting `main` and `develop`.
5. Enable the pull-request and branch restrictions above.
6. Enable **Require status checks to pass** and select every listed check.
7. Set the ruleset to **Active**.
8. Open a test pull request with an intentionally failing check and confirm GitHub disables merge.
9. Fix the test failure and confirm merge becomes available only after all checks and review requirements pass.

Record the ruleset URL and test pull-request URL in `docs/PRODUCTION_HARDENING_TRACKER.md` before marking `PROD-002` done.
