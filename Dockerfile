# Use the official Debian slim image as a base
# Pinned to trixie because LibreOffice comes from trixie-backports (PDF/UA-2 needs LibreOffice 25.8+)
FROM debian:trixie-slim

# Update system and install Python, LibreOffice Writer (without GUI), and fonts
# - fonts-crosextra-carlito / caladea are metric-compatible with Calibri / Cambria
# - fonts-liberation2 is metric-compatible with Arial, Times New Roman and Courier New
RUN echo "deb http://deb.debian.org/debian trixie-backports main" > /etc/apt/sources.list.d/backports.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    fontconfig \
    fonts-crosextra-caladea \
    fonts-crosextra-carlito \
    fonts-dejavu-core \
    fonts-liberation2 \
    && apt-get install -y --no-install-recommends -t trixie-backports \
    libreoffice-writer-nogui \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/doc-to-pdf/

# Create a virtual environment and install dependencies
ENV VIRTUAL_ENV=venv
RUN python3 -m venv venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY requirements.txt /usr/doc-to-pdf/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY config.json /usr/doc-to-pdf/
COPY src/ /usr/doc-to-pdf/src/

# License
COPY THIRD_PARTY_LICENSES.md /THIRD_PARTY_LICENSES.md
LABEL license="LibreOffice (MPL-2.0), Carlito, Caladea and Liberation fonts (OFL-1.1), DejaVu fonts (Bitstream Vera Fonts License)"

ENTRYPOINT ["/usr/doc-to-pdf/venv/bin/python3", "/usr/doc-to-pdf/src/main.py"]
