name: Build Android APK
on:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build APK
        uses: flet-dev/flet-build-action@v1
        with:
          target: apk
