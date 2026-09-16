FROM nginx:1.27-alpine
COPY . /usr/share/nginx/html
COPY default.conf.template /etc/nginx/templates/default.conf.template
ENV PORT=8080
EXPOSE 8080
