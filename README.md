# gh-social

[![CI](https://github.com/ajangsupardi/gh-social/actions/workflows/ci.yml/badge.svg)](https://github.com/ajangsupardi/gh-social/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/gh-social.svg)](https://pypi.org/project/gh-social/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A small guide to socializing on GitHub without doing all the work yourself.**

---

## Chapter 1: The Problem

Ever feel lonely on GitHub?

You know the drill. Someone follows you, and you follow them back. *Thanks for the follow! Here's one back.* You do this over and over, day after day.

But then one day, you start to wonder.

*I have 500 followers, but why am I following 2,000 people?*

And the worst part? Out of those 2,000 people, **only 347 follow you back.** The rest? Gone. They took your follow and vanished. No goodbye message. No explanation. Nothing.

You start asking yourself: *Am I not interesting enough? Or were they just here for the free follow?*

Don't worry. You're not alone. And now, there's something you can do about it.

---

## Chapter 2: Meet gh-social

gh-social was born out of exactly that frustration.

Imagine having a small tool that does three simple things for you.

**First**, it helps you **follow back** everyone who follows you. No more opening profiles one by one, clicking follow, and closing tabs. Let the tool handle it.

**Second**, it helps you **stop following** people who never followed you back. The ghosts. The ones who only show up when they want something. It's time to say goodbye.

**Third**, if you're into a repository and want to know who else stars it, this tool can help you **follow them**. You might just find a community of people who share your interests.

---

## Chapter 3: Getting Started

Before we begin, there are a few things you'll need.

### What You Need

- **Python** version 3.10 or newer. Not sure? Type `python --version` in your terminal.
- **GitHub CLI** (`gh`). It's like a command-line version of GitHub. Don't have it? Visit [cli.github.com](https://cli.github.com/).
- A minute or two of your time.

### Installing

The easiest way:

```bash
pipx install gh-social
```

No `pipx`? `pip` works too:

```bash
pip install gh-social
```

### Setting Up

gh-social borrows your identity from the GitHub CLI. So make sure you're logged in:

```bash
gh auth login
```

Done? You're ready.

---

## Chapter 4: How to Use It

### The Easy Way

Type this in your terminal:

```bash
gh-social
```

You'll see a menu. Pick a number, answer a few simple questions, and let gh-social do the rest.

No commands to memorize. No flags to remember. Everything is right there in a friendly menu.

### The Quick Way

If you already know what you want, you can type commands directly:

```
gh-social follow somename
gh-social unfollow
gh-social stargazers somename/repo
```

But don't worry — everything can also be done from the interactive menu.

---

## Chapter 5: Good to Know

### Preview Before You Commit

gh-social has a feature called *dry-run*. It's like a preview mode where you can see what the tool is going to do **before** it actually does it.

Think of it like writing a text to your ex. There's a "send" button, but there's also a "preview" option. You can read what you wrote before you hit send.

Same idea here. You can see the list of people who will be followed or unfollowed before anything happens. Happy with it? Then go ahead.

Don't want dry-run? You don't have to. It's on by default — just turn it off when you're ready.

### Set a Limit

You don't have to process everyone at once. Say you only want to follow back 50 people for now:

```
gh-social follow somename --limit 50
```

Like ordering food. Start with 50. Want more? Order again.

### There Are Bots Too

Turns out, not every account on GitHub belongs to a human. Some are bots. gh-social can detect them and remove them from your lists. So you don't have to check each one manually.

---

## Chapter 6: Wrapping Up

GitHub should be fun. You meet new people, discover cool projects, and build things together.

But sometimes, the social side gets tiring. Especially when you feel like you're the only one putting in the effort.

gh-social is here to help with that. Not to replace human connection, but to handle the boring technical stuff — so you can focus on what actually matters: **building something cool.**

Happy socializing.

---

> *"I followed 50 people using gh-social. 48 followed back. The other 2? Maybe they're asleep. Or maybe that's just how it is."*

gh-social v1.2.7 — [MIT License](LICENSE)
