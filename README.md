# 🦖 Pose Capture

*A lightweight, motion-capture game architecture built for accessibility and low-resource machines.*

---

## ✨ Overview

This is a personal project I designed inspired by real-world use. My girlfriend works at an intermediate unit with developmentally disabled children, many of whom are non-verbal, but love dancing and moving to music and animals on TV. One child in particular loves pretending to be a dinosaur. So I thought, **why not let him actually be one?**

The goal of this project wasn’t to build a single polished game, but to design a **flexible, low-cost motion capture architecture** that can:

* Run on limited hardware (e.g. school-issued laptops)
* Support full-body movement and interaction
* Easily swap out games while reusing the same motion capture + character system

Unlike Unreal Engine or Unity solutions, this system is intentionally lightweight and purpose-built.

---

## 🎮 How It Works

1. The game runs on a computer.
2. A phone connects over **HTTPS** and acts as the camera.
3. A configuration screen allows scaling, cropping, and positioning.
4. The game starts.
5. The on-screen character mirrors the player’s movements in real time.

---

## 🧱 Tech Stack

* **Ultralytics YOLO v11n** – Pose tracking
* **Flask** - Web server & frame uploads
* **OpenCV** - Frame processing
* **Cloudflare Tunnel** - HTTPS remote camera access (`mcappy.org`)
* **Pygame** - Rendering & game logic

---

## 🧪 Tests

The `tests/` folder shows the system evolving step by step (I encourage you to run test 1 and 2):

* **Test 1** – Basic YOLO pose detection using a local camera
* **Test 2** – Manual keypoint drawing with Pygame
* **Test 3** – Remote camera capture via HTTPS + Cloudflare tunnel

These tests demonstrate how pose data moves from raw camera input to real-time game control.

---

## 📁 Project Structure

### Core

* **`app.py`** – Main entry point; starts Flask, Cloudflare tunnel, and game loop
* **`flask_app.py`** – Receives camera frames via POST
* **`cloudflared.py`** – Manages HTTPS tunnel for mcappy.org (stands for motion capture .py)

### Website

* **`index.html`** – Live camera preview + camera switch
* **`script.js`** – Frame upload loop, camera controls, basic access protection

### Game

* **`main.py`** – Game loop, sprite loading, and setup
* **`cam_configuration.py`** – Camera scaling/cropping UI with target box
* **`draw_character.py`** – Core pose-to-character rendering system
* **`meteor_game.py`** – Simple dinosaur game (collect eggs, avoid meteors)

The game can be swapped out easily without changing the motion capture pipeline.

---

## 🧠 Character Rendering Highlights

* Pose data is buffered and averaged to reduce flicker
* Movement is mapped using **relative screen percentages**, not raw pixels
* Appendages stretch between joints using sprites
* Torso and head use adaptive scaling and fallback logic when keypoints drop out

This keeps movement smooth and stable even with imperfect pose detection.

---

## ❤️ Why This Project Matters

This project was incredibly fun and meaningful to build. It combines technical problem-solving with real-world impact and accessibility.

Nearly all technologies used here were self-taught during development:

**Python, OpenCV, YOLO, Flask, Pygame, Cloudflare, JavaScript, HTTPS tunneling, remote camera capture, and pose detection.**

It showcases my ability to independently learn new tools, evaluate tradeoffs, and integrate them into a cohesive system designed around real constraints.

---

🦕 *Built with curiosity, persistence, and a lot of trial and error.*
