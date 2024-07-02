FROM effectiverange/er-devc-amd64:latest

ARG USERNAME=$USER
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user and get ownership of /opt/cross for package installation
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME && chown -R $USERNAME:$USERNAME /opt/debs /var/chroot/buildroot \
    && sed -ri "s/(users=.*)/\1,$USERNAME/g" /etc/schroot/chroot.d/buildroot

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libcamera-dev \
    python3-picamera2 \
    nfs-common \
    sudo \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Copy the project files
COPY . /home/$USERNAME/app
WORKDIR /home/$USERNAME/app

# Set the default user. Omit if you want to keep the default as root.
USER $USERNAME
