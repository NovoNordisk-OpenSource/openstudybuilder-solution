ARG CYPRESS_IMAGE=cypress/browsers:node16.16.0-chrome107-ff107

FROM $CYPRESS_IMAGE

# Node user (uid:1000) is already created by default. Firefox refuses to run as root.
ARG UID=1000
RUN [ "x$UID" = "x1000" ] || { \
        echo "Changing uid & gid of node user to $UID" \
        && usermod --uid "$UID" node \
        && groupmod --gid "$UID" node \
    ;}

ARG WORKDIR=/tests
WORKDIR $WORKDIR
RUN chown "$UID" "$WORKDIR"

USER $UID

# Install NodeJS packages (preserving cache at ~/.cache/yarn)
COPY --chown=$UID ./package*.json ./yarn.lock ./
RUN yarn install

# Copy the tests
COPY --chown=$UID ./ ./

# Run the tests (exit code is 0 if all passes, else the number of tests failing, or 1 if configuration error)
CMD yarn run test:run
