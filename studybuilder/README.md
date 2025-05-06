# studybuilder

## General prerequisites

- Nodejs 16 or above is required to run this app. If you are using a
  debian based system and your installed version is too old, you can
  install a newer version using packages provided by Node's team
  ([Example](https://computingforgeeks.com/how-to-install-node-js-on-ubuntu-debian/)).

## Windows prerequisites to follow the project setup below
- Make sure nodejs and yarn have been installed with the help of a
  superuser (BJGI)
- vue-cli-service installed globally in anaconda. Open anaconda as administrator: yarn global add @vue/cli

## Ubuntu prerequisites

- A command called yarn is already installed on Ubuntu systems but it
  is not the right one. You must install the yarnpkg package instead
  and use it instead of yarn in the following examples.

```
sudo apt remove cmdtest
sudo apt remove yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt-get update
sudo apt-get install yarn -y
```

## Enable authentication

Edit the ``config.json`` file and update or define the following variables:
```
"OAUTH_ENABLED": "true",
"OAUTH_RBAC_ENABLED": "true",
"OAUTH_METADATA_URL": "<URL to the OpenID Connect Metadata document>",
"OAUTH_API_APP_ID": "<Application ID of the clinical-mdr-api>",
"OAUTH_UI_APP_ID": "<Applicaiton ID of StudyBuilder UI>",
```

## Project setup
```
yarn install
```

### Compiles and hot-reloads for development
```
yarn dev
```

### Compiles and minifies for production
```
yarn build
```

### Run your unit tests
```
yarn test:unit
```

### Run your integration tests
See [README.md of the system-tests repository.](https://dev.azure.com/orgremoved/Clinical-MDR/_git/system-tests)

### Lints and fixes files
```
yarn lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).


## Environments
Environment files contained in main directory are used to build proper environments in NN cloud please do not modify them:

```
.env.staging, .env.dev
```

unless you know what you are doing.



