# FPL Frog - Back end FPL web application

This is the FPL Frog back end web application for FPL, built with Node and Typescript, Python and FireBase.

This server runs web scraping services that collect statistical data from across several sources, including xG data, that can be synced with users' FPL teams.

## Project Status

This project is currently in production. Data is scraped and then sent to the connected Firebase account, which can then be accessed by the front end application.

## Installation and Setup

Example:
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
