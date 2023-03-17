# FPL Frog - Back end FPL web application

This is the FPL Frog back end web application for FPL, built with Node and TypeScript, Python and FireBase.

This server runs web scraping services that collect statistical data from across several sources, including xG data, that can be synced with users' FPL teams. Data is scraped and then sent to the connected Firebase account, which can then be accessed by the front end application.

The project is deployed with Docker.

## Project Status

This project is currently in production.

## Installation and Setup

Clone down this repository. You will need node and npm installed globally on your machine.

Installation:

        npm install

To Run Test Suite:

        npm test

To run a build:

        npm run build

To Start Server (ensure there is a build ready to be run):

        npm start

To Start Dev Server:

        npm run dev

To Visit App:

        localhost:5000/

## Deployment

The project is setup to be deployed using Docker, using a custom Dockerfile based off of the offical Node.JS "Slim" image. The Dockerfile is configured to install Node, Python3, Python3 Pip and all required Python packages.

You will need to have Docker installed on your system before running the following commands. You can get Docker [here](https://docs.docker.com/get-docker/).

To run the Docker build:

        docker build -t your-docker-username/your-chosen-tag-name

To run the Docker container locally on localhost:3000:

        docker container run -d -p 3000:3000 your-docker-username/your-chosen-tag-name
