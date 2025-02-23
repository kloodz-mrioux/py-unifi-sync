.. _contributing:

Contributors Guide
===================
Welcome to the unifi-sync community! We’re excited you’re here to help improve this open-source project. This guide will walk you through 
contributing whether it’s fixing bugs, adding features, or enhancing documentation. Every contribution makes unifi-sync more valuable for 
users syncing with UniFi systems.


Getting Started
---------------
   * Fork the Repository: Click "Fork" on our GitHub repository to create your own copy.
   * Clone Locally: Clone your fork to your machine:
   * Set Up the Environment: Install dependencies and configure the project. See the :ref:`install` for details.
   * Create a Branch: Work on a new branch for your changes:

Ways to Contribute
------------------
   * Code: Add functionality, fix bugs, or optimize unifi-sync’s performance.
   * Documentation: Improve READMEs, guides, or code comments.
      * We use Sphinx/reStructuredText for docs.
      * Documentation Tutorial https://sphinx-tutorial.readthedocs.io/step-1/
   * Issues: Report bugs or suggest enhancements via GitHub Issues.
   * Reviews: Provide feedback on pull requests to help maintain quality.

Submitting Changes
------------------
   * Commit Your Work: Use clear, descriptive commit messages
   * Push to Your Fork
   * Open a Pull Request (PR):
      * Navigate to the main unifi-sync repository and click "New Pull Request."
      * Select your branch and fill out the PR template, describing your changes.
      * Link related issues (e.g., "Fixes #42").

   * Code Review: Respond to maintainer feedback. We aim to review PRs within 7 days.
   * :ref:`release-process`

Guidelines
----------
   * Code Style: Follow [PEP 8/style-guide-name] (see [style-guide-link]). Use tools like [flake8] if specified.
   * Testing: Ensure changes pass existing tests. Add new ones in tests/ for features or fixes
   * Documentation: Update docs for code changes. Build locally to verify:
   * Respect: Be collaborative and kind

Tips for Success
----------------
   * Start small: Look for "good first issue" labels in GitHub Issues.
   * Ask questions: Use [GitHub Discussions/community-channel] if you need clarification.
   * Stay synced: Pull the latest from main before working:

Troubleshooting
---------------
   * Build Errors: Verify dependency versions or ask in your PR.
   * Docs Issues: If using Sphinx, ensure rst_prolog or directives in conf.py are correctly set up.

Recognition
-----------
   * All contributors are listed in our :ref:`authors`. Thank you for powering unifi-sync!