FROM node:20  
WORKDIR /app  
ARG NEXT_PUBLIC_IP
ENV NEXT_PUBLIC_IP=$NEXT_PUBLIC_IP
COPY package*.json ./  
RUN npm i  
COPY . .  
RUN npm run build  
EXPOSE 3000
CMD ["npm", "start"]