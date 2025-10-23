FROM node:lts-alpine

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
VOLUME /app
EXPOSE 5173
CMD [ "npx","serve","-l", "5173", "dist"]