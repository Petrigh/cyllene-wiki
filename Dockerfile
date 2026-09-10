# Local preview of the GitHub Pages site.
# Mirrors what GitHub builds by using the `github-pages` gem from the Gemfile.
FROM ruby:3.3-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      ca-certificates \
      libssl-dev \
      zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /site

# Install gems in their own layer so editing wiki pages doesn't re-resolve them.
COPY Gemfile ./
RUN bundle install

# 4000 = site, 35729 = livereload
EXPOSE 4000 35729

CMD ["bundle", "exec", "jekyll", "serve", \
     "--host", "0.0.0.0", \
     "--port", "4000", \
     "--livereload", "--livereload-port", "35729", \
     "--force_polling", \
     "--incremental"]
