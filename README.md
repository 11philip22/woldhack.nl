<p align="center">
  <img src="static/favicon.svg" alt="woldhack logo" width="96" height="96">
</p>

# woldhack

Personal Hugo site for [woldhack.nl](https://woldhack.nl/), containing posts, project notes, and a small tools page. The site uses a custom local Hugo theme in `themes/woldhack`.

## Deployment

Pushing to `master` runs `.github/workflows/deploy.yml`, builds the site with Hugo Extended, writes `static/CNAME`, uploads `public/`, and deploys to GitHub Pages.

For the manual `gh-pages` workflow, use:

```sh
./publish.sh
```

The script requires a clean working tree before it rebuilds and force-pushes the `gh-pages` branch.
