# use official node runtime as a parent image, slim as we only need basics
FROM node:19-slim

# set working directory
WORKDIR /fplfrog-server

# bundle app source
COPY . .

# install app dependencies
RUN npm install

# build app
RUN npm run build

# make port 3000 available to the outside world
EXPOSE 3000

# run the app
CMD node dist/index.js