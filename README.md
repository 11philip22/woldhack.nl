<p align="center">
  <img src="static/favicon.svg" alt="woldhack logo" width="96" height="96">
</p>

# woldhack

Personal Hugo site for [woldhack.nl](https://woldhack.nl/), containing posts, project notes, and a small tools page. The site uses a custom local Hugo theme in `themes/woldhack`.

## Features

- Hugo-powered static site with posts, projects, about, and tools sections.
- Custom `woldhack` theme with dark/light mode, monospace styling, and generated canvas backgrounds.
- GitHub Pages deployment through GitHub Actions.
- Optional legacy `publish.sh` workflow for publishing to a `gh-pages` worktree.

## Getting Started

Install [Hugo Extended](https://gohugo.io/installation/) first. CI builds with Hugo `0.154.0`, and the local theme requires Hugo `0.146.0` or newer.

Run the site locally:

```sh
hugo server
```

Then open `http://localhost:1313/`.

Build the production site:

```sh
hugo --gc --minify --baseURL 'https://woldhack.nl/'
```

The generated site is written to `public/`.

> [!NOTE]
> `hugo.toml` uses `https://example.org/` as a placeholder `baseURL`. The deploy workflow overrides it with `https://woldhack.nl/`.

## Project Structure

| Path | Purpose |
| --- | --- |
| `content/` | Site content, grouped by section. |
| `content/posts/` | Blog posts. |
| `content/projects/` | Project pages. |
| `content/tools/` | Tools page. |
| `static/` | Favicons, web manifest, and static assets. |
| `themes/woldhack/` | Local Hugo theme, layouts, CSS, and JavaScript. |
| `.github/workflows/deploy.yml` | GitHub Pages deployment workflow. |
| `publish.sh` | Manual `gh-pages` publishing script. |

## Writing Content

Create a new post:

```sh
hugo new posts/my-post/index.md
```

Create a new project page:

```sh
hugo new projects/my-project.md
```

Update the front matter, set `draft: false` when the page is ready, then run `hugo server` to preview it.

## Deployment

Pushing to `master` runs `.github/workflows/deploy.yml`, builds the site with Hugo Extended, writes `static/CNAME`, uploads `public/`, and deploys to GitHub Pages.

For the manual `gh-pages` workflow, use:

```sh
./publish.sh
```

The script requires a clean working tree before it rebuilds and force-pushes the `gh-pages` branch.
