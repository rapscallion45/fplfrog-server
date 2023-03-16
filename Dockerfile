# use official node runtime as a parent image, slim as we only need the basics
FROM node:19-slim

# install python and package dependencies
RUN apt-get update || : && apt-get install python -y python3-pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -I \
    "numpy==1.24.2" "pandas==1.5.3" "requests==2.28.2" \
    "beautifulsoup4==4.11.2" "lxml==4.9.2" \
    "unidecode==1.3.6" "firebase_admin==6.1.0"

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