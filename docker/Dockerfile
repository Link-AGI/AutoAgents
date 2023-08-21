FROM tiangolo/uwsgi-nginx:python3.10

ENV LISTEN_PORT 7860
ENV USE_HTML_ROOT /app/autoagents/frontend/app

EXPOSE 7860

RUN chown -R 1000 /app /etc/nginx /usr/local/lib/python3.10/site-packages /usr/local/bin /var/log /var/run /etc/supervisor/conf.d /run /tmp /etc/uwsgi /var/cache /entrypoint.sh

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Install Python dependencies and install autoagents
RUN git clone https://github.com/LinkSoul-AI/AutoAgents autoagents && \
    cd autoagents && \
    pip install -r requirements.txt --user && \
    python setup.py install && \
    pip cache purge && \
    cp docker/prestart.sh /app/prestart.sh && \
    cp docker/entrypoint.sh /entrypoint.sh && \
    chmod +x /entrypoint.sh && \
    sed -i 's/nodaemon=true/nodaemon=true\nuser=user/g' /etc/supervisor/conf.d/supervisord.conf && \
    sed -i 's/nginx/user/g' /etc/uwsgi/uwsgi.ini && \
    sed -i 's/nginx;/user;/g' /etc/nginx/nginx.conf
