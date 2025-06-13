#!/usr/bin/env bash
# Render의 리눅스 환경에서 headless Chrome 설치

apt-get update
apt-get install -y wget unzip curl gnupg
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb
