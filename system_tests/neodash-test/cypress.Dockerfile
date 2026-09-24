ARG CYPRESS_IMAGE=cypress/browsers:node-20.18.0-chrome-130.0.6723.69-1-ff-131.0.3-edge-130.0.2849.52-1

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

# Install NodeJS packages (preserving cache at ~/.npm)
COPY --chown=$UID ./package*.json ./package-lock.json ./
RUN npm install

# Copy the tests
COPY --chown=$UID ./ ./

# Run the tests (exit code is 0 if all passes, else the number of tests failing, or 1 if configuration error)
CMD npm run test:run
