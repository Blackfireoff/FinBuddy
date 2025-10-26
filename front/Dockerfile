FROM node:lts-alpine

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "dev"]
#CMD [ "npx","serve","-s", "-l", "5173", "dist"]