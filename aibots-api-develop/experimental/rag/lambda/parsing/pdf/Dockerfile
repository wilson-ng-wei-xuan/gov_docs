FROM public.ecr.aws/lambda/python:3.9 as builder

# Prepare dev tools
RUN yum -y update
RUN yum -y install wget libstdc++ autoconf automake libtool autoconf-archive pkg-config gcc gcc-c++ make libjpeg-devel libpng-devel libtiff-devel zlib-devel
RUN yum group install -y "Development Tools"

# Build leptonica
WORKDIR /opt
RUN wget http://www.leptonica.org/source/leptonica-1.82.0.tar.gz
RUN ls -la
RUN tar -zxvf leptonica-1.82.0.tar.gz
WORKDIR ./leptonica-1.82.0
RUN ./configure
RUN make -j
RUN make install
RUN cd .. && rm leptonica-1.82.0.tar.gz

# Build tesseract
RUN wget https://github.com/tesseract-ocr/tesseract/archive/refs/tags/5.2.0.tar.gz
RUN tar -zxvf 5.2.0.tar.gz
WORKDIR ./tesseract-5.2.0
RUN ./autogen.sh
RUN PKG_CONFIG_PATH=/usr/local/lib/pkgconfig LIBLEPT_HEADERSDIR=/usr/local/include ./configure --with-extra-includes=/usr/local/include --with-extra-libraries=/usr/local/lib
RUN make install
RUN /sbin/ldconfig
RUN cd .. && rm 5.2.0.tar.gz

# install language packs
RUN wget https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
RUN mkdir -p /usr/local/share/tessdata
RUN mv eng.traineddata /usr/local/share/tessdata/

FROM public.ecr.aws/lambda/python:3.9

# Copy necessary files from the builder stage
COPY --from=builder /usr/local/bin/tesseract /usr/local/bin/tesseract
COPY --from=builder /usr/local/share/tessdata /usr/local/share/tessdata
COPY --from=builder /usr/local/lib/libtesseract* /usr/local/lib/
COPY --from=builder /usr/local/lib/liblept* /usr/local/lib/

# Additional dependencies for Tesseract
COPY --from=builder /usr/lib64/libjpeg.so.62 /usr/lib64/libjpeg.so.62
COPY --from=builder /usr/lib64/libjbig.so.2.0 /usr/lib64/libjbig.so.2.0
COPY --from=builder /usr/lib64/libtiff.so.5 /usr/lib64/libtiff.so.5
COPY --from=builder /usr/lib64/libgomp.so.1 /usr/lib64/libgomp.so.1

ENV PATH="/usr/local/bin:${PATH}"
ENV TESSDATA_PREFIX="/usr/local/share/tessdata/"
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/lib64:${LD_LIBRARY_PATH}"

# Verify Tesseract installation and environment variables
RUN echo "TESSDATA_PREFIX is set to $TESSDATA_PREFIX"
RUN echo "PATH is set to $PATH"
RUN echo "LD_LIBRARY_PATH is set to $LD_LIBRARY_PATH"
RUN ls -la /usr/local/bin/tesseract
RUN ls -la /usr/local/share/tessdata/
RUN ls -la /usr/local/lib/libtesseract*
RUN tesseract --version

# Install mesa-libGL and any other dependencies
#RUN yum install -y mesa-libGL
#RUN yum install git -y

# Set the working directory back to /var/task
WORKDIR /var/task

RUN yum install poppler-utils -y

COPY . /var/task

# Install requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -t .

# Create the /tmp directory and make it writable
RUN mkdir -p /tmp && chmod 777 /tmp

# Download NLTK data to the /tmp directory
RUN python -m nltk.downloader -d /tmp punkt averaged_perceptron_tagger

# Set environment variable for NLTK data
ENV NLTK_DATA=/tmp

CMD ["lambda_function.lambda_handler"]