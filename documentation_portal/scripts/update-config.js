#!/usr/bin/env node
// Script to update config.json from stdin to stdout interpolating with some environment variables

const fs = require('fs')

const args = process.argv.slice(2)

if (args.length < 1 || args.length > 2) {
  console.error('Requires one or two arguments: SRC.json [DST.json]')
  process.exit(1)
}

let conf = {}
if (args.length === 2) {
  conf = JSON.parse(fs.readFileSync(args.shift(), { encoding: 'utf8' }))
}

if (process.env.BUILD_NUMBER) {
  conf.BUILD_NUMBER = process.env.BUILD_NUMBER
}
if (process.env.BUILD_BRANCH) {
  conf.BUILD_BRANCH = process.env.BUILD_BRANCH
}
if (process.env.BUILD_COMMIT) {
  conf.BUILD_COMMIT = process.env.BUILD_COMMIT
}

fs.writeFileSync(args[0], JSON.stringify(conf, null, 4), { encoding: 'utf8' })

process.exit(0)
