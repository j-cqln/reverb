# Reverb

<img src="/static/assets/app/logo.png" alt="Reverb" width="50"/>

A music-sharing social media app

## Table of contents

- [Reverb](#reverb)
  - [Table of contents](#table-of-contents)
  - [Getting started](#getting-started)
  - [Features](#features)
  - [Team](#team)
  - [Acknowledgements](#acknowledgements)

## Getting started

### Running locally

Follow the [Spotify API guide](https://developer.spotify.com/documentation/web-api) to get credentials (`CLIENT_ID` and `CLIENT_SECRET`). When creating an app on the Spotify dashboard, set `Redirect URI` to `http://127.0.0.1/`. Create a `.env` file in the root directory. In this file, set `CLIENT_ID`, `CLIENT_SECRET`, and define `SECRET_KEY`, which can be any value.

Then, run `python server.py [port]` in the terminal to launch the app at `http://127.0.0.1:port`.

## Features

![Info image](/static/assets/docs/info.png)

Listen, discover, critique, curate, & share with friends

With Reverb, you can:
- Search for songs, albums, users, and their collections
- Review songs and albums, or enter a personal journal entry
- Create collections of songs and albums
- Customize your profile, add friends, and visit their pages
- Discover new music: popular on Spotify, Reverb trends, or friends' tunes
- Listen to a snippet of every song

## Team

[Jacqueline](https://github.com/j-cqln) - frontend, backend, UI/UX, database

[Jennifer](https://github.com/jennifer-jimenez) - backend, database design

[Jeff](https://github.com/jeffpham231) - frontend, backend

[Michael](https://github.com/MichaelOfodile) - frontend, backend

## Acknowledgements

Spotify, for use of the API and embedded music player widgets

CS 419 teaching staff, for support throughout the semester
