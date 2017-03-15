# Dockerfile for image cati/brainvisa-opensource:ubuntu-16.04-bug_fix

FROM cati/brainvisa-opensource:ubuntu-16.04-bug_fix 

RUN cd /tmp && \
    wget ftp://ftp.freedesktop.org/pub/mesa/mesa-17.0.0.tar.gz && \
    tar xvf mesa-17.0.0.tar.gz && \
    cd mesa-17.0.0 && \
    ./configure --enable-glx=xlib --disable-dri --disable-egl --with-gallium-drivers=swrast --disable-gbm --prefix=$HOME/mesa && \
    make && \
    make install && \
    cd .. && \
    rm -Rf mesa-17.0.0
    
USER root
RUN apt-get update && apt-get install -y tightvncserver wmaker x11-apps net-tools


USER brainvisa
RUN git clone https://github.com/novnc/noVNC.git
RUN git clone https://github.com/kanaka/websockify noVNC/utils/websockify
RUN echo 'write password' > /tmp/pwd && \
    echo 'read password' >> /tmp/pwd && \
    mkdir $HOME/.vnc && \
    cat /tmp/pwd | vncpasswd -f > $HOME/.vnc/passwd && \
    chmod go-r $HOME/.vnc/passwd && \
    rm /tmp/pwd
COPY vnc_xstartup /home/brainvisa/.vnc/xstartup

ENV USER=brainvisa
ENV LD_LIBRARY_PATH=/home/brainvisa/mesa/lib
COPY docker_entrypoint /home/brainvisa/docker_entrypoint
CMD ["/home/brainvisa/docker_entrypoint"]

EXPOSE 8080
