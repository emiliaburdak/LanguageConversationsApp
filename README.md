# LanguageConversations 
Conversational application, which simulates real-time spoken dialogue

## Overview
This app, created using Flask, is made to mimic real conversations, using technologies like Speech-to-Text (STT) and Text-to-Speech (TTS), along with OpenAI's GPT-3.5-turbo model. It provides a full communication experience with easy-to-use features such as secure login with JWT tokens, improving sentences, giving example answer, translating using Deepl API, and creating personal dictionary filled with words and sentences you marked during conversations.

## Features
**Real-time Dialogue Simulation**: Utilizes STT and TTS for dynamic conversations.
- **OpenAI GPT-3.5 Integration**: Leverages the power of GPT-3.5-turbo for intelligent responses.
- **Secure Authentication**: Implements JWT tokens for secure access.
- **Sentence Enhancement**: Refines and improves user input sentences.
- **Hint Generation**:Provides example sentences when you're stuck, offering a starting point for your own custom replies.
- **Translation Capability**: Supports multiple languages through Deepl API and translate chosen words and sentences.
- **Personal Dictionary**: Enables users to effortlessly create a personal dictionary by simply clicking on a word.


## Prerequisites
Before you begin, ensure you have met the following requirements:
- You have installed the latest version of Python 3.
- The app integrates OpenAI's GPT-3.5-turbo model. You need to have an API key from OpenAI. Register and get your API key from OpenAI's website. 
- For the translation feature, a Deepl API key is required. Obtain it from Deepl's website.