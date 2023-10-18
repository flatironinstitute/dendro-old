Here are some important notes for developers regarding the `vercel.json`
See: https://vercel.com/docs/projects/project-configuration

Note that there is a `_vercel_dev.json` and a `_vercel_prod.json`. One is required for local dev and the other is required for prod. In package.json, notice in the deploy script, the `_vercel_prod.json` gets copied onto `vercel.json` and then after the build, `_vercel_dev.json` gets copied onto the `vercel.json`. I'd like the `_vercel_dev.json` to be the one in the source repo.